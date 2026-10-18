import CoreLocation
import HealthKit
import XCTest

@testable import Rint

/// Opt-in synthetic data for exercising the actual Health permission/import UI.
/// Never seeds a physical device or runs in the normal unit-test scheme.
final class SimulatorHealthFixtureTests: XCTestCase {
  /// Exercises the real reader, durable outbox and local API after UI onboarding.
  /// It deliberately requires the named synthetic account and a connected journal.
  @MainActor func testRescanLocalDemoHistoryWithoutDuplicates() async throws {
    #if targetEnvironment(simulator)
      let api = APIClient.shared
      guard ProcessInfo.processInfo.environment["RINT_HEALTH_FIXTURE"] == "1",
        api.server == "http://localhost:5080", api.email == "demo@rint.invalid", api.signedIn
      else { throw XCTSkip("Opt-in local simulator demo integration") }
      let importer = HealthImporter.shared
      importer.restore()
      guard importer.state.connected else {
        throw XCTSkip("Complete simulator Health onboarding first")
      }
      let before = try JSONDecoder().decode(
        APIResponse<FeedResponse>.self, from: await api.request("workouts?per_page=100"))
      let fixture = try XCTUnwrap(before.data.workouts.first { $0.title == "Apple Health Run" })
      await importer.rescanHistory()
      for _ in 0..<120 {
        let analysis = try JSONDecoder().decode(
          APIResponse<NativeAnalysis>.self,
          from: await api.request("rint/activities/\(fixture.id)/analysis"))
        let after = try JSONDecoder().decode(
          APIResponse<FeedResponse>.self, from: await api.request("workouts?per_page=100"))
        if let updated = after.data.workouts.first(where: { $0.id == fixture.id }),
          abs((updated.distance ?? 0) - 4.8) < 0.001
        {
          XCTAssertEqual(after.data.workouts.count, before.data.workouts.count)
          XCTAssertEqual(after.data.workouts.filter { $0.title == "Apple Health Run" }.count, 1)
          XCTAssertEqual(analysis.data.summary.distanceM, 4800, accuracy: 0.01)
          XCTAssertGreaterThanOrEqual(
            analysis.data.recording.points.filter { $0.heartRate != nil }.count, 30)
          let sharing =
            try JSONSerialization.jsonObject(
              with: await api.request("rint/activities/\(fixture.id)/sharing")) as? [String: Any]
          let settings = sharing?["data"] as? [String: Any]
          XCTAssertEqual(settings?["visibility"] as? String, "private")
          XCTAssertEqual(settings?["privacy_radius_m"] as? Int, 1500)
          return
        }
        try await Task.sleep(for: .milliseconds(500))
      }
      XCTFail("The retained Health revision did not reach the local server within 60 seconds")
    #else
      throw XCTSkip("Synthetic integration is restricted to simulators")
    #endif
  }

