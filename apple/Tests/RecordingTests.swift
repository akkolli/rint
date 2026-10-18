import XCTest

@testable import Rint

final class RecordingTests: XCTestCase {
  func testFeedPaceKeepsFractionalPrecisionUntilUnitConversion() throws {
    let seconds = try XCTUnwrap(DisplayUnits.seconds("0:05:52.32"))
    XCTAssertEqual(seconds, 352.32, accuracy: 0.0001)
    XCTAssertEqual(compactTimeLabel(seconds * 1.609344), "09:27")
    XCTAssertNil(DisplayUnits.seconds(""))
    XCTAssertNil(DisplayUnits.seconds("0:99:00"))
    let data = Data(
      """
      {"id":"feed-run","user":{"username":"Runner"},"moving":"0:05:52.32","distance":1}
      """.utf8)
    let workout = try JSONDecoder().decode(FeedActivity.self, from: data)
    XCTAssertEqual(DisplayUnits.seconds(workout.moving), seconds)
    XCTAssertEqual(workout.distance, 1)
  }
  func testLongChartKeepsPeaksAndDoesNotBridgeSamplingGaps() {
    let points = (0..<10000).map { i in
      Sample(t: Double(i < 5000 ? i : i + 120), heartRate: i == 3241 ? 220 : 140)
    }
    let full = ChartStream.values(points, metric: "heart_rate")
    let drawn = ChartStream.reduced(full)
    XCTAssertLessThanOrEqual(drawn.count, 2004)
    XCTAssertTrue(drawn.contains { $0.value == 220 })
    XCTAssertNotEqual(drawn.first?.segment, drawn.last?.segment)
    XCTAssertNil(ChartStream.nearest(full, at: 5060))
  }
  func testOfflineRoundTripRetainsSensorOnlyWorkoutAndLaps() throws {
    let id = UUID()
    let envelope = Envelope(
      id: id, sportID: 1, title: "Indoor run",
      recording: Recording(
        startedAt: "2026-10-11T12:00:00Z",
        points: [
          Sample(t: 0, d: 0, heartRate: 120), Sample(t: 10, d: 0, active: false, heartRate: 140),
        ], laps: [Lap(start: 0, end: 10, name: "Warm-up")]),
      account: "https://fitness.example|me@example.org")
    try RecordingDisk.save(envelope)
    let recovered = try RecordingDisk.load(RecordingDisk.file(id))
    XCTAssertEqual(recovered.id, id)
    XCTAssertEqual(recovered.account, envelope.account)
    XCTAssertNil(recovered.recording.points[0].lat)
    XCTAssertEqual(recovered.recording.points[1].heartRate, 140)
    XCTAssertFalse(recovered.recording.points[1].active)
    XCTAssertEqual(recovered.recording.laps.count, 1)
    try RecordingDisk.acknowledge(id)
    XCTAssertFalse(FileManager.default.fileExists(atPath: RecordingDisk.file(id).path))
  }
  func testDraftIsNotEligibleForUpload() throws {
    let id = UUID()
    let envelope = Envelope(
      id: id, sportID: 1, title: "In progress",
      recording: Recording(startedAt: "2026-10-11T12:00:00Z", points: [Sample(t: 0, d: 0)]),
      account: "server|owner")
    try RecordingDisk.save(envelope, draft: true)
    XCTAssertFalse(RecordingDisk.pending().contains(RecordingDisk.file(id, draft: true)))
    XCTAssertTrue(RecordingDisk.drafts().contains(RecordingDisk.file(id, draft: true)))
    try FileManager.default.removeItem(at: RecordingDisk.file(id, draft: true))
  }
  func testServerPayloadPreservesSIUnitsAndSensorNames() throws {
    let envelope = Envelope(
      id: UUID(), sportID: 7, title: "Run",
      recording: Recording(
        startedAt: "2026-10-11T12:00:00Z", points: [Sample(t: 60, d: 200, heartRate: 123)]),
      account: "server|owner")
    let json = try XCTUnwrap(
      JSONSerialization.jsonObject(with: RecordingDisk.encoder.encode(envelope)) as? [String: Any])
    XCTAssertEqual(json["sport_id"] as? Int, 7)
    let recording = try XCTUnwrap(json["recording"] as? [String: Any])
    XCTAssertEqual(recording["started_at"] as? String, "2026-10-11T12:00:00Z")
    let points = try XCTUnwrap(recording["points"] as? [[String: Any]])
    XCTAssertEqual(points[0]["heart_rate"] as? Double, 123)
    XCTAssertEqual(points[0]["d"] as? Double, 200)
  }
  func testDisplayRoundsConsistentlyAndConvertsUnitsWithoutChangingSamples() {
    XCTAssertEqual(compactTimeLabel(337.6), "05:38")
    XCTAssertEqual(compactTimeLabel(59.8), "01:00")
    XCTAssertEqual(compactTimeLabel(3599.8), "1:00:00")
    let previous = UserDefaults.standard.bool(forKey: "imperial_units")
    defer { UserDefaults.standard.set(previous, forKey: "imperial_units") }
    UserDefaults.standard.set(true, forKey: "imperial_units")
    XCTAssertEqual(DisplayUnits.distance(1609.344), "1.00")
    XCTAssertEqual(DisplayUnits.pace(300), "08:03")
  }
  func testHealthRetryRemainsAfterServerAcknowledgesWorkout() throws {
    let envelope = Envelope(
      id: UUID(), sportID: 1, title: "Run",
      recording: Recording(
        startedAt: "2026-10-11T12:00:00Z", points: [Sample(t: 0, d: 0), Sample(t: 60, d: 200)]),
      account: "server|owner", healthActivity: 37, indoor: false)
    try RecordingDisk.save(envelope)
    try HealthSaveDisk.save(HealthSaveJob(envelope: envelope, activity: 37, indoor: false))
    defer { try? HealthSaveDisk.complete(envelope.id) }
    try RecordingDisk.acknowledge(envelope.id)
    let recovered = try HealthSaveDisk.load(HealthSaveDisk.file(envelope.id))
    XCTAssertEqual(recovered.envelope.recording.points.last?.d, 200)
    XCTAssertEqual(recovered.envelope.healthActivity, 37)
    XCTAssertTrue(HealthSaveDisk.pending().contains(HealthSaveDisk.file(envelope.id)))
  }
  func testServerDurationsDisplayRoundedSecondsWithoutLosingDays() {
    XCTAssertEqual(DisplayUnits.duration("0:00:39.806304"), "00:40")
    XCTAssertEqual(DisplayUnits.duration("0:59:59.8"), "1:00:00")
    XCTAssertEqual(DisplayUnits.duration("2 days, 0:00:05.1"), "48:00:05")
    XCTAssertEqual(DisplayUnits.duration(nil), "—")
    XCTAssertEqual(DisplayUnits.duration("invalid"), "—")
  }
  func testRecoveredDistanceKeepsIndependentAnchorsAndPauseBoundaries() {
    let intervals = HealthSaveDisk.distanceIntervals([
      Sample(t: 0, d: 0), Sample(t: 5, heartRate: 140),
      Sample(t: 10, d: 100, active: false), Sample(t: 15, active: false, heartRate: 120),
      Sample(t: 20, d: 100), Sample(t: 25, heartRate: 140), Sample(t: 30, d: 200),
      Sample(t: 31, heartRate: 140),
    ])
    XCTAssertEqual(intervals.count, 2)
    XCTAssertEqual(intervals.reduce(0) { $0 + $1.meters }, 200)
    XCTAssertEqual(intervals[0].end, 10)
    XCTAssertEqual(intervals[1].start, 20)
  }
}
