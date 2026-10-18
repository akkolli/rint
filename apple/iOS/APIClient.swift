import BackgroundTasks
import Combine
import Foundation
import HealthKit
import Network
import Security

enum TokenVault {
  static func remove(account: String) throws {
    let query: [String: Any] = [
      kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: "org.rint.token",
      kSecAttrAccount as String: account,
    ]
    let status = SecItemDelete(query as CFDictionary)
    if status != errSecSuccess && status != errSecItemNotFound {
      throw NSError(domain: NSOSStatusErrorDomain, code: Int(status))
    }
  }
  static func save(_ token: String, account: String) throws {
    let query: [String: Any] = [
      kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: "org.rint.token",
      kSecAttrAccount as String: account,
    ]
    SecItemDelete(query as CFDictionary)
    var entry = query
    entry[kSecValueData as String] = Data(token.utf8)
    entry[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
    let status = SecItemAdd(entry as CFDictionary, nil)
    if status != errSecSuccess { throw NSError(domain: NSOSStatusErrorDomain, code: Int(status)) }
  }
  static func load(account: String) -> String? {
    let query: [String: Any] = [
      kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: "org.rint.token",
      kSecAttrAccount as String: account, kSecReturnData as String: true,
      kSecMatchLimit as String: kSecMatchLimitOne,
    ]
    var result: CFTypeRef?
    guard SecItemCopyMatching(query as CFDictionary, &result) == errSecSuccess,
      let data = result as? Data
    else { return nil }
    return String(data: data, encoding: .utf8)
  }
}
struct SportChoice: Codable, Identifiable {
  let id: Int
  let label: String
}
struct SportsResponse: Decodable { let sports: [SportChoice] }
struct FeedUser: Codable {
  let username: String
  var picture: Bool? = nil
}
struct FeedPhoto: Codable, Identifiable {
  let id: String
  let url: String
}
struct FeedActivity: Codable, Identifiable {
  let id: String
  let title: String?
  let distance: Double?
  let duration: String?
  let user: FeedUser
  let likesCount: Int?
  let liked: Bool?
  let mediaAttachments: [FeedPhoto]?
  var sportID: Int? = nil
  var moving: String? = nil
  var workoutDate: String? = nil
  var workoutVisibility: String? = nil
  var withStream: Bool? = nil
  var withGeometry: Bool? = nil
  var description: String? = nil
  var averageHeartRate: Double? = nil
  enum CodingKeys: String, CodingKey {
    case id, title, distance, duration, user, liked, description
    case likesCount = "likes_count"
    case mediaAttachments = "media_attachments"
    case moving
    case sportID = "sport_id"
    case workoutDate = "workout_date"
    case workoutVisibility = "workout_visibility"
    case withStream = "with_stream"
    case withGeometry = "with_geometry"
    case averageHeartRate = "ave_hr"
  }
  var date: Date? {
    guard let workoutDate else { return nil }
    if let date = DisplayUnits.date(workoutDate) { return date }
    // FitTrackee serializes dates as RFC 1123; imported recordings use ISO 8601.
    let formatter = DateFormatter()
    formatter.locale = Locale(identifier: "en_US_POSIX")
    formatter.timeZone = TimeZone(secondsFromGMT: 0)
    formatter.dateFormat = "EEE, dd MMM yyyy HH:mm:ss zzz"
    return formatter.date(from: workoutDate)
  }
}
struct Pagination: Decodable {
  let hasNext: Bool
  enum CodingKeys: String, CodingKey { case hasNext = "has_next" }
}
struct APIResponse<T: Decodable>: Decodable {
  let data: T
  let pagination: Pagination?
}
struct FeedResponse: Decodable { let workouts: [FeedActivity] }
struct NativeSummary: Codable {
  let distanceM: Double
  let elapsedS: Double
  let movingS: Double
  let pausedS: Double
  let averages: [String: Double]
  let activeEnergyKcal: Double?
  let healthReportedActiveS: Double?
  var paceSKM: Double? = nil
  var activeS: Double? = nil
  var start: Double? = nil
  var end: Double? = nil
  var name: String? = nil
  enum CodingKeys: String, CodingKey {
    case averages
    case distanceM = "distance_m"
    case elapsedS = "elapsed_s"
    case movingS = "moving_s"
    case pausedS = "paused_s"
    case activeEnergyKcal = "active_energy_kcal"
    case healthReportedActiveS = "health_reported_active_s"
    case paceSKM = "pace_s_km"
    case name
    case start, end
    case activeS = "active_s"
  }
  var activePace: Double? {
    distanceM > 0 ? (activeS ?? max(0, elapsedS - pausedS)) * 1000 / distanceM : nil
  }
}
struct NativeEffort: Codable, Identifiable {
  let distanceM: Double
  let elapsedS: Double
  var start: Double? = nil
  var end: Double? = nil
  var id: Double { distanceM }
  enum CodingKeys: String, CodingKey {
    case distanceM = "distance_m"
    case elapsedS = "elapsed_s"
    case start, end
  }
}
struct NativeRoutePreview: Decodable { let points: [Sample] }
struct NativeAnalysis: Decodable {
  let recording: Recording
  let summary: NativeSummary
  let bestEfforts: [NativeEffort]
  let splitsKM: [NativeSummary]
  var splitsMile: [NativeSummary]? = nil
  let warnings: [String]?
  var laps: [NativeSummary]? = nil
  enum CodingKeys: String, CodingKey {
    case recording, summary, warnings, laps
    case bestEfforts = "best_efforts"
    case splitsKM = "splits_km"
    case splitsMile = "splits_mile"
  }
}
final class APIClient: ObservableObject {
  static let shared = APIClient()
  @Published var server =
    UserDefaults.standard.string(forKey: "server")
    ?? Bundle.main.object(forInfoDictionaryKey: "RintDefaultServerURL") as? String ?? ""
  @Published var email = UserDefaults.standard.string(forKey: "email") ?? ""
  @Published var signedIn = false
  @Published var error: String?
  @Published var sports: [SportChoice] = []
  @Published var feed: [FeedActivity] = []
  @Published var sportID = UserDefaults.standard.integer(forKey: "sport_id")
  @Published var username = ""
  @Published var pictureAvailable = false
  @Published var unreadNotifications = 0
  @Published var hasMoreFeed = false
  @Published var selectedTab = 0
  @Published var selectedTrainingSection = "Week"
  @Published var showingHealth = false
  @Published var refreshing = false
  @Published var loadingMore = false
  @Published var imperial = UserDefaults.standard.bool(forKey: "imperial_units")
  private var feedPage = 1
  var account: String {
    server.trimmingCharacters(in: CharacterSet(charactersIn: "/")) + "|" + email.lowercased()
  }
  init() {
    signedIn = TokenVault.load(account: account) != nil
    restoreSports()
  }
  private func restoreSports() {
    let data = UserDefaults.standard.data(forKey: "sports-" + HealthIdentity.accountKey(account))
    sports = data.flatMap { try? JSONDecoder().decode([SportChoice].self, from: $0) } ?? []
  }
  private func url(_ path: String) throws -> URL {
    guard let root = URL(string: server), let host = root.host,
      root.scheme == "https"
        || (root.scheme == "http" && ["localhost", "127.0.0.1"].contains(host)), root.user == nil,
      root.password == nil
    else {
      throw NSError(
        domain: "Rint", code: 0,
        userInfo: [NSLocalizedDescriptionKey: "Enter your server’s HTTPS address."])
    }
    let parts = path.split(separator: "?", maxSplits: 1)
    var components = URLComponents(
      url: root.appendingPathComponent("api").appendingPathComponent(String(parts[0])),
      resolvingAgainstBaseURL: false)!
    if parts.count > 1 { components.percentEncodedQuery = String(parts[1]) }
    return components.url!
  }
  func request(_ path: String, method: String = "GET", body: Data? = nil) async throws -> Data {
    var request = URLRequest(url: try url(path))
    request.httpMethod = method
    request.httpBody = body
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    if let token = TokenVault.load(account: account) {
      request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
    }
    let (data, response) = try await URLSession.shared.data(for: request)
    guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
      let message =
        (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["message"] as? String
        ?? "Your server could not complete this request."
      if (response as? HTTPURLResponse)?.statusCode == 401 {
        await MainActor.run {
          try? TokenVault.remove(account: account)
          signedIn = false
          error = "Your session expired. Sign in again; saved workouts stay on this device."
        }
      }
      throw NSError(
        domain: "Rint", code: (response as? HTTPURLResponse)?.statusCode ?? 0,
        userInfo: [NSLocalizedDescriptionKey: message])
    }
    return data
  }
  @MainActor func login(password: String) async {
    do {
      let data = try await request(
        "auth/login", method: "POST",
        body: JSONSerialization.data(withJSONObject: ["email": email, "password": password]))
      guard
        let token = (try JSONSerialization.jsonObject(with: data) as? [String: Any])?["auth_token"]
          as? String
      else { return }
      try TokenVault.save(token, account: account)
      UserDefaults.standard.set(server, forKey: "server")
      UserDefaults.standard.set(email, forKey: "email")
      UserDefaults.standard.set(account, forKey: "account")
      signedIn = true
      restoreSports()
      error = nil
      await refresh()
      HealthImporter.shared.observe()
      if HealthImporter.shared.state.automatic {
        await HealthImporter.shared.synchronize(refreshRecent: true)
      }
      SyncQueue.shared.sync(force: true)
    } catch { self.error = error.localizedDescription }
  }
  @MainActor func signOut() {
    let token = TokenVault.load(account: account)
    let endpoint = try? url("auth/logout")
    do {
      try TokenVault.remove(account: account)
    } catch {
      self.error = error.localizedDescription
      return
    }
    signedIn = false
    TrainingStore.shared.clear()
    HealthImporter.shared.stopObserving()
    feed = []
    sports = []
    username = ""
    pictureAvailable = false
    unreadNotifications = 0
    hasMoreFeed = false
    error = nil
    // Cancel delivery, preserving the durable, account-bound workout outbox.
    SyncQueue.shared.session.getAllTasks { tasks in tasks.forEach { $0.cancel() } }
    if let host = URL(string: server)?.host {
      for cookie in HTTPCookieStorage.shared.cookies ?? [] {
        if cookie.domain.trimmingCharacters(in: CharacterSet(charactersIn: ".")) == host {
          HTTPCookieStorage.shared.deleteCookie(cookie)
        }
      }
    }
    URLCache.shared.removeAllCachedResponses()
    if let endpoint, let token {
      var request = URLRequest(url: endpoint, timeoutInterval: 10)
      request.httpMethod = "POST"
      request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
      Task { _ = try? await URLSession.shared.data(for: request) }
    }
  }
  @MainActor func refresh() async {
    guard !refreshing else { return }
    refreshing = true
    defer { refreshing = false }
    do {
      sports = try JSONDecoder().decode(
        APIResponse<SportsResponse>.self, from: await request("sports")
      ).data.sports
      UserDefaults.standard.set(
        try JSONEncoder().encode(sports),
        forKey: "sports-" + HealthIdentity.accountKey(account))
      let timeline = try JSONDecoder().decode(
        APIResponse<FeedResponse>.self, from: await request("timeline"))
      feed = timeline.data.workouts
      hasMoreFeed = timeline.pagination?.hasNext ?? false
      feedPage = 1
      let profile =
        try JSONSerialization.jsonObject(with: await request("auth/profile")) as? [String: Any]
      username = (profile?["data"] as? [String: Any])?["username"] as? String ?? ""
      pictureAvailable = (profile?["data"] as? [String: Any])?["picture"] as? Bool ?? false
      imperial = (profile?["data"] as? [String: Any])?["imperial_units"] as? Bool ?? false
      UserDefaults.standard.set(imperial, forKey: "imperial_units")
      if !sports.contains(where: { $0.id == sportID }) {
        sportID =
          sports.first(where: { $0.label.lowercased() == "running" })?.id ?? sports.first?.id ?? 0
      }
      configureWatch()
      error = nil
      await refreshUnread()
    } catch { self.error = error.localizedDescription }
  }
  @MainActor func refreshUnread() async {
    let requestedAccount = account
    if let data = try? await request("notifications?per_page=1&status=unread"),
      let result = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
      let pagination = result["pagination"] as? [String: Any], requestedAccount == account
    {
      unreadNotifications = pagination["total"] as? Int ?? 0
    }
  }
  @MainActor func moreFeed() async {
    guard !loadingMore else { return }
    loadingMore = true
    defer { loadingMore = false }
    do {
      let response = try JSONDecoder().decode(
        APIResponse<FeedResponse>.self, from: await request("timeline?page=\(feedPage+1)"))
      let existing = Set(feed.map(\.id))
      feed += response.data.workouts.filter { !existing.contains($0.id) }
      feedPage += 1
      hasMoreFeed = response.pagination?.hasNext ?? false
    } catch { self.error = error.localizedDescription }
  }
  func configureWatch() {
    UserDefaults.standard.set(sportID, forKey: "sport_id")
    WatchBridge.shared.configure(
      account: account, sportID: sportID,
      activity: WorkoutKind.type(sports.first(where: { $0.id == sportID })?.label ?? "Running"),
      sports: sports.map {
        ["id": $0.id, "label": $0.label, "activity": Int(WorkoutKind.type($0.label).rawValue)]
      })
  }
  func uploadRequest() throws -> URLRequest {
    var request = URLRequest(url: try url("rint/recordings"))
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    guard let token = TokenVault.load(account: account) else {
      throw NSError(
        domain: "Rint", code: 401,
        userInfo: [NSLocalizedDescriptionKey: "Sign in to sync your retained workouts."])
    }
    request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
    return request
  }
}

final class SyncQueue: NSObject, ObservableObject, URLSessionDataDelegate, URLSessionTaskDelegate {
  static let shared = SyncQueue()
  @Published var pending = 0
  @Published var message = ""
  var backgroundCompletion: (() -> Void)?
  private let monitor = NWPathMonitor()
  private var responses: [Int: Data] = [:]
  private let lock = NSLock()
  private var retryTimer: Timer?
  private var scheduling = false
  private let retryStore = UserDefaults.standard
  private func nextAttempt(_ id: UUID) -> Date {
    Date(timeIntervalSince1970: retryStore.double(forKey: "retry-at-" + id.uuidString))
  }
  private func scheduleRetry() {
    retryTimer?.invalidate()
    let dates = RecordingDisk.pending(account: APIClient.shared.account, needsReview: false)
      .compactMap { url -> Date? in
        guard let id = UUID(uuidString: url.deletingPathExtension().lastPathComponent) else {
          return nil
        }
        return nextAttempt(id)
      }
    guard let date = dates.min() else {
      BGTaskScheduler.shared.cancel(taskRequestWithIdentifier: "org.rint.sync")
      return
    }
    let delay = max(30, date.timeIntervalSinceNow)
    retryTimer = Timer.scheduledTimer(withTimeInterval: delay, repeats: false) { [weak self] _ in
      self?.sync()
    }
    let request = BGProcessingTaskRequest(identifier: "org.rint.sync")
    request.requiresNetworkConnectivity = true
    request.earliestBeginDate = Date(timeIntervalSinceNow: delay)
    BGTaskScheduler.shared.cancel(taskRequestWithIdentifier: request.identifier)
    try? BGTaskScheduler.shared.submit(request)
  }
  lazy var session: URLSession = {
    let config = URLSessionConfiguration.background(withIdentifier: "org.rint.workout-upload")
    config.waitsForConnectivity = true
    config.isDiscretionary = false
    config.sessionSendsLaunchEvents = true
    return URLSession(configuration: config, delegate: self, delegateQueue: nil)
  }()
  override init() {
    super.init()
    monitor.pathUpdateHandler = { [weak self] path in
      if path.status == .satisfied { DispatchQueue.main.async { self?.sync() } }
    }
    monitor.start(queue: DispatchQueue(label: "rint.network"))
    WatchBridge.shared.received = { [weak self] in self?.sync() }
  }
  func sync(force: Bool = false, scheduled: (() -> Void)? = nil) {
    pending = RecordingDisk.pending(account: APIClient.shared.account).count
    let files = RecordingDisk.pending(account: APIClient.shared.account, needsReview: false)
    guard APIClient.shared.signedIn else {
      scheduled?()
      return
    }
    guard !scheduling else {
      scheduled?()
      return
    }
    scheduling = true
    session.getAllTasks { tasks in
      DispatchQueue.main.async {
        defer { self.scheduling = false }
        let active = Set(tasks.compactMap(\.taskDescription))
        var slots = max(0, 1 - tasks.count)
        for url in files {
          guard slots > 0 else { break }
          guard let id = UUID(uuidString: url.deletingPathExtension().lastPathComponent),
            !active.contains(id.uuidString), force || self.nextAttempt(id) <= Date()
          else { continue }
          guard let envelope = try? RecordingDisk.load(url),
            envelope.account == APIClient.shared.account, !active.contains(envelope.id.uuidString),
            envelope.duplicateCandidates == nil,
            force || self.nextAttempt(envelope.id) <= Date()
          else { continue }
          do {
            let task = self.session.uploadTask(
              with: try APIClient.shared.uploadRequest(), fromFile: url)
            task.taskDescription = envelope.id.uuidString
            task.resume()
            slots -= 1
          } catch { DispatchQueue.main.async { self.message = error.localizedDescription } }
        }
        self.scheduleRetry()
        scheduled?()
      }
    }
    APIClient.shared.configureWatch()
  }
  func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive data: Data) {
    lock.lock()
    responses[dataTask.taskIdentifier, default: Data()].append(data)
    lock.unlock()
  }
  func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
    lock.lock()
    let data = responses.removeValue(forKey: task.taskIdentifier)
    lock.unlock()
    let status = (task.response as? HTTPURLResponse)?.statusCode ?? 0
    if error == nil, (200..<300).contains(status),
      let id = task.taskDescription.flatMap(UUID.init(uuidString:)), let data,
      let result = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
      let saved = result["data"] as? [String: Any], saved["workout_id"] is String
    {
      do {
        let workoutID = saved["workout_id"] as? String
        try CompletionDisk.update(id, stage: .server, workoutID: workoutID)
        try RecordingDisk.acknowledge(id)
        WatchBridge.shared.acknowledge(id, workoutID: workoutID)
        DispatchQueue.main.async {
          self.retryStore.removeObject(forKey: "retry-at-" + id.uuidString)
          self.retryStore.removeObject(forKey: "retry-count-" + id.uuidString)
          self.pending = RecordingDisk.pending(account: APIClient.shared.account).count
          self.message = "Workout synced."
          self.scheduleRetry()
          self.sync()
          Task { await APIClient.shared.refresh() }
        }
      } catch { DispatchQueue.main.async { self.message = error.localizedDescription } }
    } else {
      DispatchQueue.main.async {
        if status == 409, let data,
          let result = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
          result["code"] as? String == "possible_duplicate",
          let candidates = result["candidates"],
          let id = task.taskDescription.flatMap(UUID.init(uuidString:)),
          var envelope = try? RecordingDisk.load(RecordingDisk.file(id)),
          envelope.healthOrigin != nil
        {
          do {
            envelope.duplicateCandidates = try JSONDecoder().decode(
              [HealthDuplicate].self,
              from: JSONSerialization.data(withJSONObject: candidates))
            try RecordingDisk.save(envelope)
            HealthImporter.shared.refreshReviews()
            self.message = "Review a possible duplicate in Your data → Apple Health & Watch."
            self.scheduleRetry()
            return
          } catch { self.message = error.localizedDescription }
        }
        if let id = task.taskDescription.flatMap(UUID.init(uuidString:)) {
          let key = "retry-count-" + id.uuidString
          let count = min(6, self.retryStore.integer(forKey: key) + 1)
          self.retryStore.set(count, forKey: key)
          // Avoid repeated authentication or validation failures; a manual retry bypasses this delay.
          let delay =
            (status == 0 || status == 429 || status >= 500)
            ? min(3600, 30 * pow(2, Double(count))) : 3600
          self.retryStore.set(
            Date().addingTimeInterval(delay).timeIntervalSince1970,
            forKey: "retry-at-" + id.uuidString)
        }
        let serverMessage =
          data.flatMap { try? JSONSerialization.jsonObject(with: $0) as? [String: Any] }?["message"]
          as? String
        self.message =
          status == 401
          ? "Sign in again to resume synchronization. Your workouts are retained."
          : "\(serverMessage ?? "Upload interrupted (\(status)).") Your workout is retained; automatic retry is scheduled."
        self.scheduleRetry()
      }
    }
  }
  func urlSessionDidFinishEvents(forBackgroundURLSession session: URLSession) {
    DispatchQueue.main.async {
      self.backgroundCompletion?()
      self.backgroundCompletion = nil
    }
  }
}