  @MainActor func testCreateSyntheticWatchHistory() async throws {
    #if targetEnvironment(simulator)
      guard ProcessInfo.processInfo.environment["RINT_HEALTH_FIXTURE"] == "1" else {
        throw XCTSkip("Opt-in simulator fixture")
      }
      let health = HKHealthStore()
      let types: Set<HKSampleType> = [
        .workoutType(), HKSeriesType.workoutRoute(), HKQuantityType(.heartRate),
        HKQuantityType(.distanceWalkingRunning), HKQuantityType(.activeEnergyBurned),
      ]
      try await health.requestAuthorization(
        toShare: types, read: Set(types.map { $0 as HKObjectType }))
      let predicate = HKQuery.predicateForObjects(
        withMetadataKey: HKMetadataKeySyncIdentifier,
        allowedValues: ["rint.simulator.history.fixture"])
      let existing: [HKWorkout] = try await withCheckedThrowingContinuation { continuation in
        health.execute(
          HKSampleQuery(
            sampleType: .workoutType(), predicate: predicate, limit: 1, sortDescriptors: nil
          ) { _, samples, error in
            if let error {
              continuation.resume(throwing: error)
            } else {
              continuation.resume(returning: samples as? [HKWorkout] ?? [])
            }
          })
      }
      if let workout = existing.first {
        try await verifyImport(workout, health: health)
        return
      }
      let start = ISO8601DateFormatter().date(from: "2026-10-10T20:00:00Z")!
      let configuration = HKWorkoutConfiguration()
      configuration.activityType = .running
      configuration.locationType = .outdoor
      let device = HKDevice(
        name: "Rint synthetic Watch fixture", manufacturer: "Rint", model: "Apple Watch simulator",
        hardwareVersion: "fixture", firmwareVersion: nil, softwareVersion: "27",
        localIdentifier: "rint-simulator", udiDeviceIdentifier: nil)
      let builder = HKWorkoutBuilder(
        healthStore: health, configuration: configuration, device: device)
      try await builder.beginCollection(at: start)
      try await builder.addMetadata([
        HKMetadataKeySyncIdentifier: "rint.simulator.history.fixture", HKMetadataKeySyncVersion: 1,
        "RintSimulatorFixture": true,
      ])
      var samples: [HKQuantitySample] = []
      for index in 0...30 {
        let date = start.addingTimeInterval(Double(index * 30))
        samples.append(
          HKQuantitySample(
            type: HKQuantityType(.heartRate),
            quantity: HKQuantity(
              unit: .count().unitDivided(by: .minute()), doubleValue: 130 + Double(index % 8)),
            start: date, end: date))
        if index > 0 {
          samples.append(
            HKQuantitySample(
              type: HKQuantityType(.distanceWalkingRunning),
              quantity: HKQuantity(unit: .meter(), doubleValue: 160),
              start: date.addingTimeInterval(-30), end: date))
        }
      }
      samples.append(
        HKQuantitySample(
          type: HKQuantityType(.activeEnergyBurned),
          quantity: HKQuantity(unit: .kilocalorie(), doubleValue: 300), start: start,
          end: start.addingTimeInterval(900)))
      try await builder.addSamples(samples)
      try await builder.endCollection(at: start.addingTimeInterval(900))
      let savedWorkout = try await builder.finishWorkout()
      let workout = try XCTUnwrap(savedWorkout)
      let route = HKWorkoutRouteBuilder(healthStore: health, device: device)
      let locations = (0...30).map { index in
        let angle = Double(index) / 30 * .pi * 2
        return CLLocation(
          coordinate: CLLocationCoordinate2D(
            latitude: 37.79 + sin(angle) * 0.007, longitude: -122.4 + cos(angle) * 0.009),
          altitude: 12, horizontalAccuracy: 3, verticalAccuracy: 3,
          timestamp: start.addingTimeInterval(Double(index * 30)))
      }
      try await route.insertRouteData(locations)
      _ = try await route.finishRoute(
        with: workout,
        metadata: [
          HKMetadataKeySyncIdentifier: "rint.simulator.history.fixture.route",
          HKMetadataKeySyncVersion: 1,
        ])
      try await verifyImport(workout, health: health)
    #else
      throw XCTSkip("Synthetic fixture is restricted to simulators")
    #endif
  }
  @MainActor private func verifyImport(_ workout: HKWorkout, health: HKHealthStore) async throws {
    let envelope = try await HealthWorkoutReader(store: health).envelope(
      workout, sports: [SportChoice(id: 5, label: "Running")], account: "simulator-fixture")
    XCTAssertTrue(HealthConversion.isWatch(workout))
    XCTAssertEqual(envelope.recording.points.compactMap(\.d).max() ?? 0, 4800, accuracy: 0.01)
    XCTAssertGreaterThanOrEqual(envelope.recording.points.filter { $0.heartRate != nil }.count, 30)
    XCTAssertGreaterThanOrEqual(envelope.recording.points.filter { $0.lat != nil }.count, 30)
    XCTAssertEqual(envelope.healthOrigin?.reportedDistanceM ?? 0, 4800, accuracy: 0.01)
  }
}
