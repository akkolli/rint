import SwiftUI

struct NativeWorkoutSummary: View {
  let workout: WorkoutCompletion
  let recordAgain: () -> Void
  @EnvironmentObject var queue: SyncQueue
  var body: some View {
    VStack(alignment: .leading, spacing: 24) {
      Image(systemName: "checkmark.circle.fill").font(.system(size: 40)).foregroundStyle(
        RintStyle.violet)
      VStack(alignment: .leading, spacing: 8) {
        Text("Workout complete.").font(.system(.largeTitle, design: .rounded).bold()).tracking(-1)
        Text(workout.finished.formatted(date: .abbreviated, time: .shortened)).font(.subheadline)
          .foregroundStyle(RintStyle.muted)
      }
      LazyVGrid(
        columns: [GridItem(.flexible()), GridItem(.flexible())], alignment: .leading, spacing: 24
      ) {
        RintMetric(
          title: "Distance", value: DisplayUnits.distance(workout.distance),
          unit: DisplayUnits.distanceUnit)
        RintMetric(title: "Active time", value: compactTimeLabel(workout.active))
        RintMetric(
          title: workout.usesSpeed ? "Active speed" : "Active pace",
          value: workout.usesSpeed
            ? DisplayUnits.speed(workout.active > 0 ? workout.distance / workout.active : nil)
            : DisplayUnits.pace(workout.pace),
          unit: workout.usesSpeed ? DisplayUnits.speedUnit : "/" + DisplayUnits.distanceUnit)
        RintMetric(
          title: "Average heart rate",
          value: workout.heartRate.map { String(format: "%.0f", $0) } ?? "—", unit: "bpm")
      }
      Text(
        compactTimeLabel(workout.elapsed) + " elapsed · "
          + compactTimeLabel(max(0, workout.elapsed - workout.active)) + " paused"
      )
      .font(.caption).foregroundStyle(RintStyle.muted)
      VStack(alignment: .leading, spacing: 14) {
        Label("Saved on this iPhone", systemImage: "checkmark.circle.fill")
        Label(
          workout.stage == .server ? "Synced to Rint" : "Waiting to upload to Rint",
          systemImage: workout.stage == .server
            ? "checkmark.circle.fill" : "arrow.triangle.2.circlepath")
        if workout.stage != .server {
          Text("Your workout is safely retained. Upload resumes when your server is reachable.")
            .font(.caption).foregroundStyle(RintStyle.muted)
          Button("Try upload now") { queue.sync(force: true) }.font(.subheadline).frame(
            minHeight: 44)
        }
      }.font(.subheadline.weight(.semibold)).rintPanel()
      if let id = workout.workoutID {
        NavigationLink {
          NativeActivityDestination(workoutID: id)
        } label: {
          Text("View workout & share").frame(maxWidth: .infinity)
        }.buttonStyle(RintPrimaryButton())
      }
      Button("Record another workout", action: recordAgain).buttonStyle(RintSecondaryButton())
    }
  }
}
