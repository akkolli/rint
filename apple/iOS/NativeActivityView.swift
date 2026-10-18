import Charts
import SwiftUI

struct NativeActivityView: View {
  let workout: FeedActivity
  var openConversation = false
  var initialEffortDistance: Double? = nil
  @StateObject private var training = TrainingStore.shared
  @State private var detailSection = "Charts"
  @State private var selectedRange = false
  @State private var fullPaceRange = false
  @State private var focusedBounds: ClosedRange<Double> = 0...1
  @State private var completeBounds: ClosedRange<Double> = 0...1
  @State private var clippedPaceCount = 0
  @AppStorage("imperial_units") private var imperial = false
  @State private var presentedWorkout: FeedActivity?
  @State private var openedConversation = false
  @State private var focusedInitialEffort = false
  @EnvironmentObject var api: APIClient
  @Environment(\.dynamicTypeSize) private var typeSize
  @State private var analysis: NativeAnalysis?
  @State private var analysisLoading = true
  @State private var analysisError: String?
  @State private var error: String?
  @State private var metric = "pace"
  @State private var selectedTime: Double?
  @State private var readings: [ChartReading] = []
  @State private var displayedReadings: [ChartReading] = []
  @State private var metricStreams: [String: [ChartReading]] = [:]
  @State private var cachedImperial: Bool?
  @State private var showingNotes = false
  @State private var availableMetrics: Set<String> = []
  @State private var table = "Splits"
  @State private var comments: [NativeComment] = []
  @State private var draftComment = ""
  @State private var composingComment = false
  @State private var commentVisibility = "public"
  @State private var liked = false
  @State private var likeBusy = false
  @State private var posting = false
  @State private var showingSharing = false
  @State private var comparing = false
  @State private var comparisonActivity: FeedActivity?
  @State private var comparisonReadings: [ChartReading] = []
  @State private var comparisonAnalysis: NativeAnalysis?
  @State private var comparisonLoading = false
  @State private var comparisonError: String?
  @State private var intervalStart = 0.0
  @State private var intervalEnd = 1.0
  @State private var interval: NativeSummary?
  @State private var intervalBusy = false
  @State private var intervalError: String?
  @State private var reporting = false
  private let metrics = [
    ("pace", "Pace"), ("heart_rate", "Heart rate"), ("elevation", "Elevation"),
    ("cadence", "Cadence"), ("power", "Power"),
  ]
  var body: some View {
    ScrollViewReader { proxy in
      ScrollView {
        VStack(alignment: .leading, spacing: 10) {
          VStack(alignment: .leading, spacing: 4) {
            RintEyebrow(
              text: api.sports.first(where: { $0.id == workout.sportID })?.label ?? "Workout")
            Text(
              EffortPresentation.title(
                presentedWorkout ?? workout,
                sport: api.sports.first(where: { $0.id == workout.sportID })?.label ?? "Workout")
            ).font(
              .system(.title2, design: .rounded).bold()
            )
            .tracking(-1)
            HStack {
              NavigationLink {
                NativePersonView(username: workout.user.username)
              } label: {
                Label(workout.user.username, systemImage: "person.crop.circle")
              }
              if let date = workout.date {
                Text("· " + date.formatted(date: .abbreviated, time: .omitted))
              }
            }.font(.caption).foregroundStyle(RintStyle.muted)
          }
          if let analysis {
            workoutOverview(analysis)
            Picker("Activity section", selection: $detailSection) {
              Text("Charts").tag("Charts")
              Text("Best efforts").tag("Best efforts")
              Text("Splits & laps").tag("Splits & laps")
            }.pickerStyle(.segmented)
            if detailSection == "Charts" {
              chartPanel(analysis).id("chart")
              intervalPanel(analysis)
            } else if detailSection == "Best efforts" {
              effortPanel(analysis)
            } else {
              splitPanel(analysis)
            }
          } else if analysisLoading {
            ProgressView("Loading your metrics").frame(maxWidth: .infinity).padding(28)
          } else {
            HStack(alignment: .top, spacing: 16) {
              RintMetric(
                title: "Distance",
                value: workout.distance.map { DisplayUnits.distance($0 * 1000) } ?? "—",
                unit: DisplayUnits.distanceUnit)
              RintMetric(
                title: "Moving time",
                value: DisplayUnits.duration(workout.moving ?? workout.duration)
              )
            }
            if workout.withStream == false {
              RintNotice(
                text:
                  "This workout has summary data only. Sample charts, splits and sustained efforts need an original recording.",
                icon: "info.circle")
            } else {
              if let analysisError {
                RintNotice(text: analysisError, icon: "exclamationmark.circle")
              }
              Button("Retry loading metrics") { Task { await loadAnalysis() } }.buttonStyle(
                RintSecondaryButton())
            }
          }
          HStack(spacing: 20) {
            Button {
              toggleLike()
            } label: {
              Label(liked ? "Liked" : "Like", systemImage: liked ? "heart.fill" : "heart").frame(
                minHeight: 44)
            }
            .disabled(likeBusy).foregroundStyle(liked ? RintStyle.heart : RintStyle.ink)
            Spacer()
            Button {
              composingComment = true
              proxy.scrollTo("conversation", anchor: .top)
            } label: {
              Label(
                "\(comments.count) " + (comments.count == 1 ? "comment" : "comments"),
                systemImage: "bubble"
              )
              .frame(minHeight: 44)
            }
            if workout.user.username != api.username,
              let url = URL(string: api.server)?.appendingPathComponent(
                "workouts/\(workout.id)")
            {
              ShareLink(item: url)
            }
          }.font(.subheadline.weight(.semibold)).frame(minHeight: 48)
          if workout.user.username != api.username {
            Button("Report activity") { reporting = true }.font(.caption).frame(minHeight: 44)
          }
          if let caption = (presentedWorkout ?? workout).description, !caption.isEmpty {
            Text(caption).font(.subheadline).fixedSize(horizontal: false, vertical: true)
          }
          NativeActivityPhotos(
            photos: workout.mediaAttachments ?? [], workoutID: workout.id,
            canAttach: workout.user.username == api.username, compactEmpty: true)
          conversation.id("conversation")
          if let error { RintNotice(text: error, icon: "exclamationmark.circle") }
        }.padding(.horizontal, 16).padding(.vertical, 8)
      }.background(RintStyle.paper).navigationTitle("Activity").navigationBarTitleDisplayMode(
        .inline
      )
      .toolbar {
        ToolbarItem(placement: .topBarTrailing) {
          if workout.user.username == api.username {
            Button {
              showingSharing = true
            } label: {
              Image(systemName: "square.and.arrow.up")
            }.accessibilityLabel("Sharing & exports")
          }
        }
      }
      .toolbar {
        ToolbarItem(placement: .topBarTrailing) {
          Menu {
            Button("Calculation notes", systemImage: "info.circle") { showingNotes = true }
            if workout.user.username == api.username {
              Button("Edit & export", systemImage: "square.and.arrow.up") { showingSharing = true }
            }
          } label: {
            Image(systemName: "ellipsis")
          }.accessibilityLabel("Activity options")
        }
      }
      .sheet(isPresented: $showingNotes) {
        NavigationStack {
          ScrollView {
            if let analysis {
              VStack(alignment: .leading, spacing: 10) {
                Text(
                  "Active pace excludes recorded pauses. Moving time excludes low-speed periods too. Splits and best efforts use elapsed time, including pauses. Distance crossings use the original stream; gaps aren’t filled with invented data."
                ).font(.footnote)
                if let energy = analysis.summary.activeEnergyKcal {
                  Text("Active energy: \(Int(energy)) kcal · reported by Health").font(.caption)
                }
                if let active = analysis.summary.healthReportedActiveS {
                  Text("Health active time: \(compactTimeLabel(active))").font(.caption)
                }
                Text(
                  "Elapsed pace: " + DisplayUnits.pace(analysis.summary.paceSKM) + " /"
                    + DisplayUnits.distanceUnit
                ).font(.caption)
                ForEach(analysis.warnings ?? [], id: \.self) { Text($0).font(.caption) }
              }.foregroundStyle(RintStyle.muted).padding(.top, 12)

            }
          }.padding(20).navigationTitle("Calculation notes").navigationBarTitleDisplayMode(.inline)
            .toolbar {
              ToolbarItem(placement: .confirmationAction) {
                Button("Done") { showingNotes = false }
              }
            }
        }.presentationDetents([.medium, .large])
      }
      .toolbar(.hidden, for: .tabBar)
      .onChange(of: analysisLoading) { _, loading in
        if !loading && openConversation && !openedConversation {
          openedConversation = true
          Task { @MainActor in
            await Task.yield()
            proxy.scrollTo("conversation", anchor: .top)
          }
        }
        if !loading && selectedRange && initialEffortDistance != nil && !focusedInitialEffort {
          focusedInitialEffort = true
          Task { @MainActor in
            await Task.yield()
            proxy.scrollTo("chart", anchor: .center)
          }
        }
      }
      .onChange(of: metric) { _, _ in updateReadings() }
      .onChange(of: imperial) { _, _ in updateReadings() }
      .sheet(isPresented: $comparing) {
        NativeComparisonPicker(current: workout, selection: $comparisonActivity)
      }
      .sheet(isPresented: $reporting) {
        NativeReportView(objectID: workout.id, objectType: "workout")
      }
      .onChange(of: comparisonActivity?.id) { _, _ in Task { await loadComparison() } }
      .onChange(of: intervalStart) { _, _ in
        interval = nil
        intervalError = nil
      }
      .onChange(of: intervalEnd) { _, _ in
        interval = nil
        intervalError = nil
      }
      .sheet(
        isPresented: $showingSharing,
        onDismiss: {
          Task {
            if let response = try? JSONDecoder().decode(
              APIResponse<FeedResponse>.self,
              from: await api.request("workouts/\(workout.id)"))
            {
              presentedWorkout = response.data.workouts.first
            }
          }
        }
      ) {
        NativeSharingView(workout: workout).environmentObject(api)
      }
      .task {
        liked = workout.liked ?? false
        composingComment = openConversation
        commentVisibility = workout.workoutVisibility ?? "private"
        await loadComments()
        await loadAnalysis()
      }
    }
  }
  @MainActor func loadAnalysis() async {
    analysisLoading = true
    analysisError = nil
    defer { analysisLoading = false }
    do {
      analysis = try JSONDecoder().decode(
        APIResponse<NativeAnalysis>.self,
        from: await api.request("rint/activities/\(workout.id)/analysis")
      ).data
      availableMetrics = Set(
        metrics.compactMap { key, _ in
          if key == "pace" && analysis?.recording.summaryOnly == true { return nil }
          return ChartStream.values(analysis?.recording.points ?? [], metric: key).isEmpty
            ? nil : key
        })
      if !available(metric) { metric = metrics.first(where: { available($0.0) })?.0 ?? "pace" }
      intervalEnd = max(1, analysis?.summary.elapsedS ?? 1)
      metricStreams = [:]
      updateReadings()
      if let initialEffortDistance,
        let effort = analysis?.bestEfforts.first(where: { $0.distanceM == initialEffortDistance })
      {
        selectEffort(effort)
      }
      if workout.user.username == api.username { await training.load(api: api) }
    } catch { self.analysisError = error.localizedDescription }
  }
  func available(_ key: String) -> Bool { availableMetrics.contains(key) }
  @ViewBuilder private func workoutOverview(_ analysis: NativeAnalysis) -> some View {
    LazyVGrid(
      columns: Array(
        repeating: GridItem(.flexible(), alignment: .leading),
        count: typeSize.isAccessibilitySize ? 2 : 3), alignment: .leading, spacing: 10
    ) {
      if analysis.summary.distanceM > 0 {
        RintMetric(
          title: "Distance", value: DisplayUnits.distance(analysis.summary.distanceM),
          unit: DisplayUnits.distanceUnit)
      }
      RintMetric(
        title: "Active time",
        value: compactTimeLabel(
          analysis.summary.activeS ?? analysis.summary.elapsedS - analysis.summary.pausedS))
      if analysis.summary.distanceM > 0 {
        let cycling =
          api.sports.first(where: { $0.id == workout.sportID })?.label.lowercased().contains("cycl")
          == true
        RintMetric(
          title: cycling ? "Active speed" : "Active pace",
          value: cycling
            ? DisplayUnits.speed(analysis.summary.activePace.map { 1000 / $0 })
            : DisplayUnits.pace(analysis.summary.activePace),
          unit: cycling ? DisplayUnits.speedUnit : "/" + DisplayUnits.distanceUnit)
      } else {
        if let energy = analysis.summary.activeEnergyKcal {
          RintMetric(title: "Active energy", value: String(Int(energy.rounded())), unit: "kcal")
        }
        if let power = analysis.summary.averages["power"] {
          RintMetric(title: "Average power", value: String(Int(power.rounded())), unit: "W")
        }
      }
    }
    HStack(alignment: .top, spacing: 12) {
      Label(
        (analysis.summary.averages["heart_rate"].map { String(format: "%.0f", $0) } ?? "—")
          + " bpm avg.", systemImage: "heart.fill"
      )
      .foregroundStyle(RintStyle.heart).monospacedDigit()
      .accessibilityLabel(
        "Average heart rate, "
          + (analysis.summary.averages["heart_rate"].map { String(format: "%.0f", $0) }
            ?? "unavailable") + " beats per minute")
      Spacer(minLength: 0)
      Text(
        "\(compactTimeLabel(analysis.summary.elapsedS)) elapsed · \(compactTimeLabel(analysis.summary.pausedS)) paused · \(compactTimeLabel(analysis.summary.movingS)) moving"
      )
      .foregroundStyle(RintStyle.muted).multilineTextAlignment(.trailing)
    }.font(.caption2)
    NativeRouteMap(
      points: analysis.recording.points, height: typeSize.isAccessibilitySize ? 185 : 140,
      selectedTime: selectedTime, onSelectTime: { selectTime($0) },
      onMetricChange: { if available($0) { metric = $0 } })
  }
  @ViewBuilder func effortPanel(_ analysis: NativeAnalysis) -> some View {
    VStack(alignment: .leading, spacing: 8) {
      Text(
        "Elapsed time includes pauses."
      )
      .font(.caption).foregroundStyle(RintStyle.muted)
      if analysis.bestEfforts.isEmpty {
        RintNotice(
          text:
            "This recording doesn’t have a continuous distance stream long enough to verify a standard effort.",
          icon: "info.circle")
      }
      ForEach(analysis.bestEfforts) { effort in
        Button {
          selectEffort(effort)
        } label: {
          VStack(alignment: .leading, spacing: 5) {
            HStack(alignment: .firstTextBaseline) {
              Text(EffortPresentation.distance(effort.distanceM)).font(.headline)
              Spacer()
              Text(compactTimeLabel(effort.elapsedS)).font(
                .system(.title3, design: .rounded).bold()
              ).monospacedDigit()
              Image(systemName: "chevron.right").font(.caption)
            }
            if typeSize.isAccessibilitySize {
              effortContext(effort)
            } else {
              HStack(alignment: .firstTextBaseline) {
                effortContext(effort)
              }
            }
            if workout.user.username == api.username
              && training.bests.contains(where: {
                $0.sportID == workout.sportID && $0.distanceM == effort.distanceM
                  && abs($0.elapsedS - effort.elapsedS) <= 0.01
              })
            {
              Label("All-time best", systemImage: "trophy.fill").font(.caption2.bold())
                .foregroundStyle(RintStyle.power)
            }
          }.foregroundStyle(RintStyle.ink).padding(.vertical, 10)
            .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
            .contentShape(Rectangle())
            .overlay(alignment: .bottom) {
              Rectangle().fill(RintStyle.line).frame(height: 1)
            }
        }.buttonStyle(.plain)
      }
      if workout.user.username == api.username {
        NavigationLink {
          NativeProgressView(initialSection: "Records")
        } label: {
          Label("See all-time records", systemImage: "arrow.up.right").font(.subheadline.bold())
            .frame(minHeight: 44)
        }
      }
    }
  }
  @ViewBuilder private func effortContext(_ effort: NativeEffort) -> some View {
    if let start = effort.start, let end = effort.end {
      Text("\(compactTimeLabel(start)) – \(compactTimeLabel(end))")
        .accessibilityLabel("Interval \(compactTimeLabel(start)) to \(compactTimeLabel(end))")
        .font(.caption2).foregroundStyle(RintStyle.muted)
    }
    if !typeSize.isAccessibilitySize { Spacer(minLength: 8) }
    Text(
      DisplayUnits.pace(effort.elapsedS * 1000 / effort.distanceM) + " /"
        + DisplayUnits.distanceUnit
    ).font(.caption).foregroundStyle(RintStyle.muted)
  }
  @ViewBuilder func splitPanel(_ analysis: NativeAnalysis) -> some View {
    VStack(alignment: .leading, spacing: 16) {
      Picker("Distance splits or device laps", selection: $table) {
        Text(DisplayUnits.imperial ? "Miles" : "Kilometres").tag("Splits")
        Text("Device laps").tag("Laps")
      }.pickerStyle(.segmented)
      Text("Elapsed pace · includes pauses")
        .font(.caption).foregroundStyle(RintStyle.muted)
      let rows =
        table == "Laps"
        ? analysis.laps ?? []
        : (DisplayUnits.imperial ? analysis.splitsMile ?? [] : analysis.splitsKM)
      if rows.isEmpty {
        RintNotice(
          text: table == "Laps"
            ? "No device laps were recorded."
            : "Distance splits aren’t available for this recording.", icon: "info.circle")
      }
      ForEach(Array(rows.enumerated()), id: \.offset) { index, row in
        Button {
          intervalStart = row.start ?? 0
          intervalEnd = row.end ?? row.elapsedS
          selectedRange = true
          selectedTime = intervalStart
          interval = row
          detailSection = "Charts"
        } label: {
          HStack(spacing: 16) {
            Text(row.name ?? String(index + 1)).font(.subheadline.bold()).frame(
              minWidth: 24, alignment: .leading)
            VStack(alignment: .leading, spacing: 5) {
              Text(DisplayUnits.distance(row.distanceM) + " " + DisplayUnits.distanceUnit).font(
                .subheadline)
              Text(compactTimeLabel(row.elapsedS)).font(.caption).foregroundStyle(RintStyle.muted)
            }
            Spacer()
            Text(DisplayUnits.pace(row.paceSKM)).font(.headline).monospacedDigit()
            Text("/" + DisplayUnits.distanceUnit).font(.caption).foregroundStyle(RintStyle.muted)
            Image(systemName: "chevron.right").font(.caption).foregroundStyle(RintStyle.muted)
          }.foregroundStyle(RintStyle.ink).padding(.vertical, 12)
        }.buttonStyle(.plain)
        Divider()
      }
    }
  }
  func selectEffort(_ effort: NativeEffort) {
    guard let start = effort.start, let end = effort.end else {
      detailSection = "Best efforts"
      return
    }
    intervalStart = start
    intervalEnd = end
    selectedTime = readings.first(where: { $0.t >= start && $0.t <= end })?.t ?? start
    selectedRange = true
    detailSection = "Charts"
  }
  @ViewBuilder func chartPanel(_ analysis: NativeAnalysis) -> some View {
    let bounds = chartBounds
    VStack(alignment: .leading, spacing: 10) {
      ScrollView(.horizontal, showsIndicators: false) {
        HStack(spacing: 6) {
          ForEach(metrics.filter { available($0.0) }, id: \.0) { key, label in
            Button {
              metric = key
            } label: {
              Text(label).font(.caption.weight(metric == key ? .bold : .regular)).padding(
                .horizontal, 14
              ).frame(minHeight: 44)
                .foregroundStyle(metric == key ? RintStyle.ink : RintStyle.muted)
                .background(metric == key ? RintStyle.soft : .clear, in: Capsule())
            }.buttonStyle(.plain).disabled(!available(key)).opacity(available(key) ? 1 : 0.4)
              .accessibilityAddTraits(metric == key ? .isSelected : [])
          }
        }
      }
      HStack(alignment: .firstTextBaseline) {
        VStack(alignment: .leading, spacing: 3) {
          Text(selectedTime.map { readingLabel(at: $0) } ?? "—")
            .font(.system(size: 25, weight: .semibold, design: .rounded)).monospacedDigit()
            .foregroundStyle(RintStyle.metricColor(metric))
        }
        Spacer()
        if let selectedTime {
          VStack(alignment: .trailing, spacing: 3) {
            Text(compactTimeLabel(selectedTime)).font(.subheadline.weight(.semibold))
              .monospacedDigit()
            if let distance = ChartStream.nearest(
              metricStreams["distance"] ?? [], at: selectedTime)?.value
            {
              Text(
                DisplayUnits.distance(distance) + " " + DisplayUnits.distanceUnit
              )
              .font(.caption2).foregroundStyle(RintStyle.muted)
            }
          }
        }
      }
      if let selectedTime {
        HStack(spacing: 18) {
          ForEach(
            ["pace", "heart_rate", "power"].filter { $0 != metric && available($0) }, id: \.self
          ) { key in
            if let value = ChartStream.nearest(metricStreams[key] ?? [], at: selectedTime)?.value {
              Text(
                key == "pace"
                  ? compactTimeLabel(value * 60) + " /" + DisplayUnits.distanceUnit
                  : String(format: "%.0f", value) + (key == "power" ? " W" : " bpm")
              )
              .font(.caption.weight(.medium)).monospacedDigit().foregroundStyle(RintStyle.muted)
            }
          }
        }
      }
      if displayedReadings.isEmpty {
        Text("No samples for this metric. Choose another chart.").font(.footnote).foregroundStyle(
          RintStyle.muted
        ).frame(height: 180)
      } else {
        Chart {
          if selectedRange {
            RectangleMark(
              xStart: .value("Start", intervalStart), xEnd: .value("End", intervalEnd),
              yStart: .value("Low", bounds.lowerBound), yEnd: .value("High", bounds.upperBound)
            )
            .foregroundStyle(RintStyle.metricColor(metric).opacity(0.12))
          }
          ForEach(displayedReadings) { reading in
            AreaMark(
              x: .value("Elapsed seconds", reading.t),
              yStart: .value("Baseline", bounds.lowerBound),
              yEnd: .value("Value", min(bounds.upperBound, max(bounds.lowerBound, reading.value))),
              series: .value("Section", "activity-\(reading.segment)")
            )
            .foregroundStyle(
              LinearGradient(
                colors: [
                  RintStyle.metricColor(metric).opacity(0.18),
                  RintStyle.metricColor(metric).opacity(0.02),
                ], startPoint: .top, endPoint: .bottom))
            LineMark(
              x: .value("Elapsed seconds", reading.t),
              y: .value("Value", min(bounds.upperBound, max(bounds.lowerBound, reading.value))),
              series: .value("Section", "activity-\(reading.segment)")
            )
            .foregroundStyle(by: .value("Workout", "This workout"))
            .lineStyle(StrokeStyle(lineWidth: 2))
          }
          ForEach(ChartStream.reduced(comparisonReadings)) { reading in
            LineMark(
              x: .value("Elapsed seconds", reading.t),
              y: .value("Value", min(bounds.upperBound, max(bounds.lowerBound, reading.value))),
              series: .value("Section", "comparison-\(reading.segment)")
            )
            .foregroundStyle(by: .value("Workout", "Comparison"))
            .lineStyle(StrokeStyle(lineWidth: 2, dash: [5, 3]))
          }
          if let selectedTime {
            if let reading = ChartStream.nearest(readings, at: selectedTime) {
              PointMark(
                x: .value("Selected time", reading.t),
                y: .value(
                  "Selected value", min(bounds.upperBound, max(bounds.lowerBound, reading.value)))
              )
              .foregroundStyle(RintStyle.metricColor(metric)).symbolSize(55).accessibilityHidden(
                true)
            }
            RuleMark(x: .value("Selected time", selectedTime)).foregroundStyle(RintStyle.muted)
              .lineStyle(StrokeStyle(lineWidth: 1, dash: [4, 3]))
          }
        }.frame(height: typeSize.isAccessibilitySize ? 190 : 150).chartYScale(domain: bounds)
          .chartXScale(
            domain: selectedRange
              ? intervalStart...max(intervalStart + 1, intervalEnd)
              : 0...max(1, analysis.summary.elapsedS)
          )
          .chartForegroundStyleScale([
            "This workout": RintStyle.metricColor(metric), "Comparison": RintStyle.power,
          ])
          .chartLegend(.hidden)
          .chartPlotStyle { plot in plot.clipped() }
          .chartXAxis {
            AxisMarks { value in
              AxisGridLine()
              AxisValueLabel {
                if let seconds = value.as(Double.self) {
                  Text(compactTimeLabel(seconds)).font(.caption2)
                }
              }
            }
          }
          .chartYAxis {
            AxisMarks(position: .trailing) { value in
              AxisGridLine()
              AxisValueLabel {
                if let number = value.as(Double.self) {
                  Text(
                    metric == "pace"
                      ? compactTimeLabel(number * 60) : String(format: "%.0f", number)
                  )
                  .font(.caption2)
                }
              }
            }
          }
          .chartOverlay { proxy in
            GeometryReader { geometry in
              PlotTouchOverlay { point in
                guard let anchor = proxy.plotFrame else { return }
                let frame = geometry[anchor]
                let x = min(max(0, point.x - frame.minX), max(0, frame.width - 0.01))
                if let time = proxy.value(atX: x, as: Double.self) { selectTime(time) }
              }
            }
          }
          .accessibilityElement(children: .ignore)
          .accessibilityLabel((metrics.first(where: { $0.0 == metric })?.1 ?? "Workout") + " chart")
          .accessibilityValue(
            selectedTime.map { compactTimeLabel($0) + ", " + readingLabel(at: $0) } ?? "No sample"
          )
          .accessibilityAdjustableAction { direction in
            selectTime((selectedTime ?? 0) + (direction == .increment ? 10 : -10))
          }
        if metric == "pace" {
          HStack {
            Text(
              clippedPaceCount > 0 && !fullPaceRange
                ? "\(clippedPaceCount) slow readings beyond this scale"
                : "30-second pace"
            ).font(.caption2).foregroundStyle(RintStyle.muted)
            Spacer()
            Button(fullPaceRange ? "Focus scale" : "Full range") { fullPaceRange.toggle() }
              .font(.caption2.bold()).frame(minHeight: 44)
          }
        }
        if selectedRange {
          HStack {
            Text("\(compactTimeLabel(intervalStart)) – \(compactTimeLabel(intervalEnd)) selected")
              .font(.caption.bold())
            Spacer()
            Button("Clear") { selectedRange = false }.font(.caption).frame(minHeight: 44)
          }
        }
      }
      Button {
        comparing = true
      } label: {
        Label(
          comparisonActivity == nil
            ? "Compare a workout" : "Comparing: " + (comparisonActivity?.title ?? "Workout"),
          systemImage: "square.on.square")
      }.font(.caption).frame(minHeight: 44)
      if comparisonActivity != nil {
        if comparisonLoading { ProgressView("Loading comparison…").font(.caption) }
        if let comparisonError {
          RintNotice(text: comparisonError, icon: "exclamationmark.circle")
          Button("Retry comparison") { Task { await loadComparison() } }
            .font(.caption).frame(minHeight: 44).disabled(comparisonLoading)
        } else if comparisonAnalysis != nil && comparisonReadings.isEmpty {
          Text("The comparison workout has no samples for this metric.")
            .font(.caption).foregroundStyle(RintStyle.muted)
        }
        Text("Solid: this workout · dashed: comparison").font(.caption2).foregroundStyle(
          RintStyle.muted)
      }
    }.rintPanel(padding: 12)
  }
  func selectTime(_ time: Double) {
    guard let first = readings.first, let last = readings.last else { return }
    let clamped = min(last.t, max(first.t, time))
    selectedTime = ChartStream.nearest(readings, at: clamped)?.t ?? clamped
  }
  var chartBounds: ClosedRange<Double> {
    fullPaceRange ? completeBounds : focusedBounds
  }

