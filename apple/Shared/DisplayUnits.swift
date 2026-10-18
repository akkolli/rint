import Foundation

/// Display only: recordings always retain SI units and unrounded timestamps.
enum DisplayUnits {
  static func date(_ raw: String) -> Date? {
    let formatter = ISO8601DateFormatter()
    if let date = formatter.date(from: raw) { return date }
    formatter.formatOptions.insert(.withFractionalSeconds)
    return formatter.date(from: raw)
  }
  static var imperial: Bool { UserDefaults.standard.bool(forKey: "imperial_units") }
  static var distanceUnit: String { imperial ? "mi" : "km" }
  static var distanceSize: Double { imperial ? 1609.344 : 1000 }
  static var paceFactor: Double { distanceSize / 1000 }
  static var speedUnit: String { imperial ? "mph" : "km/h" }
  static func speed(_ metersPerSecond: Double?) -> String {
    metersPerSecond.map { String(format: "%.1f", $0 * 3600 / distanceSize) } ?? "—"
  }
  static func distance(_ meters: Double, decimals: Int = 2) -> String {
    String(format: "%.*f", decimals, meters / distanceSize)
  }
  static func pace(_ secondsPerKM: Double?) -> String {
    secondsPerKM.map { compactTimeLabel($0 * paceFactor) } ?? "—"
  }
  static func duration(_ raw: String?) -> String {
    seconds(raw).map { compactTimeLabel($0) } ?? "—"
  }
  static func seconds(_ raw: String?) -> Double? {
    guard let raw else { return nil }
    let parts = raw.split(separator: ",", maxSplits: 1)
    var days = 0.0
    if parts.count == 2 {
      guard let count = Double(parts[0].split(separator: " ").first ?? ""),
        count.isFinite, count >= 0, count <= 7
      else {
        return nil
      }
      days = count
    }
    guard let clockText = parts.last else { return nil }
    let clock = clockText.trimmingCharacters(in: .whitespaces).split(separator: ":")
      .compactMap { Double($0) }
    guard clock.count == 3, clock.allSatisfy({ $0.isFinite && $0 >= 0 }),
      clock[0] <= 168, clock[1] < 60, clock[2] < 60
    else { return nil }
    return days * 86400 + clock[0] * 3600 + clock[1] * 60 + clock[2]
  }
}
func compactTimeLabel(_ seconds: Double) -> String {
  let s = seconds.isFinite ? max(0, Int(seconds.rounded())) : 0
  return s < 3600
    ? String(format: "%02d:%02d", s / 60, s % 60)
    : String(format: "%d:%02d:%02d", s / 3600, (s / 60) % 60, s % 60)
}
