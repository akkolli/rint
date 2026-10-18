import Foundation
import HealthKit
import XCTest

@testable import Rint

final class HealthImportTests: XCTestCase {
  func testOutboxIndexTracksReviewDecisionsAndCanRecoverLegacyFiles() throws {
    let id = UUID()
    let legacyID = UUID()
    let account = "index-test|" + UUID().uuidString
    var envelope = Envelope(
      id: id, sportID: 1, title: "Watch run",
      recording: Recording(
        startedAt: "2026-01-01T00:00:00Z", points: [Sample(t: 0), Sample(t: 60)]),
      account: account,
      duplicateCandidates: [
        HealthDuplicate(id: "existing", title: "Run", startedAt: "2026-01-01T00:00:00Z")
      ])
    defer {
      try? RecordingDisk.acknowledge(id)
      try? RecordingDisk.acknowledge(legacyID)
    }
    try RecordingDisk.save(envelope)
    XCTAssertTrue(RecordingDisk.pending(account: account, needsReview: false).isEmpty)
    XCTAssertEqual(RecordingDisk.pending(account: account, needsReview: true).count, 1)
    envelope.duplicateCandidates = nil
    envelope.keepSeparate = true
    try RecordingDisk.save(envelope)
    XCTAssertEqual(RecordingDisk.pending(account: account, needsReview: false).count, 1)
    XCTAssertTrue(RecordingDisk.pending(account: account + "-other").isEmpty)
    envelope.id = legacyID
    // Pre-upgrade/crash-recovered recordings have no header; rebuilding keeps them eligible.
    try RecordingDisk.encoder.encode(envelope).write(
      to: RecordingDisk.file(legacyID), options: .atomic)
    XCTAssertEqual(RecordingDisk.pending(account: account, needsReview: false).count, 2)
    try RecordingDisk.acknowledge(id)
    XCTAssertEqual(RecordingDisk.pending(account: account).count, 1)
  }
  private func origin(_ id: UUID) -> HealthOrigin {
    HealthOrigin(
      workoutID: id, sourceBundle: "com.apple.health", sourceName: "Apple Watch",
      productType: "Watch7,1", activityType: HKWorkoutActivityType.running.rawValue,
      indoor: false, reportedDuration: 600)
  }
  func testAccountAndRevisionOutboxesCannotOverwriteOrAcknowledgeEachOther() throws {
    let source = origin(UUID())
    let old = Recording(
      startedAt: "2026-10-10T12:00:00Z",
      points: [Sample(t: 0, d: 0), Sample(t: 600, d: 3000)])
    var richer = old
    richer.points[1].heartRate = 145
    let firstID = try HealthIdentity.deliveryID(
      account: "server|alice", origin: source, recording: old)
    let revisionID = try HealthIdentity.deliveryID(
      account: "server|alice", origin: source, recording: richer)
    let otherID = try HealthIdentity.deliveryID(
      account: "server|bob", origin: source, recording: old)
    XCTAssertEqual(
      firstID,
      try HealthIdentity.deliveryID(account: "server|alice", origin: source, recording: old))
    XCTAssertNotEqual(firstID, revisionID)
    XCTAssertNotEqual(firstID, otherID)
    for (id, recording, account) in [
      (firstID, old, "server|alice"), (revisionID, richer, "server|alice"),
      (otherID, old, "server|bob"),
    ] {
      try RecordingDisk.save(
        Envelope(
          id: id, sportID: 1, title: "Watch run", recording: recording,
          account: account, healthOrigin: source))
    }
    defer {
      try? RecordingDisk.acknowledge(revisionID)
      try? RecordingDisk.acknowledge(otherID)
    }
    try RecordingDisk.acknowledge(firstID)
    XCTAssertEqual(
      try RecordingDisk.load(RecordingDisk.file(revisionID)).recording.points[1].heartRate, 145)
    XCTAssertEqual(try RecordingDisk.load(RecordingDisk.file(otherID)).account, "server|bob")
  }
  func testAnchorAndUnfinishedJobsSurviveRestartAndFailedRead() throws {
    let account = "health-test|" + UUID().uuidString
    defer { try? FileManager.default.removeItem(at: HealthSyncState.file(account: account)) }
    let first = UUID()
    let second = UUID()
    let deleted = UUID()
    var state = HealthSyncState()
    state.connected = true
    state.automatic = true
    state.pendingIDs = [deleted]
    state.checkpoint(ids: [first, first, second], deleted: [deleted], anchor: Data([1, 2, 3]))
    try state.save(account: account)
    var restarted = try HealthSyncState.load(account: account)
    XCTAssertEqual(restarted.anchor, Data([1, 2, 3]))
    XCTAssertEqual(restarted.pendingIDs, [first, second])
    restarted.failures[second.uuidString] = "Health is locked; retry after unlocking."
    restarted.retained(first, revision: UUID())
    try restarted.save(account: account)
    let retry = try HealthSyncState.load(account: account)
    XCTAssertEqual(retry.pendingIDs, [second])
    XCTAssertEqual(retry.failures.count, 1)
    XCTAssertTrue(retry.automatic)
    XCTAssertTrue(try HealthSyncState.load(account: account + "-other").pendingIDs.isEmpty)
  }
  func testManualAndAutomaticPausesCarryAcrossSensorOnlySamples() {
    let start = Date(timeIntervalSince1970: 1000)
    let events: [HKWorkoutEvent] = [
      event(.pause, at: 10, start: start), event(.resume, at: 20, start: start),
      event(.motionPaused, at: 30, start: start), event(.motionResumed, at: 40, start: start),
    ]
    let result = HealthConversion.applyEvents(
      points: [
        Sample(t: 0), Sample(t: 15, heartRate: 150),
        Sample(t: 25, power: 220), Sample(t: 35, heartRate: 145), Sample(t: 50),
      ],
      events: events, start: start, elapsed: 50)
    XCTAssertFalse(result.points.first { $0.t == 15 }!.active)
    XCTAssertTrue(result.points.first { $0.t == 25 }!.active)
    XCTAssertFalse(result.points.first { $0.t == 35 }!.active)
    XCTAssertTrue(result.points.last!.active)
    XCTAssertEqual(result.points.first { $0.t == 15 }?.heartRate, 150)
    XCTAssertTrue(result.points.allSatisfy { $0.lat == nil })
  }
  func testModernLapIntervalsAndLegacyLapEndMarkers() {
    let start = Date(timeIntervalSince1970: 1000)
    let result = HealthConversion.applyEvents(
      points: [Sample(t: 0), Sample(t: 100)],
      events: [
        event(.lap, at: 10, start: start), event(.lap, at: 30, start: start),
        event(.lap, at: 40, duration: 20, start: start),
        event(.segment, at: 70, duration: 15, start: start),
      ], start: start, elapsed: 100)
    XCTAssertEqual(result.laps.map(\.start), [0, 10, 40, 70])
    XCTAssertEqual(result.laps.map(\.end), [10, 30, 60, 85])
    XCTAssertTrue(result.laps.last!.name.hasPrefix("Interval"))
  }
  func testIndoorAndUnsupportedSportsUseExplicitMappings() {
    XCTAssertEqual(
      HealthConversion.sportLabel(type: .running, indoor: true, pool: false), "Indoor Running")
    XCTAssertEqual(
      HealthConversion.sportLabel(type: .cycling, indoor: true, pool: false), "Indoor Cycling")
    XCTAssertEqual(
      HealthConversion.sportLabel(type: .swimming, indoor: true, pool: true), "Pool Swimming")
    XCTAssertEqual(
      HealthConversion.sportLabel(type: .swimming, indoor: false, pool: false),
      "Open Water Swimming")
    XCTAssertEqual(
      HealthConversion.sportLabel(type: .mixedCardio, indoor: true, pool: false), "Workout")
  }
  func testDuplicateReviewAndPrivacyProvenanceSurviveOfflineRestart() throws {
    let id = UUID()
    let envelope = Envelope(
      id: id, sportID: 1, title: "Apple Watch workout",
      recording: Recording(
        startedAt: "2026-10-10T12:00:00Z", points: [Sample(t: 0), Sample(t: 600)], summaryOnly: true
      ),
      account: "server|alice", healthOrigin: origin(UUID()),
      duplicateCandidates: [
        HealthDuplicate(id: "existing", title: "Morning run", startedAt: "2026-10-10T12:00:00Z")
      ])
    try RecordingDisk.save(envelope)
    defer { try? RecordingDisk.acknowledge(id) }
    let recovered = try RecordingDisk.load(RecordingDisk.file(id))
    XCTAssertEqual(recovered.healthOrigin?.sourceBundle, "com.apple.health")
    XCTAssertEqual(recovered.duplicateCandidates?.first?.id, "existing")
    XCTAssertTrue(recovered.recording.summaryOnly!)
    XCTAssertNil(recovered.keepSeparate)
  }
  private func event(_ type: HKWorkoutEventType, at t: Double, duration: Double = 0, start: Date)
    -> HKWorkoutEvent
  {
    HKWorkoutEvent(
      type: type,
      dateInterval: DateInterval(start: start.addingTimeInterval(t), duration: duration),
      metadata: nil)
  }
}
