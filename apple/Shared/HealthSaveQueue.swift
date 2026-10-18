import Combine
import CoreLocation
import Foundation
import HealthKit

struct HealthSaveJob: Codable {
  let envelope: Envelope
  let activity: UInt
  let indoor: Bool
  var energyKcal: Double? = nil
  var workoutID: UUID? = nil
}
/// Independent of the server outbox: a successful upload must not discard a
/// failed Health save. Sync identifiers make retries safe after process death.
enum HealthSaveDisk {
  static var directory: URL {
    let url = RecordingDisk.directory.appendingPathComponent("Health saves", isDirectory: true)
    try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
    return url
  }
  static func file(_ id: UUID) -> URL { directory.appendingPathComponent(id.uuidString + ".json") }
  static func save(_ job: HealthSaveJob) throws {
    try RecordingDisk.encoder.encode(job).write(
      to: file(job.envelope.id),
      options: [.atomic, .completeFileProtectionUntilFirstUserAuthentication])
  }
  static func pending() -> [URL] {
    ((try? FileManager.default.contentsOfDirectory(at: directory, includingPropertiesForKeys: nil))
      ?? []).filter { $0.pathExtension == "json" }
  }
  static func load(_ url: URL) throws -> HealthSaveJob {
    try JSONDecoder().decode(HealthSaveJob.self, from: Data(contentsOf: url))
  }
  static func complete(_ id: UUID) throws { try FileManager.default.removeItem(at: file(id)) }
  static func metadata(_ id: UUID, suffix: String = "") -> [String: Any] {
    [
      "RintRecordingID": id.uuidString, HKMetadataKeyExternalUUID: id.uuidString,
      HKMetadataKeySyncIdentifier: "org.rint.recording." + id.uuidString + suffix,
      HKMetadataKeySyncVersion: 1,
    ]
  }
  static func distanceIntervals(_ points: [Sample]) -> [(
    start: Double, end: Double, meters: Double
  )] {
    let anchors = points.filter { $0.d != nil }.sorted { $0.t < $1.t }
    return zip(anchors, anchors.dropFirst()).compactMap { previous, point in
      guard let a = previous.d, let b = point.d, b > a, point.t > previous.t,
        previous.active, point.distanceGap != true, previous.distanceGap != true
      else { return nil }
      return (start: previous.t, end: point.t, meters: b - a)
    }
  }
}
@MainActor final class HealthSaveQueue: ObservableObject {
  static let shared = HealthSaveQueue()
  @Published var pending = HealthSaveDisk.pending().count
  @Published var retrying = false
  @Published var error: String?
  private let health = HKHealthStore()
  func update() { pending = HealthSaveDisk.pending().count }
  func retry(account: String) async {
    guard !retrying else { return }
    retrying = true
    error = nil
    defer {
      retrying = false
      update()
    }
    for url in HealthSaveDisk.pending() {
      do {
        var job = try HealthSaveDisk.load(url)
        guard job.envelope.account == account else { continue }
        guard health.authorizationStatus(for: HKObjectType.workoutType()) == .sharingAuthorized
        else {
          throw NSError(
            domain: "Rint", code: 1,
            userInfo: [
              NSLocalizedDescriptionKey:
                "Allow Rint to write workouts in Health permissions, then retry. Your recording remains saved."
            ])
        }
        let workout: HKWorkout
        if let existing = try await existingWorkout(job) {
          workout = existing
        } else {
          workout = try await rebuildWorkout(job)
        }
        job.workoutID = workout.uuid
        try HealthSaveDisk.save(job)
        try await saveRoute(job, workout: workout)
        try HealthSaveDisk.complete(job.envelope.id)
      } catch { self.error = error.localizedDescription }
    }
  }
  private func existingWorkout(_ job: HealthSaveJob) async throws -> HKWorkout? {
    let predicate =
      job.workoutID.map { HKQuery.predicateForObject(with: $0) }
      ?? HKQuery.predicateForObjects(
        withMetadataKey: "RintRecordingID", allowedValues: [job.envelope.id.uuidString])
    return try await withCheckedThrowingContinuation { continuation in
      health.execute(
        HKSampleQuery(
          sampleType: .workoutType(), predicate: predicate, limit: 1, sortDescriptors: nil
        ) { _, samples, error in
          if let error {
            continuation.resume(throwing: error)
          } else {
            continuation.resume(returning: samples?.first as? HKWorkout)
          }
        })
    }
  }
  private func rebuildWorkout(_ job: HealthSaveJob) async throws -> HKWorkout {
    guard let start = ISO8601DateFormatter().date(from: job.envelope.recording.startedAt),
      let last = job.envelope.recording.points.last, last.t > 0
    else { throw CocoaError(.fileReadCorruptFile) }
    let configuration = HKWorkoutConfiguration()
    configuration.activityType = HKWorkoutActivityType(rawValue: job.activity) ?? .other
    configuration.locationType = job.indoor ? .indoor : .outdoor
    let builder = HKWorkoutBuilder(
      healthStore: health, configuration: configuration, device: .local())
    try await builder.beginCollection(at: start)
    try await builder.addMetadata(HealthSaveDisk.metadata(job.envelope.id))
    let distanceType = HKQuantityType(
      configuration.activityType == .cycling
        ? .distanceCycling
        : configuration.activityType == .swimming ? .distanceSwimming : .distanceWalkingRunning)
    var samples: [HKQuantitySample] = []
    var events: [HKWorkoutEvent] = []
    for (index, interval) in HealthSaveDisk.distanceIntervals(job.envelope.recording.points)
      .enumerated()
    {
      samples.append(
        HKQuantitySample(
          type: distanceType, quantity: HKQuantity(unit: .meter(), doubleValue: interval.meters),
          start: start.addingTimeInterval(interval.start),
          end: start.addingTimeInterval(interval.end),
          metadata: HealthSaveDisk.metadata(job.envelope.id, suffix: ".distance.\(index)")))
    }
    for pair in zip(
      job.envelope.recording.points, job.envelope.recording.points.dropFirst()
    ) {
      let (previous, point) = pair
      if previous.active != point.active {
        events.append(
          HKWorkoutEvent(
            type: point.active ? .resume : .pause,
            dateInterval: DateInterval(start: start.addingTimeInterval(point.t), duration: 0),
            metadata: nil))
      }
    }
    if let energy = job.energyKcal, energy > 0 {
      samples.append(
        HKQuantitySample(
          type: HKQuantityType(.activeEnergyBurned),
          quantity: HKQuantity(unit: .kilocalorie(), doubleValue: energy), start: start,
          end: start.addingTimeInterval(last.t),
          metadata: HealthSaveDisk.metadata(job.envelope.id, suffix: ".energy")))
    }
    events += job.envelope.recording.laps.map {
      HKWorkoutEvent(
        type: .lap,
        dateInterval: DateInterval(start: start.addingTimeInterval($0.end), duration: 0),
        metadata: nil)
    }
    if !samples.isEmpty { try await builder.addSamples(samples) }
    if !events.isEmpty { try await builder.addWorkoutEvents(events) }
    try await builder.endCollection(at: start.addingTimeInterval(last.t))
    guard let workout = try await builder.finishWorkout() else {
      throw CocoaError(.fileWriteUnknown)
    }
    return workout
  }
  func saveRoute(_ job: HealthSaveJob, workout: HKWorkout) async throws {
    guard let start = ISO8601DateFormatter().date(from: job.envelope.recording.startedAt) else {
      throw CocoaError(.fileReadCorruptFile)
    }
    let locations = job.envelope.recording.points.compactMap { point -> CLLocation? in
      guard let lat = point.lat, let lon = point.lon, lat.isFinite, lon.isFinite else { return nil }
      return CLLocation(
        coordinate: CLLocationCoordinate2D(latitude: lat, longitude: lon),
        altitude: point.elevation ?? 0, horizontalAccuracy: 5,
        verticalAccuracy: point.elevation == nil ? -1 : 5,
        timestamp: start.addingTimeInterval(point.t))
    }
    guard !locations.isEmpty else { return }
    let route = HKWorkoutRouteBuilder(healthStore: health, device: .local())
    for offset in stride(from: 0, to: locations.count, by: 500) {
      try await route.insertRouteData(Array(locations[offset..<min(offset + 500, locations.count)]))
    }
    _ = try await route.finishRoute(
      with: workout, metadata: HealthSaveDisk.metadata(job.envelope.id, suffix: ".route"))
  }
}
