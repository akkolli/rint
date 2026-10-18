import SwiftUI

struct NativeProfileEditor: View {
  @EnvironmentObject var api: APIClient
  @State private var firstName = ""
  @State private var lastName = ""
  @State private var location = ""
  @State private var bio = ""
  @State private var birthDate = ""
  @State private var loading = true
  @State private var loaded = false
  @State private var saving = false
  @State private var message: String?
  @State private var error: String?
  private var valid: Bool {
    firstName.count <= 80 && lastName.count <= 80 && location.count <= 80 && bio.count <= 500
  }
  var body: some View {
    Form {
      Section("Your public profile") {
        NavigationLink("Profile photo") { NativePhotoAttachment(workoutID: nil) }
        TextField("First name", text: $firstName).textContentType(.givenName)
        TextField("Last name", text: $lastName).textContentType(.familyName)
        TextField("Location", text: $location).textContentType(.addressCity)
        TextField("About you", text: $bio, axis: .vertical).lineLimit(3...6)
        Text("\(bio.count)/500 characters").font(.caption).foregroundStyle(
          bio.count > 500 ? .red : RintStyle.muted)
        Text(
          "These details appear on your profile. Share only what you want your community to see."
        )
        .font(.footnote).foregroundStyle(RintStyle.muted)
      }.disabled(loading || saving)
      Section("Birthday · optional") {
        TextField("YYYY-MM-DD", text: $birthDate).textInputAutocapitalization(.never)
          .autocorrectionDisabled()
        Text(
          "Leave blank to remove your birthday. You can keep your profile hidden in Units & privacy."
        )
        .font(.footnote).foregroundStyle(RintStyle.muted)
      }.disabled(loading || saving)
      Section {
        if loading { ProgressView("Loading profile…") }
        Button(saving ? "Saving…" : "Save profile") { Task { await save() } }
          .disabled(loading || saving || !loaded || !valid)
        if !valid {
          Text("Names and location allow 80 characters; your bio allows 500.").font(.footnote)
        }
        if let message { RintNotice(text: message, icon: "checkmark.circle") }
        if let error {
          RintNotice(text: error, icon: "exclamationmark.circle")
          if !loaded { Button("Try again") { Task { await load() } } }
        }
      }
    }.scrollContentBackground(.hidden).background(RintStyle.paper)
      .navigationTitle("Edit profile").navigationBarTitleDisplayMode(.inline)
      .task { await load() }
  }
  @MainActor func load() async {
    loading = true
    error = nil
    defer { loading = false }
    do {
      let response =
        try JSONSerialization.jsonObject(with: await api.request("auth/profile")) as? [String: Any]
      guard let profile = response?["data"] as? [String: Any] else {
        throw CocoaError(.fileReadCorruptFile)
      }
      firstName = profile["first_name"] as? String ?? ""
      lastName = profile["last_name"] as? String ?? ""
      location = profile["location"] as? String ?? ""
      bio = profile["bio"] as? String ?? ""
      if let raw = profile["birth_date"] as? String, !raw.isEmpty {
        let parser = DateFormatter()
        parser.locale = Locale(identifier: "en_US_POSIX")
        parser.timeZone = TimeZone(secondsFromGMT: 0)
        parser.dateFormat = "EEE, dd MMM yyyy HH:mm:ss zzz"
        if let date = parser.date(from: raw) {
          parser.dateFormat = "yyyy-MM-dd"
          birthDate = parser.string(from: date)
        } else {
          throw CocoaError(.fileReadCorruptFile)
        }
      } else {
        birthDate = ""
      }
      loaded = true
    } catch { self.error = error.localizedDescription }
  }
  @MainActor func save() async {
    guard valid, loaded, !saving, !loading else { return }
    saving = true
    message = nil
    error = nil
    defer { saving = false }
    do {
      let date = birthDate.trimmingCharacters(in: .whitespacesAndNewlines)
      if !date.isEmpty {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(secondsFromGMT: 0)
        formatter.dateFormat = "yyyy-MM-dd"
        formatter.isLenient = false
        guard let parsed = formatter.date(from: date), formatter.string(from: parsed) == date,
          parsed <= Date()
        else {
          throw NSError(
            domain: "Rint", code: 1,
            userInfo: [
              NSLocalizedDescriptionKey: "Enter a valid birthday as YYYY-MM-DD, or leave it blank."
            ])
        }
      }
      _ = try await api.request(
        "auth/profile/edit", method: "POST",
        body: JSONSerialization.data(withJSONObject: [
          "first_name": firstName, "last_name": lastName, "location": location, "bio": bio,
          "birth_date": date,
        ]))
      await api.refresh()
      message = "Your profile is saved."
    } catch { self.error = error.localizedDescription }
  }
}

