import Foundation

struct HealthSyncState: Codable {
  var connected = false
  var automatic = false
  var watchOnly = false
  var since: Date? = nil
  var anchor: Data? = nil
  var pendingIDs: [UUID] = []
  var failures: [String: String] = [:]
  var revisions: [String: UUID] = [:]
  var lastChecked: Date? = nil
  var historyComplete = false

  mutating func checkpoint(ids: [UUID], deleted: [UUID], anchor: Data) {
    let removed = Set(deleted)
    pendingIDs.removeAll { removed.contains($0) }
    for id in ids where !pendingIDs.contains(id) && !removed.contains(id) { pendingIDs.append(id) }
    for id in deleted { failures.removeValue(forKey: id.uuidString) }
    self.anchor = anchor
  }
  mutating func retained(_ id: UUID, revision: UUID) {
    revisions[id.uuidString] = revision
    pendingIDs.removeAll { $0 == id }
    failures.removeValue(forKey: id.uuidString)
  }
  static func file(account: String) -> URL {
    RecordingDisk.directory.appendingPathComponent(
      HealthIdentity.accountKey(account) + ".healthstate")
  }
  static func load(account: String) throws -> HealthSyncState {
    let url = file(account: account)
    guard FileManager.default.fileExists(atPath: url.path) else { return HealthSyncState() }
    return try JSONDecoder().decode(Self.self, from: Data(contentsOf: url))
  }
  func save(account: String) throws {
    try RecordingDisk.encoder.encode(self).write(
      to: Self.file(account: account),
      options: [.atomic, .completeFileProtectionUntilFirstUserAuthentication])
  }
}
