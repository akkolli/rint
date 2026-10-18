import ImageIO
import PhotosUI
import SwiftUI
import UniformTypeIdentifiers

// Decode at a bounded size and re-encode pixels only. No source EXIF/GPS metadata
// is sent to the server when attaching a photo from the native app.
enum NativePhotoPreparation {
  static func jpeg(_ source: Data) throws -> Data {
    guard source.count <= 50 * 1024 * 1024,
      let imageSource = CGImageSourceCreateWithData(source as CFData, nil),
      let cg = CGImageSourceCreateThumbnailAtIndex(
        imageSource, 0,
        [
          kCGImageSourceCreateThumbnailFromImageAlways: true,
          kCGImageSourceCreateThumbnailWithTransform: true,
          kCGImageSourceThumbnailMaxPixelSize: 2048,
          kCGImageSourceShouldCacheImmediately: true,
        ] as CFDictionary)
    else {
      throw NSError(
        domain: "Rint", code: 1,
        userInfo: [NSLocalizedDescriptionKey: "Choose a readable image up to 50 MB."])
    }
    let output = NSMutableData()
    guard
      let destination = CGImageDestinationCreateWithData(
        output, UTType.jpeg.identifier as CFString, 1, nil)
    else {
      throw CocoaError(.fileWriteUnknown)
    }
    CGImageDestinationAddImage(
      destination, cg, [kCGImageDestinationLossyCompressionQuality: 0.88] as CFDictionary)
    guard CGImageDestinationFinalize(destination) else { throw CocoaError(.fileWriteUnknown) }
    return output as Data
  }
}

struct NativePhotoAttachment: View {
  let workoutID: String?
  @EnvironmentObject var api: APIClient
  @Environment(\.dismiss) var dismiss
  @State private var selection: PhotosPickerItem?
  @State private var photo: Data?
  @State private var uploadedID: String?
  @State private var choosing = false
  @State private var processing = false
  @State private var uploading = false
  @State private var error: String?
  @State private var complete = false
  var body: some View {
    NavigationStack {
      ScrollView {
        VStack(alignment: .leading, spacing: 24) {
          Text(workoutID == nil ? "Put a face to your efforts." : "A little more of the story.")
            .font(.title2.bold())
          Text(
            workoutID == nil
              ? "Your photo appears wherever your profile is shown. Location metadata is removed before upload."
              : "Add a photo to this workout. It follows the workout’s photo audience; location metadata is removed before upload."
          )
          .font(.subheadline).foregroundStyle(RintStyle.muted)
          if let photo, let image = UIImage(data: photo) {
            Image(uiImage: image).resizable().scaledToFit().clipShape(
              RoundedRectangle(cornerRadius: 16)
            )
            .accessibilityLabel("Photo ready to attach")
          }
          if processing { ProgressView("Preparing photo…") }
          if uploading { ProgressView("Uploading and attaching…") }
          if complete {
            RintNotice(
              text: workoutID == nil ? "Profile photo updated." : "Photo added to this workout.",
              icon: "checkmark.circle")
            Button("Done") { dismiss() }.buttonStyle(RintPrimaryButton())
          } else {
            PhotosPicker(
              selection: $selection, matching: .images, preferredItemEncoding: .compatible
            ) {
              Label(
                photo == nil ? "Choose a photo" : "Choose another photo",
                systemImage: "photo.on.rectangle")
            }.buttonStyle(.bordered).disabled(processing || uploading || uploadedID != nil)
            Button("Choose an image file") { choosing = true }.disabled(
              processing || uploading || uploadedID != nil)
            if photo != nil {
              Button(
                uploading
                  ? "Uploading…"
                  : uploadedID == nil
                    ? (workoutID == nil ? "Save profile photo" : "Add photo")
                    : "Retry attaching photo"
              ) {
                Task { await attach() }
              }.buttonStyle(RintPrimaryButton()).disabled(processing || uploading)
            }
          }
          if let error { RintNotice(text: error, icon: "exclamationmark.circle") }
        }.padding(24)
      }.background(RintStyle.paper).navigationTitle(
        workoutID == nil ? "Profile photo" : "Add a photo"
      ).navigationBarTitleDisplayMode(
        .inline
      )
      .toolbar {
        ToolbarItem(placement: .cancellationAction) {
          Button("Close") { dismiss() }.disabled(uploading)
        }
      }
      .interactiveDismissDisabled(uploading)
      .onChange(of: selection) { _, item in
        guard let item else { return }
        Task {
          processing = true
          error = nil
          defer { processing = false }
          do {
            guard let data = try await item.loadTransferable(type: Data.self) else {
              throw CocoaError(.fileReadCorruptFile)
            }
            photo = try await Task.detached { try NativePhotoPreparation.jpeg(data) }.value
            uploadedID = nil
          } catch { self.error = error.localizedDescription }
        }
      }
      .fileImporter(isPresented: $choosing, allowedContentTypes: [.image]) { result in
        Task {
          processing = true
          error = nil
          defer { processing = false }
          do {
            let url = try result.get()
            let scoped = url.startAccessingSecurityScopedResource()
            defer { if scoped { url.stopAccessingSecurityScopedResource() } }
            let data = try await Task.detached {
              let size = try url.resourceValues(forKeys: [.fileSizeKey]).fileSize ?? 0
              guard size > 0, size <= 50 * 1024 * 1024 else { throw CocoaError(.fileReadTooLarge) }
              return try NativePhotoPreparation.jpeg(Data(contentsOf: url))
            }.value
            photo = data
            uploadedID = nil
          } catch { self.error = error.localizedDescription }
        }
      }
    }
  }
  @MainActor func attach() async {
    guard let photo, !uploading else { return }
    uploading = true
    error = nil
    defer { uploading = false }
    do {
      guard let workoutID else {
        _ = try await api.uploadPhoto(photo, profile: true)
        await api.refresh()
        complete = true
        return
      }
      if uploadedID == nil {
        let response = try await api.uploadPhoto(photo)
        uploadedID = try JSONDecoder().decode(FeedPhoto.self, from: response).id
      }
      // Read all existing attachments rather than the feed's truncated preview.
      let response =
        try JSONSerialization.jsonObject(with: await api.request("workouts/\(workoutID)"))
        as? [String: Any]
      guard let data = response?["data"] as? [String: Any],
        let workout = (data["workouts"] as? [[String: Any]])?.first,
        let media = workout["media_attachments"] as? [[String: Any]], let uploadedID
      else { throw CocoaError(.fileReadCorruptFile) }
      var ids = media.compactMap { $0["id"] as? String }
      if !ids.contains(uploadedID) { ids.append(uploadedID) }
      guard ids.count <= 20 else {
        throw NSError(
          domain: "Rint", code: 1,
          userInfo: [
            NSLocalizedDescriptionKey:
              "This workout already has 20 photos. Manage existing photos on the web before adding another."
          ])
      }
      _ = try await api.request(
        "workouts/\(workoutID)", method: "PATCH",
        body: JSONSerialization.data(withJSONObject: ["media_attachment_ids": ids]))
      await api.refresh()
      complete = true
    } catch {
      self.error =
        "\(error.localizedDescription) Your selected photo is kept here so you can retry."
    }
  }
}
