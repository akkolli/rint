import AudioToolbox
import SwiftUI
import UIKit

enum RintStyle {
  static let accent = Color(red: 0.83, green: 0.95, blue: 0.42)
  static let accentInk = Color(red: 0.12, green: 0.15, blue: 0.09)
  static let paper = adaptive(0xF4F6F7, 0x10171D)
  static let surface = adaptive(0xFFFFFF, 0x19232B)
  static let soft = adaptive(0xEAF0F2, 0x22313B)
  static let line = adaptive(0xDFE6E9, 0x30414D)
  static let ink = adaptive(0x172B35, 0xEDF3F6)
  static let muted = adaptive(0x5D6D78, 0xA6B6C1)
  static let distance = adaptive(0x18786C, 0x79D5BF)
  static let violet = adaptive(0x7052D6, 0xB09AF6)
  static let heart = adaptive(0xB93E5B, 0xF08DA5)
  static let power = adaptive(0x93601A, 0xEDBE72)
  static func adaptive(_ light: Int, _ dark: Int) -> Color {
    Color(
      UIColor { traits in
        let hex = traits.userInterfaceStyle == .dark ? dark : light
        return UIColor(
          red: CGFloat((hex >> 16) & 255) / 255,
          green: CGFloat((hex >> 8) & 255) / 255, blue: CGFloat(hex & 255) / 255, alpha: 1)
      })
  }
  static func metricColor(_ metric: String) -> Color {
    metric == "heart_rate" ? heart : metric == "power" ? power : violet
  }
}
struct RintPrimaryButton: ButtonStyle {
  @Environment(\.isEnabled) private var enabled
  @Environment(\.accessibilityReduceMotion) private var reduceMotion
  func makeBody(configuration: Configuration) -> some View {
    configuration.label.font(.headline).frame(maxWidth: .infinity).padding(.vertical, 16)
      .foregroundStyle(RintStyle.accentInk)
      .background(
        RintStyle.accent.opacity(enabled ? (configuration.isPressed ? 0.75 : 1) : 0.4),
        in: Capsule()
      )
      .opacity(enabled ? 1 : 0.6)
      .scaleEffect(configuration.isPressed && !reduceMotion ? 0.98 : 1)
      .animation(reduceMotion ? nil : .easeOut(duration: 0.16), value: configuration.isPressed)
  }
}
struct RintSecondaryButton: ButtonStyle {
  func makeBody(configuration: Configuration) -> some View {
    configuration.label.font(.subheadline.weight(.semibold)).frame(maxWidth: .infinity)
      .padding(.vertical, 14).foregroundStyle(RintStyle.ink)
      .background(configuration.isPressed ? RintStyle.line : RintStyle.soft, in: Capsule())
  }
}
extension View {
  func rintPanel(padding: CGFloat = 20) -> some View {
    self.padding(padding).frame(maxWidth: .infinity, alignment: .leading)
      .background(RintStyle.surface, in: RoundedRectangle(cornerRadius: 22))
      .overlay(RoundedRectangle(cornerRadius: 22).stroke(RintStyle.line, lineWidth: 1))
  }
}
struct RintEyebrow: View {
  let text: String
  var body: some View {
    Text(text.uppercased()).font(.caption2.weight(.bold)).tracking(1.2).foregroundStyle(
      RintStyle.muted)
  }
}
struct RintMetric: View {
  let title: String
  let value: String
  var unit: String = ""
  var body: some View {
    VStack(alignment: .leading, spacing: 8) {
      Text(title).font(.caption).foregroundStyle(RintStyle.muted)
      HStack(alignment: .firstTextBaseline, spacing: 4) {
        Text(value).font(.system(.title2, design: .rounded).weight(.semibold)).monospacedDigit()
        if !unit.isEmpty { Text(unit).font(.caption).foregroundStyle(RintStyle.muted) }
      }
    }.frame(maxWidth: .infinity, alignment: .leading)
      .accessibilityElement(children: .combine)
  }
}
struct RintNotice: View {
  let text: String
  var icon = "checkmark.shield"
  var body: some View {
    Label(text, systemImage: icon).font(.footnote).foregroundStyle(RintStyle.muted)
      .fixedSize(horizontal: false, vertical: true)
  }
}
struct RintRoutePreview: View {
  let points: [Sample]
  var sampledOutline = false
  private var segments: [[CGPoint]] {
    var paths: [[CGPoint]] = []
    var current: [CGPoint] = []
    var previous: Sample?
    for p in points {
      if p.lat == nil || p.lon == nil
        || (!sampledOutline && previous != nil && p.t - previous!.t > 60)
      {
        if current.count > 1 { paths.append(current) }
        current = []
      }
      if let lat = p.lat, let lon = p.lon, lat.isFinite, lon.isFinite {
        current.append(CGPoint(x: lon, y: lat))
      }
      previous = p
    }
    if current.count > 1 { paths.append(current) }
    return paths.map { path in
      let stride = max(1, Int(ceil(Double(path.count) / 400)))
      return path.enumerated().filter {
        $0.offset == 0 || $0.offset == path.count - 1 || $0.offset % stride == 0
      }.map(\.element)
    }
  }
  var body: some View {
    let segments = segments
    ZStack(alignment: .bottomLeading) {
      RintStyle.soft
      if segments.isEmpty {
        VStack(spacing: 12) {
          Image(systemName: "figure.run").font(.largeTitle).foregroundStyle(RintStyle.violet)
          Text("An effort worth keeping.").font(.headline)
          Text("Indoor, private or without GPS.").font(.caption).foregroundStyle(RintStyle.muted)
        }.frame(maxWidth: .infinity, maxHeight: .infinity)
      } else {
        Canvas { context, size in
          let origin = segments[0][0]
          let cosine = cos(origin.y * .pi / 180)
          let coordinates = segments.map {
            $0.map { point in
              var longitude = (point.x - origin.x).truncatingRemainder(dividingBy: 360)
              if longitude > 180 { longitude -= 360 }
              if longitude < -180 { longitude += 360 }
              return CGPoint(x: longitude * cosine, y: point.y)
            }
          }
          let all = coordinates.flatMap { $0 }
          let minX = all.map(\.x).min() ?? 0
          let maxX = all.map(\.x).max() ?? 1
          let minY = all.map(\.y).min() ?? 0
          let maxY = all.map(\.y).max() ?? 1
          let scale = min(
            (size.width - 60) / max(maxX - minX, 0.00001),
            (size.height - 64) / max(maxY - minY, 0.00001))
          for row in coordinates {
            var path = Path()
            for (i, p) in row.enumerated() {
              let position = CGPoint(
                x: size.width / 2 + (p.x - (minX + maxX) / 2) * scale,
                y: size.height / 2 - (p.y - (minY + maxY) / 2) * scale - 8)
              if i == 0 { path.move(to: position) } else { path.addLine(to: position) }
            }
            context.stroke(
              path, with: .color(RintStyle.violet),
              style: StrokeStyle(lineWidth: 3, lineCap: .round, lineJoin: .round))
          }
        }.accessibilityLabel("Recorded route outline")
        Text("RECORDED ROUTE · OUTLINE").font(.system(size: 9, weight: .semibold)).tracking(1)
          .foregroundStyle(RintStyle.muted).padding(16)
      }
    }.frame(height: 180).clipShape(RoundedRectangle(cornerRadius: 16))
  }
}

/// Optional confirmation sound. System sound playback respects the silent switch.
enum RintFeedback {
  private static let sound: SystemSoundID = {
    var result: SystemSoundID = 0
    if let url = Bundle.main.url(forResource: "appreciation", withExtension: "wav") {
      AudioServicesCreateSystemSoundID(url as CFURL, &result)
    }
    return result
  }()
  static func appreciation() {
    guard UserDefaults.standard.bool(forKey: "rintInteractionSounds"), sound != 0 else { return }
    AudioServicesPlaySystemSound(sound)
  }
}
