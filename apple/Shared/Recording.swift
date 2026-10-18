import Foundation

struct Sample: Codable, Identifiable, Equatable {
  var t: Double
  var d: Double?
  var active: Bool = true
  var lat: Double?
  var lon: Double?
  var heartRate: Double?
  var cadence: Double?
  var power: Double?
  var elevation: Double?
  var distanceGap: Bool?
  var routeGap: Bool?
  var id: Double { t }
  enum CodingKeys: String, CodingKey {
    case t, d, active, lat, lon, cadence, power, elevation
    case heartRate = "heart_rate"
    case distanceGap = "distance_gap"
    case routeGap = "route_gap"
  }
}
struct Lap: Codable {
  var start: Double
  var end: Double
  var name: String
}
struct Recording: Codable {
  var version = 1
  var startedAt: String
  var points: [Sample]
  var laps: [Lap] = []
  var summaryOnly: Bool? = nil
  enum CodingKeys: String, CodingKey {
    case version, points, laps
    case startedAt = "started_at"
    case summaryOnly = "summary_only"
  }
}
struct Envelope: Codable, Identifiable {
  var id: UUID
  var sportID: Int
  var title: String
  var recording: Recording
  var account: String
  var healthActivity: UInt? = nil
  var indoor: Bool? = nil
  var recorderProgress: WorkoutProgress? = nil
  var healthOrigin: HealthOrigin? = nil
  var duplicateWorkoutID: String? = nil
  var keepSeparate: Bool? = nil
  // Local review state travels with the durable outbox, but is ignored by the server.
  var duplicateCandidates: [HealthDuplicate]? = nil
  enum CodingKeys: String, CodingKey {
    case id, title, recording, account, indoor
    case healthActivity = "health_activity"
    case recorderProgress = "recorder_progress"
    case sportID = "sport_id"
    case healthOrigin = "health_origin"
    case duplicateWorkoutID = "duplicate_workout_id"
    case keepSeparate = "keep_separate"
    case duplicateCandidates = "duplicate_candidates"
  }
}
enum RecordingDisk {
  struct Header: Codable {
    var account: String
    var needsReview: Bool
  }
  private static var headers: [UUID: Header] = [:]
  private static let headerLock = NSLock()
  static let encoder: JSONEncoder = {
    let e = JSONEncoder()
    e.outputFormatting = [.sortedKeys]
    return e
  }()
  static var directory: URL {
    let root = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
      .appendingPathComponent("Rint", isDirectory: true)
    try? FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
    return root
  }
  static func file(_ id: UUID, draft: Bool = false) -> URL {
    directory.appendingPathComponent(id.uuidString + (draft ? ".draft" : ".json"))
  }
  static func save(_ envelope: Envelope, draft: Bool = false) throws {
    try encoder.encode(envelope).write(
      to: file(envelope.id, draft: draft),
      options: [.atomic, .completeFileProtectionUntilFirstUserAuthentication])
    if !draft {
      saveHeader(
        Header(account: envelope.account, needsReview: envelope.duplicateCandidates != nil),
        id: envelope.id)
    }
  }
  static func load(_ url: URL) throws -> Envelope {
    try JSONDecoder().decode(Envelope.self, from: Data(contentsOf: url))
  }
  static func pending() -> [URL] {
    ((try? FileManager.default.contentsOfDirectory(at: directory, includingPropertiesForKeys: nil))
      ?? []).filter { $0.pathExtension == "json" }
  }
  static func pending(account: String, needsReview: Bool? = nil) -> [URL] {
    pending().filter { url in
      guard let header = try? header(url) else { return false }
      return header.account == account && (needsReview == nil || header.needsReview == needsReview)
    }
  }
  private static func header(_ url: URL) throws -> Header {
    guard let id = UUID(uuidString: url.deletingPathExtension().lastPathComponent) else {
      throw CocoaError(.fileReadCorruptFile)
    }
    headerLock.lock()
    let cached = headers[id]
    headerLock.unlock()
    if let cached { return cached }
    let metadata = directory.appendingPathComponent(id.uuidString + ".header")
    if let data = try? Data(contentsOf: metadata),
      let header = try? JSONDecoder().decode(Header.self, from: data)
    {
      headerLock.lock()
      headers[id] = header
      headerLock.unlock()
      return header
    }
    // Upgrade old outboxes once; the recording remains authoritative.
    let envelope = try load(url)
    let header = Header(account: envelope.account, needsReview: envelope.duplicateCandidates != nil)
    saveHeader(header, id: id)
    return header
  }
  private static func saveHeader(_ header: Header, id: UUID) {
    headerLock.lock()
    defer { headerLock.unlock() }
    headers[id] = header
    let url = directory.appendingPathComponent(id.uuidString + ".header")
    do {
      try encoder.encode(header).write(
        to: url,
        options: [.atomic, .completeFileProtectionUntilFirstUserAuthentication])
    } catch {
      // Never leave an obsolete index; a missing index is rebuilt from the payload.
      try? FileManager.default.removeItem(at: url)
    }
  }
  static func drafts() -> [URL] {
    ((try? FileManager.default.contentsOfDirectory(at: directory, includingPropertiesForKeys: nil))
      ?? []).filter { $0.pathExtension == "draft" }
  }
  static func acknowledge(_ id: UUID) throws {
    let url = file(id)
    if FileManager.default.fileExists(atPath: url.path) {
      try FileManager.default.removeItem(at: url)
    }
    let metadata = directory.appendingPathComponent(id.uuidString + ".header")
    if FileManager.default.fileExists(atPath: metadata.path) {
      try FileManager.default.removeItem(at: metadata)
    }
    headerLock.lock()
    headers.removeValue(forKey: id)
    headerLock.unlock()
  }
}
func elapsedLabel(_ seconds: Double) -> String {
  let s = max(0, Int(seconds))
  return String(format: "%02d:%02d:%02d", s / 3600, (s / 60) % 60, s % 60)
}
