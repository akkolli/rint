import Charts
import HealthKit
import SwiftUI

struct PhoneRoot: View {
  @EnvironmentObject var api: APIClient
  @EnvironmentObject var recorder: WorkoutRecorder
  @State private var password = ""
  @State private var connecting = false
  var body: some View {
    if !api.signedIn {
      NavigationStack {
        ScrollView {
          VStack(alignment: .leading, spacing: 28) {
            HStack(spacing: 12) {
              Text("r.").font(.system(.title, design: .rounded).bold().italic())
                .foregroundStyle(RintStyle.accentInk).padding(12).background(
                  RintStyle.accent, in: RoundedRectangle(cornerRadius: 16))
              Text("Rint").font(.title2.bold())
            }.padding(.top, 24)
            VStack(alignment: .leading, spacing: 18) {
              Text("Sign in").font(.title3.bold())
              VStack(alignment: .leading, spacing: 6) {
                Text("Server address").font(.caption).foregroundStyle(RintStyle.muted)
                TextField("https://fitness.example.org", text: $api.server).keyboardType(.URL)
                  .textInputAutocapitalization(.never).autocorrectionDisabled()
              }
              Divider()
              TextField("Email", text: $api.email).textInputAutocapitalization(.never)
                .autocorrectionDisabled().keyboardType(.emailAddress).textContentType(.username)
              Divider()
              SecureField("Password", text: $password).textContentType(.password)
              Button {
                connecting = true
                Task {
                  await api.login(password: password)
                  password = ""
                  connecting = false
                }
              } label: {
                HStack {
                  if connecting { ProgressView() }
                  Text(connecting ? "Connecting…" : "Connect")
                }
              }.buttonStyle(RintPrimaryButton()).disabled(
                connecting || password.isEmpty || api.server.isEmpty || api.email.isEmpty)
            }.rintPanel()
            if let error = api.error {
              Label(error, systemImage: "exclamationmark.circle").font(.footnote).foregroundStyle(
                RintStyle.heart)
            }
          }.padding(24)
        }.background(RintStyle.paper).toolbar(.hidden, for: .navigationBar)
      }
    } else {
      TabView(selection: $api.selectedTab) {
        FeedView().tabItem { Label("Feed", systemImage: "house") }.tag(0)
        NativeProgressView().tabItem { Label("Progress", systemImage: "chart.xyaxis.line") }.tag(1)
        RecordView().tabItem { Label("Record", systemImage: "figure.run") }.tag(2)
          .badge(recorder.active ? (recorder.paused ? "Paused" : "Live") : nil)
        NavigationStack { NativePeopleView() }.tabItem { Label("People", systemImage: "person.2") }
          .tag(3)
        NavigationStack { NativePersonView(username: api.username) }
          .tabItem { Label("You", systemImage: "person.crop.circle") }.tag(4)
      }.tint(RintStyle.ink)
    }
  }
}
struct FeedView: View {
  @EnvironmentObject var api: APIClient
  @EnvironmentObject var queue: SyncQueue
  var body: some View {
    NavigationStack {
      ScrollView {
        LazyVStack(alignment: .leading, spacing: 12) {
          VStack(alignment: .leading, spacing: 6) {
            RintEyebrow(text: "Your training, at a glance")
            Text("Overview").font(.system(.largeTitle, design: .default).weight(.bold)).tracking(-1.2)
          }.padding(.top, 8).padding(.bottom, 6)
          NativeTrainingSnapshot()
          HStack {
            Text("Activity feed").font(.subheadline.weight(.semibold))
            Spacer()
            if api.refreshing {
              ProgressView().accessibilityLabel("Refreshing feed")
            } else {
              Text("Latest first").font(.caption2).foregroundStyle(RintStyle.muted)
            }
          }.padding(.top, 8).padding(.bottom, 2)
          if queue.pending > 0 {
            RintNotice(
              text: "\(queue.pending) workouts safely retained, waiting to sync.",
              icon: "arrow.triangle.2.circlepath")
          }
          if api.feed.isEmpty && !api.refreshing && api.error == nil {
            VStack(alignment: .leading, spacing: 16) {
              Image(systemName: "figure.run").font(.largeTitle).foregroundStyle(RintStyle.violet)
              Text("No workouts yet").font(.title2.bold())
              Text("Import or record a workout.").font(.subheadline)
                .foregroundStyle(RintStyle.muted)
              NavigationLink {
                HealthImportView()
              } label: {
                Label("Import workouts", systemImage: "applewatch")
              }
              .buttonStyle(RintPrimaryButton())
            }.rintPanel()
          }
          ForEach(api.feed) { NativeFeedCard(workout: $0) }
          if api.hasMoreFeed {
            Button(api.loadingMore ? "Loading…" : "Load more activities") {
              Task { await api.moreFeed() }
            }.disabled(api.loadingMore).buttonStyle(
              RintSecondaryButton())
          }
          if let error = api.error {
            RintNotice(text: error, icon: "exclamationmark.circle")
            Button("Try again") { Task { await api.refresh() } }.buttonStyle(RintSecondaryButton())
          }
        }.padding(.horizontal, 16).padding(.top, 8).padding(.bottom, 16)
      }.background(RintStyle.paper).navigationTitle("rint").navigationBarTitleDisplayMode(.inline)
        .toolbar {
          ToolbarItem(placement: .topBarLeading) {
            NavigationLink {
              NativeInboxView()
            } label: {
              Image(systemName: "bell").overlay(alignment: .topTrailing) {
                if api.unreadNotifications > 0 {
                  Text(api.unreadNotifications > 99 ? "99+" : String(api.unreadNotifications))
                    .font(.system(size: 9, weight: .bold)).padding(4)
                    .foregroundStyle(RintStyle.accentInk).background(
                      RintStyle.accent, in: Capsule()
                    ).offset(x: 9, y: -9)
                }
              }
            }.accessibilityLabel("Notifications, \(api.unreadNotifications) unread")
          }
          ToolbarItem(placement: .topBarTrailing) {
            Button {
              api.selectedTab = 4
            } label: {
              NativeAvatar(username: api.username, picture: api.pictureAvailable)
            }.accessibilityLabel("Your profile")
          }
        }
        .refreshable { await api.refresh() }
    }
  }
}
struct NativeFeedCard: View {
  let workout: FeedActivity
  @EnvironmentObject var api: APIClient
  @Environment(\.dynamicTypeSize) private var typeSize
  @State private var route: NativeRoutePreview?
  @State private var routeFailed = false
  @State private var showingSharing = false
  @State private var showingActivity = false
  @State private var liked = false
  @State private var likes = 0
  @State private var busy = false
  @State private var error: String?
  var body: some View {
    VStack(alignment: .leading, spacing: 0) {
      HStack(spacing: 8) {
        NavigationLink {
          NativePersonView(username: workout.user.username)
        } label: {
          NativeAvatar(
            username: workout.user.username, picture: workout.user.picture ?? false, size: 32
          )
          .frame(width: 44, height: 44).contentShape(Rectangle())
        }.accessibilityLabel("View " + workout.user.username + "’s profile")
        Button {
          showingActivity = true
        } label: {
          VStack(alignment: .leading, spacing: 3) {
            Text(activityTitle).font(.headline).foregroundStyle(RintStyle.ink)
            Text(workout.user.username + " · " + compactDate + " · " + sportLabel)
              .font(.caption2).foregroundStyle(RintStyle.muted)
              .fixedSize(horizontal: false, vertical: true)
          }.frame(maxWidth: .infinity, alignment: .leading).contentShape(Rectangle())
        }.buttonStyle(.plain).accessibilityLabel(
          activityTitle + ", " + workout.user.username + ", " + dateLabel)
        Image(systemName: workout.workoutVisibility == "private" ? "lock" : "person.2")
          .font(.caption).foregroundStyle(RintStyle.muted).accessibilityLabel(
            workout.workoutVisibility == "private" ? "Private activity" : "Shared activity")
      }.padding(.horizontal, 12).padding(.top, 10)
      Button {
        showingActivity = true
      } label: {
        VStack(alignment: .leading, spacing: 0) {
          LazyVGrid(
            columns: Array(
              repeating: GridItem(.flexible(), alignment: .leading),
              count: typeSize.isAccessibilitySize ? 1 : metricCount),
            alignment: .leading, spacing: 8
          ) {
            if let distance = workout.distance {
              feedMetric(
                "Distance", DisplayUnits.distance(distance * 1000), DisplayUnits.distanceUnit)
            }
            feedMetric(
              workout.moving == nil ? "Elapsed time" : "Moving time",
              DisplayUnits.duration(workout.moving ?? workout.duration))
            if let motionMetric {
              feedMetric(motionMetric.title, motionMetric.value, motionMetric.unit)
            }
            if let heartRate = workout.averageHeartRate {
              feedMetric("Avg. HR", String(Int(heartRate.rounded())), "bpm")
            }
          }.padding(.horizontal, 12).padding(.top, 8).padding(.bottom, 12)
          if let photo = workout.mediaAttachments?.first, let url = URL(string: photo.url) {
            AsyncImage(url: url) { image in
              image.resizable().scaledToFill()
            } placeholder: {
              RintStyle.soft
            }
            .frame(height: 148).clipped().accessibilityLabel("Activity photo")
          } else if workout.withStream == true && workout.withGeometry != false {
            if let route, route.points.filter({ $0.lat != nil && $0.lon != nil }).count >= 2 {
              NativeRouteMap(points: route.points, sampled: true, height: 140, interactive: false)
                .overlay { Color.clear.contentShape(Rectangle()) }
            } else if routeFailed {
              Label("Map unavailable", systemImage: "exclamationmark.circle")
                .font(.caption).foregroundStyle(RintStyle.muted).frame(minHeight: 44)
            } else if route == nil {
              ProgressView("Loading route…").font(.caption).frame(height: 140)
            }
          }
        }.frame(maxWidth: .infinity, alignment: .leading).contentShape(Rectangle())
      }.buttonStyle(.plain).accessibilityLabel(cardSummary)
        .accessibilityHint("Opens workout metrics, route and best efforts")
      Divider()
      NativeFeedActionLayout(columns: metricCount, stacked: typeSize.isAccessibilitySize) {
        Button {
          busy = true
          Task {
            do {
              _ = try await api.request(
                "workouts/\(workout.id)/like\(liked ? "/undo" : "")", method: "POST")
              liked.toggle()
              likes += liked ? 1 : -1
              if liked { RintFeedback.appreciation() }
            } catch { self.error = error.localizedDescription }
            busy = false
          }
        } label: {
          HStack(spacing: 5) {
            Label(liked ? "Liked" : "Like", systemImage: liked ? "heart.fill" : "heart")
            if likes > 0 { Text(String(likes)).monospacedDigit() }
          }.frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
            .contentShape(Rectangle())
        }
        .foregroundStyle(liked ? RintStyle.heart : RintStyle.muted).disabled(busy)
        .sensoryFeedback(.selection, trigger: liked)
        .accessibilityLabel(liked ? "Unlike activity" : "Like activity")
        .accessibilityValue("\(likes) likes")
        NavigationLink {
          NativeActivityView(workout: workout, openConversation: true)
        } label: {
          Label("Comment", systemImage: "bubble")
            .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
            .contentShape(Rectangle())
        }
        if workout.user.username == api.username {
          Button {
            showingSharing = true
          } label: {
            Label("Share", systemImage: "square.and.arrow.up")
              .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
              .contentShape(Rectangle())
          }.accessibilityLabel("Share activity")
        } else if let url = URL(string: api.server)?.appendingPathComponent(
          "workouts/\(workout.id)")
        {
          ShareLink(item: url) {
            Label("Share", systemImage: "square.and.arrow.up")
              .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
              .contentShape(Rectangle())
          }.accessibilityLabel("Share activity")
        }
      }.font(.caption).foregroundStyle(RintStyle.muted).buttonStyle(.borderless)
        .frame(minHeight: 44).padding(.horizontal, 12)
      if let error { RintNotice(text: error, icon: "exclamationmark.circle") }
    }.navigationDestination(isPresented: $showingActivity) {
      NativeActivityView(workout: workout)
    }.sheet(isPresented: $showingSharing) {
      NativeSharingView(workout: workout)
    }.frame(maxWidth: .infinity, alignment: .leading)
      .contentShape(Rectangle()).onTapGesture { showingActivity = true }
      .background(RintStyle.surface, in: RoundedRectangle(cornerRadius: 16))
      .clipShape(RoundedRectangle(cornerRadius: 16))
      .overlay(RoundedRectangle(cornerRadius: 16).stroke(RintStyle.line, lineWidth: 1)).task {
        liked = workout.liked ?? false
        likes = workout.likesCount ?? 0
        if workout.withStream == true && workout.withGeometry != false
          && (workout.mediaAttachments?.isEmpty ?? true)
        {
          do {
            route = try JSONDecoder().decode(
              APIResponse<NativeRoutePreview>.self,
              from: await api.request("rint/activities/\(workout.id)/preview")
            ).data
          } catch { routeFailed = true }
        }
      }
  }
  private var sportLabel: String {
    api.sports.first(where: { $0.id == workout.sportID })?.label ?? "Workout"
  }
  private var activityTitle: String { EffortPresentation.title(workout, sport: sportLabel) }
  private var compactDate: String {
    workout.date?.formatted(.dateTime.month(.abbreviated).day()) ?? ""
  }
  private var motionMetric: (title: String, value: String, unit: String)? {
    guard let distance = workout.distance, distance.isFinite, distance > 0,
      let seconds = DisplayUnits.seconds(workout.moving ?? workout.duration), seconds >= 1
    else { return nil }
    let moving = workout.moving != nil
    if ["Running", "Indoor Running", "Trail", "Hiking", "Walking"].contains(sportLabel) {
      return (
        moving ? "Moving pace" : "Elapsed pace", DisplayUnits.pace(seconds / distance),
        "/" + DisplayUnits.distanceUnit
      )
    }
    return (
      moving ? "Moving speed" : "Avg. speed", DisplayUnits.speed(distance * 1000 / seconds),
      DisplayUnits.speedUnit
    )
  }
  private var metricCount: Int {
    1 + (workout.distance == nil ? 0 : 1) + (motionMetric == nil ? 0 : 1)
      + (workout.averageHeartRate == nil ? 0 : 1)
  }
  private func feedMetric(_ title: String, _ value: String, _ unit: String = "") -> some View {
    VStack(alignment: .leading, spacing: 2) {
      Text(title).font(.caption2).foregroundStyle(RintStyle.muted)
      ViewThatFits(in: .horizontal) {
        HStack(alignment: .firstTextBaseline, spacing: 2) {
          Text(value).font(.system(.title3, design: .rounded).weight(.semibold)).monospacedDigit()
          if !unit.isEmpty { Text(unit).font(.caption2).foregroundStyle(RintStyle.muted) }
        }
        VStack(alignment: .leading, spacing: 0) {
          Text(value).font(.system(.title3, design: .rounded).weight(.semibold)).monospacedDigit()
          if !unit.isEmpty { Text(unit).font(.caption2).foregroundStyle(RintStyle.muted) }
        }
      }
    }.foregroundStyle(
      title == "Distance" ? RintStyle.distance
        : title == "Avg. HR" ? RintStyle.heart
        : title.contains("pace") || title.contains("speed") ? RintStyle.violet : RintStyle.ink
    ).accessibilityElement(children: .combine)
  }
  var dateLabel: String {
    workout.date?.formatted(date: .abbreviated, time: .shortened) ?? "Workout"
  }
  private var cardSummary: String {
    let title = EffortPresentation.title(
      workout,
      sport: api.sports.first(where: { $0.id == workout.sportID })?.label ?? "Workout")
    var result =
      title + ", Distance "
      + (workout.distance.map { DisplayUnits.distance($0 * 1000) } ?? "unavailable")
      + " " + DisplayUnits.distanceUnit
      + (workout.moving == nil ? ", Elapsed time " : ", Moving time ")
      + DisplayUnits.duration(workout.moving ?? workout.duration)
    if let motionMetric {
      result += ", " + motionMetric.title + " " + motionMetric.value + " " + motionMetric.unit
    }
    if let heartRate = workout.averageHeartRate {
      result += ", Average heart rate " + String(Int(heartRate.rounded())) + " beats per minute"
    }
    return result
  }
}
/// Reuses the metric grid: Comment spans its middle columns when four metrics are shown.
private struct NativeFeedActionLayout: Layout {
  let columns: Int
  let stacked: Bool
  private let spacing: CGFloat = 8

