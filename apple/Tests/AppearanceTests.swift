import UIKit
import XCTest
@testable import Rint

final class AppearanceTests: XCTestCase {
  func testSystemPalettesKeepTextAndMetricsReadable() {
    for style in [UIUserInterfaceStyle.light, .dark] {
      let traits = UITraitCollection(userInterfaceStyle: style)
      for surface in [RintStyle.paper, RintStyle.surface, RintStyle.soft] {
        let background = UIColor(surface).resolvedColor(with: traits)
        for foreground in [RintStyle.ink, RintStyle.muted, RintStyle.distance, RintStyle.violet, RintStyle.heart, RintStyle.power] {
          let text = UIColor(foreground).resolvedColor(with: traits)
          XCTAssertGreaterThanOrEqual(contrast(text, background), 4.5)
        }
      }
      XCTAssertGreaterThanOrEqual(contrast(UIColor(RintStyle.accentInk), UIColor(RintStyle.accent)), 4.5)
    }
    let light = UIColor(RintStyle.paper).resolvedColor(with: UITraitCollection(userInterfaceStyle: .light))
    let dark = UIColor(RintStyle.paper).resolvedColor(with: UITraitCollection(userInterfaceStyle: .dark))
    XCTAssertGreaterThan(luminance(light), luminance(dark))
  }
  private func contrast(_ a: UIColor, _ b: UIColor) -> Double {
    let first = luminance(a), second = luminance(b)
    return (max(first, second) + 0.05) / (min(first, second) + 0.05)
  }
  private func luminance(_ colour: UIColor) -> Double {
    var r: CGFloat = 0, g: CGFloat = 0, b: CGFloat = 0, alpha: CGFloat = 0
    colour.getRed(&r, green: &g, blue: &b, alpha: &alpha)
    let channels = [r, g, b].map { Double($0) <= 0.04045 ? Double($0) / 12.92 : pow((Double($0) + 0.055) / 1.055, 2.4) }
    return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722
  }
}