struct NativeAccountExport: View {
  struct Job: Decodable {
    let status: String
    let fileName: String?
    let fileSize: Int?
    let progress: Int?
    enum CodingKeys: String, CodingKey {
      case status, progress
      case fileName = "file_name"
      case fileSize = "file_size"
    }
  }
  struct Response: Decodable { let request: Job? }
  @EnvironmentObject var api: APIClient
  @State private var job: Job?
  @State private var loading = true
  @State private var busy = false
  @State private var error: String?
  @State private var archive: URL?
  private var inProgress: Bool { job?.status == "queued" || job?.status == "in_progress" }
  var body: some View {
    List {
      Section {
        Label("Your history belongs to you.", systemImage: "archivebox").font(.title3.bold())
        Text(
          "Export your account, original recordings, sensor streams and activity photos as a ZIP. All exports are free."
        )
        .font(.subheadline).foregroundStyle(RintStyle.muted)
      }
      Section("Full account archive") {
        if loading { ProgressView("Checking export…") }
        if let job {
          if job.status == "successful", let name = job.fileName {
            Label("Archive ready", systemImage: "checkmark.circle")
            if let size = job.fileSize {
              Text(ByteCountFormatter.string(fromByteCount: Int64(size), countStyle: .file)).font(
                .caption)
            }
            Button(busy ? "Downloading…" : "Download archive") { Task { await download(name) } }
              .disabled(busy)
          } else if inProgress {
            ProgressView(value: Double(job.progress ?? 0), total: 100)
            Text(
              job.status == "queued"
                ? "Waiting for your server to prepare the archive." : "Preparing your archive…")
            Text(
              "You can leave this screen and come back. Self-hosted servers need the export worker enabled."
            )
            .font(.footnote).foregroundStyle(RintStyle.muted)
          } else {
            Label("Export needs attention", systemImage: "exclamationmark.circle")
          }
        }
        if let archive { ShareLink("Save or share archive", item: archive) }
        Button(busy ? "Working…" : "Request a new export") { Task { await requestExport() } }
          .disabled(busy || loading || inProgress)
        Text(
          "Your server limits how often a new archive can be requested. Existing archives remain downloadable until they expire."
        )
        .font(.footnote).foregroundStyle(RintStyle.muted)
        Button("Refresh status") { Task { await load() } }.disabled(busy)
        if let error { RintNotice(text: error, icon: "exclamationmark.circle") }
      }
    }.scrollContentBackground(.hidden).background(RintStyle.paper)
      .navigationTitle("Export your data").navigationBarTitleDisplayMode(.inline)
      .task { await load() }.refreshable { await load() }
  }
  @MainActor func load() async {
    loading = true
    error = nil
    defer { loading = false }
    do {
      job = try JSONDecoder().decode(Response.self, from: await api.request("auth/account/export"))
        .request
    } catch { self.error = error.localizedDescription }
  }
  @MainActor func requestExport() async {
    busy = true
    error = nil
    defer { busy = false }
    do {
      job = try JSONDecoder().decode(
        Response.self, from: await api.request("auth/account/export/request", method: "POST")
      ).request
      archive = nil
    } catch { self.error = error.localizedDescription }
  }
  @MainActor func download(_ name: String) async {
    busy = true
    error = nil
    defer { busy = false }
    do { archive = try await api.downloadAccountArchive(name) } catch {
      self.error = error.localizedDescription
    }
  }
}
