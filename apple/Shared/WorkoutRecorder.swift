import Combine
import CoreLocation
import Foundation
import HealthKit

#if os(watchOS)
  import WatchKit
#endif

final class WorkoutRecorder: NSObject, ObservableObject, HKWorkoutSessionDelegate,
  HKLiveWorkoutBuilderDelegate, CLLocationManagerDelegate
{
  let health = HKHealthStore()
  private let location = CLLocationManager()
  private var session: HKWorkoutSession?
  private var builder: HKLiveWorkoutBuilder?
  private var routeBuilder: HKWorkoutRouteBuilder?
  private var lastLocation: CLLocation?
  private var timer: Timer?
  private var started = Date()
  private var lapStart = 0.0
  private var lastHeartAt: Date?
  private var lastPower: Double?
  private var lastCadence: Double?
  private var lastPowerAt: Date?
  private var lastCadenceAt: Date?
  private var envelope: Envelope?
  private var progress = WorkoutProgress()
  private var locationPermission: CheckedContinuation<Void, Error>?
  @Published var ending = false
  @Published var starting = false
  @Published var lapMessage: String?
  var startDate: Date { started }
  var lapCount: Int { envelope?.recording.laps.count ?? 0 }
  var currentActivity: HKWorkoutActivityType? { session?.workoutConfiguration.activityType }
  var liveHeartRate: Double? {
    lastHeartAt.map { Date().timeIntervalSince($0) <= 15 } == true ? heartRate : nil
  }
  var routeStatus: String {
    if session?.workoutConfiguration.locationType == .indoor {
      return "Indoor workout · no GPS route"
    }
    return lastLocation.map { Date().timeIntervalSince($0.timestamp) <= 20 } == true
      ? "GPS ready" : "Finding GPS"
  }
  @Published var active = false
  @Published var paused = false
  @Published var elapsed = 0.0
  @Published var distance = 0.0
  @Published var heartRate: Double?
  @Published var error: String?
  @Published var savedMessage: String?
  @Published var lastCompletion: WorkoutCompletion?
  @Published var recovering = false
  var completed: (() -> Void)?
  var pace: String {
    // This is average active pace, not an instantaneous GPS estimate.
    let activeSeconds = activeDuration
    return distance > 0 ? DisplayUnits.pace(activeSeconds / distance * 1000) : "—"
  }
  var activeDuration: Double {
    activeDuration(at: Date())
  }
  func activeDuration(at date: Date) -> Double {
    progress.duration(at: max(0, date.timeIntervalSince(started)))
  }
  func restoreCompletion(account: String) {
    lastCompletion = CompletionDisk.latest(account: account)
  }
  override init() {
    super.init()
    location.delegate = self
    location.activityType = .fitness
    location.desiredAccuracy = kCLLocationAccuracyBest
    location.distanceFilter = 5
    #if os(iOS)
      location.allowsBackgroundLocationUpdates = true
      location.showsBackgroundLocationIndicator = true
    #endif
  }
  @MainActor func requestAccess(needsLocation: Bool = true) async throws {
    guard HKHealthStore.isHealthDataAvailable() else {
      throw NSError(
        domain: "Rint", code: 1,
        userInfo: [NSLocalizedDescriptionKey: "Apple Health is unavailable on this device."])
    }
    let read: Set<HKObjectType> = [
      HKObjectType.workoutType(), HKSeriesType.workoutRoute(), HKQuantityType(.heartRate),
      HKQuantityType(.distanceWalkingRunning), HKQuantityType(.distanceCycling),
      HKQuantityType(.distanceSwimming), HKQuantityType(.activeEnergyBurned),
      HKQuantityType(.cyclingPower), HKQuantityType(.runningPower), HKQuantityType(.cyclingCadence),
    ]
    let write: Set<HKSampleType> = [
      HKObjectType.workoutType(), HKSeriesType.workoutRoute(),
      HKQuantityType(.distanceWalkingRunning), HKQuantityType(.distanceCycling),
      HKQuantityType(.distanceSwimming), HKQuantityType(.activeEnergyBurned),
    ]
    try await health.requestAuthorization(toShare: write, read: read)
    guard needsLocation else { return }
    switch location.authorizationStatus {
    case .authorizedAlways, .authorizedWhenInUse: break
    case .notDetermined:
      try await withCheckedThrowingContinuation {
        (continuation: CheckedContinuation<Void, Error>) in
        locationPermission = continuation
        location.requestWhenInUseAuthorization()
      }
    default: throw locationAccessError()
    }
  }
  @MainActor func start(
    account: String, sportID: Int, activity: HKWorkoutActivityType = .running, indoor: Bool = false
  ) async {
    guard !active && !starting else { return }
    guard RecordingDisk.drafts().isEmpty else {
      error = "Recover or save your interrupted recording before starting another."
      return
    }
    starting = true
    defer { starting = false }
    do {
      try await requestAccess(needsLocation: !indoor)
      let configuration = HKWorkoutConfiguration()
      configuration.activityType = activity
      configuration.locationType = indoor ? .indoor : .outdoor
      let workoutSession = try HKWorkoutSession(healthStore: health, configuration: configuration)
      started = Date()
      elapsed = 0
      distance = 0
      lapStart = 0
      heartRate = nil
      error = nil
      savedMessage = nil
      lapMessage = nil
      ending = false
      progress = WorkoutProgress()
      envelope = Envelope(
        id: UUID(), sportID: sportID,
        title: "\(indoor ? "Indoor " : "")\(WorkoutKind.label(activity))",
        recording: Recording(
          startedAt: ISO8601DateFormatter().string(from: started), points: [Sample(t: 0, d: 0)]),
        account: account, healthActivity: activity.rawValue, indoor: indoor)
      attach(workoutSession, configuration: configuration)
      try await builder!.addMetadata([
        "RintRecordingID": envelope!.id.uuidString,
        HKMetadataKeyExternalUUID: envelope!.id.uuidString,
        HKMetadataKeySyncIdentifier: "org.rint.recording." + envelope!.id.uuidString,
        HKMetadataKeySyncVersion: 1,
      ])
      workoutSession.startActivity(with: started)
      try await builder!.beginCollection(at: started)
      active = true
      paused = false
      if !indoor {
        routeBuilder = HKWorkoutRouteBuilder(healthStore: health, device: .local())
        location.startUpdatingLocation()
      }
      checkpoint()
      startTimer()
    } catch {
      session?.end()
      timer?.invalidate()
      location.stopUpdatingLocation()
      self.error = error.localizedDescription
      active = false
      envelope = nil
      builder = nil
      session = nil
    }
  }
  private func attach(_ workoutSession: HKWorkoutSession, configuration: HKWorkoutConfiguration) {
    session = workoutSession
    session?.delegate = self
    builder = workoutSession.associatedWorkoutBuilder()
    builder?.delegate = self
    if builder?.dataSource == nil {
      builder?.dataSource = HKLiveWorkoutDataSource(
        healthStore: health, workoutConfiguration: configuration)
    }
    #if os(iOS)
      if configuration.locationType == .outdoor {
        builder?.dataSource?.disableCollection(for: distanceQuantity(configuration.activityType))
      }
    #endif
  }
  private func distanceQuantity(_ activity: HKWorkoutActivityType) -> HKQuantityType {
    HKQuantityType(
      activity == .cycling
        ? .distanceCycling : activity == .swimming ? .distanceSwimming : .distanceWalkingRunning)
  }
  private func startTimer() {
    timer?.invalidate()
    timer = Timer.scheduledTimer(withTimeInterval: 5, repeats: true) { [weak self] _ in
      self?.sample()
    }
  }
  private func sample(at date: Date = Date(), distanceSample: Bool = false) {
    guard active, var recording = envelope else { return }
    elapsed = max(0, date.timeIntervalSince(started))
    let freshHR = lastHeartAt.map { date.timeIntervalSince($0) <= 10 } ?? false
    recording.recording.points.append(
      Sample(
        t: elapsed, d: distanceSample ? distance : nil, active: !paused,
        heartRate: freshHR ? heartRate : nil,
        cadence: lastCadenceAt.map { date.timeIntervalSince($0) <= 10 } == true ? lastCadence : nil,
        power: lastPowerAt.map { date.timeIntervalSince($0) <= 10 } == true ? lastPower : nil))
    recording.recorderProgress = progress
    envelope = recording
    checkpoint()
  }
  private func checkpoint() {
    guard let envelope else { return }
    do { try RecordingDisk.save(envelope, draft: true) } catch {
      self.error = "Recording storage failed: \(error.localizedDescription)"
    }
  }
  func pauseOrResume() {
    guard let session else { return }
    if paused { session.resume() } else { session.pause() }
  }
  func lap() {
    guard active else { return }
    sample()
    let number = (envelope?.recording.laps.count ?? 0) + 1
    envelope?.recording.laps.append(Lap(start: lapStart, end: elapsed, name: "Lap \(number)"))
    lapStart = elapsed
    checkpoint()
    let event = HKWorkoutEvent(
      type: .lap, dateInterval: DateInterval(start: Date(), duration: 0), metadata: nil)
    builder?.addWorkoutEvents([event]) { _, _ in }
    lapMessage = "Lap \(number) marked"
    #if os(watchOS)
      WKInterfaceDevice.current().play(.click)
    #endif
  }
  @MainActor func finish() async {
    guard active, !ending, let builder, var envelope else { return }
    ending = true
    sample()
    envelope = self.envelope!
    timer?.invalidate()
    location.stopUpdatingLocation()
    session?.end()
    if elapsed > lapStart {
      envelope.recording.laps.append(
        Lap(start: lapStart, end: elapsed, name: "Lap \(envelope.recording.laps.count + 1)"))
    }
    // Retain the complete recording before HealthKit or networking can fail.
    var healthJob = HealthSaveJob(
      envelope: envelope,
      activity: session?.workoutConfiguration.activityType.rawValue
        ?? HKWorkoutActivityType.other.rawValue,
      indoor: session?.workoutConfiguration.locationType == .indoor,
      energyKcal: builder.statistics(for: HKQuantityType(.activeEnergyBurned))?.sumQuantity()?
        .doubleValue(for: .kilocalorie()))
    do {
      try RecordingDisk.save(envelope)
      try HealthSaveDisk.save(healthJob)
      let completion = WorkoutCompletion(
        id: envelope.id, account: envelope.account,
        title: envelope.title, distance: distance, elapsed: elapsed,
        active: min(elapsed, activeDuration(at: started.addingTimeInterval(elapsed))),
        heartRate: builder.statistics(for: HKQuantityType(.heartRate))?.averageQuantity()?
          .doubleValue(for: HKUnit.count().unitDivided(by: .minute())), finished: Date(),
        healthActivity: healthJob.activity)
      try CompletionDisk.save(completion)
      lastCompletion = completion
      HealthSaveQueue.shared.update()
    } catch {
      self.error = error.localizedDescription
      ending = false
      active = false
      return
    }
    do {
      try await builder.endCollection(at: Date())
      if let workout = try await builder.finishWorkout() {
        healthJob.workoutID = workout.uuid
        try HealthSaveDisk.save(healthJob)
        // Rebuild the full route from the durable stream, including points
        // collected before an app restart, rather than only the recovered tail.
        try await HealthSaveQueue.shared.saveRoute(healthJob, workout: workout)
        try HealthSaveDisk.complete(envelope.id)
        HealthSaveQueue.shared.update()
      }
    } catch {
      self.error =
        "Workout retained in Rint; Apple Health save retained for retry: \(error.localizedDescription)"
    }
    try? FileManager.default.removeItem(at: RecordingDisk.file(envelope.id, draft: true))
    active = false
    paused = false
    ending = false
    routeBuilder = nil
    lastLocation = nil
    self.envelope = nil
    savedMessage = "Saved on this device. Sync will resume automatically."
    #if os(watchOS)
      WKInterfaceDevice.current().play(.success)
    #endif
    completed?()
    WatchBridge.shared.transferPending()
  }
  func recover() {
    guard let url = RecordingDisk.drafts().first, let saved = try? RecordingDisk.load(url) else {
      return
    }
    recovering = true
    envelope = saved
    started = ISO8601DateFormatter().date(from: saved.recording.startedAt) ?? Date()
    distance = saved.recording.points.compactMap(\.d).max() ?? 0
    elapsed = saved.recording.points.map(\.t).max() ?? 0
    progress = saved.recorderProgress ?? WorkoutProgress.reconstruct(saved.recording.points)
    lapStart = saved.recording.laps.last?.end ?? 0
    health.recoverActiveWorkoutSession { [weak self] session, error in
      DispatchQueue.main.async {
        guard let self else { return }
        self.recovering = false
        if let session {
          self.attach(session, configuration: session.workoutConfiguration)
          self.active = true
          self.paused = session.state == .paused
          self.progress.setActive(!self.paused, at: self.elapsed)
          if session.workoutConfiguration.locationType == .outdoor {
            self.routeBuilder = HKWorkoutRouteBuilder(healthStore: self.health, device: .local())
            self.location.startUpdatingLocation()
          }
          self.startTimer()
          self.sample()
        } else {
          self.error =
            "An interrupted recording is retained. Save the recorded portion before starting again."
        }
      }
    }
  }
  @MainActor func saveInterrupted() {
    guard var envelope else { return }
    guard envelope.recording.points.count >= 2 else {
      error = "This recording has fewer than two samples; it remains retained for recovery."
      return
    }
    envelope.title += " (recovered)"
    do {
      try RecordingDisk.save(envelope)
      try HealthSaveDisk.save(
        HealthSaveJob(
          envelope: envelope,
          activity: envelope.healthActivity ?? HKWorkoutActivityType.other.rawValue,
          indoor: envelope.indoor ?? false))
      HealthSaveQueue.shared.update()
      let points = envelope.recording.points.sorted { $0.t < $1.t }
      let activeSeconds = zip(points, points.dropFirst()).reduce(0.0) {
        $0 + ($1.0.active ? max(0, $1.1.t - $1.0.t) : 0)
      }
      let completion = WorkoutCompletion(
        id: envelope.id, account: envelope.account, title: envelope.title,
        distance: max(0, (points.compactMap(\.d).max() ?? 0) - (points.compactMap(\.d).first ?? 0)),
        elapsed: max(0, (points.last?.t ?? 0) - (points.first?.t ?? 0)), active: activeSeconds,
        heartRate: nil, finished: Date(), healthActivity: envelope.healthActivity)
      try CompletionDisk.save(completion)
      lastCompletion = completion
      try FileManager.default.removeItem(at: RecordingDisk.file(envelope.id, draft: true))
      self.envelope = nil
      error = nil
      completed?()
      WatchBridge.shared.transferPending()
    } catch { self.error = error.localizedDescription }
  }
  func workoutSession(
    _ workoutSession: HKWorkoutSession, didChangeTo toState: HKWorkoutSessionState,
    from fromState: HKWorkoutSessionState, date: Date
  ) {
    DispatchQueue.main.async {
      self.paused = toState == .paused
      if toState == .paused || toState == .running {
        self.progress.setActive(
          toState == .running, at: max(0, date.timeIntervalSince(self.started)))
      }
      if self.paused { self.lastLocation = nil }
      #if os(watchOS)
        if toState == .paused || (toState == .running && fromState == .paused) {
          WKInterfaceDevice.current().play(.click)
        }
      #endif
      self.sample(at: date, distanceSample: true)
    }
  }
  func workoutSession(_ workoutSession: HKWorkoutSession, didFailWithError error: Error) {
    DispatchQueue.main.async {
      self.error =
        "Recording interrupted: \(error.localizedDescription). The recorded portion is retained."
    }
  }
  func workoutBuilderDidCollectEvent(_ workoutBuilder: HKLiveWorkoutBuilder) {}
  func workoutBuilder(
    _ workoutBuilder: HKLiveWorkoutBuilder, didCollectDataOf collectedTypes: Set<HKSampleType>
  ) {
    DispatchQueue.main.async {
      if collectedTypes.contains(HKQuantityType(.heartRate)),
        let value = workoutBuilder.statistics(for: HKQuantityType(.heartRate))?.mostRecentQuantity()
      {
        self.heartRate = value.doubleValue(for: HKUnit.count().unitDivided(by: .minute()))
        self.lastHeartAt = Date()
      }
      let activity = self.session?.workoutConfiguration.activityType ?? .running
      let distanceType = self.distanceQuantity(activity)
      var measuredDistance = false
      let powerType = HKQuantityType(activity == .cycling ? .cyclingPower : .runningPower)
      if collectedTypes.contains(powerType),
        let value = workoutBuilder.statistics(for: powerType)?.mostRecentQuantity()
      {
        self.lastPower = value.doubleValue(for: .watt())
        self.lastPowerAt = Date()
      }
      if collectedTypes.contains(HKQuantityType(.cyclingCadence)),
        let value = workoutBuilder.statistics(for: HKQuantityType(.cyclingCadence))?
          .mostRecentQuantity()
      {
        self.lastCadence = value.doubleValue(for: HKUnit.count().unitDivided(by: .minute()))
        self.lastCadenceAt = Date()
      }
      #if os(watchOS)
        if collectedTypes.contains(distanceType),
          let value = workoutBuilder.statistics(for: distanceType)?.sumQuantity()
        {
          self.distance += self.progress.distanceChange(
            raw: value.doubleValue(for: .meter()), active: !self.paused)
          measuredDistance = true
        }
      #else
        if collectedTypes.contains(distanceType),
          self.session?.workoutConfiguration.locationType == .indoor,
          let value = workoutBuilder.statistics(for: distanceType)?.sumQuantity()
        {
          self.distance += self.progress.distanceChange(
            raw: value.doubleValue(for: .meter()), active: !self.paused)
          measuredDistance = true
        }
      #endif
      self.sample(distanceSample: measuredDistance)
    }
  }
  private func locationAccessError() -> NSError {
    NSError(
      domain: "Rint", code: 2,
      userInfo: [
        NSLocalizedDescriptionKey:
          "Allow location in Rint settings for an outdoor route, or choose an indoor workout."
      ])
  }
  func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
    DispatchQueue.main.async {
      switch manager.authorizationStatus {
      case .authorizedAlways, .authorizedWhenInUse:
        let continuation = self.locationPermission
        self.locationPermission = nil
        continuation?.resume()
      case .denied, .restricted:
        let continuation = self.locationPermission
        self.locationPermission = nil
        continuation?.resume(throwing: self.locationAccessError())
        if self.active {
          self.error =
            "Location access is off. Your time and available sensors are still being recorded."
        }
      default: break
      }
    }
  }
  func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
    guard active, !paused else { return }
    let valid = locations.filter {
      $0.horizontalAccuracy >= 0 && $0.horizontalAccuracy <= 50
        && abs($0.timestamp.timeIntervalSinceNow) < 20
        && $0.timestamp >= started
    }
    var accepted: [CLLocation] = []
    for location in valid {
      if let lastLocation {
        let delta = location.timestamp.timeIntervalSince(lastLocation.timestamp)
        let step = location.distance(from: lastLocation)
        if delta <= 0 || step / delta > 30 { continue }
        #if os(iOS)
          distance += step
          let type = distanceQuantity(session?.workoutConfiguration.activityType ?? .running)
          let sample = HKQuantitySample(
            type: type, quantity: HKQuantity(unit: .meter(), doubleValue: step),
            start: lastLocation.timestamp, end: location.timestamp)
          builder?.add([sample]) { _, error in
            if let error {
              DispatchQueue.main.async {
                self.error = "Apple Health distance: \(error.localizedDescription)"
              }
            }
          }
        #endif
      }
      lastLocation = location
      accepted.append(location)
      let t = max(0, location.timestamp.timeIntervalSince(started))
      #if os(iOS)
        let measuredDistance: Double? = distance
      #else
        // Watch distance comes from Health's measurements, independently of GPS.
        let measuredDistance: Double? = nil
      #endif
      envelope?.recording.points.append(
        Sample(
          t: t, d: measuredDistance, lat: location.coordinate.latitude,
          lon: location.coordinate.longitude,
          elevation: location.verticalAccuracy >= 0 ? location.altitude : nil))
    }
    if !accepted.isEmpty {
      routeBuilder?.insertRouteData(accepted) { _, error in
        if let error { DispatchQueue.main.async { self.error = error.localizedDescription } }
      }
      checkpoint()
    }
  }
  func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
    DispatchQueue.main.async {
      self.error =
        "Route unavailable: \(error.localizedDescription). Timed sensor recording continues."
    }
  }
}
