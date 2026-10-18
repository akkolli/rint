import SwiftUI

struct NativeCommentRow: View {
  let comment: NativeComment
  let reload: () async -> Void
  @EnvironmentObject var api: APIClient
  @State private var busy = false
  @State private var editing = false
  @State private var deleting = false
  @State private var reporting = false
  @State private var error: String?
  var body: some View {
    VStack(alignment: .leading, spacing: 8) {
      HStack {
        NavigationLink(comment.user.username) { NativePersonView(username: comment.user.username) }
          .font(.caption.bold()).foregroundStyle(RintStyle.ink)
        Spacer()
        Menu {
          if comment.user.username == api.username {
            Button("Edit comment") { editing = true }
            Button("Delete comment", role: .destructive) { deleting = true }
          } else {
            Button("Report comment") { reporting = true }
          }
        } label: {
          Image(systemName: "ellipsis").frame(width: 44, height: 44)
        }.accessibilityLabel("Comment actions")
      }
      Text(comment.text ?? "Comment unavailable").font(.subheadline).textSelection(.enabled)
      if let mentions = comment.mentions, !mentions.isEmpty {
        ScrollView(.horizontal) {
          HStack {
            ForEach(mentions, id: \.username) { person in
              NavigationLink("@" + person.username) { NativePersonView(username: person.username) }
                .font(.caption).frame(minHeight: 44)
            }
          }
        }
      }
      Button {
        busy = true
        Task {
          do {
            _ = try await api.request(
              "comments/\(comment.id)/like" + (comment.liked == true ? "/undo" : ""), method: "POST"
            )
            await reload()
          } catch { self.error = error.localizedDescription }
          busy = false
        }
      } label: {
        Label(
          "\(comment.likesCount ?? 0)", systemImage: comment.liked == true ? "heart.fill" : "heart"
        ).frame(minHeight: 44)
      }.font(.caption).foregroundStyle(comment.liked == true ? RintStyle.heart : RintStyle.muted)
        .disabled(busy).accessibilityLabel(
          comment.liked == true ? "Unlike comment" : "Like comment")
      if let error { RintNotice(text: error, icon: "exclamationmark.circle") }
    }.padding(.vertical, 4)
      .sheet(isPresented: $reporting) {
        NativeReportView(objectID: comment.id, objectType: "comment")
      }
      .sheet(isPresented: $editing) { NativeCommentEditor(comment: comment, reload: reload) }
      .confirmationDialog("Delete this comment?", isPresented: $deleting, titleVisibility: .visible)
    {
      Button("Delete comment", role: .destructive) {
        busy = true
        Task {
          do {
            _ = try await api.request("comments/\(comment.id)", method: "DELETE")
            await reload()
          } catch { self.error = error.localizedDescription }
          busy = false
        }
      }
    } message: {
      Text("This cannot be undone.")
    }
  }
}
struct NativeCommentEditor: View {
  let comment: NativeComment
  let reload: () async -> Void
  @EnvironmentObject var api: APIClient
  @Environment(\.dismiss) var dismiss
  @State private var text = ""
  @State private var busy = false
  @State private var error: String?
  var body: some View {
    NavigationStack {
      Form {
        Section("Your comment") {
          TextField("Comment", text: $text, axis: .vertical).lineLimit(3...10)
        }
        if let error { RintNotice(text: error, icon: "exclamationmark.circle") }
      }.scrollContentBackground(.hidden).background(RintStyle.paper).navigationTitle("Edit comment")
        .toolbar {
          ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } }
          ToolbarItem(placement: .confirmationAction) {
            Button(busy ? "Saving…" : "Save") {
              busy = true
              Task {
                do {
                  _ = try await api.request(
                    "comments/\(comment.id)", method: "PATCH",
                    body: JSONSerialization.data(withJSONObject: [
                      "text": text, "text_visibility": comment.textVisibility ?? "private",
                    ]))
                  await reload()
                  dismiss()
                } catch { self.error = error.localizedDescription }
                busy = false
              }
            }.disabled(busy || text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
          }
        }.onAppear { text = comment.text ?? "" }
    }
  }
}