  private func widths(_ width: CGFloat, count: Int) -> [CGFloat] {
    guard count > 0 else { return [] }
    if stacked { return Array(repeating: width, count: count) }
    let usesFourColumns = columns == 4 && count == 3
    let slots = usesFourColumns ? 4 : count
    let unit = max(0, (width - spacing * CGFloat(slots - 1)) / CGFloat(slots))
    return usesFourColumns ? [unit, unit * 2 + spacing, unit] : Array(repeating: unit, count: count)
  }

  func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
    let width = proposal.width ?? 320
    let sizes = zip(subviews, widths(width, count: subviews.count)).map { view, itemWidth in
      view.sizeThatFits(ProposedViewSize(width: itemWidth, height: nil))
    }
    let height = stacked
      ? sizes.reduce(0) { $0 + max(44, $1.height) }
      : max(44, sizes.map(\.height).max() ?? 0)
    return CGSize(width: width, height: height)
  }

  func placeSubviews(
    in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()
  ) {
    var x = bounds.minX
    var y = bounds.minY
    for (view, width) in zip(subviews, widths(bounds.width, count: subviews.count)) {
      let height = stacked
        ? max(44, view.sizeThatFits(ProposedViewSize(width: width, height: nil)).height)
        : bounds.height
      view.place(
        at: CGPoint(x: x, y: y), anchor: .topLeading,
        proposal: ProposedViewSize(width: width, height: height))
      if stacked { y += height } else { x += width + spacing }
    }
  }
}

