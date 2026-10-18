import Charts
import SwiftUI

struct NativeWeeklySummary: View {
  @Environment(\.dynamicTypeSize) private var typeSize
  let weeks: [NativeWeek]
  var sport = 0
  @State private var selectedWeek: String?
  private var index: Int {
    weeks.firstIndex(where: { $0.week == selectedWeek }) ?? max(0, weeks.count - 1)
  }
  var body: some View {
    if !weeks.isEmpty {
      let selected = weeks[index]
      VStack(alignment: .leading, spacing: 8) {
        HStack(alignment: .top) {
          VStack(alignment: .leading, spacing: 5) {
            Text(
              index == weeks.count - 1
                ? "This week · in progress" : "Week of " + label(selected.week)
            )
            .font(.caption.weight(.semibold)).foregroundStyle(RintStyle.muted)
            HStack(alignment: .firstTextBaseline, spacing: 5) {
              Text(DisplayUnits.distance(selected.distanceM, decimals: 1))
                .font(.system(.largeTitle, design: .rounded).bold()).monospacedDigit()
                .tracking(-1)
              Text(DisplayUnits.distanceUnit).font(.subheadline).foregroundStyle(RintStyle.muted)
            }
          }
          Spacer()
          VStack(alignment: .trailing, spacing: 6) {
            Text("\(selected.activities) " + (selected.activities == 1 ? "workout" : "workouts"))
              .font(.subheadline.weight(.semibold))
            Text(compactTimeLabel(selected.elapsedS)).font(.subheadline).monospacedDigit()
            Text("elapsed · Mon–Sun").font(.caption2).foregroundStyle(RintStyle.muted)
          }.padding(.top, 6)
        }
        weeklyChart
        HStack {
          Text(
            "8 weeks"
              + (index > 0
                ? " · Previous week "
                  + DisplayUnits.distance(weeks[index - 1].distanceM, decimals: 1) + " "
                  + DisplayUnits.distanceUnit : "")
          )
          .font(.caption2).foregroundStyle(RintStyle.muted)
          Spacer()
          if index != weeks.count - 1 {
            Button("This week") { selectedWeek = weeks.last?.week }.font(.caption.weight(.semibold))
          }
        }
      }.rintPanel(padding: 14)
    }
  }
  @ViewBuilder private var weeklyChart: some View {
    let selected = weeks[index]
    Chart {
      ForEach(weeks.indices, id: \.self) { i in
        let week = weeks[i]
        BarMark(
          x: .value("Week", Double(i)),
          y: .value("Distance", week.distanceM / DisplayUnits.distanceSize),
          width: .fixed(22)
        )
        .foregroundStyle(i == index ? RintStyle.violet.opacity(0.3) : RintStyle.soft)
        .cornerRadius(4)
        .accessibilityLabel("Week of " + label(week.week))
        .accessibilityValue(
          DisplayUnits.distance(week.distanceM, decimals: 1) + " " + DisplayUnits.distanceUnit
        )
      }
      ForEach(weeks.indices, id: \.self) { i in
        let week = weeks[i]
        LineMark(
          x: .value("Week", Double(i)),
          y: .value("Distance", week.distanceM / DisplayUnits.distanceSize)
        )
        .foregroundStyle(RintStyle.violet).lineStyle(StrokeStyle(lineWidth: 2.5))
        .accessibilityHidden(true)
        PointMark(
          x: .value("Week", Double(i)),
          y: .value("Distance", week.distanceM / DisplayUnits.distanceSize)
        )
        .foregroundStyle(i == index ? RintStyle.violet : RintStyle.muted).symbolSize(
          i == index ? 65 : 18
        )
        .accessibilityHidden(true)
      }
      RuleMark(x: .value("Selected week", Double(index))).foregroundStyle(
        RintStyle.violet.opacity(0.35)
      )
      .lineStyle(StrokeStyle(lineWidth: 1, dash: [3, 3])).accessibilityHidden(true)
    }.frame(height: typeSize.isAccessibilitySize ? 180 : 130)
      .chartXScale(domain: -0.5...Double(weeks.count) - 0.5)
      .chartXAxis {
        AxisMarks(values: Array(weeks.indices).map(Double.init)) { value in
          AxisValueLabel {
            if let i = value.as(Double.self), weeks.indices.contains(Int(i)) {
              Text(label(weeks[Int(i)].week)).font(.system(size: 9))
            }
          }
        }
      }
      .chartYAxis {
        AxisMarks(
          position: .trailing,
          values: .automatic(desiredCount: typeSize.isAccessibilitySize ? 3 : 5)
        ) {
          AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5))
          AxisValueLabel()
        }
      }
      .chartOverlay { proxy in
        GeometryReader { geometry in
          PlotTouchOverlay { point in
            guard let anchor = proxy.plotFrame else { return }
            let frame = geometry[anchor]
            if let i = PlotSelection.index(
              x: point.x - frame.minX, width: frame.width, count: weeks.count)
            {
              selectedWeek = weeks[i].week
            }
          }
        }
      }
      .accessibilityElement(children: .ignore)
      .accessibilityLabel("Weekly distance chart")
      .accessibilityValue(
        label(selected.week) + ", " + DisplayUnits.distance(selected.distanceM) + " "
          + DisplayUnits.distanceUnit
      )
      .accessibilityAdjustableAction { direction in
        let next = min(weeks.count - 1, max(0, index + (direction == .increment ? 1 : -1)))
        selectedWeek = weeks[next].week
      }
  }
  private func label(_ key: String) -> String {
    TrainingDates.date(key)?.formatted(.dateTime.month(.abbreviated).day()) ?? key
  }
}

