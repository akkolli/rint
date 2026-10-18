import AppKit

// The same r. mark used by the web UI. Generate from the repository root.
let size = 1024
let context = CGContext(
  data: nil, width: size, height: size, bitsPerComponent: 8, bytesPerRow: size * 4,
  space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
context.setFillColor(CGColor(red: 0.83, green: 0.95, blue: 0.42, alpha: 1))
context.fill(CGRect(x: 0, y: 0, width: size, height: size))
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(cgContext: context, flipped: false)
let mark = NSAttributedString(
  string: "r.",
  attributes: [
    .font: NSFont.systemFont(ofSize: 660, weight: .black),
    .foregroundColor: NSColor(srgbRed: 0.12, green: 0.15, blue: 0.09, alpha: 1), .kern: -25,
  ])
let bounds = mark.size()
mark.draw(at: NSPoint(x: (1024 - bounds.width) / 2 - 12, y: (1024 - bounds.height) / 2 + 20))
NSGraphicsContext.restoreGraphicsState()
let rep = NSBitmapImageRep(cgImage: context.makeImage()!)
let png = rep.representation(using: .png, properties: [:])!
for platform in ["iOS", "Watch"] {
  try png.write(
    to: URL(fileURLWithPath: "apple/\(platform)/Assets.xcassets/AppIcon.appiconset/AppIcon.png"))
}
