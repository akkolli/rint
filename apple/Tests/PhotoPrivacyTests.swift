import ImageIO
import UIKit
import UniformTypeIdentifiers
import XCTest

@testable import Rint

final class PhotoPrivacyTests: XCTestCase {
  func testAttachmentRemovesLocationMetadataAndBoundsImageSize() throws {
    let image = UIGraphicsImageRenderer(size: CGSize(width: 2400, height: 1200)).image { context in
      UIColor.green.setFill()
      context.fill(CGRect(x: 0, y: 0, width: 2400, height: 1200))
    }
    let source = NSMutableData()
    let destination = try XCTUnwrap(
      CGImageDestinationCreateWithData(source, UTType.jpeg.identifier as CFString, 1, nil))
    CGImageDestinationAddImage(
      destination, try XCTUnwrap(image.cgImage),
      [
        kCGImagePropertyGPSDictionary: [
          kCGImagePropertyGPSLatitude: 40.0, kCGImagePropertyGPSLongitude: 73.0,
        ],
        kCGImagePropertyExifDictionary: [
          kCGImagePropertyExifUserComment: "private source metadata"
        ],
      ] as CFDictionary)
    XCTAssertTrue(CGImageDestinationFinalize(destination))
    let jpeg = try NativePhotoPreparation.jpeg(source as Data)
    let decoded = try XCTUnwrap(CGImageSourceCreateWithData(jpeg as CFData, nil))
    let properties = try XCTUnwrap(
      CGImageSourceCopyPropertiesAtIndex(decoded, 0, nil) as? [CFString: Any])
    XCTAssertNil(properties[kCGImagePropertyGPSDictionary])
    let exif = properties[kCGImagePropertyExifDictionary] as? [CFString: Any]
    XCTAssertNil(exif?[kCGImagePropertyExifUserComment])
    XCTAssertLessThanOrEqual(try XCTUnwrap(properties[kCGImagePropertyPixelWidth] as? Int), 2048)
    XCTAssertThrowsError(try NativePhotoPreparation.jpeg(Data("not an image".utf8)))
  }
}