struct NativeRecordsSection: View {
  @Environment(\.dynamicTypeSize) private var typeSize
  let records: [NativeBest]
  let sport: String
  var showSport = false
  @State private var selectedDistance: Double?
  private var selected: NativeBest? {
    records.first(where: { $0.distanceM == selectedDistance }) ?? records.first(where: {
      $0.distanceM == 5000
    }) ?? records.last
  }
  private func pace(_ best: NativeBest) -> Double {
    best.elapsedS / best.distanceM * DisplayUnits.distanceSize / 60
  }
  var body: some View {
    if let selected {
      VStack(alignment: .leading, spacing: 10) {
        if showSport { Text(sport).font(.headline) }
        hero(selected)
        curve
        recordRows
        Text("Elapsed time includes pauses.").font(.caption2)
          .foregroundStyle(RintStyle.muted)
      }.rintPanel(padding: 14)
    }
  }
  @ViewBuilder private func hero(_ selected: NativeBest) -> some View {
    HStack(alignment: .firstTextBaseline) {
      VStack(alignment: .leading, spacing: 5) {
        Label(
          EffortPresentation.distance(selected.distanceM) + " best", systemImage: "trophy.fill"
        )
        .font(.caption.weight(.semibold)).foregroundStyle(RintStyle.power)
        Text(compactTimeLabel(selected.elapsedS)).font(
          .system(.largeTitle, design: .rounded).bold()
        )
        .monospacedDigit().tracking(-1)
      }
      Spacer()
      VStack(alignment: .trailing, spacing: 5) {
        Text(DisplayUnits.pace(selected.elapsedS * 1000 / selected.distanceM))
          .font(.title3.weight(.semibold)).monospacedDigit().foregroundStyle(RintStyle.violet)
        Text("/" + DisplayUnits.distanceUnit + " · elapsed pace").font(.caption2)
          .foregroundStyle(RintStyle.muted)
      }
    }
    if let id = selected.workoutID {
      NavigationLink {
        NativeActivityDestination(workoutID: id, effortDistance: selected.distanceM)
      } label: {
        HStack {
          VStack(alignment: .leading, spacing: 3) {
            Text(selected.title).font(.subheadline.weight(.medium)).lineLimit(1)
            Text(date(selected)).font(.caption).foregroundStyle(RintStyle.muted)
          }
          Spacer()
          Image(systemName: "arrow.up.right").font(.subheadline)
        }.foregroundStyle(RintStyle.ink).frame(minHeight: 44).contentShape(Rectangle())
      }.buttonStyle(.plain).accessibilityLabel(
        "Open " + selected.title + " and its " + EffortPresentation.distance(selected.distanceM)
          + " effort")
    }
  }
  @ViewBuilder private var curve: some View {
    if let selected {
      if records.count > 1 {
        VStack(alignment: .leading, spacing: 8) {
          Text("Best pace across distances").font(.caption.weight(.semibold)).foregroundStyle(
            RintStyle.muted)
          Chart {
            ForEach(records.indices, id: \.self) { i in
              let best = records[i]
              LineMark(x: .value("Distance", Double(i)), y: .value("Pace", pace(best)))
                .foregroundStyle(RintStyle.violet).lineStyle(StrokeStyle(lineWidth: 2))
                .accessibilityHidden(true)
              PointMark(x: .value("Distance", Double(i)), y: .value("Pace", pace(best)))
                .symbolSize(best.id == selected.id ? 70 : 24).foregroundStyle(
                  best.id == selected.id ? RintStyle.violet : RintStyle.muted
                )
                .accessibilityLabel(EffortPresentation.distance(best.distanceM))
                .accessibilityValue(DisplayUnits.pace(best.elapsedS * 1000 / best.distanceM))

            }
          }.frame(height: typeSize.isAccessibilitySize ? 140 : 80)
            .chartXScale(domain: -0.5...Double(records.count) - 0.5)
            .chartYScale(domain: .automatic(includesZero: false))
            .chartXAxis {
              AxisMarks(values: Array(records.indices).map(Double.init)) { value in
                AxisValueLabel {
                  if let i = value.as(Double.self), records.indices.contains(Int(i)) {
                    Text(EffortPresentation.distance(records[Int(i)].distanceM)).font(
                      .system(size: 9))
                  }
                }
              }
            }
            .chartYAxis {
              AxisMarks(
                position: .trailing,
                values: .automatic(desiredCount: typeSize.isAccessibilitySize ? 3 : 5)
              ) { value in
                AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5))
                AxisValueLabel {
                  if let v = value.as(Double.self) {
                    Text(compactTimeLabel(v * 60)).font(.caption2)
                  }
                }
              }
            }
            .chartOverlay { proxy in
              GeometryReader { geometry in
                PlotTouchOverlay { point in
                  guard let anchor = proxy.plotFrame else { return }
                  let frame = geometry[anchor]
                  if let i = PlotSelection.index(
                    x: point.x - frame.minX, width: frame.width, count: records.count)
                  {
                    selectedDistance = records[i].distanceM
                  }
                }
              }
            }
        }
      }
    }
  }
  private var recordRows: some View {
    VStack(spacing: 0) {
      HStack {
        Text("Distance")
        Spacer()
        Text("Time · pace")
      }.font(.caption2).foregroundStyle(RintStyle.muted).padding(.bottom, 6)
      ForEach(records) { best in
        if let id = best.workoutID {
          NavigationLink {
            NativeActivityDestination(workoutID: id, effortDistance: best.distanceM)
          } label: {
            HStack(spacing: 12) {
              VStack(alignment: .leading, spacing: 4) {
                Text(EffortPresentation.distance(best.distanceM)).font(
                  .subheadline.weight(.semibold))
                Text(best.title).font(.caption2).foregroundStyle(RintStyle.muted).lineLimit(1)
                Text(date(best)).font(.caption2).foregroundStyle(RintStyle.muted)
              }
              Spacer()
              VStack(alignment: .trailing, spacing: 4) {
                Text(compactTimeLabel(best.elapsedS)).font(.title3.weight(.semibold))
                  .monospacedDigit()
                Text(
                  DisplayUnits.pace(best.elapsedS * 1000 / best.distanceM) + " /"
                    + DisplayUnits.distanceUnit
                )
                .font(.caption2).foregroundStyle(RintStyle.muted)
              }
              Image(systemName: "chevron.right").font(.caption2).foregroundStyle(
                RintStyle.muted)
            }.foregroundStyle(RintStyle.ink).padding(.vertical, 6).contentShape(Rectangle())
          }.buttonStyle(.plain)
          if best.id != records.last?.id { Divider() }
        }
      }
    }
  }
  private func date(_ best: NativeBest) -> String {
    best.date.flatMap(DisplayUnits.date)?.formatted(date: .abbreviated, time: .omitted)
      ?? "Recorded workout"
  }
}
