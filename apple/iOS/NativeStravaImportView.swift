import SwiftUI
import UniformTypeIdentifiers

struct NativeImportItem: Decodable, Identifiable {
  let index: Int
  let title: String
  let sport: String
  let status: String
  var error: String? = nil
  var workoutID: String? = nil
  var id: Int { index }
  enum CodingKeys: String, CodingKey {
    case index, title, sport, status, error
    case workoutID = "workout_id"
  }
}
struct NativeImportBatch: Decodable, Identifiable {
  let id: String
  let visibility: String
  let total: Int
  let completed: Int
  let items: [NativeImportItem]
  var pending: Int { items.filter { $0.status == "pending" }.count }
  var failures: Int { items.filter { $0.status == "error" }.count }
  var duplicates: Int { items.filter { $0.status == "duplicate" }.count }
}
struct NativeStravaImportView: View {
  @EnvironmentObject var api: APIClient
  @State private var batches: [NativeImportBatch] = []
  @State private var batch: NativeImportBatch?
  @State private var choosingFile = false
  @State private var loading = false
  @State private var running = false
  @State private var stopAfterBatch = false
  @State private var progress: Double?
  @State private var audience = "private"
  @State private var error: String?
  var body: some View {
    List {
      Section {
        Label("Bring your Strava history", systemImage: "square.and.arrow.down").font(
          .title2.bold())
        Text(
          "Choose your account export ZIP. Rint preserves original FIT, GPX and TCX recordings, titles, dates, sport types and available photos."
        ).font(.subheadline).foregroundStyle(RintStyle.muted)
        Button("Choose export ZIP") { choosingFile = true }.disabled(loading || running)
        if let progress {
          ProgressView(value: progress) {
            Text(
              progress == 0
                ? "Preparing your archive…" : "Uploading archive · \(Int(progress * 100))%")
          }
        }
        Text(
          "Archives up to 512 MB. Processing can resume after you leave; interrupted archive uploads must be selected again."
        ).font(.footnote).foregroundStyle(RintStyle.muted)
      }
      if let batch {
        Section("Review before importing") {
          HStack {
            RintMetric(title: "Activities", value: String(batch.total))
            RintMetric(title: "Duplicates", value: String(batch.duplicates))
          }
          Picker("Activity audience", selection: $audience) {
            Text("Only me").tag("private")
            Text("Followers").tag("followers_only")
            Text("Everyone").tag("public")
          }.disabled(running)
          RintNotice(
            text:
              "Routes stay private. You can share a protected route later from each activity. Photo location metadata is removed.",
            icon: "lock.shield")
          ProgressView(value: Double(batch.completed), total: Double(max(1, batch.total))) {
            Text("\(batch.completed) of \(batch.total) reviewed")
          }
          if running {
            Button(stopAfterBatch ? "Pausing after this batch…" : "Pause import") {
              stopAfterBatch = true
            }.disabled(stopAfterBatch)
          } else if batch.pending > 0 {
            Button(batch.completed > 0 ? "Resume import" : "Import activities") {
              Task { await process() }
            }
          } else {
            Label("Import complete", systemImage: "checkmark.circle").foregroundStyle(
              RintStyle.violet)
          }
          if batch.failures > 0 && !running {
            Button("Retry \(batch.failures) failed activities") {
              Task { await process(retry: true) }
            }
          }
        }
        Section("Activities") {
          ForEach(batch.items) { item in
            VStack(alignment: .leading, spacing: 6) {
              if let id = item.workoutID {
                NavigationLink(item.title) { NativeActivityDestination(workoutID: id) }
              } else {
                Text(item.title).font(.headline)
              }
              Text("\(item.sport) · \(item.status.capitalized)").font(.caption).foregroundStyle(
                RintStyle.muted)
              if let error = item.error {
                Text(error).font(.footnote).foregroundStyle(RintStyle.heart)
              }
            }.padding(.vertical, 4)
          }
        }
      }
      if !batches.isEmpty {
        Section("Previous imports") {
          ForEach(batches) { previous in
            Button {
              batch = previous
              audience = previous.visibility
            } label: {
              HStack {
                Text("\(previous.completed)/\(previous.total) activities")
                Spacer()
                Text(previous.pending > 0 ? "Resume" : "Review").font(.caption)
              }
            }.disabled(running || loading)
          }
        }
      }
      if let error {
        Section {
          RintNotice(text: error, icon: "exclamationmark.circle")
          Button("Refresh imports") { Task { await load() } }
        }
      }
      if loading && progress == nil { ProgressView("Loading imports…") }
    }.scrollContentBackground(.hidden).background(RintStyle.paper).navigationTitle(
      "Strava migration"
    ).navigationBarTitleDisplayMode(.inline)
      .fileImporter(isPresented: $choosingFile, allowedContentTypes: [.zip]) { result in
        switch result {
        case .success(let url): Task { await upload(url) }
        case .failure(let failure): error = failure.localizedDescription
        }
      }.task { await load() }.onDisappear { stopAfterBatch = true }
  }
  @MainActor func load() async {
    loading = true
    error = nil
    defer { loading = false }
    do {
      batches = try JSONDecoder().decode(
        APIResponse<[NativeImportBatch]>.self, from: await api.request("rint/imports")
      ).data
    } catch { self.error = error.localizedDescription }
  }
  @MainActor func upload(_ url: URL) async {
    loading = true
    error = nil
    progress = 0
    let scoped = url.startAccessingSecurityScopedResource()
    defer {
      if scoped { url.stopAccessingSecurityScopedResource() }
      loading = false
      progress = nil
    }
    do {
      let data = try await api.uploadArchive(url) { value in Task { @MainActor in progress = value }
      }
      batch = try JSONDecoder().decode(APIResponse<NativeImportBatch>.self, from: data).data
      audience = batch?.visibility ?? "private"
      await load()
    } catch { self.error = error.localizedDescription }
  }
  @MainActor func process(retry: Bool = false) async {
    guard let id = batch?.id, !running else { return }
    running = true
    stopAfterBatch = false
    error = nil
    defer { running = false }
    do {
      var shouldRetry = retry
      repeat {
        let updated = try JSONDecoder().decode(
          APIResponse<NativeImportBatch>.self,
          from: await api.request(
            "rint/imports/\(id)", method: "POST",
            body: JSONSerialization.data(withJSONObject: [
              "visibility": audience, "retry_errors": shouldRetry,
            ]))
        ).data
        batch = updated
        shouldRetry = false
      } while (batch?.pending ?? 0) > 0 && !stopAfterBatch
      await load()
      await api.refresh()
    } catch { self.error = error.localizedDescription }
  }
}
final class ArchiveUploadProgress: NSObject, URLSessionTaskDelegate {
  let update: (Double) -> Void
  init(_ update: @escaping (Double) -> Void) { self.update = update }
  func urlSession(
    _ session: URLSession, task: URLSessionTask, didSendBodyData bytesSent: Int64,
    totalBytesSent: Int64, totalBytesExpectedToSend: Int64
  ) {
    if totalBytesExpectedToSend > 0 {
      update(Double(totalBytesSent) / Double(totalBytesExpectedToSend))
    }
  }
}
