import XCTest

@testable import Rint

final class TrainingExperienceTests: XCTestCase {
  func testWeeklyTapRegionsIncludeEmptyWeeksAndBothEdges() {
    XCTAssertEqual(PlotSelection.index(x: -12, width: 320, count: 8), 0)
    XCTAssertEqual(PlotSelection.index(x: 60, width: 320, count: 8), 1)
    XCTAssertEqual(PlotSelection.index(x: 321, width: 320, count: 8), 7)
    XCTAssertNil(PlotSelection.index(x: 10, width: 0, count: 8))
    XCTAssertNil(PlotSelection.index(x: .nan, width: 320, count: 8))
  }
  func testRoutePowerUsesIndependentSensorTimesAndPreservesPrivacyBreaks() {
    let points = [
      Sample(t: 0, lat: 40, lon: -73), Sample(t: 5, power: 100),
      Sample(t: 10, lat: 40.001, lon: -73), Sample(t: 15, power: 300),
      Sample(t: 20, lat: 40.002, lon: -73), Sample(t: 22, routeGap: true),
      Sample(t: 25, lat: 40.003, lon: -73),
    ]
    let result = RouteIntensity.build(points, metric: "power")
    XCTAssertEqual(result.low, 100)
    XCTAssertEqual(result.high, 300)
    XCTAssertEqual(result.sections.map(\.band), [0, 4])
    XCTAssertEqual(result.sections.map { $0.points.map(\.t) }, [[0, 10], [10, 20]])
    XCTAssertNil(RouteIntensity.reading(result.readings, at: 50))
  }
  func testMissingSensorIntervalsHaveNoInventedRouteIntensity() {
    let result = RouteIntensity.build(
      [
        Sample(t: 0, lat: 40, lon: -73, power: 0),
        Sample(t: 10, lat: 40.001, lon: -73), Sample(t: 100, power: 200),
      ], metric: "power")
    XCTAssertNil(result.sections.first?.band)
    XCTAssertEqual(result.low, 0)
  }
  func testPausedClockAndDistanceStayFrozenAcrossCheckpointRecovery() throws {
    var progress = WorkoutProgress()
    XCTAssertEqual(progress.distanceChange(raw: 100, active: true), 100)
    progress.setActive(false, at: 40)
    XCTAssertEqual(progress.duration(at: 1000), 40)
    XCTAssertEqual(progress.distanceChange(raw: 150, active: false), 0)
    let saved = try JSONEncoder().encode(progress)
    progress = try JSONDecoder().decode(WorkoutProgress.self, from: saved)
    XCTAssertEqual(progress.duration(at: 2000), 40)
    progress.setActive(true, at: 2000)
    XCTAssertEqual(progress.duration(at: 2030), 70)
    XCTAssertEqual(progress.distanceChange(raw: 170, active: true), 20)
    XCTAssertEqual(progress.distanceChange(raw: 5, active: true), 5)
  }
  func testGPSRemainsConnectedAcrossSensorSamplesButNotPrivacyOrGPSGaps() {
    let points = [
      Sample(t: 0, lat: 40, lon: -73), Sample(t: 3, heartRate: 140),
      Sample(t: 10, lat: 40.001, lon: -73), Sample(t: 15, routeGap: true),
      Sample(t: 20, lat: 40.002, lon: -73), Sample(t: 25, power: 100),
      Sample(t: 30, lat: 40.003, lon: -73), Sample(t: 120, lat: 40.004, lon: -73),
    ]
    let rows = RouteStream.segments(points)
    XCTAssertEqual(rows.count, 2)
    XCTAssertEqual(rows.map { $0.map(\.t) }, [[0, 10], [20, 30]])
  }
  func testRollingPaceDoesNotExplodeAtTinyIndependentDistanceSamples() {
    let points = (0...120).map { i in
      Sample(t: Double(i), d: Double(i / 10) * 30 + Double(i % 10) * 0.0001)
    }
    let rows = ChartStream.values(points, metric: "pace")
    XCTAssertTrue(rows.filter { $0.t > 30 }.allSatisfy { $0.value < 10 })
    let withOutlier = rows + [ChartReading(id: 200, t: 200, value: 150, segment: 1)]
    XCTAssertLessThan(ChartStream.bounds(withOutlier, metric: "pace").upperBound, 20)
    XCTAssertGreaterThan(
      ChartStream.bounds(withOutlier, metric: "pace", fullRange: true).upperBound, 150)
  }
  func testCompletionReceiptSurvivesUploadAndCannotRegress() throws {
    let id = UUID()
    let value = WorkoutCompletion(
      id: id, account: "test-summary-account", title: "Run", distance: 5000,
      elapsed: 1800, active: 1700, heartRate: 140, finished: Date())
    defer { try? FileManager.default.removeItem(at: CompletionDisk.file(id)) }
    try CompletionDisk.save(value)
    try CompletionDisk.update(id, stage: .server, workoutID: "activity-123")
    try CompletionDisk.update(id, stage: .phone)
    let saved = try XCTUnwrap(CompletionDisk.latest(account: value.account))
    XCTAssertEqual(saved.stage, .server)
    XCTAssertEqual(saved.workoutID, "activity-123")
    XCTAssertNil(CompletionDisk.latest(account: "different-account"))
    XCTAssertFalse(RecordingDisk.pending().contains(CompletionDisk.file(id)))
  }
  func testEffortIntervalsAndActivePaceDecodeWithoutLosingElapsedBasis() throws {
    let data = Data(
      """
      {"distance_m":5000,"elapsed_s":1800,"moving_s":1600,"active_s":1700,"paused_s":100,"pace_s_km":360,"averages":{},"start":60,"end":1860}
      """.utf8)
    let summary = try JSONDecoder().decode(NativeSummary.self, from: data)
    XCTAssertEqual(summary.activePace, 340)
    XCTAssertEqual(summary.paceSKM, 360)
    XCTAssertEqual(summary.start, 60)
    XCTAssertEqual(summary.end, 1860)
  }
}
