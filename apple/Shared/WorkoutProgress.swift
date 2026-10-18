import Foundation

/// Checkpointed timing and distance state; independent of sensor callback frequency.
struct WorkoutProgress: Codable {
  var activeSeconds = 0.0
  var activeSince: Double? = 0
  var deviceDistanceAnchor = 0.0

  func duration(at elapsed: Double) -> Double {
    activeSeconds + (activeSince.map { max(0, elapsed - $0) } ?? 0)
  }
  mutating func setActive(_ active: Bool, at elapsed: Double) {
    if active {
      if activeSince == nil { activeSince = elapsed }
    } else if let since = activeSince {
      activeSeconds += max(0, elapsed - since)
      activeSince = nil
    }
  }
  mutating func distanceChange(raw: Double, active: Bool) -> Double {
    guard raw.isFinite, raw >= 0 else { return 0 }
    let delta = raw >= deviceDistanceAnchor ? raw - deviceDistanceAnchor : raw
    deviceDistanceAnchor = raw
    return active ? delta : 0
  }
  static func reconstruct(_ points: [Sample]) -> Self {
    var result = Self()
    for point in points.sorted(by: { $0.t < $1.t }) {
      result.setActive(point.active, at: point.t)
    }
    result.deviceDistanceAnchor = points.compactMap(\.d).max() ?? 0
    return result
  }
}
