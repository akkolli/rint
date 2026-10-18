import CoreLocation
import Foundation
import HealthKit

enum HealthConversion {
  static func sportLabel(type: HKWorkoutActivityType, indoor: Bool, pool: Bool) -> String {
    switch type {
    case .running: return indoor ? "Indoor Running" : "Running"
    case .cycling: return indoor ? "Indoor Cycling" : "Cycling (Sport)"
    case .walking: return "Walking"
    case .hiking: return "Hiking"
    case .swimming: return pool ? "Pool Swimming" : "Open Water Swimming"
    case .traditionalStrengthTraining, .functionalStrengthTraining: return "Strength Training"
    case .yoga: return "Yoga"
    case .rowing: return "Rowing"
    default: return "Workout"
    }
  }
  static func isWatch(_ workout: HKWorkout) -> Bool {
    (workout.sourceRevision.productType ?? "").lowercased().hasPrefix("watch")
      || (workout.device?.model ?? "").lowercased().contains("watch")
  }
  static func applyEvents(points: [Sample], events: [HKWorkoutEvent], start: Date, elapsed: Double)
    -> (points: [Sample], laps: [Lap])
  {
    let events = events.sorted { $0.dateInterval.start < $1.dateInterval.start }
    let timer = events.filter {
      [.pause, .resume, .motionPaused, .motionResumed].contains($0.type)
    }
    var points = points
    for event in timer {
      let t = event.dateInterval.start.timeIntervalSince(start)
      if (0...elapsed).contains(t) { points.append(Sample(t: t)) }
    }
    points.sort { $0.t < $1.t }
    var running = true
    var index = 0
    for p in points.indices {
      while index < timer.count
        && timer[index].dateInterval.start.timeIntervalSince(start) <= points[p].t
      {
        running = [.resume, .motionResumed].contains(timer[index].type)
        index += 1
      }
      points[p].active = running
    }
    var laps: [Lap] = []
    var lastLapEnd = 0.0
    for event in events where event.type == .lap || event.type == .segment {
      let a = max(0, event.dateInterval.start.timeIntervalSince(start))
      let b = min(elapsed, event.dateInterval.end.timeIntervalSince(start))
      let from = event.dateInterval.duration > 0 ? a : lastLapEnd
      let to = event.dateInterval.duration > 0 ? b : a
      if to > from && to <= elapsed {
        laps.append(
          Lap(
            start: from, end: to,
            name: "\(event.type == .lap ? "Lap" : "Interval") \(laps.count + 1)"))
        if event.type == .lap { lastLapEnd = to }
      }
    }
    return (points, laps)
  }
}

