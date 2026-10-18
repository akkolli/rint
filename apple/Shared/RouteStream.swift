import Foundation

/// GPS and sensor samples have independent clocks. Only an explicit privacy
/// break or a gap between GPS fixes may disconnect the displayed route.
enum RouteStream {
  static func protected(_ points: [Sample], radius: Double) -> [Sample] {
    let fixes = points.filter { $0.lat != nil && $0.lon != nil }
    guard let first = fixes.first, let last = fixes.last else { return points }
    return points.map { point in
      var result = point
      if point.lat != nil && point.lon != nil,
        distance(point, first) < radius || distance(point, last) < radius
      {
        result.lat = nil
        result.lon = nil
        result.routeGap = true
      }
      return result
    }
  }
  private static func distance(_ a: Sample, _ b: Sample) -> Double {
    guard let aLat = a.lat, let aLon = a.lon, let bLat = b.lat, let bLon = b.lon else {
      return .infinity
    }
    let latitude = (bLat - aLat) * .pi / 180
    let longitude = (bLon - aLon) * .pi / 180
    let h =
      pow(sin(latitude / 2), 2) + cos(aLat * .pi / 180) * cos(bLat * .pi / 180)
      * pow(sin(longitude / 2), 2)
    return 6371008.8 * 2 * asin(min(1, sqrt(max(0, h))))
  }
  static func segments(_ points: [Sample], sampled: Bool = false) -> [[Sample]] {
    var result: [[Sample]] = []
    var row: [Sample] = []
    for point in points {
      let located =
        point.lat.map { $0.isFinite && abs($0) <= 90 } == true
        && point.lon.map { $0.isFinite && abs($0) <= 180 } == true
      if point.routeGap == true
        || (located && !sampled
          && row.last.map {
            point.t - $0.t > 60
          } == true)
      {
        if row.count > 1 { result.append(row) }
        row = []
      }
      if located { row.append(point) }
    }
    if row.count > 1 { result.append(row) }
    return result
  }
}