struct RecordView: View {
  @ObservedObject private var bridge = WatchBridge.shared
  @EnvironmentObject var api: APIClient
  @EnvironmentObject var recorder: WorkoutRecorder
  @EnvironmentObject var queue: SyncQueue
  @State private var indoor = false
  @State private var confirmFinish = false
  @State private var showingCompletion = true
  @ScaledMetric(relativeTo: .largeTitle) private var clockSize = 64
  @Environment(\.dynamicTypeSize) private var typeSize
  var body: some View {
    NavigationStack {
      ScrollView {
        VStack(alignment: .leading, spacing: 16) {
          if recorder.active {
            HStack {
              Label(
                recorder.ending ? "Saving workout…" : recorder.paused ? "Paused" : "Recording",
                systemImage: recorder.paused ? "pause.circle.fill" : "record.circle"
              )
              .font(.headline).foregroundStyle(recorder.paused ? .orange : RintStyle.ink)
              Spacer()
              Text(recorder.ending ? "SAVING" : "SAVED ON DEVICE").font(.caption2.weight(.semibold))
                .foregroundStyle(
                  RintStyle.muted)
            }
            VStack(alignment: .leading, spacing: 12) {
              RintEyebrow(text: "Elapsed time")
              WorkoutClock(started: recorder.startDate).font(
                .system(size: clockSize, weight: .semibold, design: .rounded)
              )
              .monospacedDigit().minimumScaleFactor(0.6).lineLimit(1)
            }.padding(.vertical, 4)
            LazyVGrid(
              columns: Array(
                repeating: GridItem(.flexible()), count: typeSize.isAccessibilitySize ? 2 : 3),
              alignment: .leading,
              spacing: 16
            ) {
              RintMetric(
                title: "Distance", value: DisplayUnits.distance(recorder.distance),
                unit: DisplayUnits.distanceUnit)
              RintMetric(
                title: recorder.currentActivity == .cycling
                  ? "Average active speed" : "Average active pace",
                value: recorder.currentActivity == .cycling
                  ? DisplayUnits.speed(
                    recorder.activeDuration > 0 ? recorder.distance / recorder.activeDuration : nil)
                  : recorder.pace,
                unit: recorder.currentActivity == .cycling
                  ? DisplayUnits.speedUnit : "/" + DisplayUnits.distanceUnit)
              RintMetric(
                title: "Heart rate",
                value: recorder.liveHeartRate.map { String(format: "%.0f", $0) } ?? "—", unit: "bpm"
              )
            }.rintPanel()
            Text(
              recorder.routeStatus
                + (recorder.liveHeartRate == nil ? " · Waiting for heart rate" : "")
            )
            .font(.caption).foregroundStyle(RintStyle.muted)
            Button {
              recorder.pauseOrResume()
            } label: {
              Label(
                recorder.paused ? "Resume workout" : "Pause workout",
                systemImage: recorder.paused ? "play.fill" : "pause.fill")
            }.buttonStyle(RintPrimaryButton()).disabled(recorder.ending)
            HStack {
              Button {
                recorder.lap()
              } label: {
                Label("Lap \(recorder.lapCount + 1)", systemImage: "flag")
              }.buttonStyle(RintSecondaryButton())
              Button {
                confirmFinish = true
              } label: {
                Label("Finish", systemImage: "stop.fill")
              }.buttonStyle(RintSecondaryButton())
            }
            .disabled(recorder.ending)
          } else if showingCompletion, let completion = recorder.lastCompletion {
            NativeWorkoutSummary(workout: completion) { showingCompletion = false }
          } else {
            VStack(alignment: .leading, spacing: 14) {
              VStack(alignment: .leading, spacing: 8) {
                Picker("Workout", selection: $api.sportID) {
                  ForEach(api.sports) { Text($0.label).tag($0.id) }
                }
                .onChange(of: api.sportID) { _, _ in api.configureWatch() }.disabled(
                  recorder.starting)
                Divider()
                Toggle("Indoor workout", isOn: $indoor).disabled(recorder.starting)
              }.rintPanel(padding: 14)
              Button {
                let label = api.sports.first(where: { $0.id == api.sportID })?.label ?? "Running"
                Task {
                  await recorder.start(
                    account: api.account, sportID: api.sportID, activity: WorkoutKind.type(label),
                    indoor: indoor)
                }
              } label: {
                Label(
                  recorder.starting ? "Getting ready…" : "Start workout", systemImage: "play.fill")
              }
              .buttonStyle(RintPrimaryButton()).disabled(
                api.sportID == 0 || recorder.recovering || !RecordingDisk.drafts().isEmpty)
              Divider().padding(.vertical, 4)
              Text("Import").font(.subheadline.weight(.semibold))
              NavigationLink {
                HealthImportView()
              } label: {
                Label("Apple Health", systemImage: "heart.text.square")
                  .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
              }
              NavigationLink {
                NativeStravaImportView()
              } label: {
                Label("Strava export", systemImage: "square.and.arrow.down")
                  .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
              }
            }
          }
          if let error = recorder.error {
            RintNotice(text: error, icon: "exclamationmark.circle")
            if !recorder.active && !RecordingDisk.drafts().isEmpty {
              Button("Save interrupted recording") { recorder.saveInterrupted() }.buttonStyle(
                RintPrimaryButton())
            }
          }
          if let message = recorder.savedMessage {
            if recorder.lastCompletion == nil {
              RintNotice(text: message, icon: "checkmark.circle")
            }
          }
          if queue.pending > 0 {
            RintNotice(
              text: "\(queue.pending) workouts retained for sync.",
              icon: "arrow.triangle.2.circlepath")
          }
        }.padding(16)
      }.background(RintStyle.paper).navigationTitle("Record").navigationBarTitleDisplayMode(.inline)
        .onAppear { recorder.restoreCompletion(account: api.account) }
        .onChange(of: recorder.lastCompletion?.id) { _, id in
          if id != nil { showingCompletion = true }
        }
        .onChange(of: queue.message) { _, _ in recorder.restoreCompletion(account: api.account) }
        .onChange(of: bridge.completionRevision) { _, _ in
          recorder.restoreCompletion(account: api.account)
        }
        .confirmationDialog(
          "Finish this workout?", isPresented: $confirmFinish, titleVisibility: .visible
        ) {
          Button("Finish and save") { Task { await recorder.finish() } }
          Button("Keep recording", role: .cancel) {}
        } message: {
          Text("Saved on this device before syncing.")
        }
    }
  }
}
struct NativeComment: Decodable, Identifiable {
  let id: String
  let user: FeedUser
  let text: String?
  var textVisibility: String? = nil
  var likesCount: Int? = nil
  var liked: Bool? = nil
  var mentions: [FeedUser]? = nil
  enum CodingKeys: String, CodingKey {
    case id, user, text, liked, mentions
    case likesCount = "likes_count"
    case textVisibility = "text_visibility"
  }
}
struct NativeComments: Decodable { let comments: [NativeComment] }
struct NativeMonth: Decodable, Identifiable {
  let month: String
  let sportID: Int
  let distanceM: Double
  let activities: Int
  var elapsedS: Double? = nil
  var id: String { month + String(sportID) }
  enum CodingKeys: String, CodingKey {
    case month, activities
    case sportID = "sport_id"
    case distanceM = "distance_m"
    case elapsedS = "elapsed_s"
  }
}
struct NativeBest: Decodable, Identifiable {
  var workoutID: String? = nil
  let sportID: Int
  let distanceM: Double
  let elapsedS: Double
  let title: String
  var date: String? = nil
  var start: Double? = nil
  var end: Double? = nil
  var id: String { String(sportID) + ":" + String(distanceM) }
  enum CodingKeys: String, CodingKey {
    case title, date, start, end
    case workoutID = "workout_id"
    case sportID = "sport_id"
    case distanceM = "distance_m"
    case elapsedS = "elapsed_s"
  }
}
struct NativeProgressView: View {
  var initialSection = "Week"
  @EnvironmentObject var api: APIClient
  @StateObject private var training = TrainingStore.shared
  @State private var section = "Week"
  @State private var configuredAccount = ""
  @State private var sport = 0
  @State private var activities: [FeedActivity] = []
  @State private var query = ""
  @State private var loadingActivities = false
  @State private var activityError: String?
  @State private var page = 0
  @State private var more = false
  @State private var requestID = UUID()
  private var records: [NativeBest] {
    training.bests.filter { sport == 0 || $0.sportID == sport }.sorted {
      $0.distanceM < $1.distanceM
    }
  }
  var body: some View {
    NavigationStack {
      ScrollView {
        LazyVStack(alignment: .leading, spacing: 14) {
          Picker("Training view", selection: $section) {
            Text("Week").tag("Week")
            Text("Records").tag("Records")
            Text("History").tag("History")
          }.pickerStyle(.segmented)
          HStack {
            Text(
              section == "Records"
                ? "All-time bests" : section == "History" ? "Workouts" : "Weekly distance"
            )
            .font(.headline).tracking(-0.3)
            Spacer()
            Picker("Sport", selection: $sport) {
              Text("All sports").tag(0)
              ForEach(api.sports) { Text($0.label).tag($0.id) }
            }.labelsHidden().fixedSize().tint(RintStyle.ink)
          }
          if section == "Week" {
            if training.weeksLoaded {
              NativeWeeklySummary(weeks: training.recentWeeks(sport: sport), sport: sport)
            } else if training.weeklyLoading {
              ProgressView("Loading your weekly mileage…").frame(maxWidth: .infinity).padding(24)
            }
            Button {
              section = "Records"
            } label: {
              HStack {
                Image(systemName: "trophy.fill").foregroundStyle(RintStyle.power)
                VStack(alignment: .leading, spacing: 4) {
                  Text("All-time bests").font(.headline)
                  Text("\(records.count) distances").font(.caption)
                    .foregroundStyle(RintStyle.muted)
                }
                Spacer()
                Image(systemName: "chevron.right").font(.caption.bold())
              }.foregroundStyle(RintStyle.ink).padding(.vertical, 12)
            }.buttonStyle(.plain)
            Divider()
            Text("Recent workouts").font(.title3.bold())
            activityRows
          } else if section == "Records" {
            if training.analyzing {
              HStack {
                ProgressView()
                Text(training.analysisMessage ?? "Preparing your records…").font(.caption)
              }
            } else if let message = training.analysisMessage {
              RintNotice(text: message, icon: "info.circle")
            }
            if records.isEmpty && !training.loading {
              ContentUnavailableView(
                "No records yet", systemImage: "trophy",
                description: Text(
                  "A recording with enough distance samples will establish a best effort. Summary-only workouts can’t verify one."
                ))
            }
            ForEach(Array(Set(records.map(\.sportID))).sorted(), id: \.self) { sportID in
              NativeRecordsSection(
                records: records.filter { $0.sportID == sportID },
                sport: api.sports.first(where: { $0.id == sportID })?.label ?? "Workout",
                showSport: sport == 0)
            }
            Button {
              Task { await training.load(api: api) }
            } label: {
              Label("Refresh records", systemImage: "arrow.clockwise")
            }.font(.subheadline).frame(minHeight: 44).disabled(training.loading)
          } else {
            HStack {
              Image(systemName: "magnifyingglass").foregroundStyle(RintStyle.muted)
              TextField("Find a workout", text: $query).submitLabel(.search)
                .onSubmit { Task { await loadActivities(reset: true) } }
              if !query.isEmpty {
                Button {
                  query = ""
                } label: {
                  Image(systemName: "xmark.circle.fill")
                }.accessibilityLabel("Clear search")
              }
            }.padding(14).background(RintStyle.soft, in: RoundedRectangle(cornerRadius: 12))
            activityRows
          }
          if training.loading && training.weeks.isEmpty { ProgressView("Loading your training…") }
          if let error = training.error {
            RintNotice(text: error, icon: "exclamationmark.circle")
            Button("Try again") { Task { await training.load(api: api) } }.buttonStyle(
              RintSecondaryButton())
          }
        }.padding(.horizontal, 16).padding(.vertical, 12)
      }.background(RintStyle.paper).navigationTitle("Progress").navigationBarTitleDisplayMode(
        .inline
      )
      .task {
        if configuredAccount != api.account {
          configuredAccount = api.account
          section = initialSection == "Records" ? "Records" : api.selectedTrainingSection
          sport = api.sports.first(where: { $0.label.lowercased() == "running" })?.id ?? 0
        }
        await loadActivities(reset: true)
        await training.load(api: api)
      }
      .refreshable {
        await loadActivities(reset: true)
        await training.load(api: api)
      }
      .task(id: sport) { await loadActivities(reset: true) }
      .onChange(of: api.selectedTrainingSection) { _, value in section = value }
      .task(id: query) {
        do { try await Task.sleep(for: .milliseconds(350)) } catch { return }
        await loadActivities(reset: true)
      }
    }
  }
  @ViewBuilder private var activityRows: some View {
    ForEach(activities) { workout in
      NavigationLink {
        NativeActivityView(workout: workout)
      } label: {
        HStack(spacing: 14) {
          Image(systemName: "figure.run").font(.title3).foregroundStyle(RintStyle.violet)
            .frame(width: 42, height: 42).background(RintStyle.soft, in: Circle())
          VStack(alignment: .leading, spacing: 5) {
            Text(
              EffortPresentation.title(
                workout,
                sport: api.sports.first(where: { $0.id == workout.sportID })?.label ?? "Workout")
            )
            .font(.subheadline.bold()).foregroundStyle(RintStyle.ink)
            Text(workout.date?.formatted(date: .abbreviated, time: .shortened) ?? "Workout")
              .font(.caption).foregroundStyle(RintStyle.muted)
          }
          Spacer()
          Text(
            workout.distance.map {
              DisplayUnits.distance($0 * 1000) + " " + DisplayUnits.distanceUnit
            } ?? "—"
          )
          .font(.subheadline.weight(.semibold)).monospacedDigit().foregroundStyle(RintStyle.ink)
        }.padding(.vertical, 8)
      }.buttonStyle(.plain)
      Divider()
    }
    if loadingActivities { ProgressView("Loading workouts…") }
    if more {
      Button("More workouts") { Task { await loadActivities() } }.buttonStyle(RintSecondaryButton())
        .disabled(loadingActivities)
    }
    if let activityError {
      RintNotice(text: activityError, icon: "exclamationmark.circle")
      Button("Retry workouts") { Task { await loadActivities(reset: true) } }
    } else if activities.isEmpty && !loadingActivities {
      Text(query.isEmpty ? "Your workouts will appear here." : "No workouts match this search.")
        .font(.subheadline).foregroundStyle(RintStyle.muted)
    }
  }
  @MainActor private func loadActivities(reset: Bool = false) async {
    if !reset && loadingActivities { return }
    let identifier = UUID()
    requestID = identifier
    loadingActivities = true
    let next = reset ? 1 : page + 1
    let requestedAccount = api.account
    defer { if requestID == identifier { loadingActivities = false } }
    do {
      let escaped =
        query.addingPercentEncoding(
          withAllowedCharacters: .urlQueryAllowed.subtracting(CharacterSet(charactersIn: "&+?=")))
        ?? ""
      let response = try JSONDecoder().decode(
        APIResponse<FeedResponse>.self,
        from: await api.request(
          "workouts?per_page=25&page=\(next)" + (sport == 0 ? "" : "&sport_id=\(sport)")
            + (query.isEmpty ? "" : "&title=\(escaped)")))
      guard requestID == identifier, requestedAccount == api.account else { return }
      activities =
        reset
        ? response.data.workouts
        : activities
          + response.data.workouts.filter { row in !activities.contains(where: { $0.id == row.id })
          }
      page = next
      more = response.pagination?.hasNext ?? false
      activityError = nil
    } catch { if requestID == identifier { activityError = error.localizedDescription } }
  }
}

