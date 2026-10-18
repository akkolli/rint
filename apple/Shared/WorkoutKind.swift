import HealthKit

enum WorkoutKind {
  static func type(_ label: String) -> HKWorkoutActivityType {
    let label = label.lowercased()
    if label.contains("cycl") || label.contains("biking") { return .cycling }
    if label.contains("running") || label == "trail" { return .running }
    if label.contains("walking") { return .walking }
    if label.contains("hiking") { return .hiking }
    if label.contains("swim") { return .swimming }
    if label.contains("strength") { return .traditionalStrengthTraining }
    if label.contains("yoga") { return .yoga }
    if label.contains("rowing") { return .rowing }
    return .other
  }
  static func label(_ type: HKWorkoutActivityType) -> String {
    switch type {
    case .running: return "Run"
    case .cycling: return "Ride"
    case .walking: return "Walk"
    case .swimming: return "Swim"
    case .hiking: return "Hike"
    case .traditionalStrengthTraining: return "Strength workout"
    default: return "Workout"
    }
  }
}
