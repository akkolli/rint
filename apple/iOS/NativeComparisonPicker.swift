import SwiftUI

struct NativeComparisonPicker: View {
  let current: FeedActivity
  @Binding var selection: FeedActivity?
  @EnvironmentObject var api: APIClient
  @Environment(\.dismiss) private var dismiss
  @State private var activities: [FeedActivity] = []
  @State private var page = 0
  @State private var more = true
  @State private var loading = false
  @State private var error: String?
  var body: some View {
    NavigationStack {
      List {
        Section {
          Text(
            "Compare against another of your workouts. Charts align by elapsed time from the start."
          ).font(.subheadline).foregroundStyle(RintStyle.muted)
        }
        Button("Remove comparison") {
          selection = nil
          dismiss()
        }
        ForEach(activities.filter { $0.id != current.id && $0.withStream != false }) { activity in
          Button {
            selection = activity
            dismiss()
          } label: {
            VStack(alignment: .leading, spacing: 5) {
              Text(activity.title ?? "Activity").font(.headline)
              if let date = activity.date {
                Text(date.formatted(date: .abbreviated, time: .omitted)).font(.caption)
                  .foregroundStyle(RintStyle.muted)
              }
            }.padding(.vertical, 4)
          }
        }
        if loading { ProgressView("Loading workouts…") }
        if more { Button("Load more workouts") { Task { await load() } }.disabled(loading) }
        if let error {
          RintNotice(text: error, icon: "exclamationmark.circle")
          Button("Try again") { Task { await load() } }
        }
      }.scrollContentBackground(.hidden).background(RintStyle.paper).navigationTitle(
        "Compare activity"
      )
      .toolbar { ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } } }
      .task { await load() }
    }
  }
  @MainActor func load() async {
    guard !loading else { return }
    loading = true
    error = nil
    defer { loading = false }
    do {
      let sport = current.sportID.map { "&sport_id=\($0)" } ?? ""
      let response = try JSONDecoder().decode(
        APIResponse<FeedResponse>.self,
        from: await api.request("workouts?per_page=25&page=\(page + 1)" + sport))
      activities += response.data.workouts.filter { row in
        !activities.contains(where: { $0.id == row.id })
      }
      page += 1
      more = response.pagination?.hasNext ?? false
    } catch { self.error = error.localizedDescription }
  }
}
