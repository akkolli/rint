import SwiftUI

struct WorkoutClock: View {
  let started: Date
  var body: some View {
    TimelineView(.periodic(from: .now, by: 1)) { context in
      Text(elapsedLabel(max(0, context.date.timeIntervalSince(started)))).monospacedDigit()
    }.accessibilityLabel("Elapsed time")
  }
}
struct ActiveWorkoutClock: View {
  @ObservedObject var recorder: WorkoutRecorder
  var body: some View {
    TimelineView(.periodic(from: .now, by: 1)) { context in
      Text(compactTimeLabel(recorder.activeDuration(at: context.date))).monospacedDigit()
    }.accessibilityLabel("Active time, excluding pauses")
  }
}
