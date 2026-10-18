import Foundation

enum PlotSelection {
  static func index(x: Double, width: Double, count: Int) -> Int? {
    guard width > 0, x.isFinite, count > 0 else { return nil }
    let fraction = min(1, max(0, x / width))
    return min(count - 1, Int(floor(fraction * Double(count))))
  }
}
