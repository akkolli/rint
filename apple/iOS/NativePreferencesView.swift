import SwiftUI

struct NativePreferencesView: View {
  @EnvironmentObject var api: APIClient
  @AppStorage("rintInteractionSounds") private var interactionSounds = false
  @State private var profile: [String: Any] = [:]
  @State private var imperial = false
  @State private var manualFollowers = true
  @State private var hidden = false
  @State private var hrVisibility = "private"
  @State private var loading = true
  @State private var saving = false
  @State private var message: String?
  @State private var error: String?
  private let keys = [
    "analysis_visibility", "calories_visibility", "date_format", "display_ascent",
    "hide_profile_in_users_directory", "hr_visibility", "imperial_units", "language",
    "manually_approves_followers", "map_visibility", "media_visibility",
    "missing_elevations_processing", "segments_creation_event", "split_workout_charts",
    "start_elevation_at_zero", "timezone", "use_dark_mode", "use_raw_gpx_speed", "weekm",
    "workouts_visibility",
  ]
  var body: some View {
    Form {
      Section("Display units") {
        Picker("Distance & pace", selection: $imperial) {
          Text("Kilometres · /km").tag(false)
          Text("Miles · /mi").tag(true)
        }
        Text(
          "Saved to your account and applied on the web, iPhone and your connected Watch. Original recordings keep their precision."
        ).font(.footnote).foregroundStyle(RintStyle.muted)
      }
      Section("Interaction") {
        Toggle("Interaction sounds", isOn: $interactionSounds)
        Text("A quiet confirmation when you like an activity. Off by default; applies to this iPhone.")
          .font(.footnote).foregroundStyle(RintStyle.muted)
      }
      Section("Your community") {
        Toggle("Approve followers yourself", isOn: $manualFollowers)
        Toggle("Hide from the people directory", isOn: $hidden)
      }
      Section("Heart rate privacy") {
        Picker("Who can see heart rate", selection: $hrVisibility) {
          Text("Only me").tag("private")
          Text("Followers").tag("followers_only")
          Text("Everyone").tag("public")
        }
        Text(
          "Your activity’s audience still applies. New recordings and imports start private; choose activity and route audiences when you share."
        ).font(.footnote).foregroundStyle(RintStyle.muted)
      }
      Section {
        if loading { ProgressView("Loading preferences…") }
        Button(saving ? "Saving…" : "Save preferences") { Task { await save() } }.disabled(
          loading || saving || profile.isEmpty)
        if let message { RintNotice(text: message, icon: "checkmark.circle") }
        if let error {
          RintNotice(text: error, icon: "exclamationmark.circle")
          if profile.isEmpty { Button("Try again") { Task { await load() } } }
        }
      }
    }.scrollContentBackground(.hidden).background(RintStyle.paper).navigationTitle(
      "Units & privacy"
    ).navigationBarTitleDisplayMode(.inline).task { await load() }
  }
  @MainActor func load() async {
    loading = true
    error = nil
    defer { loading = false }
    do {
      let data =
        try JSONSerialization.jsonObject(with: await api.request("auth/profile")) as? [String: Any]
      profile = data?["data"] as? [String: Any] ?? [:]
      imperial = profile["imperial_units"] as? Bool ?? false
      manualFollowers = profile["manually_approves_followers"] as? Bool ?? true
      hidden = profile["hide_profile_in_users_directory"] as? Bool ?? false
      hrVisibility = profile["hr_visibility"] as? String ?? "private"
    } catch { self.error = error.localizedDescription }
  }
  @MainActor func save() async {
    saving = true
    error = nil
    message = nil
    defer { saving = false }
    do {
      // Fetch again before patching the legacy full-preferences API, preserving
      // changes made on another device to every setting outside this form.
      let data =
        try JSONSerialization.jsonObject(with: await api.request("auth/profile")) as? [String: Any]
      let current = data?["data"] as? [String: Any] ?? [:]
      var payload = current.filter { keys.contains($0.key) }
      payload["imperial_units"] = imperial
      payload["manually_approves_followers"] = manualFollowers
      payload["hide_profile_in_users_directory"] = hidden
      payload["hr_visibility"] = hrVisibility
      _ = try await api.request(
        "auth/profile/edit/preferences", method: "POST",
        body: JSONSerialization.data(withJSONObject: payload))
      await api.refresh()
      message = "Preferences saved to your account."
    } catch { self.error = error.localizedDescription }
  }
}
