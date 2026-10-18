import Combine
import Foundation
import HealthKit
import WatchConnectivity

final class WatchBridge: NSObject, WCSessionDelegate, ObservableObject {
  static let shared = WatchBridge()
  @Published var error: String?
  @Published var completionRevision = 0
  var received: (() -> Void)?
  private var desiredContext: [String: Any]?
  private let contextLock = NSLock()
  private override init() {
    super.init()
    if WCSession.isSupported() {
      WCSession.default.delegate = self
      WCSession.default.activate()
    }
  }
  func transferPending() {
    guard WCSession.isSupported(), WCSession.default.activationState == .activated else { return }
    #if os(watchOS)
      let outstanding = Set(
        WCSession.default.outstandingFileTransfers.compactMap { $0.file.metadata?["id"] as? String }
      )
      for url in RecordingDisk.pending() {
        if let recording = try? RecordingDisk.load(url),
          !outstanding.contains(recording.id.uuidString)
        {
          var metadata: [String: Any] = ["id": recording.id.uuidString]
          if let summary = try? Data(contentsOf: CompletionDisk.file(recording.id)) {
            metadata["completion"] = summary
          }
          WCSession.default.transferFile(url, metadata: metadata)
        }
      }
    #endif
  }
  func configure(
    account: String, sportID: Int, activity: HKWorkoutActivityType = .running,
    sports: [[String: Any]] = []
  ) {
    contextLock.lock()
    desiredContext = [
      "account": account, "sport_id": sportID, "workout_activity": Int(activity.rawValue),
      "imperial_units": DisplayUnits.imperial, "sports": sports,
    ]
    contextLock.unlock()
    sendConfiguration()
  }
  private func sendConfiguration() {
    contextLock.lock()
    let context = desiredContext
    contextLock.unlock()
    guard WCSession.isSupported(), WCSession.default.activationState == .activated,
      let context
    else { return }
    do {
      try WCSession.default.updateApplicationContext(context)
      DispatchQueue.main.async { self.error = nil }
    } catch { DispatchQueue.main.async { self.error = error.localizedDescription } }
  }
  func acknowledge(_ id: UUID, workoutID: String? = nil) {
    guard WCSession.isSupported() else { return }
    var receipt = ["ack": id.uuidString]
    if let workoutID { receipt["workout_id"] = workoutID }
    WCSession.default.transferUserInfo(receipt)
  }
  func session(
    _ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState,
    error: Error?
  ) {
    sendConfiguration()
    transferPending()
  }
  func session(_ session: WCSession, didReceive file: WCSessionFile) {
    // Apple's temporary file disappears when this callback returns. Copy durably first.
    do {
      let envelope = try RecordingDisk.load(file.fileURL)
      try RecordingDisk.save(envelope)
      #if os(iOS)
        if let data = file.metadata?["completion"] as? Data,
          var summary = try? JSONDecoder().decode(WorkoutCompletion.self, from: data),
          summary.id == envelope.id, summary.account == envelope.account
        {
          if FileManager.default.fileExists(atPath: CompletionDisk.file(envelope.id).path) {
            try? CompletionDisk.update(envelope.id, stage: .phone)
          } else {
            summary.stage = .phone
            try? CompletionDisk.save(summary)
          }
        }
        session.transferUserInfo(["received": envelope.id.uuidString])
        DispatchQueue.main.async { self.completionRevision += 1 }
      #endif
      DispatchQueue.main.async { self.received?() }
    } catch {
      DispatchQueue.main.async {
        self.error = "Could not retain watch workout: \(error.localizedDescription)"
      }
    }
  }
  func session(_ session: WCSession, didReceiveUserInfo userInfo: [String: Any]) {
    if let text = userInfo["received"] as? String, let id = UUID(uuidString: text) {
      do { try CompletionDisk.update(id, stage: .phone) } catch {
        DispatchQueue.main.async { self.error = error.localizedDescription }
      }
      DispatchQueue.main.async { self.completionRevision += 1 }
    }
    if let text = userInfo["ack"] as? String, let id = UUID(uuidString: text) {
      do {
        try CompletionDisk.update(id, stage: .server, workoutID: userInfo["workout_id"] as? String)
        try RecordingDisk.acknowledge(id)
      } catch {
        DispatchQueue.main.async { self.error = error.localizedDescription }
      }
      DispatchQueue.main.async { self.completionRevision += 1 }
    }
  }
  func session(_ session: WCSession, didReceiveApplicationContext context: [String: Any]) {
    if let account = context["account"] as? String {
      UserDefaults.standard.set(account, forKey: "account")
    }
    if let sport = context["sport_id"] as? Int {
      UserDefaults.standard.set(sport, forKey: "sport_id")
    }
    if let sports = context["sports"] as? [[String: Any]],
      let data = try? JSONSerialization.data(withJSONObject: sports)
    {
      UserDefaults.standard.set(data, forKey: "watch_sports")
    }
    if let imperial = context["imperial_units"] as? Bool {
      UserDefaults.standard.set(imperial, forKey: "imperial_units")
    }
    if let activity = context["workout_activity"] as? Int {
      UserDefaults.standard.set(activity, forKey: "workout_activity")
    }
  }
  #if os(iOS)
    func sessionDidBecomeInactive(_ session: WCSession) {}
    func sessionDidDeactivate(_ session: WCSession) { session.activate() }
  #endif
}
