import UIKit
import XCTest

@testable import Rint

/// Opt-in transport checks against the synthetic local account. These exercise
/// real iOS networking and server persistence, not photo-picker/touch acceptance.
final class SimulatorAccountFixtureTests: XCTestCase {
  @MainActor func testLocalProfilePhotoPrivacyAndAccountArchive() async throws {
    #if targetEnvironment(simulator)
      let api = APIClient.shared
      guard ProcessInfo.processInfo.environment["RINT_HEALTH_FIXTURE"] == "1",
        api.server == "http://localhost:5080", api.email == "demo@rint.invalid", api.signedIn
      else { throw XCTSkip("Opt-in local simulator demo integration") }
      let profile =
        try JSONSerialization.jsonObject(with: await api.request("auth/profile")) as? [String: Any]
      let current = try XCTUnwrap(profile?["data"] as? [String: Any])
      var payload = [
        "first_name": current["first_name"] as? String ?? "",
        "last_name": current["last_name"] as? String ?? "", "bio": current["bio"] as? String ?? "",
        "location": current["location"] as? String ?? "", "birth_date": "",
      ]
      // This demo has no birthday. Do not clear another fixture's value.
      guard current["birth_date"] is NSNull else { throw XCTSkip("Demo birthday must be unset") }
      _ = try await api.request(
        "auth/profile/edit", method: "POST", body: JSONSerialization.data(withJSONObject: payload))
      let saved =
        try JSONSerialization.jsonObject(with: await api.request("auth/profile")) as? [String: Any]
      XCTAssertEqual(
        (saved?["data"] as? [String: Any])?["location"] as? String, payload["location"])
      payload.removeAll()
      let activities = try JSONDecoder().decode(
        APIResponse<FeedResponse>.self, from: await api.request("workouts?per_page=100"))
      let workout = try XCTUnwrap(activities.data.workouts.first { $0.title == "Apple Health Run" })
      let sharingPath = "rint/activities/\(workout.id)/sharing"
      let sharingBefore = try await api.request(sharingPath)
      let defaultsKey = "rint.simulator.account-photo-fixture"
      var photoID = UserDefaults.standard.string(forKey: defaultsKey)
      let detail = try JSONDecoder().decode(
        APIResponse<FeedResponse>.self, from: await api.request("workouts/\(workout.id)"))
      var ids = detail.data.workouts.first?.mediaAttachments?.map(\.id) ?? []
      if photoID == nil || !ids.contains(photoID!) {
        let image = UIGraphicsImageRenderer(size: CGSize(width: 320, height: 240)).image {
          context in
          UIColor(red: 0.79, green: 0.95, blue: 0.20, alpha: 1).setFill()
          context.fill(CGRect(x: 0, y: 0, width: 320, height: 240))
          "Rint · simulator photo".draw(
            at: CGPoint(x: 30, y: 100),
            withAttributes: [
              .font: UIFont.boldSystemFont(ofSize: 20), .foregroundColor: UIColor.black,
            ])
        }
        let jpeg = try NativePhotoPreparation.jpeg(
          try XCTUnwrap(image.jpegData(compressionQuality: 0.9)))
        photoID = try JSONDecoder().decode(FeedPhoto.self, from: await api.uploadPhoto(jpeg)).id
        ids.append(try XCTUnwrap(photoID))
        _ = try await api.request(
          "workouts/\(workout.id)", method: "PATCH",
          body: JSONSerialization.data(withJSONObject: ["media_attachment_ids": ids]))
        UserDefaults.standard.set(photoID, forKey: defaultsKey)
      }
      let after = try JSONDecoder().decode(
        APIResponse<FeedResponse>.self, from: await api.request("workouts/\(workout.id)"))
      XCTAssertEqual(after.data.workouts.first?.mediaAttachments?.map(\.id), ids)
      let sharingAfter = try await api.request(sharingPath)
      XCTAssertEqual(
        try JSONSerialization.jsonObject(with: sharingAfter) as? NSDictionary,
        try JSONSerialization.jsonObject(with: sharingBefore) as? NSDictionary)
      let export = try JSONDecoder().decode(
        NativeAccountExport.Response.self, from: await api.request("auth/account/export"))
      let job = try XCTUnwrap(export.request)
      XCTAssertEqual(
        job.status, "successful", "Prepare the synthetic account archive locally first")
      let file = try await api.downloadAccountArchive(try XCTUnwrap(job.fileName))
      let handle = try FileHandle(forReadingFrom: file)
      defer {
        try? handle.close()
        try? FileManager.default.removeItem(at: file)
      }
      XCTAssertEqual(try handle.read(upToCount: 2), Data([0x50, 0x4b]))
      XCTAssertGreaterThan(try file.resourceValues(forKeys: [.fileSizeKey]).fileSize ?? 0, 100)
    #else
      throw XCTSkip("Synthetic integration is restricted to simulators")
    #endif
  }
}