struct SettingsView: View {
  @State private var confirmingSignOut = false
  @ObservedObject private var healthSaves = HealthSaveQueue.shared
  @EnvironmentObject var api: APIClient
  @EnvironmentObject var queue: SyncQueue
  var body: some View {
    Form {
      Section {
        NavigationLink {
          HealthImportView()
        } label: {
          importRow(
            "Apple Health", detail: "Your Watch history and automatic workout sync",
            icon: "heart.fill", color: RintStyle.heart)
        }
        NavigationLink {
          NativeStravaImportView()
        } label: {
          importRow(
            "Strava archive", detail: "Bring your activities, original files and photos",
            icon: "arrow.down.doc", color: RintStyle.violet)
        }
      } header: {
        Text("Import workouts")
      } footer: {
        Text("Imports start private. Review your activities before sharing.")
      }
      Section("Your data") {
        NavigationLink {
          NativeAccountExport()
        } label: {
          Label("Export your data", systemImage: "square.and.arrow.down")
        }
        NavigationLink {
          NativePreferencesView()
        } label: {
          Label("Units & privacy", systemImage: "slider.horizontal.3")
        }
      }
      Section("Sync status") {
        Label(
          queue.pending == 0
            ? "Workout uploads up to date" : "\(queue.pending) workouts waiting to upload",
          systemImage: queue.pending == 0 ? "checkmark.circle" : "arrow.triangle.2.circlepath")
        if !queue.message.isEmpty { Text(queue.message).font(.footnote) }
        if queue.pending > 0 {
          Button("Retry upload") { queue.sync(force: true) }
        }
        Label(
          healthSaves.pending == 0
            ? "No Health saves pending" : "\(healthSaves.pending) Health saves waiting",
          systemImage: healthSaves.pending == 0 ? "checkmark.circle" : "heart.text.square")
        if healthSaves.pending > 0 {
          Button(healthSaves.retrying ? "Retrying…" : "Retry Health saves") {
            Task { await healthSaves.retry(account: api.account) }
          }.disabled(healthSaves.retrying)
        }
        if let error = healthSaves.error {
          RintNotice(text: error, icon: "exclamationmark.circle")
        }
      }
      Section {
        LabeledContent("Server", value: api.server)
        NavigationLink("Edit profile") { NativeProfileEditor() }
        NavigationLink("Invite friends") { NativeInvitation() }
        Button("Sign out", role: .destructive) { confirmingSignOut = true }
      } header: {
        Text("Account")
      } footer: {
        Text("Metrics, charts and exports are always free.")
      }
    }.scrollContentBackground(.hidden).background(RintStyle.paper)
      .navigationTitle("Imports & data").navigationBarTitleDisplayMode(.inline)
      .confirmationDialog(
        "Sign out of Rint?", isPresented: $confirmingSignOut, titleVisibility: .visible
      ) {
        Button("Sign out", role: .destructive) { api.signOut() }
      } message: {
        Text("Unsynced workouts stay on this device and sync when you reconnect to this account.")
      }
  }
  func importRow(_ title: String, detail: String, icon: String, color: Color) -> some View {
    HStack(spacing: 14) {
      Image(systemName: icon).font(.title3).foregroundStyle(color)
        .frame(width: 44, height: 44).background(
          color.opacity(0.1), in: RoundedRectangle(cornerRadius: 12))
      VStack(alignment: .leading, spacing: 5) {
        Text(title).font(.headline).foregroundStyle(RintStyle.ink)
        Text(detail).font(.caption).foregroundStyle(RintStyle.muted)
      }
    }.padding(.vertical, 8)

  }
}