extension APIClient {
  func uploadArchive(_ source: URL, progress: @escaping (Double) -> Void) async throws -> Data {
    let boundary = "rint-" + UUID().uuidString
    let payload = FileManager.default.temporaryDirectory.appendingPathComponent(
      "rint-import-" + UUID().uuidString)
    defer { try? FileManager.default.removeItem(at: payload) }
    try await Task.detached {
      let size = try source.resourceValues(forKeys: [.fileSizeKey]).fileSize ?? 0
      guard size > 0, size <= 512 * 1024 * 1024 else {
        throw NSError(
          domain: "Rint", code: 1,
          userInfo: [NSLocalizedDescriptionKey: "Choose a nonempty ZIP up to 512 MB."])
      }
      FileManager.default.createFile(
        atPath: payload.path, contents: nil,
        attributes: [.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication])
      let output = try FileHandle(forWritingTo: payload)
      let input = try FileHandle(forReadingFrom: source)
      defer {
        try? output.close()
        try? input.close()
      }
      try output.write(
        contentsOf: Data(
          "--\(boundary)\r\nContent-Disposition: form-data; name=\"file\"; filename=\"strava.zip\"\r\nContent-Type: application/zip\r\n\r\n"
            .utf8))
      while let chunk = try input.read(upToCount: 64 * 1024), !chunk.isEmpty {
        try output.write(contentsOf: chunk)
      }
      try output.write(contentsOf: Data("\r\n--\(boundary)--\r\n".utf8))
    }.value
    var request = URLRequest(url: try url("rint/imports"))
    request.httpMethod = "POST"
    request.timeoutInterval = 300
    request.setValue(
      "multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
    if let token = TokenVault.load(account: account) {
      request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
    }
    let (data, response) = try await URLSession.shared.upload(
      for: request, fromFile: payload, delegate: ArchiveUploadProgress(progress))
    guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
      let message =
        (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["message"] as? String
        ?? "Archive upload failed. Select the ZIP again to retry."
      throw NSError(
        domain: "Rint", code: (response as? HTTPURLResponse)?.statusCode ?? 0,
        userInfo: [NSLocalizedDescriptionKey: message])
    }
    return data
  }
}

extension APIClient {
  func uploadPhoto(_ jpeg: Data, profile: Bool = false) async throws -> Data {
    let boundary = "rint-" + UUID().uuidString
    var body = Data(
      "--\(boundary)\r\nContent-Disposition: form-data; name=\"file\"; filename=\"workout.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n"
        .utf8)
    body.append(jpeg)
    body.append(Data("\r\n--\(boundary)--\r\n".utf8))
    var request = URLRequest(url: try url(profile ? "auth/picture" : "media"))
    request.httpMethod = "POST"
    request.setValue(
      "multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
    if let token = TokenVault.load(account: account) {
      request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
    }
    let (data, response) = try await URLSession.shared.upload(for: request, from: body)
    try await validateResourceResponse(response, data: data)
    return data
  }
  func downloadAccountArchive(_ name: String) async throws -> URL {
    guard !name.isEmpty, !name.contains("/"), !name.contains("\\"), name.hasSuffix(".zip") else {
      throw CocoaError(.fileReadInvalidFileName)
    }
    var request = URLRequest(url: try url("auth/account/export/" + name))
    if let token = TokenVault.load(account: account) {
      request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
    }
    let (temporary, response) = try await URLSession.shared.download(for: request)
    defer { try? FileManager.default.removeItem(at: temporary) }
    if let http = response as? HTTPURLResponse, !(200..<300).contains(http.statusCode) {
      // Only error responses are read into memory; full archives stream to disk.
      try await validateResourceResponse(
        response, data: (try? Data(contentsOf: temporary)) ?? Data())
    } else {
      try await validateResourceResponse(response, data: Data())
    }
    let destination = FileManager.default.temporaryDirectory.appendingPathComponent(
      "rint-account-" + UUID().uuidString + ".zip")
    try FileManager.default.moveItem(at: temporary, to: destination)
    try FileManager.default.setAttributes(
      [.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication],
      ofItemAtPath: destination.path)
    return destination
  }
  private func validateResourceResponse(_ response: URLResponse, data: Data) async throws {
    guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
      let message =
        (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["message"] as? String
        ?? "Your server could not complete the transfer. Please try again."
      if (response as? HTTPURLResponse)?.statusCode == 401 {
        await MainActor.run {
          try? TokenVault.remove(account: account)
          signedIn = false
          error = "Your session expired. Sign in again; saved workouts stay on this device."
        }
      }
      throw NSError(
        domain: "Rint", code: (response as? HTTPURLResponse)?.statusCode ?? 0,
        userInfo: [NSLocalizedDescriptionKey: message])
    }
  }
}
