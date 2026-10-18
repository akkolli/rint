import CryptoKit
import Foundation

struct HealthOrigin: Codable {
  var workoutID: UUID
  var sourceBundle: String
  var sourceName: String
  var productType: String?
  var activityType: UInt
  var indoor: Bool
  var syncIdentifier: String?
  var syncVersion: Int?
  var externalUUID: String?
  var rintRecordingID: String?
  var activeEnergyKcal: Double?
  var reportedDuration: Double
  var reportedDistanceM: Double? = nil
  var warnings: [String] = []
  enum CodingKeys: String, CodingKey {
    case indoor, warnings
    case workoutID = "workout_id"
    case sourceBundle = "source_bundle"
    case sourceName = "source_name"
    case productType = "product_type"
    case activityType = "activity_type"
    case syncIdentifier = "sync_identifier"
    case syncVersion = "sync_version"
    case externalUUID = "external_uuid"
    case rintRecordingID = "rint_recording_id"
    case activeEnergyKcal = "active_energy_kcal"
    case reportedDuration = "reported_duration_s"
    case reportedDistanceM = "reported_distance_m"
  }
}

struct HealthDuplicate: Codable, Identifiable {
  var id: String
  var title: String
  var startedAt: String
  enum CodingKeys: String, CodingKey {
    case id, title
    case startedAt = "started_at"
  }
}

enum HealthIdentity {
  static func accountKey(_ account: String) -> String {
    SHA256.hash(data: Data(account.utf8)).map { String(format: "%02x", $0) }.joined()
  }
  static func deliveryID(account: String, origin: HealthOrigin, recording: Recording) throws -> UUID
  {
    // Acknowledging an older upload must never delete a newer revision or another account's file.
    var data = Data((account + "|" + origin.workoutID.uuidString + "|").utf8)
    data.append(try RecordingDisk.encoder.encode(recording))
    data.append(try RecordingDisk.encoder.encode(origin))
    let bytes = Array(SHA256.hash(data: data).prefix(16))
    return UUID(
      uuid: (
        bytes[0], bytes[1], bytes[2], bytes[3], bytes[4], bytes[5], bytes[6], bytes[7],
        bytes[8], bytes[9], bytes[10], bytes[11], bytes[12], bytes[13], bytes[14], bytes[15]
      ))
  }
}
