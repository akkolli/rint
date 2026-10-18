import SwiftUI
import UIKit

struct HealthImportView: View {
  @StateObject private var health = HealthImporter.shared
  @EnvironmentObject var api: APIClient
  @EnvironmentObject var queue: SyncQueue
  @Environment(\.dismiss) private var dismiss
  @State private var watchOnly = false
  @State private var allHistory = true
  @State private var since = Calendar.current.date(byAdding: .year, value: -1, to: Date())!
  private var selectionChanged: Bool {
    watchOnly != health.state.watchOnly || (allHistory ? nil : since) != health.state.since
  }

  var body: some View {
    Form {
      Section {
        VStack(alignment: .leading, spacing: 12) {
          HStack {
            Image(systemName: "heart.fill").font(.title2).foregroundStyle(RintStyle.heart)
              .accessibilityHidden(true)
            Spacer()
            Label(
              health.state.connected ? "Health setup complete" : "Private by default",
              systemImage: health.state.connected ? "checkmark.circle" : "lock.shield"
            ).font(.caption).foregroundStyle(RintStyle.muted)
          }
          Text("Workout history")
            .font(.title.bold()).tracking(-0.6)
          Text(
            "Imports are private. Existing sharing settings stay unchanged."
          )
          .font(.subheadline).foregroundStyle(RintStyle.muted)
        }.padding(.vertical, 4)
      }.listRowBackground(Color.clear).listRowInsets(
        EdgeInsets(top: 4, leading: 4, bottom: 4, trailing: 4))
      Section("1 · Choose your history") {
        Toggle("Apple Watch workouts only", isOn: $watchOnly).disabled(health.busy)
        Toggle("All available history", isOn: $allHistory).disabled(health.busy)
        if !allHistory {
          DatePicker("From", selection: $since, in: ...Date(), displayedComponents: .date)
            .disabled(health.busy)
        }
        Button(health.state.connected ? "Review selected history" : "Connect Apple Health") {
          Task { await health.connect(watchOnly: watchOnly, since: allHistory ? nil : since) }
        }.buttonStyle(RintSecondaryButton()).disabled(health.busy)
        if let count = health.previewCount, !selectionChanged {
          Label("\(count) accessible workouts", systemImage: "checklist").font(.headline).padding(
            .vertical, 8)
        }
        if health.state.connected && !health.state.historyComplete {
          Button(
            health.state.historyComplete ? "Check for missing workouts" : "Import selected history"
          ) {
            Task {
              if health.state.historyComplete {
                await health.rescanHistory()
              } else {
                await health.synchronize(refreshRecent: true)
              }
            }
          }.buttonStyle(RintPrimaryButton()).disabled(
            health.busy || selectionChanged || health.previewCount == 0)
          if selectionChanged {
            Text("Review your updated selection before importing.").font(.footnote)
              .foregroundStyle(RintStyle.muted)
          }
        }
      }
      if health.state.connected {
        Section("2 · Import & review") {
          if health.busy {
            ProgressView(value: Double(health.processed), total: Double(max(1, health.total)))
            Text("\(health.processed) of \(health.total) checked · progress saved").font(.caption)
          }
          if !health.message.isEmpty { Text(health.message).font(.subheadline) }
          if health.state.historyComplete && !health.busy && health.reviews.isEmpty {
            Label("History checked", systemImage: "checkmark.circle.fill").font(.headline)
            Text(
              queue.pending == 0
                ? "Open your workouts to explore charts and best efforts."
                : "\(queue.pending) workouts are retained on your phone while uploads finish."
            )
            .font(.footnote).foregroundStyle(RintStyle.muted)
            Button("View my workouts") {
              api.selectedTrainingSection = "History"
              api.selectedTab = 1
              dismiss()
            }.buttonStyle(RintPrimaryButton())
            Button("Check for missing workouts") { Task { await health.rescanHistory() } }
              .font(.subheadline).frame(minHeight: 44).disabled(selectionChanged)
          }
        }
      }
      if !health.reviews.isEmpty {
        Section("Review possible matches") {
          ForEach(health.reviews) { envelope in
            HealthDuplicateReview(envelope: envelope, health: health)
          }
        }
      }
      if !health.state.failures.isEmpty {
        Section("Workouts needing attention") {
          ForEach(health.state.failures.keys.sorted(), id: \.self) { id in
            VStack(alignment: .leading) {
              Text(id).font(.caption)
              Text(health.state.failures[id] ?? "").font(.footnote)
            }
          }
          Button("Retry failed reads") { Task { await health.synchronize() } }.disabled(health.busy)
        }
      }
      Section("3 · Keep future workouts in sync") {
        Toggle(
          "Automatically sync new workouts",
          isOn: Binding(
            get: { health.state.automatic },
            set: { health.setAutomatic($0) })
        ).disabled(!health.state.connected || health.busy)
        if let date = health.state.lastChecked {
          LabeledContent("Last checked", value: date.formatted())
        }
        Label(
          queue.pending == 0 ? "No uploads waiting" : "\(queue.pending) workouts waiting to upload",
          systemImage: queue.pending == 0 ? "checkmark.circle" : "arrow.triangle.2.circlepath"
        ).font(.footnote)
        Text(
          "iOS decides when background updates run. Opening Rint catches up; offline workouts stay on your phone until uploaded."
        )
        .font(.caption).foregroundStyle(.secondary)
      }
      Section("Access and privacy") {
        Text(
          "Apple does not tell Rint which read permissions you declined. Missing workouts or charts may mean limited access. You can change access in Health → your profile → Apps → Rint."
        )
        .font(.footnote)
        Button("Open app settings") {
          if let url = URL(string: UIApplication.openSettingsURLString) {
            UIApplication.shared.open(url)
          }
        }
        if health.state.connected {
          Button("Disconnect Health", role: .destructive) { health.disconnect() }
        }
        Text(
          "Deleting a workout in Health does not delete an imported Rint activity. Disconnecting stops Health reads; retained uploads can still finish."
        )
        .font(.caption).foregroundStyle(.secondary)
      }
    }.scrollContentBackground(.hidden).background(RintStyle.paper)
      .navigationTitle("Apple Health & Watch").navigationBarTitleDisplayMode(.inline)
      .toolbar(.hidden, for: .tabBar)
      .tint(RintStyle.ink)
      .onAppear {
        health.restore()
        watchOnly = health.state.watchOnly
        allHistory = health.state.since == nil
        since = health.state.since ?? since
      }
  }
}

