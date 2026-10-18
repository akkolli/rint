import XCTest

@testable import Rint

final class APIResponseTests: XCTestCase {
  func testSportsEnvelopeMatchesFitTrackee() throws {
    let data = Data(#"{"data":{"sports":[{"id":5,"label":"Running","is_active":true}]}}"#.utf8)
    let response = try JSONDecoder().decode(APIResponse<SportsResponse>.self, from: data)
    XCTAssertEqual(response.data.sports.first?.id, 5)
    XCTAssertEqual(response.data.sports.first?.label, "Running")
  }

  func testTimelineSupportsRestrictedMetricsAndServerDates() throws {
    let data = Data(
      #"{"data":{"workouts":[{"id":"activity","title":"Morning run","distance":null,"duration":null,"moving":null,"workout_date":"Sat, 10 Oct 2026 12:00:00 GMT","user":{"username":"runner"},"media_attachments":[],"with_stream":false}]},"pagination":{"has_next":true}}"#
        .utf8)
    let response = try JSONDecoder().decode(APIResponse<FeedResponse>.self, from: data)
    let workout = try XCTUnwrap(response.data.workouts.first)
    XCTAssertNil(workout.duration)
    XCTAssertNil(workout.distance)
    XCTAssertEqual(workout.date, ISO8601DateFormatter().date(from: "2026-10-10T12:00:00Z"))
    XCTAssertEqual(response.pagination?.hasNext, true)
  }
}
