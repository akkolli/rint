import Foundation

struct ChartReading: Identifiable {
  let id: Int
  let t: Double
  let value: Double
  let segment: Int
}

enum ChartStream {
  static func values(_ samples: [Sample], metric: String) -> [ChartReading] {
    var result: [ChartReading] = []
    var segment = 0
    var last = -Double.infinity
    var interrupted = false
    var windowStart = 0
    for (index, sample) in samples.enumerated() {
      var value: Double?
      switch metric {
      case "heart_rate": value = sample.heartRate
      case "power": value = sample.power
      case "elevation": value = sample.elevation
      case "cadence": value = sample.cadence
      default:
        if index > 0 {
          let previous = samples[index - 1]
          if previous.active, previous.distanceGap != true, sample.distanceGap != true,
            let a = previous.d, let b = sample.d, b > a, sample.t - previous.t <= 60
          {
            while windowStart < index - 1 && samples[windowStart + 1].t <= sample.t - 30 {
              windowStart += 1
            }
            let anchor = samples[windowStart]
            let target = max(anchor.t, sample.t - 30)
            var anchorDistance = anchor.d ?? a
            if windowStart + 1 <= index {
              let next = samples[windowStart + 1]
              if let nextDistance = next.d, next.t > anchor.t {
                anchorDistance +=
                  (nextDistance - anchorDistance) * (target - anchor.t) / (next.t - anchor.t)
              }
            }
            let dt = sample.t - target
            let distance = b - anchorDistance
            // A 30-second distance window avoids spikes from tiny increments
            // between independently sampled sensors. Stops are visible gaps.
            if dt >= 5, distance / dt >= 0.3 {
              value = dt / distance * 1000 / 60
            }
          } else {
            windowStart = index
          }
        }
      }
      guard let value, value.isFinite else {
        if metric == "pace" { interrupted = true }
        continue
      }
      if sample.t - last > 60 || interrupted { segment += 1 }
      result.append(ChartReading(id: index, t: sample.t, value: value, segment: segment))
      last = sample.t
      interrupted = false
    }
    return result
  }

  static func bounds(_ rows: [ChartReading], metric: String, fullRange: Bool = false)
    -> ClosedRange<Double>
  {
    let sorted = rows.map(\.value).filter(\.isFinite).sorted()
    guard let low = sorted.first, let high = sorted.last else { return 0...1 }
    var upper = high
    if metric == "pace", !fullRange, sorted.count >= 20 {
      let q1 = sorted[sorted.count / 4]
      let q3 = sorted[sorted.count * 3 / 4]
      upper = min(high, max(q3 + max(1, (q3 - q1) * 3), q3 * 1.25))
    }
    let padding = max(0.5, (upper - low) * 0.12)
    return max(0, low - padding)...(upper + padding)
  }

  static func reduced(_ rows: [ChartReading], buckets: Int = 500) -> [ChartReading] {
    guard rows.count > buckets * 4, let first = rows.first, let last = rows.last else {
      return rows
    }
    let duration = max(1, last.t - first.t)
    var result: [ChartReading] = []
    var start = 0
    func bucket(_ i: Int) -> Int { Int((rows[i].t - first.t) / duration * Double(buckets)) }
    for i in 1...rows.count {
      if i < rows.count && bucket(i) == bucket(start) { continue }
      var low = start
      var high = start
      for j in start..<i {
        if rows[j].value < rows[low].value { low = j }
        if rows[j].value > rows[high].value { high = j }
      }
      result.append(contentsOf: Set([start, low, high, i - 1]).sorted().map { rows[$0] })
      start = i
    }
    return result
  }

  static func nearest(_ rows: [ChartReading], at time: Double) -> ChartReading? {
    guard !rows.isEmpty else { return nil }
    var lo = 0
    var hi = rows.count
    while lo < hi {
      let mid = (lo + hi) / 2
      if rows[mid].t < time { lo = mid + 1 } else { hi = mid }
    }
    let a = rows[max(0, lo - 1)]
    let b = rows[min(rows.count - 1, lo)]
    if time < rows[0].t || time > rows[rows.count - 1].t { return nil }
    if time != a.t && time != b.t && (b.t - a.t > 60 || a.segment != b.segment) { return nil }
    let point = abs(a.t - time) <= abs(b.t - time) ? a : b
    return abs(point.t - time) <= 60 ? point : nil
  }
}
