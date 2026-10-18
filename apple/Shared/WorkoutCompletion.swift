import Foundation
import HealthKit

struct WorkoutCompletion: Codable, Identifiable {
  enum Stage: String, Codable { case device, phone, server }
  let id: UUID
  let account: String
  let title: String
  let distance: Double
  let elapsed: Double
  let active: Double
  let heartRate: Double?
  let finished: Date
  var healthActivity: UInt? = nil
  var stage: Stage = .device
  var workoutID: String?
  var pace: Double? { distance > 0 ? active * 1000 / distance : nil }
  var usesSpeed: Bool { healthActivity == HKWorkoutActivityType.cycling.rawValue }
}
enum CompletionDisk {
  static func file(_ id: UUID) -> URL {
    RecordingDisk.directory.appendingPathComponent(id.uuidString + ".summary")
  }
  static func save(_ value: WorkoutCompletion) throws {
    try JSONEncoder().encode(value).write(
      to: file(value.id), options: [.atomic, .completeFileProtectionUntilFirstUserAuthentication])
  }
  static func latest(account: String) -> WorkoutCompletion? {
    let files =
      (try? FileManager.default.contentsOfDirectory(
        at: RecordingDisk.directory, includingPropertiesForKeys: nil)) ?? []
    return files.filter { $0.pathExtension == "summary" }.compactMap {
      try? JSONDecoder().decode(WorkoutCompletion.self, from: Data(contentsOf: $0))
    }.filter { $0.account == account }.max { $0.finished < $1.finished }
  }
  static func update(_ id: UUID, stage: WorkoutCompletion.Stage, workoutID: String? = nil) throws {
    guard FileManager.default.fileExists(atPath: file(id).path) else { return }
    var value = try JSONDecoder().decode(WorkoutCompletion.self, from: Data(contentsOf: file(id)))
    // A delayed phone receipt must never regress a server acknowledgement.
    if value.stage != .server { value.stage = stage }
    if let workoutID { value.workoutID = workoutID }
    try save(value)
  }
}