final class HealthWorkoutReader {
  let store: HKHealthStore
  init(store: HKHealthStore) { self.store = store }
  static let readTypes: Set<HKObjectType> = [
    HKObjectType.workoutType(), HKSeriesType.workoutRoute(), HKQuantityType(.heartRate),
    HKQuantityType(.distanceWalkingRunning), HKQuantityType(.distanceCycling),
    HKQuantityType(.distanceSwimming), HKQuantityType(.cyclingPower), HKQuantityType(.runningPower),
    HKQuantityType(.cyclingCadence), HKQuantityType(.activeEnergyBurned),
  ]
  func query<T: HKSample>(_ type: HKSampleType, predicate: NSPredicate?) async throws -> [T] {
    try await withCheckedThrowingContinuation { continuation in
      let query = HKSampleQuery(
        sampleType: type, predicate: predicate, limit: HKObjectQueryNoLimit,
        sortDescriptors: [NSSortDescriptor(key: HKSampleSortIdentifierStartDate, ascending: true)]
      ) {
        _, samples, error in
        if let error {
          continuation.resume(throwing: error)
        } else {
          continuation.resume(returning: samples as? [T] ?? [])
        }
      }
      store.execute(query)
    }
  }
  func workout(_ id: UUID) async throws -> HKWorkout? {
    let workouts: [HKWorkout] = try await query(
      HKObjectType.workoutType(),
      predicate: HKQuery.predicateForObject(with: id))
    return workouts.first
  }
  private func quantities(_ identifier: HKQuantityTypeIdentifier, workout: HKWorkout, unit: HKUnit)
    async throws -> [(Date, Double)]
  {
    // Expand quantity series: treating a condensed sample as one average loses the chart.
    let type = HKQuantityType(identifier)
    let workoutPredicate = HKQuery.predicateForObjects(from: workout)
    let samples: [HKQuantitySample] = try await query(type, predicate: workoutPredicate)
    var values: [(Date, Double)] = samples.filter { $0.count <= 1 }.map {
      ($0.endDate, $0.quantity.doubleValue(for: unit))
    }
    // Standalone cumulative samples do not necessarily have series entries.
    // Read them directly, and expand only condensed samples to avoid double counting.
    let seriesPredicate = NSCompoundPredicate(andPredicateWithSubpredicates: [
      workoutPredicate, NSPredicate(format: "%K > 1", HKPredicateKeyPathCount),
    ])
    let descriptor = HKQuantitySeriesSampleQueryDescriptor(
      predicate: .quantitySample(type: type, predicate: seriesPredicate))
    for try await result in descriptor.results(for: store) {
      values.append((result.dateInterval.end, result.quantity.doubleValue(for: unit)))
    }
    return values.sorted { $0.0 < $1.0 }
  }
  func envelope(_ workout: HKWorkout, sports: [SportChoice], account: String) async throws
    -> Envelope
  {
    let elapsed = workout.endDate.timeIntervalSince(workout.startDate)
    guard elapsed > 0, elapsed <= 7 * 86400 else {
      throw error("This workout has an unsupported duration.")
    }
    let indoor = workout.metadata?[HKMetadataKeyIndoorWorkout] as? Bool ?? false
    let pool =
      (workout.metadata?[HKMetadataKeySwimmingLocationType] as? NSNumber)?.intValue
      == HKWorkoutSwimmingLocationType.pool.rawValue
    let label = HealthConversion.sportLabel(
      type: workout.workoutActivityType, indoor: indoor, pool: pool)
    guard
      let sport = sports.first(where: { $0.label == label })
        ?? sports.first(where: { $0.label == "Workout" })
    else {
      throw error("Your server needs the \(label) or Workout sport. Update the server, then retry.")
    }
    var points = [Sample(t: 0), Sample(t: elapsed)]
    for (identifier, unit, field) in [
      (HKQuantityTypeIdentifier.heartRate, HKUnit.count().unitDivided(by: .minute()), "hr"),
      (.cyclingPower, .watt(), "power"), (.runningPower, .watt(), "power"),
      (.cyclingCadence, HKUnit.count().unitDivided(by: .minute()), "cadence"),
    ] {
      for (date, value) in try await quantities(identifier, workout: workout, unit: unit) {
        let t = date.timeIntervalSince(workout.startDate)
        guard (0...elapsed).contains(t), value.isFinite, value >= 0 else { continue }
        var p = Sample(t: t)
        if field == "hr" { p.heartRate = value }
        if field == "power" { p.power = value }
        if field == "cadence" { p.cadence = value }
        points.append(p)
      }
    }
    let distanceType: HKQuantityTypeIdentifier =
      workout.workoutActivityType == .cycling
      ? .distanceCycling
      : workout.workoutActivityType == .swimming ? .distanceSwimming : .distanceWalkingRunning
    let distances = try await quantities(distanceType, workout: workout, unit: .meter())
    var total = 0.0
    var distanceCount = 0
    for (date, distance) in distances {
      let t = date.timeIntervalSince(workout.startDate)
      guard t > 0, t <= elapsed, distance.isFinite, distance >= 0 else { continue }
      total += distance
      points.append(Sample(t: t, d: total))
      distanceCount += 1
    }
    let routes: [HKWorkoutRoute] = try await query(
      HKSeriesType.workoutRoute(),
      predicate: HKQuery.predicateForObjects(from: workout))
    var routeCount = 0
    for route in routes {
      for location in try await locations(route) {
        let t = location.timestamp.timeIntervalSince(workout.startDate)
        guard (0...elapsed).contains(t), location.horizontalAccuracy >= 0,
          location.horizontalAccuracy <= 100, CLLocationCoordinate2DIsValid(location.coordinate)
        else { continue }
        points.append(
          Sample(
            t: t, lat: location.coordinate.latitude, lon: location.coordinate.longitude,
            elevation: location.verticalAccuracy >= 0 ? location.altitude : nil))
        routeCount += 1
      }
    }
    let reportedDistance = workout.totalDistance?.doubleValue(for: .meter())
    var warnings: [String] = []
    let summaryOnly = distanceCount < 2 && routeCount < 2 && (reportedDistance ?? 0) > 0
    if distanceCount > 0 || summaryOnly {
      points[0].d = 0
      points[1].d = distanceCount > 0 ? total : reportedDistance
    }
    if summaryOnly {
      warnings.append(
        "Health provided only total distance. Splits and fastest efforts require a timed distance stream or route."
      )
    }
    if routeCount == 0 {
      warnings.append(
        "No readable route. This may be an indoor workout or route access may be limited.")
    }
    let events = HealthConversion.applyEvents(
      points: points, events: workout.workoutEvents ?? [],
      start: workout.startDate, elapsed: elapsed)
    if abs(workout.duration - elapsed) > 1
      && !(workout.workoutEvents ?? []).contains(where: {
        [.pause, .resume, .motionPaused, .motionResumed].contains($0.type)
      })
    {
      warnings.append(
        "Health's active duration differs from elapsed time, but pause events are unavailable. Rint cannot reconstruct pause locations."
      )
    }
    let origin = HealthOrigin(
      workoutID: workout.uuid, sourceBundle: workout.sourceRevision.source.bundleIdentifier,
      sourceName: workout.sourceRevision.source.name,
      productType: workout.sourceRevision.productType,
      activityType: workout.workoutActivityType.rawValue, indoor: indoor,
      syncIdentifier: workout.metadata?[HKMetadataKeySyncIdentifier] as? String,
      syncVersion: (workout.metadata?[HKMetadataKeySyncVersion] as? NSNumber)?.intValue,
      externalUUID: workout.metadata?[HKMetadataKeyExternalUUID] as? String,
      rintRecordingID: workout.metadata?["RintRecordingID"] as? String,
      activeEnergyKcal: workout.statistics(for: HKQuantityType(.activeEnergyBurned))?.sumQuantity()?
        .doubleValue(for: .kilocalorie()),
      reportedDuration: workout.duration, reportedDistanceM: reportedDistance, warnings: warnings)
    let recording = Recording(
      startedAt: ISO8601DateFormatter().string(from: workout.startDate),
      points: events.points, laps: events.laps, summaryOnly: summaryOnly)
    return Envelope(
      id: try HealthIdentity.deliveryID(account: account, origin: origin, recording: recording),
      sportID: sport.id, title: "Apple Health \(WorkoutKind.label(workout.workoutActivityType))",
      recording: recording, account: account, healthOrigin: origin)
  }
  private func locations(_ route: HKWorkoutRoute) async throws -> [CLLocation] {
    try await withCheckedThrowingContinuation { continuation in
      var collected: [CLLocation] = []
      var completed = false
      let query = HKWorkoutRouteQuery(route: route) { _, locations, done, error in
        guard !completed else { return }
        if let error {
          completed = true
          continuation.resume(throwing: error)
          return
        }
        collected += locations ?? []
        if done {
          completed = true
          continuation.resume(returning: collected)
        }
      }
      store.execute(query)
    }
  }
  private func error(_ message: String) -> NSError {
    NSError(domain: "Rint.Health", code: 0, userInfo: [NSLocalizedDescriptionKey: message])
  }
}
