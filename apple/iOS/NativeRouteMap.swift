import MapKit
import SwiftUI

struct NativeRouteMap: View {
  let points: [Sample]
  var sampled = false
  var height: CGFloat = 240
  var interactive = true
  var selectedTime: Double? = nil
  var onSelectTime: ((Double) -> Void)? = nil
  var onMetricChange: ((String) -> Void)? = nil
  @State private var expanded = false
  @State private var segments: [[Sample]] = []
  @State private var lines: [RouteLine] = []
  @State private var fixes: [Sample] = []
  @State private var touchFixes: [Sample] = []
  @State private var prepared = false
  @State private var metric = "power"
  @State private var available: [String] = []
  @State private var intensity: RouteIntensity?
  private let colours: [Color] = [.teal, .blue, RintStyle.violet, .orange, .pink]
  private struct RouteLine: Identifiable {
    let id: Int
    let coordinates: [CLLocationCoordinate2D]
    let band: Int?
  }
  private var selected: Sample? {
    guard let selectedTime, !fixes.isEmpty else { return nil }
    var lo = 0
    var hi = fixes.count
    while lo < hi {
      let mid = (lo + hi) / 2
      if fixes[mid].t < selectedTime { lo = mid + 1 } else { hi = mid }
    }
    let a = fixes[max(0, lo - 1)]
    let b = fixes[min(fixes.count - 1, lo)]
    let nearest = abs(a.t - selectedTime) <= abs(b.t - selectedTime) ? a : b
    return abs(nearest.t - selectedTime) <= 30 ? nearest : nil
  }
  var body: some View {
    Group {
      if !prepared {
        ProgressView("Loading route…").frame(maxWidth: .infinity).frame(height: height)
      } else if segments.isEmpty {
        Label("No GPS route available", systemImage: "location.slash")
          .font(.caption).foregroundStyle(RintStyle.muted).padding(.vertical, 8)
      } else {
        VStack(alignment: .leading, spacing: 8) {
          canvas(height: height).overlay(alignment: .bottomTrailing) {
            if interactive {
              Button {
                expanded = true
              } label: {
                Image(systemName: "arrow.up.left.and.arrow.down.right").frame(width: 44, height: 44)
                  .background(.regularMaterial, in: Circle())
              }.accessibilityLabel("Open full-screen route map").padding(10)
            }
          }
          if interactive { legend }
        }.sheet(isPresented: $expanded) {
          NavigationStack {
            VStack(spacing: 10) {
              canvas(height: nil)
              legend.padding(.horizontal, 16)
            }
            .padding(.bottom, 12).navigationTitle("Route").navigationBarTitleDisplayMode(.inline)
            .toolbar {
              ToolbarItem(placement: .confirmationAction) { Button("Done") { expanded = false } }
            }
          }
        }
      }
    }.onAppear { prepare() }.onChange(of: points) { _, _ in prepare() }
      .onChange(of: metric) { _, value in
        paint()
      }
  }
  private var legend: some View {
    VStack(alignment: .leading, spacing: 5) {
      HStack(spacing: 10) {
        if !available.isEmpty {
          Menu {
            ForEach(available, id: \.self) { key in
              Button(title(key)) {
                metric = key
                onMetricChange?(key)
              }
            }
          } label: {
            Label(title(metric), systemImage: "line.3.horizontal.decrease").font(
              .caption.weight(.semibold)
            )
            .frame(minHeight: 44)
          }.accessibilityLabel("Route colour, " + title(metric))
          if let intensity {
            HStack(spacing: 6) {
              Text(value(intensity.low)).monospacedDigit()
              LinearGradient(
                colors: abs(intensity.high - intensity.low) < 0.001
                  ? [colours[0], colours[0]] : colours,
                startPoint: .leading, endPoint: .trailing
              )
              .frame(width: 62, height: 5).clipShape(Capsule()).accessibilityHidden(true)
              Text(value(intensity.high)).monospacedDigit()
            }.font(.caption2).foregroundStyle(RintStyle.muted)
          }
        } else {
          Text("Route · no effort samples").font(.caption2).foregroundStyle(RintStyle.muted)
        }
        Spacer(minLength: 0)
        if let selectedTime, let intensity {
          if let reading = RouteIntensity.reading(intensity.readings, at: selectedTime) {
            VStack(alignment: .trailing, spacing: 2) {
              Text(value(reading.value)).font(.caption.weight(.semibold)).monospacedDigit()
              Text(compactTimeLabel(selectedTime)).font(.caption2).monospacedDigit()
                .foregroundStyle(RintStyle.muted)
            }
          } else {
            Text("No sample").font(.caption2).foregroundStyle(RintStyle.muted)
          }
        }
      }
      if !available.contains("power"), !available.isEmpty {
        Text("No power data").font(.caption2)
          .foregroundStyle(RintStyle.muted)
      }
      if intensity?.sections.contains(where: { $0.band == nil }) == true {
        Text("Grey: no sensor data").font(.caption2).foregroundStyle(
          RintStyle.muted)
      }
    }
  }
  private func prepare() {
    segments = RouteStream.segments(points, sampled: sampled)
    fixes = segments.flatMap { $0 }
    touchFixes = segments.flatMap { row in
      row.enumerated().filter {
        $0.offset == 0 || $0.offset == row.count - 1 || $0.offset % max(1, row.count / 500) == 0
      }.map(\.element)
    }
    available = interactive ? RouteIntensity.available(points) : []
    if !available.contains(metric) { metric = available.first ?? "power" }
    paint()
    prepared = true
  }
  private func paint() {
    if available.contains(metric) {
      let result = RouteIntensity.build(points, metric: metric, sampled: sampled)
      intensity = result
      lines = result.sections.map { row in
        RouteLine(
          id: row.id,
          coordinates: row.points.map {
            CLLocationCoordinate2D(latitude: $0.lat!, longitude: $0.lon!)
          }, band: row.band)
      }
    } else {
      intensity = nil
      lines = segments.enumerated().map { i, row in
        RouteLine(
          id: i,
          coordinates: row.enumerated().filter {
            $0.offset == 0 || $0.offset == row.count - 1
              || $0.offset % max(1, row.count / 1500) == 0
          }.map { CLLocationCoordinate2D(latitude: $0.element.lat!, longitude: $0.element.lon!) },
          band: nil)
      }
    }
  }
  private func canvas(height: CGFloat?) -> some View {
    MapReader { proxy in
      Map(initialPosition: .automatic, interactionModes: interactive ? .all : []) {
        ForEach(lines) { row in
          MapPolyline(coordinates: row.coordinates)
            .stroke(
              intensity == nil
                ? RintStyle.violet : row.band.map { colours[$0] } ?? RintStyle.muted.opacity(0.5),
              style: StrokeStyle(lineWidth: 4, lineCap: .round))
        }
        if let first = segments.first?.first {
          Annotation(
            "Route start",
            coordinate: CLLocationCoordinate2D(latitude: first.lat!, longitude: first.lon!)
          ) {
            Circle().fill(RintStyle.accent).frame(width: 10, height: 10).overlay(
              Circle().stroke(.black, lineWidth: 2))
          }
        }
        if let last = segments.last?.last {
          Annotation(
            "Route finish",
            coordinate: CLLocationCoordinate2D(latitude: last.lat!, longitude: last.lon!)
          ) {
            Image(systemName: "flag.fill").font(.caption).padding(6).background(
              .regularMaterial, in: Circle())
          }
        }
        if let selected {
          Annotation(
            "Selected moment",
            coordinate: CLLocationCoordinate2D(latitude: selected.lat!, longitude: selected.lon!)
          ) {
            Circle().fill(RintStyle.ink).frame(width: 13, height: 13).overlay(
              Circle().stroke(.white, lineWidth: 3))
          }
        }
      }.mapStyle(.standard(elevation: .flat, pointsOfInterest: .excludingAll))
        .mapControls {
          if interactive {
            MapCompass()
            MapScaleView()
          }
        }
        .simultaneousGesture(
          SpatialTapGesture().onEnded { gesture in
            guard interactive, onSelectTime != nil else { return }
            let nearest = touchFixes.compactMap { fix -> (Sample, Double)? in
              guard
                let position = proxy.convert(
                  CLLocationCoordinate2D(latitude: fix.lat!, longitude: fix.lon!), to: .local)
              else { return nil }
              return (fix, hypot(position.x - gesture.location.x, position.y - gesture.location.y))
            }.min(by: { $0.1 < $1.1 })
            if let nearest, nearest.1 <= 44 { onSelectTime?(nearest.0.t) }
          })
    }.frame(height: height).clipShape(RoundedRectangle(cornerRadius: 14))
      .accessibilityLabel("Activity route on a geographic map")
      .allowsHitTesting(interactive)
  }
  private func title(_ key: String) -> String {
    key == "power" ? "Power" : key == "heart_rate" ? "Heart rate" : "Pace"
  }
  private func value(_ number: Double) -> String {
    metric == "pace"
      ? DisplayUnits.pace(number * 60) + " /" + DisplayUnits.distanceUnit
      : String(format: "%.0f", number) + (metric == "power" ? " W" : " bpm")
  }
}
