import SwiftUI

struct NativeActivityPhotos: View {
  let photos: [FeedPhoto]
  let workoutID: String
  let canAttach: Bool
  var compactEmpty = false
  @EnvironmentObject var api: APIClient
  @State private var currentPhotos: [FeedPhoto] = []
  @State private var attaching = false
  @State private var selected: FeedPhoto?
  var body: some View {
    if !photos.isEmpty || !currentPhotos.isEmpty || canAttach {
      VStack(alignment: .leading, spacing: 12) {
        HStack {
          if !compactEmpty || !currentPhotos.isEmpty { Text("Photos").font(.headline) }
          Spacer()
          if canAttach {
            Button("Add photo", systemImage: "plus") { attaching = true }.frame(minHeight: 44)
          }
        }
        if currentPhotos.isEmpty && !compactEmpty {
          Text("Add a moment from your workout.").font(.footnote).foregroundStyle(RintStyle.muted)
        }
        ScrollView(.horizontal, showsIndicators: false) {
          HStack(spacing: 12) {
            ForEach(currentPhotos) { photo in
              Button {
                selected = photo
              } label: {
                AsyncImage(url: URL(string: photo.url)) { phase in
                  if let image = phase.image {
                    image.resizable().scaledToFill()
                  } else if phase.error != nil {
                    Label("Photo unavailable", systemImage: "photo").font(.caption).foregroundStyle(
                      RintStyle.muted)
                  } else {
                    ProgressView().frame(maxWidth: .infinity, maxHeight: .infinity)
                  }
                }.frame(width: 280, height: 200).background(RintStyle.soft).clipped().clipShape(
                  RoundedRectangle(cornerRadius: 16))
              }.buttonStyle(.plain).accessibilityLabel("Open activity photo")
            }
          }
        }
      }.sheet(item: $selected) { photo in
        NativePhotoViewer(photos: currentPhotos, initial: photo.id)
      }
      .sheet(isPresented: $attaching, onDismiss: { Task { await refresh() } }) {
        NativePhotoAttachment(workoutID: workoutID)
      }.task {
        currentPhotos = photos
        await refresh()
      }
    }
  }
  @MainActor func refresh() async {
    if let response = try? JSONDecoder().decode(
      APIResponse<FeedResponse>.self, from: await api.request("workouts/\(workoutID)")),
      let workout = response.data.workouts.first
    {
      currentPhotos = workout.mediaAttachments ?? []
    }
  }
}
struct NativePhotoViewer: View {
  let photos: [FeedPhoto]
  let initial: String
  @Environment(\.dismiss) var dismiss
  @State private var selection = ""
  var body: some View {
    NavigationStack {
      TabView(selection: $selection) {
        ForEach(photos) { photo in
          ZoomablePhoto(url: URL(string: photo.url)).tag(photo.id)
        }
      }.tabViewStyle(.page).background(.black).navigationTitle("Activity photos")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } } }
        .onAppear { selection = initial }
    }
  }
}
private struct ZoomablePhoto: View {
  let url: URL?
  @State private var scale = 1.0
  @GestureState private var zoom = 1.0
  var body: some View {
    ScrollView([.horizontal, .vertical]) {
      AsyncImage(url: url) { phase in
        if let image = phase.image {
          image.resizable().scaledToFit().frame(width: 350 * min(4, max(1, scale * zoom)))
        } else if phase.error != nil {
          Label("Photo unavailable", systemImage: "photo").foregroundStyle(.white)
        } else {
          ProgressView().tint(.white)
        }
      }
    }.defaultScrollAnchor(.center)
      .simultaneousGesture(
        MagnifyGesture().updating($zoom) { value, state, _ in state = value.magnification }.onEnded
        { value in scale = min(4, max(1, scale * value.magnification)) }
      )
      .accessibilityLabel("Activity photo. Pinch to zoom.")
  }
}
