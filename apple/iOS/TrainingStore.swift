import Combine
import Foundation

struct NativeWeek: Decodable, Identifiable {
  let week: String
  let sportID: Int
  let distanceM: Double
  let activities: Int
  let elapsedS: Double
  var id: String { week + ":" + String(sportID) }
  enum CodingKeys: String, CodingKey {
    case week, activities
    case sportID = "sport_id"
    case distanceM = "distance_m"
    case elapsedS = "elapsed_s"
  }
}
struct BestResponse: Decodable {
  struct Coverage: Decodable { let pending: Int }
  let data: [NativeBest]
  var coverage: Coverage?
}
enum TrainingDates {
  static var calendar: Calendar {
    var calendar = Calendar(identifier: .gregorian)
    calendar.timeZone = .current
    calendar.firstWeekday = 2
    calendar.minimumDaysInFirstWeek = 4
    return calendar
  }
  static func key(_ date: Date) -> String {
    let parts = calendar.dateComponents([.year, .month, .day], from: date)
    return String(format: "%04d-%02d-%02d", parts.year!, parts.month!, parts.day!)
  }
  static func date(_ key: String) -> Date? {
    let parts = key.prefix(10).split(separator: "-").compactMap { Int($0) }
    guard parts.count == 3 else { return nil }
    return calendar.date(from: DateComponents(year: parts[0], month: parts[1], day: parts[2]))
  }
  static func monday(_ date: Date = Date()) -> Date {
    calendar.dateInterval(of: .weekOfYear, for: date)!.start
  }
}
enum EffortPresentation {
  static func distance(_ meters: Double) -> String {
    if abs(meters - 1609.344) < 0.01 { return "1 mile" }
    if abs(meters - 21097.5) < 0.01 { return "Half marathon" }
    if abs(meters - 42195) < 0.01 { return "Marathon" }
    return meters < 1000 ? "\(Int(meters)) m" : String(format: "%.3g km", meters / 1000)
  }
  static func title(_ workout: FeedActivity, sport: String) -> String {
    let original = workout.title ?? ""
    guard original.isEmpty || original.hasPrefix("Apple Health ") || original == "Workout" else {
      return original
    }
    let hour = workout.date.map { Calendar.current.component(.hour, from: $0) } ?? 12
    let period = hour < 12 ? "Morning" : hour < 17 ? "Afternoon" : "Evening"
    let activity =
      sport.lowercased().contains("run")
      ? "run"
      : sport.lowercased().contains("cycl")
        ? "ride"
        : sport.lowercased().contains("walk") ? "walk" : sport.lowercased()
    return period + " " + activity
  }
}

@MainActor final class TrainingStore: ObservableObject {
  static let shared = TrainingStore()
  @Published var weeks: [NativeWeek] = []
  @Published var bests: [NativeBest] = []
  @Published var loading = false
  @Published var analyzing = false
  @Published var analysisMessage: String?
  @Published var error: String?
  @Published var weeklyLoading = false
  @Published var weeksLoaded = false
  private var account = ""
  private var generation = UUID()
  func clear() {
    generation = UUID()
    loading = false
    analyzing = false
    weeklyLoading = false
    weeksLoaded = false
    account = ""
    weeks = []
    bests = []
    error = nil
    analysisMessage = nil
  }
  func resetIfNeeded(_ api: APIClient) {
    if account != api.account {
      clear()
      account = api.account
      weeks = []
      bests = []
      error = nil
      analysisMessage = nil
    }
  }
  func loadWeeks(api: APIClient) async {
    resetIfNeeded(api)
    guard !weeklyLoading else { return }
    let current = generation
    weeklyLoading = true
    defer { if current == generation { weeklyLoading = false } }
    let requestedAccount = api.account
    do {
      let timezone =
        TimeZone.current.identifier.addingPercentEncoding(
          withAllowedCharacters: .urlQueryAllowed) ?? "UTC"
      let rows = try JSONDecoder().decode(
        APIResponse<[NativeWeek]>.self,
        from: await api.request("rint/history?period=week&timezone=\(timezone)")
      ).data
      guard requestedAccount == api.account else { return }
      weeks = rows
      weeksLoaded = true
      error = nil
    } catch { if requestedAccount == api.account { self.error = error.localizedDescription } }
  }
  func load(api: APIClient) async {
    resetIfNeeded(api)
    guard !loading else { return }
    let current = generation
    loading = true
    defer {
      if current == generation {
        loading = false
        analyzing = false
      }
    }
    let requestedAccount = api.account
    await loadWeeks(api: api)
    do {
      var response = try JSONDecoder().decode(
        BestResponse.self,
        from: await api.request("rint/bests"))
      guard requestedAccount == api.account else { return }
      bests = response.data
      if (response.coverage?.pending ?? 0) > 0 {
        analyzing = true
        var cursor = 0
        var reviewed = 0
        var failures = 0
        var more = true
        while more && !Task.isCancelled && requestedAccount == api.account {
          struct Batch: Decodable {
            let cursor: Int
            let processed: Int
            let hasMore: Bool
            let errors: [Failure]
            struct Failure: Decodable { let message: String }
            enum CodingKeys: String, CodingKey {
              case cursor, processed, errors
              case hasMore = "has_more"
            }
          }
          let batch = try JSONDecoder().decode(
            APIResponse<Batch>.self,
            from: await api.request(
              "rint/bests/refresh", method: "POST",
              body: JSONSerialization.data(withJSONObject: ["cursor": cursor]))
          ).data
          cursor = batch.cursor
          reviewed += batch.processed
          failures += batch.errors.count
          more = batch.hasMore
          guard requestedAccount == api.account else { return }
          analysisMessage = "Preparing your records · \(reviewed) recordings reviewed"
          response = try JSONDecoder().decode(
            BestResponse.self,
            from: await api.request("rint/bests"))
          guard requestedAccount == api.account else { return }
          bests = response.data
        }
        analysisMessage =
          failures > 0
          ? "\(failures) recordings need another attempt. Your completed records are shown."
          : Task.isCancelled ? "Preparation paused. Open Records to continue." : nil
      }
    } catch {
      if requestedAccount == api.account {
        self.error = "Your records couldn’t refresh. \(error.localizedDescription)"
      }
    }
  }
  func recentWeeks(sport: Int, count: Int = 8, now: Date = Date()) -> [NativeWeek] {
    let monday = TrainingDates.monday(now)
    return (0..<count).reversed().map { offset in
      let start = TrainingDates.calendar.date(byAdding: .day, value: -offset * 7, to: monday)!
      let key = TrainingDates.key(start)
      let rows = weeks.filter { $0.week == key && (sport == 0 || $0.sportID == sport) }
      return NativeWeek(
        week: key, sportID: sport, distanceM: rows.reduce(0) { $0 + $1.distanceM },
        activities: rows.reduce(0) { $0 + $1.activities },
        elapsedS: rows.reduce(0) { $0 + $1.elapsedS })
    }
  }
}
