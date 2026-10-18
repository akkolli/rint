import SwiftUI

/// Single taps select immediately; horizontal scrubbing leaves vertical page scrolling available.
struct PlotTouchOverlay: View {
  let select: (CGPoint) -> Void
  var body: some View {
    Rectangle().fill(.clear).contentShape(Rectangle())
      .onTapGesture(coordinateSpace: .local) { select($0) }
      .simultaneousGesture(
        DragGesture(minimumDistance: 8).onChanged { value in
          guard abs(value.translation.width) >= abs(value.translation.height) else { return }
          select(value.location)
        }
      )
      .accessibilityHidden(true)
  }
}
