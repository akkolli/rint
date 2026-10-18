import HealthKit
import SwiftUI

private let rintLime = Color(red: 0.83, green: 0.95, blue: 0.42)

@main
struct RintWatchApp: App {
  @StateObject private var recorder = WorkoutRecorder()
  @StateObject private var bridge = WatchBridge.shared
  @Environment(\.scenePhase) private var scenePhase
  var body: some Scene {
    WindowGroup {
      NavigationStack { WatchRecordView() }.environmentObject(recorder).environmentObject(bridge)
        .tint(rintLime).task {
          recorder.recover()
          bridge.transferPending()
          await HealthSaveQueue.shared.retry(
            account: UserDefaults.standard.string(forKey: "account") ?? "")
        }.onChange(of: scenePhase) { phase in
          if phase == .active {
            bridge.transferPending()
            Task {
              await HealthSaveQueue.shared.retry(
                account: UserDefaults.standard.string(forKey: "account") ?? "")
            }
          }
        }
    }
  }
}
struct WatchSport: Decodable, Identifiable {
  let id: Int
  let label: String
  let activity: Int
}
struct WatchRecordView: View {
  @EnvironmentObject var recorder: WorkoutRecorder
  @EnvironmentObject var bridge: WatchBridge
  @AppStorage("account") private var account = ""
  @AppStorage("sport_id") private var sportID = 0
  @ObservedObject private var healthSaves = HealthSaveQueue.shared
  @AppStorage("imperial_units") private var imperial = false
  @AppStorage("workout_activity") private var activity = Int(HKWorkoutActivityType.running.rawValue)
  @AppStorage("watch_sports") private var sportsData = Data()
  private var sports: [WatchSport] {
    (try? JSONDecoder().decode([WatchSport].self, from: sportsData)) ?? []
  }
  @State private var indoor = false
  @State private var finishConfirmation = false
  @State private var showingCompletion = true
  @State private var workoutPage = 0
  @Environment(\.dynamicTypeSize) private var typeSize
  private var liveMetrics: some View {
    VStack(alignment: .leading, spacing: 6) {
      HStack {
        Label(
          recorder.paused ? "PAUSED" : "RECORDING",
          systemImage: recorder.paused ? "pause.fill" : "record.circle"
        )
        .font(.caption2.bold()).foregroundStyle(recorder.paused ? .orange : rintLime)
        Spacer()
      }
      HStack(alignment: .firstTextBaseline, spacing: 8) {
        VStack(alignment: .leading, spacing: 1) {
          Text("Active time").font(.caption2).foregroundStyle(.secondary)
          ActiveWorkoutClock(recorder: recorder)
            .font(.system(.title2, design: .rounded).bold()).monospacedDigit()
        }
        Spacer(minLength: 0)
        VStack(alignment: .trailing, spacing: 1) {
          Text("Elapsed").font(.caption2).foregroundStyle(.secondary)
          WorkoutClock(started: recorder.startDate).font(.caption2).foregroundStyle(.secondary)
        }
      }
      HStack(alignment: .firstTextBaseline, spacing: 4) {
        Text(DisplayUnits.distance(recorder.distance))
          .font(.system(.title, design: .rounded).bold()).monospacedDigit().foregroundStyle(
            rintLime)
        Text(DisplayUnits.distanceUnit).font(.caption).foregroundStyle(.secondary)
        Spacer()
        VStack(alignment: .trailing, spacing: 1) {
          Text(
            recorder.currentActivity == .cycling
              ? "AVG " + DisplayUnits.speedUnit.uppercased()
              : "PACE /" + DisplayUnits.distanceUnit.uppercased()
          )
          .font(.caption2).foregroundStyle(.secondary)
          Text(
            recorder.currentActivity == .cycling
              ? DisplayUnits.speed(
                recorder.activeDuration > 0
                  ? recorder.distance / recorder.activeDuration : nil) : recorder.pace
          )
          .font(.headline).monospacedDigit()
        }
      }
      HStack {
        Label(
          (recorder.liveHeartRate.map { String(format: "%.0f", $0) } ?? "—") + " bpm",
          systemImage: "heart.fill"
        )
        .foregroundStyle(.pink).font(.subheadline.weight(.semibold)).monospacedDigit()
        Spacer()
        if let message = recorder.lapMessage {
          Text(message).font(.caption2).foregroundStyle(rintLime).lineLimit(1)
        } else {
          Text("Lap \(recorder.lapCount + 1)").font(.caption2).foregroundStyle(.secondary)
        }
      }
      HStack(spacing: 8) {
        Button {
          recorder.pauseOrResume()
        } label: {
          Label(
            recorder.paused ? "Resume" : "Pause",
            systemImage: recorder.paused ? "play.fill" : "pause.fill")
        }.frame(maxWidth: .infinity, minHeight: 44)
        Button {
          workoutPage = 1
        } label: {
          Image(systemName: "ellipsis").frame(width: 32, height: 44)
        }.accessibilityLabel("Workout controls")
      }.buttonStyle(.bordered)
    }.padding(.horizontal, 4)
  }
  var body: some View {
    Group {
      if recorder.active {
        TabView(selection: $workoutPage) {
          Group {
            if typeSize >= .xxxLarge { ScrollView { liveMetrics } } else { liveMetrics }
          }.tag(0)
          ScrollView {
            VStack(spacing: 8) {
              HStack {
                Button {
                  workoutPage = 0
                } label: {
                  Image(systemName: "chevron.left").frame(width: 32, height: 28)
                }.buttonStyle(.plain).accessibilityLabel("Back to workout metrics")
                Text("Controls").font(.subheadline.bold())
                Spacer()
              }
              Text(recorder.lapMessage ?? recorder.routeStatus).font(.caption2)
                .foregroundStyle(recorder.lapMessage == nil ? Color.secondary : rintLime)
              HStack(spacing: 8) {
                Button {
                  recorder.pauseOrResume()
                } label: {
                  Label(
                    recorder.paused ? "Resume" : "Pause",
                    systemImage: recorder.paused ? "play.fill" : "pause.fill"
                  )
                  .font(.caption2).frame(maxWidth: .infinity, minHeight: 44)
                }
                Button {
                  recorder.lap()
                } label: {
                  Label("Lap \(recorder.lapCount + 1)", systemImage: "flag")
                    .font(.caption2).frame(maxWidth: .infinity, minHeight: 44)
                }.accessibilityLabel("Mark lap \(recorder.lapCount + 1)")
              }
              Button {
                finishConfirmation = true
              } label: {
                Label(recorder.ending ? "Saving…" : "Finish & save", systemImage: "stop.fill")
              }.tint(.orange).frame(minHeight: 44)
              Text("Saved on Watch until safely synchronized.").font(.caption2).foregroundStyle(
                .secondary)
              if healthSaves.pending > 0 {
                Text("\(healthSaves.pending) Health saves waiting").font(.caption2)
                Button(healthSaves.retrying ? "Retrying…" : "Retry Health save") {
                  Task { await healthSaves.retry(account: account) }
                }.disabled(healthSaves.retrying)
                if let error = healthSaves.error {
                  Text(error).font(.caption2).foregroundStyle(.orange)
                }
              }
              if let error = recorder.error { Text(error).font(.caption2).foregroundStyle(.orange) }
            }.buttonStyle(.bordered).padding(.horizontal, 4)
          }.tag(1)
        }.tabViewStyle(.page).disabled(recorder.ending)
      } else if showingCompletion, let completion = recorder.lastCompletion {
        ScrollView {
          VStack(alignment: .leading, spacing: 14) {
            Label("Workout complete", systemImage: "checkmark.circle.fill").font(.headline)
              .foregroundStyle(rintLime)
            HStack(alignment: .firstTextBaseline, spacing: 4) {
              Text(DisplayUnits.distance(completion.distance)).font(
                .system(.largeTitle, design: .rounded).bold()
              ).monospacedDigit()
              Text(DisplayUnits.distanceUnit).font(.caption).foregroundStyle(.secondary)
            }
            HStack {
              VStack(alignment: .leading, spacing: 4) {
                Text("ACTIVE TIME").font(.system(size: 9, weight: .semibold)).foregroundStyle(
                  .secondary)
                Text(compactTimeLabel(completion.active)).font(.headline).monospacedDigit()
              }
              Spacer()
              VStack(alignment: .trailing, spacing: 4) {
                Text(
                  completion.usesSpeed
                    ? "SPEED " + DisplayUnits.speedUnit.uppercased()
                    : "PACE /" + DisplayUnits.distanceUnit.uppercased()
                ).font(.system(size: 9, weight: .semibold)).foregroundStyle(.secondary)
                Text(
                  completion.usesSpeed
                    ? DisplayUnits.speed(
                      completion.active > 0 ? completion.distance / completion.active : nil)
                    : DisplayUnits.pace(completion.pace)
                ).font(.headline).monospacedDigit()
              }
            }
            Divider()
            Label(
              completion.stage == .server
                ? "Synced to Rint"
                : completion.stage == .phone ? "Received by iPhone" : "Saved on Watch",
              systemImage: completion.stage == .server
                ? "checkmark.circle.fill" : "checkmark.shield"
            )
            .font(.caption.bold()).foregroundStyle(rintLime)
            if completion.stage != .server {
              Text(
                completion.stage == .phone
                  ? "Watch copy kept until upload completes."
                  : "Saved here. Syncs when iPhone reconnects."
              ).font(.caption2).foregroundStyle(.secondary)
            }
            if completion.stage != .server {
              Button("Retry sync") { bridge.transferPending() }.buttonStyle(.bordered)
            }
            Button("New workout") { showingCompletion = false }.buttonStyle(.borderedProminent)
              .foregroundStyle(.black)
          }.padding(.horizontal, 4)
        }
      } else {
        ScrollView {
          VStack(alignment: .leading, spacing: 10) {
            Text("Record").font(.system(.title3, design: .rounded).bold())
            if account.isEmpty || sportID == 0 {
              Text("Connect Rint on iPhone once. Then record with just your Watch.").font(.caption)
                .foregroundStyle(.secondary)
            }
            if !sports.isEmpty {
              NavigationLink {
                WatchSportSelection(sports: sports, selection: $sportID)
              } label: {
                VStack(spacing: 2) {
                  Text(sports.first(where: { $0.id == sportID })?.label ?? "Choose sport").font(
                    .headline)
                  Text(indoor ? "Indoor" : "Outdoor").font(.caption2).foregroundStyle(.secondary)
                }
              }.disabled(recorder.starting).onChange(of: sportID) { selected in
                if let sport = sports.first(where: { $0.id == selected }) {
                  activity = sport.activity
                }
              }
            }
            Toggle("Indoor workout", isOn: $indoor).font(.caption).disabled(recorder.starting)
            Button {
              workoutPage = 0
              Task {
                await recorder.start(
                  account: account, sportID: sportID,
                  activity: HKWorkoutActivityType(rawValue: UInt(activity)) ?? .running,
                  indoor: indoor)
              }
            } label: {
              Label(
                recorder.starting ? "Getting ready…" : "Start workout", systemImage: "play.fill"
              ).font(.headline)
            }
            .buttonStyle(.borderedProminent).foregroundStyle(.black)
            .disabled(
              account.isEmpty || sportID == 0 || !RecordingDisk.drafts().isEmpty
                || recorder.starting)
            if let message = recorder.savedMessage {
              Label(message, systemImage: "checkmark.circle").font(.caption2)
            }
            if !RecordingDisk.pending().isEmpty {
              Label(
                "\(RecordingDisk.pending().count) saved for sync",
                systemImage: "arrow.triangle.2.circlepath"
              ).font(.caption2).foregroundStyle(.secondary)
              Button("Retry transfer") { bridge.transferPending() }
            }
            if healthSaves.pending > 0 {
              Text("\(healthSaves.pending) Health saves waiting").font(.caption2)
              Button(healthSaves.retrying ? "Retrying…" : "Retry Health save") {
                Task { await healthSaves.retry(account: account) }
              }.disabled(healthSaves.retrying)
              if let error = healthSaves.error {
                Text(error).font(.caption2).foregroundStyle(.orange)
              }
            }
            if let error = recorder.error {
              Text(error).font(.caption2).foregroundStyle(.orange)
              if !RecordingDisk.drafts().isEmpty {
                Button("Save interrupted workout") { recorder.saveInterrupted() }
              }
            }
            if let error = bridge.error { Text(error).font(.caption2).foregroundStyle(.orange) }
          }.padding(.horizontal, 4)
        }
      }
    }.onAppear { recorder.restoreCompletion(account: account) }
      .onChange(of: recorder.lastCompletion?.id) { id in if id != nil { showingCompletion = true } }
      .onChange(of: bridge.completionRevision) { _ in recorder.restoreCompletion(account: account) }
      .confirmationDialog(
        "Finish this workout?", isPresented: $finishConfirmation, titleVisibility: .visible
      ) {
        Button("Finish and save") {
          finishConfirmation = false
          Task { await recorder.finish() }
        }
        Button("Keep recording", role: .cancel) {}
      }
  }
}

private struct WatchSportSelection: View {
  let sports: [WatchSport]
  @Binding var selection: Int
  @Environment(\.dismiss) private var dismiss
  var body: some View {
    List(
      sports.sorted { ($0.id == selection ? 0 : 1, $0.id) < ($1.id == selection ? 0 : 1, $1.id) }
    ) { sport in
      Button {
        selection = sport.id
        dismiss()
      } label: {
        HStack {
          Text(sport.label)
          Spacer()
          if sport.id == selection { Image(systemName: "checkmark").foregroundStyle(rintLime) }
        }
      }.accessibilityLabel(sport.label + (sport.id == selection ? ", selected" : ""))
    }.navigationTitle("Sport")
  }
}