/// A real account summary, independent of the paginated social feed.
struct NativeTrainingSnapshot: View {
  @EnvironmentObject var api: APIClient
  @Environment(\.dynamicTypeSize) private var typeSize
  @StateObject private var training = TrainingStore.shared
  private var running: Int {
    api.sports.first(where: { $0.label.lowercased() == "running" })?.id ?? 0
  }
  private var weeks: [NativeWeek] { training.recentWeeks(sport: running, count: 8) }
  var body: some View {
    Button {
      api.selectedTrainingSection = "Week"
      api.selectedTab = 1
    } label: {
      VStack(alignment: .leading, spacing: 16) {
        HStack(spacing: 8) {
          Circle().fill(RintStyle.accent).frame(width: 6, height: 6).accessibilityHidden(true)
          Text("This week").font(.caption.weight(.semibold))
          Text(running == 0 ? "All sports" : "Running").font(.caption).foregroundStyle(.white.opacity(0.75))
          Spacer(minLength: 0)
          Image(systemName: "arrow.right").foregroundStyle(RintStyle.accent)
        }
        let layout = typeSize.isAccessibilitySize ? AnyLayout(VStackLayout(alignment: .leading, spacing: 16)) : AnyLayout(HStackLayout(alignment: .center, spacing: 20))
        layout {
          VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .firstTextBaseline, spacing: 6) {
              if !training.weeksLoaded && training.weeklyLoading {
                ProgressView().tint(.white)
              } else {
                Text(training.weeksLoaded ? DisplayUnits.distance(weeks.last?.distanceM ?? 0, decimals: 1) : "—")
                  .font(.system(.largeTitle, design: .default).weight(.semibold)).monospacedDigit().tracking(-1.5)
                Text(DisplayUnits.distanceUnit).font(.subheadline).foregroundStyle(RintStyle.accent)
              }
            }
            if training.weeksLoaded {
              Text("Last week " + DisplayUnits.distance(weeks.dropLast().last?.distanceM ?? 0, decimals: 1) + " " + DisplayUnits.distanceUnit)
                .font(.caption2).foregroundStyle(.white.opacity(0.75))
            }
          }.frame(maxWidth: .infinity, alignment: .leading)
          if training.weeksLoaded {
            HStack(alignment: .top, spacing: 18) {
              VStack(alignment: .leading, spacing: 5) {
                Text(String(weeks.last?.activities ?? 0)).font(.title2.weight(.medium)).monospacedDigit()
                Text(weeks.last?.activities == 1 ? "activity" : "activities").font(.caption2).foregroundStyle(.white.opacity(0.75))
              }
              VStack(alignment: .leading, spacing: 5) {
                Text(String(format: "%.1f", (weeks.last?.elapsedS ?? 0) / 3600) + " h")
                  .font(.title2.weight(.medium)).monospacedDigit()
                Text("time recorded").font(.caption2).foregroundStyle(.white.opacity(0.75))
              }
            }
          }
        }
        if training.weeksLoaded {
          VStack(spacing: 6) {
            HStack {
              Text("8-week distance")
              Spacer()
              Text(DisplayUnits.distanceUnit)
            }.font(.caption2).foregroundStyle(.white.opacity(0.75))
            HStack(alignment: .bottom, spacing: 7) {
              ForEach(Array(weeks.enumerated()), id: \.offset) { index, week in
                VStack(spacing: 6) {
                  ZStack(alignment: .bottom) {
                    RoundedRectangle(cornerRadius: 3).fill(.white.opacity(0.04))
                    RoundedRectangle(cornerRadius: 3)
                      .fill(index == weeks.count - 1 ? RintStyle.accent : Color(red: 0.45, green: 0.60, blue: 0.58))
                      .frame(height: max(1, 28 * week.distanceM / max(1, weeks.map(\.distanceM).max() ?? 1)))
                  }.frame(height: 28)
                  if !typeSize.isAccessibilitySize {
                    Text(TrainingDates.date(week.week)?.formatted(.dateTime.month(.abbreviated).day()) ?? "")
                      .font(.system(size: 8)).foregroundStyle(.white.opacity(0.75)).lineLimit(1)
                  }
                }.frame(maxWidth: .infinity)
              }
            }.accessibilityHidden(true)
          }
        }
        if let error = training.error { Text(error).font(.caption) }
      }.foregroundStyle(.white).padding(18)
        .background(
          LinearGradient(colors: [Color(red: 0.094, green: 0.239, blue: 0.243), Color(red: 0.082, green: 0.169, blue: 0.216)], startPoint: .topLeading, endPoint: .bottomTrailing),
          in: RoundedRectangle(cornerRadius: 18)
        )
        .overlay(RoundedRectangle(cornerRadius: 18).stroke(.white.opacity(0.12), lineWidth: 1))
    }.buttonStyle(.plain)
      .accessibilityHint("Opens your weekly training history")
      .task { await training.loadWeeks(api: api) }
      .onChange(of: api.refreshing) { _, refreshing in
        if !refreshing { Task { await training.loadWeeks(api: api) } }
      }
  }
}