  func readingLabel(at time: Double) -> String {
    guard let p = ChartStream.nearest(readings, at: time) else { return "No sample" }
    if metric == "pace" { return compactTimeLabel(p.value * 60) + " /" + DisplayUnits.distanceUnit }
    return String(format: "%.0f", p.value)
      + (metric == "heart_rate"
        ? " bpm" : metric == "power" ? " W" : metric == "elevation" ? " m" : " counts/min")
  }
  var conversation: some View {
    VStack(alignment: .leading, spacing: 18) {
      HStack {
        Text("Comments").font(.headline)
        Spacer()
        if !composingComment {
          Button("Write a comment") { composingComment = true }.font(.caption.weight(.semibold))
            .frame(minHeight: 44)
        }
      }
      ForEach(comments) { comment in NativeCommentRow(comment: comment, reload: loadComments) }
      if composingComment {
        TextField("Add a comment · @mentions supported", text: $draftComment, axis: .vertical)
          .font(.subheadline).padding(14).background(
            RintStyle.soft, in: RoundedRectangle(cornerRadius: 12))
        Picker("Who can read your comment", selection: $commentVisibility) {
          if workout.workoutVisibility == "public" { Text("Everyone").tag("public") }
          if workout.workoutVisibility == "public" || workout.workoutVisibility == "followers_only"
          {
            Text("Followers").tag("followers_only")
          }
          Text("Mentioned people").tag("private")
        }.font(.caption)
        Button(posting ? "Posting…" : "Post comment") {
          posting = true
          Task {
            do {
              _ = try await api.request(
                "workouts/\(workout.id)/comments", method: "POST",
                body: JSONSerialization.data(withJSONObject: [
                  "text": draftComment, "text_visibility": commentVisibility,
                ]))
              draftComment = ""
              composingComment = false
              await loadComments()
            } catch { self.error = error.localizedDescription }
            posting = false
          }
        }.buttonStyle(RintSecondaryButton()).disabled(
          posting || draftComment.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
      }
    }.rintPanel()
  }
  func toggleLike() {
    likeBusy = true
    Task {
      do {
        _ = try await api.request(
          "workouts/\(workout.id)/like\(liked ? "/undo" : "")", method: "POST")
        liked.toggle()
      } catch { self.error = error.localizedDescription }
      likeBusy = false
    }
  }
  func loadComments() async {
    do {
      comments = try JSONDecoder().decode(
        APIResponse<NativeComments>.self, from: await api.request("workouts/\(workout.id)/comments")
      ).data.comments
    } catch { self.error = error.localizedDescription }
  }
  @ViewBuilder func intervalPanel(_ analysis: NativeAnalysis) -> some View {
    DisclosureGroup("Analyze an interval") {
      VStack(alignment: .leading, spacing: 14) {
        Text("Start: \(compactTimeLabel(intervalStart))").font(.subheadline)
        Slider(value: $intervalStart, in: 0...max(0.1, intervalEnd - 0.1)).accessibilityLabel(
          "Interval start seconds")
        Text("Finish: \(compactTimeLabel(intervalEnd))").font(.subheadline)
        Slider(
          value: $intervalEnd,
          in: min(
            intervalStart + 0.1, analysis.summary.elapsedS)...max(
              intervalStart + 0.1, analysis.summary.elapsedS)
        ).accessibilityLabel("Interval finish seconds")
        Button(intervalBusy ? "Calculating…" : "Analyze selection") {
          selectedRange = true
          intervalBusy = true
          intervalError = nil
          let requestedStart = intervalStart
          let requestedEnd = intervalEnd
          Task {
            do {
              let result = try JSONDecoder().decode(
                APIResponse<NativeSummary>.self,
                from: await api.request(
                  "rint/activities/\(workout.id)/interval", method: "POST",
                  body: JSONSerialization.data(withJSONObject: [
                    "start": requestedStart, "end": requestedEnd,
                  ]))
              ).data
              if intervalStart == requestedStart && intervalEnd == requestedEnd {
                interval = result
              }
            } catch {
              if intervalStart == requestedStart && intervalEnd == requestedEnd {
                intervalError = error.localizedDescription
              }
            }
            intervalBusy = false
          }
        }.buttonStyle(RintSecondaryButton()).disabled(intervalBusy)
        if let interval {
          HStack {
            RintMetric(
              title: "Distance", value: DisplayUnits.distance(interval.distanceM),
              unit: DisplayUnits.distanceUnit)
            RintMetric(
              title: "Elapsed pace", value: DisplayUnits.pace(interval.paceSKM),
              unit: "/" + DisplayUnits.distanceUnit)
          }
          Text(
            "\(compactTimeLabel(interval.elapsedS)) elapsed · \(compactTimeLabel(interval.movingS)) moving · \(compactTimeLabel(interval.pausedS)) paused"
          ).font(.caption).foregroundStyle(RintStyle.muted)
          if let hr = interval.averages["heart_rate"] {
            Text("Average heart rate: \(Int(hr.rounded())) bpm").font(.caption)
          }
        }
        if let intervalError { RintNotice(text: intervalError, icon: "exclamationmark.circle") }
      }.padding(.top, 14)
    }.font(.subheadline).padding(.vertical, 4)
  }
  @MainActor func loadComparison() async {
    comparisonAnalysis = nil
    comparisonReadings = []
    comparisonError = nil
    comparisonLoading = false
    guard let selected = comparisonActivity else {
      updateReadings()
      return
    }
    comparisonLoading = true
    defer {
      if comparisonActivity?.id == selected.id { comparisonLoading = false }
    }
    do {
      let loaded = try JSONDecoder().decode(
        APIResponse<NativeAnalysis>.self,
        from: await api.request("rint/activities/\(selected.id)/analysis")
      ).data
      guard comparisonActivity?.id == selected.id else { return }
      comparisonAnalysis = loaded
      updateReadings()
    } catch {
      if comparisonActivity?.id == selected.id { comparisonError = error.localizedDescription }
    }
  }
  func updateReadings() {
    let previousTime = selectedTime
    if metricStreams.isEmpty || cachedImperial != imperial {
      cachedImperial = imperial
      metricStreams = Dictionary(
        uniqueKeysWithValues: metrics.map { key, _ in
          (
            key,
            key == "pace" && analysis?.recording.summaryOnly == true
              ? []
              : ChartStream.values(analysis?.recording.points ?? [], metric: key).map { point in
                ChartReading(
                  id: point.id, t: point.t,
                  value: key == "pace" ? point.value * DisplayUnits.paceFactor : point.value,
                  segment: point.segment)
              }
          )
        })
      metricStreams["distance"] = (analysis?.recording.points ?? []).enumerated().compactMap {
        i, sample in
        sample.d.map { ChartReading(id: i, t: sample.t, value: $0, segment: 0) }
      }
    }
    readings = metricStreams[metric] ?? []
    comparisonReadings =
      metric == "pace" && comparisonAnalysis?.recording.summaryOnly == true
      ? []
      : ChartStream.values(
        comparisonAnalysis?.recording.points ?? [], metric: metric
      ).map { point in
        ChartReading(
          id: point.id, t: point.t,
          value: metric == "pace" ? point.value * DisplayUnits.paceFactor : point.value,
          segment: point.segment)
      }
    displayedReadings = ChartStream.reduced(readings)
    focusedBounds = ChartStream.bounds(readings + comparisonReadings, metric: metric)
    completeBounds = ChartStream.bounds(
      readings + comparisonReadings, metric: metric, fullRange: true)
    clippedPaceCount =
      (readings + comparisonReadings).filter { $0.value > focusedBounds.upperBound }.count
    if let previousTime {
      selectedTime = previousTime
    } else {
      selectedTime = readings.first?.t
    }
  }
}

struct NativeSharingView: View {
  let workout: FeedActivity
  @EnvironmentObject var api: APIClient
  @Environment(\.dismiss) private var dismiss
  @State private var visibility = "private"
  @State private var mapVisibility = "private"
  @State private var privacyRadius = 200.0
  @State private var title = ""
  @State private var caption = ""
  @State private var savedTitle = ""
  @State private var savedCaption = ""
  @State private var points: [Sample] = []
  @State private var loaded = false
  @State private var loading = false
  @State private var exportFormat = "csv"
  @State private var saving = false
  @State private var exporting = false
  @State private var sharingLink = false
  @State private var message: String?
  @State private var error: String?
  @State private var exportURL: URL?
  private var activityURL: URL? {
    URL(string: api.server)?.appendingPathComponent("workouts/\(workout.id)")
  }
  private var audience: String {
    visibility == "private"
      ? "Only you" : visibility == "followers_only" ? "Your followers" : "Everyone"
  }
  var body: some View {
    NavigationStack {
      ScrollView {
        VStack(alignment: .leading, spacing: 16) {
          VStack(alignment: .leading, spacing: 12) {
            Text("Workout title").font(.caption.bold()).foregroundStyle(RintStyle.muted)
            TextField("Workout title", text: $title, axis: .vertical).font(.headline).lineLimit(
              1...3
            )
            .padding(14).background(RintStyle.soft, in: RoundedRectangle(cornerRadius: 12))
            .onChange(of: title) { _, value in
              if value.count > 255 { title = String(value.prefix(255)) }
            }
            TextField("Caption", text: $caption, axis: .vertical)
              .lineLimit(2...6).padding(14).background(
                RintStyle.soft, in: RoundedRectangle(cornerRadius: 12)
              )
              .accessibilityLabel("Workout caption")
          }
          NativeActivityPhotos(
            photos: workout.mediaAttachments ?? [], workoutID: workout.id, canAttach: true,
            compactEmpty: true)
          VStack(alignment: .leading, spacing: 16) {
            HStack {
              Label("Audience", systemImage: "person.2").font(.subheadline.bold())
              Spacer()
              Picker("Activity audience", selection: $visibility) {
                Text("Only me").tag("private")
                Text("My followers").tag("followers_only")
                Text("Everyone").tag("public")
              }.labelsHidden()
            }
            DisclosureGroup("Route privacy") {
              VStack(alignment: .leading, spacing: 14) {
                Picker("Route audience", selection: $mapVisibility) {
                  Text("Only me").tag("private")
                  Text("My followers").tag("followers_only")
                  Text("Everyone").tag("public")
                }
                Text("Hide start and finish: \(Int(privacyRadius)) m").font(.subheadline)
                Slider(value: $privacyRadius, in: 200...10000, step: 100).accessibilityLabel(
                  "Route protection radius in metres")
                Text(
                  "Route sharing is limited by both audiences. Your original recording stays intact."
                )
                .font(.caption).foregroundStyle(RintStyle.muted)
              }.padding(.top, 12)
            }.font(.subheadline)
          }.rintPanel(padding: 16)
          VStack(alignment: .leading, spacing: 14) {
            HStack {
              Text("Sharing preview").font(.headline)
              Spacer()
              Text(audience).font(.caption.bold()).foregroundStyle(RintStyle.muted)
            }
            if visibility == "private" {
              Label(
                "Your workout stays private. A link does not grant other people access.",
                systemImage: "lock.shield"
              )
              .font(.footnote).foregroundStyle(RintStyle.muted)
            } else {
              if mapVisibility != "private" {
                NativeRouteMap(
                  points: RouteStream.protected(points, radius: privacyRadius), height: 180,
                  interactive: false)
              } else {
                Label("Route hidden from other people", systemImage: "location.slash").font(
                  .caption
                ).foregroundStyle(RintStyle.muted)
              }
              Text(title.isEmpty ? "Your workout" : title).font(.headline)
              HStack {
                RintMetric(
                  title: "Distance",
                  value: workout.distance.map { DisplayUnits.distance($0 * 1000) } ?? "—",
                  unit: DisplayUnits.distanceUnit)
                RintMetric(
                  title: "Moving time",
                  value: DisplayUnits.duration(workout.moving ?? workout.duration))
              }
              if !caption.isEmpty { Text(caption).font(.subheadline).lineLimit(4) }
              Text(
                "Charts and photos follow the activity audience; heart-rate access also follows your profile privacy settings."
              )
              .font(.caption2).foregroundStyle(RintStyle.muted)
            }
          }
          if loading { ProgressView("Loading saved settings…") }
          if !loaded && !loading {
            Button("Retry loading workout") { Task { await loadSettings() } }.buttonStyle(
              RintSecondaryButton())
          }
          Button(saving ? "Saving…" : "Save & share link") { Task { await save(openShare: true) } }
            .buttonStyle(RintPrimaryButton()).disabled(
              saving || !loaded || title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
          Button("Save changes") { Task { await save(openShare: false) } }
            .font(.subheadline.bold()).frame(maxWidth: .infinity, minHeight: 44).disabled(
              saving || !loaded || title.isEmpty)
          if let message { RintNotice(text: message, icon: "checkmark.circle") }
          if api.server.contains(".ts.net") {
            RintNotice(
              text:
                "Your link opens on this private Tailscale server. Recipients need network access as well as permission to view the activity.",
              icon: "network")
          }
          DisclosureGroup("Export") {
            VStack(alignment: .leading, spacing: 16) {
              Picker("Export format", selection: $exportFormat) {
                Text("Samples CSV").tag("csv")
                Text("Streams + analysis JSON").tag("json")
              }.onChange(of: exportFormat) { _, _ in exportURL = nil }
              Button(exporting ? "Preparing…" : "Prepare export") {
                exporting = true
                error = nil
                Task {
                  do {
                    let data = try await api.request(
                      "rint/activities/\(workout.id)/export?format=\(exportFormat)")
                    let url = FileManager.default.temporaryDirectory.appendingPathComponent(
                      "activity-\(workout.id).\(exportFormat)")
                    try data.write(to: url, options: .atomic)
                    exportURL = url
                  } catch { self.error = error.localizedDescription }
                  exporting = false
                }
              }.buttonStyle(RintSecondaryButton()).disabled(exporting)
              if let exportURL {
                ShareLink("Save or share export", item: exportURL).buttonStyle(RintPrimaryButton())
              }
            }.padding(.top, 16)
          }.font(.subheadline.bold())
          if let error { RintNotice(text: error, icon: "exclamationmark.circle") }
        }.padding(18)
      }.background(RintStyle.paper).navigationTitle("Share workout").navigationBarTitleDisplayMode(
        .inline
      )
      .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } } }
      .task { await loadSettings() }
      .sheet(isPresented: $sharingLink) {
        if let activityURL { NativeLinkShare(items: [activityURL]) }
      }
    }
  }
  @MainActor func save(openShare: Bool) async {
    guard loaded, !saving else { return }
    saving = true
    error = nil
    message = nil
    defer { saving = false }
    do {
      if title != savedTitle || caption != savedCaption {
        _ = try await api.request(
          "workouts/\(workout.id)", method: "PATCH",
          body: JSONSerialization.data(withJSONObject: ["title": title, "description": caption]))
      }
      _ = try await api.request(
        "rint/activities/\(workout.id)/sharing", method: "POST",
        body: JSONSerialization.data(withJSONObject: [
          "visibility": visibility, "map_visibility": mapVisibility,
          "privacy_radius_m": Int(privacyRadius),
        ]))
      savedTitle = title
      savedCaption = caption
      message = "Saved · " + audience
      await api.refresh()
      if openShare { sharingLink = true }
    } catch { self.error = "Your changes couldn’t be completed. " + error.localizedDescription }
  }
  @MainActor func loadSettings() async {
    loading = true
    error = nil
    defer { loading = false }
    do {
      let json =
        try JSONSerialization.jsonObject(
          with: await api.request("rint/activities/\(workout.id)/sharing")) as? [String: Any]
      let settings = json?["data"] as? [String: Any]
      visibility = settings?["visibility"] as? String ?? "private"
      mapVisibility = settings?["map_visibility"] as? String ?? "private"
      privacyRadius = settings?["privacy_radius_m"] as? Double ?? 200
      let detail =
        try JSONDecoder().decode(
          APIResponse<FeedResponse>.self, from: await api.request("workouts/\(workout.id)")
        ).data.workouts.first ?? workout
      title = detail.title ?? "Workout"
      caption = detail.description ?? ""
      savedTitle = title
      savedCaption = caption
      if let analysis = try? JSONDecoder().decode(
        APIResponse<NativeAnalysis>.self,
        from: await api.request("rint/activities/\(workout.id)/analysis"))
      {
        points = analysis.data.recording.points
      }
      loaded = true
    } catch { self.error = error.localizedDescription }
  }
}
