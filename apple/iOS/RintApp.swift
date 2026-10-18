import BackgroundTasks
import SwiftUI
import UIKit

@MainActor final class AppDelegate: NSObject, UIApplicationDelegate {
  func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil
  ) -> Bool {
    HealthImporter.shared.observe()
    BGTaskScheduler.shared.register(forTaskWithIdentifier: "org.rint.sync", using: nil) { task in
      DispatchQueue.main.async {
        // Complete only after the persistent URLSession tasks have been scheduled.
        SyncQueue.shared.sync { task.setTaskCompleted(success: true) }
      }
    }
    return true
  }
  func application(
    _ application: UIApplication, handleEventsForBackgroundURLSession identifier: String,
    completionHandler: @escaping () -> Void
  ) {
    SyncQueue.shared.backgroundCompletion = completionHandler
    _ = SyncQueue.shared.session
  }
}
@main
struct RintApp: App {
  @UIApplicationDelegateAdaptor(AppDelegate.self) var delegate
  @StateObject private var api = APIClient.shared
  @StateObject private var queue = SyncQueue.shared
  @StateObject private var recorder = WorkoutRecorder()
  @Environment(\.scenePhase) private var scenePhase
  var body: some Scene {
    WindowGroup {
      PhoneRoot().environmentObject(api).environmentObject(queue).environmentObject(recorder)
        .tint(RintStyle.ink)
        .task {
          recorder.completed = { queue.sync() }
          recorder.recover()
          if api.signedIn {
            await HealthSaveQueue.shared.retry(account: api.account)
            await api.refresh()
            queue.sync()
            HealthImporter.shared.observe()
            if HealthImporter.shared.state.automatic {
              await HealthImporter.shared.synchronize(refreshRecent: true)
            }
          }
        }
        .onOpenURL { url in
          guard url.scheme == "rint" else { return }
          if url.host == "record" { api.selectedTab = 2 }
          if url.host == "health", api.signedIn { api.showingHealth = true }
        }
        .sheet(isPresented: $api.showingHealth) {
          NavigationStack {
            HealthImportView().toolbar {
              ToolbarItem(placement: .confirmationAction) {
                Button("Done") { api.showingHealth = false }
              }
            }
          }.environmentObject(api).environmentObject(queue)
        }
        .onChange(of: scenePhase) { _, phase in
          if phase == .active {
            queue.sync()
            Task {
              if api.signedIn {
                await HealthSaveQueue.shared.retry(account: api.account)
                await api.refresh()
                HealthImporter.shared.observe()
                if HealthImporter.shared.state.automatic {
                  await HealthImporter.shared.synchronize(refreshRecent: true)
                }
              }
            }
          }
        }
    }
  }
}
