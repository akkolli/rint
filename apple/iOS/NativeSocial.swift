import SwiftUI
import UIKit

struct NativePerson: Decodable, Identifiable {
  let username: String
  var picture: Bool? = nil
  var followers: Int? = nil
  var following: Int? = nil
  var workouts: Int? = nil
  var followedByMe: String? = nil
  var followsMe: String? = nil
  var blocked: Bool? = nil
  var bio: String? = nil
  var location: String? = nil
  var id: String { username }
  enum CodingKeys: String, CodingKey {
    case username, picture, followers, following, blocked, bio, location
    case workouts = "nb_workouts"
    case followedByMe = "is_followed_by"
    case followsMe = "follows"
  }
}
struct NativePeopleResponse: Decodable {
  var users: [NativePerson]? = nil
  var followers: [NativePerson]? = nil
  var following: [NativePerson]? = nil
  var requests: [NativePerson]? = nil
  var blocked: [NativePerson]? = nil
  enum CodingKeys: String, CodingKey {
    case users, followers, following
    case requests = "follow_requests"
    case blocked = "blocked_users"
  }
  var people: [NativePerson] { users ?? followers ?? following ?? requests ?? blocked ?? [] }
}
struct NativeAvatar: View {
  let username: String
  var picture = false
  var size: CGFloat = 44
  @EnvironmentObject var api: APIClient
  @State private var loadedImage: UIImage?
  var body: some View {
    ZStack {
      Circle().fill(RintStyle.soft)
      Text(String(username.prefix(2)).uppercased()).font(.headline).foregroundStyle(RintStyle.ink)
      if let loadedImage { Image(uiImage: loadedImage).resizable().scaledToFill() }
    }.frame(width: size, height: size).clipShape(Circle()).accessibilityHidden(true)
      .task(id: username + api.account + String(picture)) {
        loadedImage = nil
        let account = api.account
        if picture, let data = try? await api.request("users/\(username)/picture"),
          account == api.account
        {
          loadedImage = UIImage(data: data)
        }
      }
  }
}
struct NativePeopleView: View {
  var title = "People"
  var endpoint = "users"
  @EnvironmentObject var api: APIClient
  @State private var people: [NativePerson] = []
  @State private var query = ""
  @State private var page = 1
  @State private var more = false
  @State private var loading = false
  @State private var error: String?
  var body: some View {
    List {
      if endpoint == "users" {
        Section {
          Text("Your people, your motivation.").font(.title2.bold())
          Text("Find friends on this server. Follow their workouts and share encouragement.").font(
            .subheadline
          ).foregroundStyle(RintStyle.muted)
          NavigationLink("Invite a friend") { NativeInvitation() }
        }

      }
      Section {
        ForEach(people) { person in
          NavigationLink {
            NativePersonView(username: person.username)
          } label: {
            HStack(spacing: 12) {
              NativeAvatar(username: person.username, picture: person.picture ?? false)
              VStack(alignment: .leading, spacing: 4) {
                Text(person.username).font(.headline)
                Text(
                  person.blocked == true
                    ? "Blocked"
                    : person.followedByMe == "pending"
                      ? "Follow requested"
                      : person.followedByMe == "true"
                        ? "Following" : "\(person.workouts ?? 0) workouts"
                ).font(.caption).foregroundStyle(RintStyle.muted)
              }
            }.padding(.vertical, 4)
          }
        }
        if loading { ProgressView("Loading people…") }
        if people.isEmpty && !loading && error == nil {
          ContentUnavailableView(
            endpoint == "follow-requests" ? "No requests to review" : "No people found",
            systemImage: "person.2",
            description: Text(
              endpoint == "users"
                ? "Try a different username or invite a friend." : "You’re up to date."))
        }
        if more { Button("Load more") { Task { await load(reset: false) } }.disabled(loading) }
      }
      if endpoint == "users" {
        Section {
          NavigationLink("Follow requests") {
            NativePeopleView(title: "Follow requests", endpoint: "follow-requests")
          }
          NavigationLink("Blocked people") {
            NativePeopleView(title: "Blocked people", endpoint: "auth/blocked-users")
          }
        }
      }
      if let error {
        Section {
          RintNotice(text: error, icon: "exclamationmark.circle")
          Button("Try again") { Task { await load() } }
        }
      }
    }.scrollContentBackground(.hidden).background(RintStyle.paper).navigationTitle(title)
      .searchable(text: $query, prompt: "Username").onSubmit(of: .search) { Task { await load() } }
      .onChange(of: query) { _, value in if value.isEmpty { Task { await load() } } }
      .task { await load() }.refreshable { await load() }
  }
  @MainActor func load(reset: Bool = true) async {
    guard !loading else { return }
    loading = true
    error = nil
    defer { loading = false }
    let next = reset ? 1 : page + 1
    do {
      var components = URLComponents()
      components.queryItems = [
        URLQueryItem(name: "page", value: String(next)),
        URLQueryItem(name: "per_page", value: "25"), URLQueryItem(name: "q", value: query),
      ]
      let data = try await api.request(endpoint + "?" + (components.percentEncodedQuery ?? ""))
      let batch: [NativePerson]
      let hasMore: Bool
      if endpoint == "auth/blocked-users" {
        let response = try JSONDecoder().decode(NativeBlockedResponse.self, from: data)
        batch = response.blocked
        hasMore = response.pagination?.hasNext ?? false
      } else {
        let response = try JSONDecoder().decode(APIResponse<NativePeopleResponse>.self, from: data)
        batch = response.data.people
        hasMore = response.pagination?.hasNext ?? false
      }
      people =
        reset
        ? batch : people + batch.filter { row in !people.contains(where: { $0.id == row.id }) }
      page = next
      more = hasMore
    } catch { self.error = error.localizedDescription }
  }
}
struct NativePersonView: View {
  let username: String
  @EnvironmentObject var api: APIClient
  @State private var person: NativePerson?
  @State private var workouts: [FeedActivity] = []
  @State private var error: String?
  @State private var loading = false
  @State private var busy = false
  @State private var confirmingBlock = false
  @State private var reporting = false
  var body: some View {
    ScrollView {
      VStack(alignment: .leading, spacing: 24) {
        if let person {
          HStack(spacing: 16) {
            NativeAvatar(username: username, picture: person.picture ?? false)
            VStack(alignment: .leading, spacing: 4) {
              Text(username).font(.system(.title, design: .rounded).bold())
              if let location = person.location, !location.isEmpty {
                Label(location, systemImage: "mappin").font(.caption).foregroundStyle(
                  RintStyle.muted)
              }
              if person.followsMe == "true" {
                Text("Follows you").font(.caption).foregroundStyle(RintStyle.violet)
              }
            }
          }
          HStack {
            RintMetric(title: "Workouts", value: String(person.workouts ?? 0))
            NavigationLink {
              NativePeopleView(title: "Followers", endpoint: "users/\(username)/followers")
            } label: {
              RintMetric(title: "Followers", value: String(person.followers ?? 0))
            }
            NavigationLink {
              NativePeopleView(title: "Following", endpoint: "users/\(username)/following")
            } label: {
              RintMetric(title: "Following", value: String(person.following ?? 0))
            }
          }.foregroundStyle(RintStyle.ink)
          if let bio = person.bio, !bio.isEmpty { Text(bio).font(.subheadline) }
          if username == api.username {
            HStack(spacing: 12) {
              NavigationLink("Edit profile") { NativeProfileEditor() }
                .buttonStyle(RintSecondaryButton())
              NavigationLink {
                SettingsView()
              } label: {
                Label("Imports & data", systemImage: "applewatch")
              }.buttonStyle(RintSecondaryButton())
            }
          } else {
            if person.blocked == true {
              Button("Unblock person") { action("users/\(username)/unblock") }.buttonStyle(
                RintSecondaryButton()
              ).disabled(busy)
            } else {
              Button(
                person.followedByMe == "true"
                  ? "Unfollow"
                  : person.followedByMe == "pending" ? "Cancel follow request" : "Follow"
              ) {
                action(
                  "users/\(username)/"
                    + (person.followedByMe == "true" || person.followedByMe == "pending"
                      ? "unfollow" : "follow"))
              }.buttonStyle(RintPrimaryButton()).disabled(busy)
              if person.followedByMe == "pending" {
                RintNotice(text: "Your request is waiting for approval.", icon: "clock")
              }
              if person.followsMe == "pending" {
                HStack {
                  Button("Accept request") { action("follow-requests/\(username)/accept") }
                  Button("Decline", role: .destructive) {
                    action("follow-requests/\(username)/reject")
                  }
                }.buttonStyle(RintSecondaryButton()).disabled(busy)
              }
            }
          }
          if username == api.username {
            NativeTrainingSnapshot()
          }
          HStack {
            Text("Recent activities").font(.title3.bold())
            Spacer()
            Text("Latest 5 visible").font(.caption).foregroundStyle(RintStyle.muted)
          }
          if workouts.isEmpty {
            RintNotice(text: "No workouts are shared with you yet.", icon: "lock.shield")
          }
          ForEach(workouts) { NativeFeedCard(workout: $0) }
        } else if loading {
          ProgressView("Loading profile…")
        }
        if let error {
          RintNotice(text: error, icon: "exclamationmark.circle")
          Button("Try again") { Task { await load() } }.buttonStyle(RintSecondaryButton())
        }
      }.padding(20)
    }.background(RintStyle.paper).navigationTitle(username == api.username ? "You" : "Profile")
      .navigationBarTitleDisplayMode(.inline)
      .toolbar {
        if username == api.username {
          ToolbarItem(placement: .topBarTrailing) {
            NavigationLink {
              NativePreferencesView()
            } label: {
              Image(systemName: "slider.horizontal.3")
            }.accessibilityLabel("Settings and privacy")
          }
        } else {
          ToolbarItem(placement: .topBarTrailing) {
            Menu {
              Button("Report profile") { reporting = true }
              Button("Block person", role: .destructive) { confirmingBlock = true }
            } label: {
              Image(systemName: "ellipsis")
            }.accessibilityLabel("Profile actions")
          }
        }
      }
      .confirmationDialog(
        "Block \(username)?", isPresented: $confirmingBlock, titleVisibility: .visible
      ) {
        Button("Block person", role: .destructive) { action("users/\(username)/block") }
      } message: {
        Text(
          "Their follow requests are removed and interactions are restricted. You can unblock them from People."
        )
      }
      .sheet(isPresented: $reporting) { NativeReportView(objectID: username, objectType: "user") }
      .task { await load() }.refreshable { await load() }
  }
  @MainActor func load() async {
    loading = true
    error = nil
    defer { loading = false }
    do {
      person = try JSONDecoder().decode(
        APIResponse<NativePeopleResponse>.self, from: await api.request("users/\(username)")
      ).data.people.first
      workouts = try JSONDecoder().decode(
        APIResponse<FeedResponse>.self, from: await api.request("users/\(username)/workouts")
      ).data.workouts
    } catch { self.error = error.localizedDescription }
  }
  func action(_ path: String) {
    busy = true
    Task {
      do {
        _ = try await api.request(path, method: "POST")
        await load()
        await api.refresh()
      } catch { self.error = error.localizedDescription }
      busy = false
    }
  }
}
struct NativeReportView: View {
  let objectID: String
  let objectType: String
  @EnvironmentObject var api: APIClient
  @Environment(\.dismiss) var dismiss
  @State private var note = ""
  @State private var busy = false
  @State private var sent = false
  @State private var error: String?
  var body: some View {
    NavigationStack {
      Form {
        Section("Report \(objectType)") {
          Text(
            "Describe the concern for your server’s moderators. Reports are handled by this community."
          ).font(.subheadline)
          TextField("What happened?", text: $note, axis: .vertical).lineLimit(4...10)
          if sent {
            Label("Report submitted", systemImage: "checkmark.shield")
          } else {
            Button(busy ? "Sending…" : "Submit report") {
              busy = true
              Task {
                do {
                  _ = try await api.request(
                    "reports", method: "POST",
                    body: JSONSerialization.data(withJSONObject: [
                      "object_id": objectID, "object_type": objectType, "note": note,
                    ]))
                  sent = true
                } catch { self.error = error.localizedDescription }
                busy = false
              }
            }.disabled(busy || note.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
          }
          if let error { RintNotice(text: error, icon: "exclamationmark.circle") }
        }
      }.scrollContentBackground(.hidden).background(RintStyle.paper).navigationTitle("Report")
        .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } } }
    }
  }
}
struct NativeNotification: Decodable, Identifiable {
  let id: String
  let type: String
  let markedAsRead: Bool
  var from: NativePerson? = nil
  var workout: FeedActivity? = nil
  var comment: NativeNotificationComment? = nil
  enum CodingKeys: String, CodingKey {
    case id, type, from, workout, comment
    case markedAsRead = "marked_as_read"
  }
  var message: String {
    switch type {
    case "follow_request": return "requested to follow you"
    case "follow_request_approved": return "approved your follow request"
    case "follow": return "is now following you"
    case "workout_like": return "liked your workout"
    case "workout_comment": return "commented on a workout"
    case "comment_like": return "liked your comment"
    case "mention": return "mentioned you"
    default: return type.replacingOccurrences(of: "_", with: " ").capitalized
    }
  }
}
struct NativeNotificationComment: Decodable {
  var workoutID: String? = nil
  enum CodingKeys: String, CodingKey { case workoutID = "workout_id" }
}
struct NativeInboxResponse: Decodable {
  let notifications: [NativeNotification]
  let pagination: Pagination?
}
struct NativeInboxView: View {
  @EnvironmentObject var api: APIClient
  @State private var notifications: [NativeNotification] = []
  @State private var unread = true
  @State private var loading = false
  @State private var page = 1
  @State private var more = false
  @State private var error: String?
  var body: some View {
    List {
      Section {
        Picker("Show", selection: $unread) {
          Text("Unread").tag(true)
          Text("All").tag(false)
        }.pickerStyle(.segmented)
      }
      ForEach(notifications) { item in
        VStack(alignment: .leading, spacing: 8) {
          if let workout = item.workout {
            NavigationLink {
              NativeActivityView(workout: workout)
            } label: {
              notificationLabel(item)
            }
          } else if let workoutID = item.comment?.workoutID {
            NavigationLink {
              NativeActivityDestination(workoutID: workoutID)
            } label: {
              notificationLabel(item)
            }
          } else if let person = item.from {
            NavigationLink {
              NativePersonView(username: person.username)
            } label: {
              notificationLabel(item)
            }
          } else {
            notificationLabel(item)
          }
          if !item.markedAsRead {
            Button("Mark as read") {
              Task {
                do {
                  _ = try await api.request(
                    "notifications/\(item.id)", method: "PATCH",
                    body: JSONSerialization.data(withJSONObject: ["read_status": true]))
                  await load()
                } catch { self.error = error.localizedDescription }
              }
            }.font(.caption).frame(minHeight: 44)
          }
        }.padding(.vertical, 6)
      }
      if loading { ProgressView("Loading notifications…") }
      if notifications.isEmpty && !loading && error == nil {
        ContentUnavailableView(
          "You’re up to date", systemImage: "bell.badge",
          description: Text("Likes, comments, mentions and follow requests appear here."))
      }
      if more { Button("Load more") { Task { await load(reset: false) } }.disabled(loading) }
      if let error {
        RintNotice(text: error, icon: "exclamationmark.circle")
        Button("Try again") { Task { await load() } }
      }
    }.scrollContentBackground(.hidden).background(RintStyle.paper).navigationTitle("Notifications")
      .toolbar {
        ToolbarItem(placement: .topBarTrailing) {
          Button("Read all") {
            Task {
              do {
                _ = try await api.request("notifications/mark-all-as-read", method: "POST")
                await load()
              } catch { self.error = error.localizedDescription }
            }
          }.disabled(loading || notifications.isEmpty)
        }
      }.task { await load() }.refreshable { await load() }.onChange(of: unread) { _, _ in
        Task { await load() }
      }
  }
  func notificationLabel(_ item: NativeNotification) -> some View {
    HStack(spacing: 12) {
      Image(
        systemName: item.type.contains("like")
          ? "heart"
          : item.type.contains("comment") || item.type == "mention" ? "bubble" : "person.2"
      ).foregroundStyle(RintStyle.violet).frame(width: 28)
      VStack(alignment: .leading, spacing: 4) {
        if let name = item.from?.username { Text(name).font(.headline) }
        Text(item.message).font(.subheadline)
        if let title = item.workout?.title {
          Text(title).font(.caption).foregroundStyle(RintStyle.muted)
        }
      }
      Spacer()
      if !item.markedAsRead {
        Circle().fill(RintStyle.violet).frame(width: 8, height: 8).accessibilityLabel("Unread")
      }
    }
  }
  @MainActor func load(reset: Bool = true) async {
    guard !loading else { return }
    loading = true
    error = nil
    defer { loading = false }
    let next = reset ? 1 : page + 1
    do {
      let response = try JSONDecoder().decode(
        NativeInboxResponse.self,
        from: await api.request("notifications?page=\(next)&status=\(unread ? "unread" : "all")"))
      notifications =
        reset
        ? response.notifications
        : notifications
          + response.notifications.filter { row in
            !notifications.contains(where: { $0.id == row.id })
          }
      page = next
      more = response.pagination?.hasNext ?? false
      await api.refreshUnread()
    } catch { self.error = error.localizedDescription }
  }
}

struct NativeBlockedResponse: Decodable {
  let blocked: [NativePerson]
  let pagination: Pagination?
  enum CodingKeys: String, CodingKey {
    case blocked = "blocked_users"
    case pagination
  }
}
struct NativeActivityDestination: View {
  let workoutID: String
  var effortDistance: Double? = nil
  @EnvironmentObject var api: APIClient
  @State private var workout: FeedActivity?
  @State private var error: String?
  var body: some View {
    Group {
      if let workout {
        NativeActivityView(workout: workout, initialEffortDistance: effortDistance)
      } else if let error {
        VStack(spacing: 20) {
          RintNotice(text: error, icon: "exclamationmark.circle")
          Button("Try again") { Task { await load() } }
        }.padding(24)
      } else {
        ProgressView("Loading activity…")
      }
    }.task { await load() }
  }
  @MainActor func load() async {
    error = nil
    do {
      workout = try JSONDecoder().decode(
        APIResponse<FeedResponse>.self, from: await api.request("workouts/\(workoutID)")
      ).data.workouts.first
    } catch { self.error = error.localizedDescription }
  }
}