struct HealthDuplicateReview: View {
  let envelope: Envelope
  @ObservedObject var health: HealthImporter
  @State private var choice = ""
  var body: some View {
    VStack(alignment: .leading, spacing: 16) {
      Text(envelope.title).font(.headline)
      Text(String(envelope.recording.startedAt.prefix(16))).font(.caption).foregroundStyle(
        RintStyle.muted)
      Text(
        "This may already be in your history. Linking adds Health data and preserves its sharing settings."
      )
      .font(.footnote).foregroundStyle(RintStyle.muted)
      ForEach(envelope.duplicateCandidates ?? []) { candidate in
        Button {
          choice = candidate.id
        } label: {
          HStack {
            Image(systemName: choice == candidate.id ? "checkmark.circle.fill" : "circle")
            Text("Link to " + candidate.title).multilineTextAlignment(.leading)
          }.frame(maxWidth: .infinity, minHeight: 44, alignment: .leading).padding(.vertical, 10)
        }.buttonStyle(.plain).accessibilityAddTraits(choice == candidate.id ? .isSelected : [])
      }
      Button {
        choice = "separate"
      } label: {
        Label(
          "Keep as a separate workout",
          systemImage: choice == "separate" ? "checkmark.circle.fill" : "circle"
        )
        .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading).padding(.vertical, 10)
      }.buttonStyle(.plain)
      Button("Confirm choice") {
        health.resolve(envelope, workoutID: choice == "separate" ? nil : choice)
      }
      .buttonStyle(RintPrimaryButton()).disabled(choice.isEmpty)
    }.padding(.vertical, 10)
  }
}
