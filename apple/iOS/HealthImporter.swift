import Combine
import Foundation
import HealthKit

@MainActor final class HealthImporter: ObservableObject {
  static let shared = HealthImporter()
  private let store = HKHealthStore()
  private lazy var reader = HealthWorkoutReader(store: store)
  private var observers: [HKObserverQuery] = []
  private var syncTask: Task<Void, Never>?
  private var anotherPass = false
  private var stateAccount = ""
  @Published private(set) var state = HealthSyncState()
  @Published private(set) var busy = false
  @Published private(set) var message = ""
  @Published private(set) var previewCount: Int?
  @Published private(set) var processed = 0
  @Published private(set) var total = 0
  @Published private(set) var reviews: [Envelope] = []

  func restore() {
    let account = APIClient.shared.account
    guard stateAccount != account else {
      refreshReviews()
      return
    }
    stopObserving()
    stateAccount = account
    do { state = try HealthSyncState.load(account: account) } catch {
      state = HealthSyncState()
      message = "Saved Health progress could not be read. Reconnect to safely scan again."
    }
    previewCount = nil
    refreshReviews()
  }
  func connect(watchOnly: Bool, since: Date?) async {
    guard HKHealthStore.isHealthDataAvailable(), APIClient.shared.signedIn, !busy else { return }
    restore()
    let account = stateAccount
    busy = true
    defer { busy = false }
    do {
      try await store.requestAuthorization(toShare: [], read: HealthWorkoutReader.readTypes)
      guard current(account) else { return }
      // Read permissions can expand without HealthKit reporting their status.
      // Reviewing access rescans using stable server identities.
      state.anchor = nil
      state.historyComplete = false
      if state.watchOnly != watchOnly || state.since != since {
        state.pendingIDs = []
        state.failures = [:]
        state.historyComplete = false
      }
      state.connected = true
      state.watchOnly = watchOnly
      state.since = since
      try state.save(account: account)
      let workouts: [HKWorkout] = try await reader.query(
        HKObjectType.workoutType(), predicate: predicate())
      guard current(account) else { return }
      previewCount = workouts.filter { !watchOnly || HealthConversion.isWatch($0) }.count
      message =
        previewCount == 0
        ? "No accessible workouts. Health permissions may be limited, or there may be no matching history."
        : "\(previewCount!) accessible workouts. New imports are private until you choose to share them."
    } catch { if current(account) { message = error.localizedDescription } }
  }
  func setAutomatic(_ enabled: Bool) {
    restore()
    guard state.connected else { return }
    state.automatic = enabled
    do { try state.save(account: stateAccount) } catch {
      message = error.localizedDescription
      state.automatic = false
    }
    if state.automatic {
      observe()
      Task { await synchronize(refreshRecent: true) }
    } else {
      stopObserving()
    }
  }
  func disconnect() {
    restore()
    state.connected = false
    state.automatic = false
    do { try state.save(account: stateAccount) } catch { message = error.localizedDescription }
    stopObserving()
    message = "Health sync disconnected. Imported activities and retained uploads are kept."
  }
  func observe() {
    restore()
    guard APIClient.shared.signedIn, state.connected, state.automatic, observers.isEmpty else {
      return
    }
    // Installed at app launch, including launches made by HealthKit in the background.
    for type in [HKObjectType.workoutType(), HKSeriesType.workoutRoute()] as [HKSampleType] {
      let query = HKObserverQuery(sampleType: type, predicate: nil) {
        [weak self] _, completion, error in
        Task { @MainActor in
          defer { completion() }
          guard let self else { return }
          if let error {
            self.message = "Health update failed: \(error.localizedDescription)"
            return
          }
          await self.synchronize(refreshRecent: true)
        }
      }
      observers.append(query)
      store.execute(query)
      store.enableBackgroundDelivery(for: type, frequency: .immediate) {
        [weak self] success, error in
        if !success {
          Task { @MainActor in
            self?.message =
              "Background Health delivery is unavailable: \(error?.localizedDescription ?? "open Rint to catch up")"
          }
        }
      }
    }
  }
  func stopObserving() {
    for query in observers { store.stop(query) }
    observers = []
    for type in [HKObjectType.workoutType(), HKSeriesType.workoutRoute()] as [HKObjectType] {
      store.disableBackgroundDelivery(for: type) { _, _ in }
    }
  }
  func synchronize(refreshRecent: Bool = false) async {
    restore()
    guard state.connected, APIClient.shared.signedIn else { return }
    if let syncTask {
      anotherPass = true
      await syncTask.value
      return
    }
    // Permission/history review owns the journal while its query is running.
    guard !busy else { return }
    let account = stateAccount
    let task = Task { await run(account: account, refreshRecent: refreshRecent) }
    syncTask = task
    await task.value
    syncTask = nil
  }
  func rescanHistory() async {
    restore()
    guard !busy else { return }
    state.anchor = nil
    state.historyComplete = false
    do {
      try state.save(account: stateAccount)
      await synchronize()
    } catch { message = error.localizedDescription }
  }
  private func run(account: String, refreshRecent: Bool) async {
    busy = true
    processed = 0
    total = state.pendingIDs.count
    var attempted = Set<UUID>()
    defer {
      busy = false
      SyncQueue.shared.sync()
      refreshReviews()
    }
    do {
      repeat {
        anotherPass = false
        guard current(account), state.connected else { return }
        if APIClient.shared.sports.isEmpty { await APIClient.shared.refresh() }
        // Recent rereads pick up routes and sensor samples that arrive after the workout.
        if refreshRecent {
          let recent = max(state.since ?? .distantPast, Date().addingTimeInterval(-7 * 86400))
          let workouts: [HKWorkout] = try await reader.query(
            HKObjectType.workoutType(),
            predicate:
              HKQuery.predicateForSamples(withStart: recent, end: nil))
          guard current(account) else { return }
          for workout in workouts where !state.watchOnly || HealthConversion.isWatch(workout) {
            if !state.pendingIDs.contains(workout.uuid) { state.pendingIDs.append(workout.uuid) }
          }
          try state.save(account: account)
        }
        var more = true
        while more {
          guard current(account), state.connected else { return }
          let anchor =
            try state.anchor.map {
              try NSKeyedUnarchiver.unarchivedObject(ofClass: HKQueryAnchor.self, from: $0)
            } ?? nil
          let result = try await HKAnchoredObjectQueryDescriptor(
            predicates: [.workout(predicate())],
            anchor: anchor, limit: 50
          ).result(for: store)
          guard current(account) else { return }
          let anchorData = try NSKeyedArchiver.archivedData(
            withRootObject: result.newAnchor, requiringSecureCoding: true)
          state.checkpoint(
            ids: result.addedSamples.filter { !state.watchOnly || HealthConversion.isWatch($0) }
              .map(\.uuid),
            deleted: result.deletedObjects.map(\.uuid), anchor: anchorData)
          // Advance the anchor only alongside durable jobs. A crash cannot strand a workout.
          try state.save(account: account)
          total = max(total, processed + state.pendingIDs.count)
          await processPending(account: account, attempted: &attempted)
          more = result.addedSamples.count + result.deletedObjects.count >= 50
        }
        guard current(account) else { return }
        state.historyComplete = true
        state.lastChecked = Date()
        try state.save(account: account)
        message =
          state.revisions.isEmpty && state.pendingIDs.isEmpty
          ? "No accessible workouts. Health permissions may be limited, or there may be no matching history."
          : state.failures.isEmpty
            ? "Health history checked. See upload status below."
            : "\(state.failures.count) workouts need another attempt. Successful imports are retained."
      } while anotherPass && current(account) && state.connected
    } catch {
      if current(account) {
        message = "Health sync paused: \(error.localizedDescription). Saved progress is retained."
      }
    }
  }
  private func processPending(account: String, attempted: inout Set<UUID>) async {
    for id in state.pendingIDs where !attempted.contains(id) {
      attempted.insert(id)
      guard current(account), state.connected else { return }
      do {
        guard let workout = try await reader.workout(id) else {
          state.failures[id.uuidString] =
            "This workout is no longer readable in Health. Review permissions or rescan history."
          try state.save(account: account)
          continue
        }
        let envelope = try await reader.envelope(
          workout, sports: APIClient.shared.sports, account: account)
        guard current(account), state.connected else { return }
        if state.revisions[id.uuidString] != envelope.id { try RecordingDisk.save(envelope) }
        state.retained(id, revision: envelope.id)
        try state.save(account: account)
      } catch {
        guard current(account) else { return }
        state.failures[id.uuidString] = error.localizedDescription
        do { try state.save(account: account) } catch {
          message = "Could not save Health progress: \(error.localizedDescription)"
          return
        }
      }
      processed += 1
    }
  }
  func refreshReviews() {
    reviews = RecordingDisk.pending(account: APIClient.shared.account, needsReview: true).compactMap
    { try? RecordingDisk.load($0) }.filter {
      $0.account == APIClient.shared.account && $0.duplicateCandidates != nil
    }
  }
  func resolve(_ envelope: Envelope, workoutID: String?) {
    guard envelope.account == APIClient.shared.account else { return }
    var resolved = envelope
    resolved.duplicateWorkoutID = workoutID
    resolved.keepSeparate = workoutID == nil
    resolved.duplicateCandidates = nil
    do {
      try RecordingDisk.save(resolved)
      refreshReviews()
      SyncQueue.shared.sync(force: true)
    } catch { message = error.localizedDescription }
  }
  private func current(_ account: String) -> Bool {
    APIClient.shared.signedIn && APIClient.shared.account == account && stateAccount == account
  }
  private func predicate() -> NSPredicate? {
    state.since.map { HKQuery.predicateForSamples(withStart: $0, end: nil) }
  }
}
