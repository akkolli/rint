import SwiftUI

struct NativeInvitation: View {
  @EnvironmentObject var api: APIClient
  @State private var available: Bool?
  @State private var error: String?
  var body: some View {
    ScrollView {
      VStack(alignment: .leading, spacing: 24) {
        Image(systemName: "person.2.fill").font(.largeTitle).foregroundStyle(RintStyle.violet)
        Text("Bring your people.").font(.largeTitle.bold()).tracking(-1)
        Text(
          "Friends join the same Rint server, then follow each other. Your workouts stay private until you choose to share them."
        )
        .font(.subheadline).foregroundStyle(RintStyle.muted)
        if available == true, let root = URL(string: api.server) {
          ShareLink(item: root.appendingPathComponent("register")) {
            Label("Share invitation link", systemImage: "square.and.arrow.up")
          }.buttonStyle(RintPrimaryButton())
        } else if available == false {
          VStack(alignment: .leading, spacing: 12) {
            Label("Registration is closed", systemImage: "lock").font(.headline)
            Text("The server owner needs to allow more accounts before a friend can join.").font(
              .subheadline)
            if let url = URL(string: api.server)?.appendingPathComponent(
              "administration/application/edit")
            {
              Link("Open server registration settings", destination: url).font(.subheadline.bold())
                .frame(minHeight: 44)
            }
          }.rintPanel()
        } else if error == nil {
          ProgressView("Checking invitations…")
        }
        if api.server.contains(".ts.net") {
          RintNotice(
            text:
              "This is a private Tailscale server. Friends also need access to the same Tailscale network to open your link.",
            icon: "network")
        }
        if let error {
          RintNotice(text: error, icon: "exclamationmark.circle")
          Button("Try again") { Task { await load() } }.buttonStyle(RintSecondaryButton())
        }
      }.padding(24)
    }.background(RintStyle.paper).navigationTitle("Invite friends").navigationBarTitleDisplayMode(
      .inline
    )
    .task { await load() }
  }
  @MainActor func load() async {
    error = nil
    do {
      struct Configuration: Decodable {
        let isRegistrationEnabled: Bool
        enum CodingKeys: String, CodingKey {
          case isRegistrationEnabled = "is_registration_enabled"
        }
      }
      available = try JSONDecoder().decode(
        APIResponse<Configuration>.self, from: await api.request("config")
      ).data.isRegistrationEnabled
    } catch { self.error = "Your server’s invitation status couldn’t load." }
  }
}
