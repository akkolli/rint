<template>
  <div
    ref="mapContainer"
    class="activity-route-map"
    :class="{ expanded, compact, 'no-route': !coordinates.length }"
    :style="{ '--route-legend-height': legendNote ? '64px' : '44px' }"
    @keydown.esc="expanded = false"
    :role="expanded ? 'dialog' : undefined"
    :aria-modal="expanded ? true : undefined"
    :aria-label="expanded ? 'Full-screen activity route' : undefined"
    @keydown="keepFocusInMap"
  >
    <LMap
      v-if="coordinates.length"
      ref="map"
      :bounds="bounds"
      :use-global-leaflet="true"
      :options="options"
      @ready="mapReady"
      @click="inspectRoute"
      :style="{
        height: compact ? '100%' : 'calc(100% - var(--route-legend-height))',
      }"
      aria-label="Activity route map"
    >
      <LTileLayer
        :url="`${getApiUrl()}workouts/map_tile/{s}/{z}/{x}/{y}.png`"
        :attribution="appConfig.map_attribution"
        :max-zoom="19"
        @tileerror="tileFailed = true"
      />
      <LPolyline
        v-for="(row, i) in colouredLines"
        :key="i"
        :lat-lngs="row.coordinates"
        :color="row.colour"
        :weight="4"
      />
      <LCircleMarker
        v-if="first"
        :lat-lng="first"
        :radius="6"
        color="#192c25"
        fill-color="#d4f36b"
        :fill-opacity="1"
      />
      <LCircleMarker
        v-if="selected"
        :lat-lng="selected"
        :radius="7"
        color="#fff"
        fill-color="#7052d6"
        :fill-opacity="1"
      />
    </LMap>
    <span v-else class="no-route-state">No GPS route available</span>
    <button
      v-if="!compact && coordinates.length"
      ref="expandButton"
      class="expand-map"
      @click="expanded = !expanded"
      :aria-label="expanded ? 'Close full-screen map' : 'Expand route map'"
    >
      {{ expanded ? 'Close' : 'Expand' }}
    </button>
    <div v-if="!compact && coordinates.length" class="route-legend">
      <div class="route-scale">
        <label v-if="available.length"
          ><span class="sr-only">Route colour</span
          ><select
            v-model="colourMetric"
            @change="$emit('metric-change', colourMetric)"
          >
            <option v-for="key in available" :key="key" :value="key">
              {{ title(key) }}
            </option>
          </select></label
        >
        <template v-if="intensity.readings.length"
          ><small>{{ measurement(intensity.low) }}</small
          ><span
            class="intensity-ramp"
            :style="
              Math.abs(intensity.high - intensity.low) < 0.001
                ? { background: routePalette[0] }
                : undefined
            "
            aria-hidden="true"
          /><small>{{ measurement(intensity.high) }}</small></template
        >
        <span v-if="currentReading" class="route-reading">{{
          measurement(currentReading.v)
        }}</span>
      </div>
      <small v-if="legendNote">{{ legendNote }}</small>
    </div>
    <span v-if="tileFailed" class="map-status" role="status"
      >Map tiles unavailable. Your route is still shown.</span
    >
  </div>
</template>
<script setup lang="ts">
  import {
    LMap,
    LTileLayer,
    LPolyline,
    LCircleMarker,
  } from '@vue-leaflet/vue-leaflet'
  import type {
    LatLngBoundsLiteral,
    LatLngTuple,
    MapOptions,
    LeafletMouseEvent,
  } from 'leaflet'
  import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
  import 'leaflet/dist/leaflet.css'

  import useApp from '@/composables/useApp'
  import type { ILeafletObject } from '@/types/map'
  import type { Sample } from '@/types/rint'
  import { getApiUrl } from '@/utils'
  import { metricSeries, routeSegments } from '@/utils/activityStream'
  import {
    nearbyReading,
    routeIntensity,
    routePalette,
  } from '@/utils/routeIntensity'
  const props = defineProps<{
    points: Sample[]
    sampled?: boolean
    compact?: boolean
    selectedTime?: number
    units?: string
  }>()
  const emit = defineEmits<{
    'select-time': [number]
    'metric-change': [string]
  }>()
  const colourMetric = ref('power')
  const available = computed(() =>
    props.compact
      ? []
      : ['power', 'heart_rate', 'pace'].filter(
          (key) => metricSeries(props.points, key).length > 0
        )
  )
  watch(
    available,
    (rows) => {
      if (!rows.includes(colourMetric.value))
        colourMetric.value = rows[0] || 'power'
    },
    { immediate: true }
  )
  const intensity = computed(() =>
    routeIntensity(props.points, colourMetric.value, props.sampled)
  )
  const legendNote = computed(() => {
    if (!available.value.length) return 'No sensor data'
    const notes: string[] = []
    if (!available.value.includes('power')) notes.push('No power data')
    if (intensity.value.sections.some((row) => row.band === undefined))
      notes.push('Grey: no sensor data')
    return notes.join(' · ')
  })
  const colouredLines = computed(() =>
    available.value.includes(colourMetric.value)
      ? intensity.value.sections.map((row) => ({
          coordinates: row.points.map((p) => [p.lat!, p.lon!] as LatLngTuple),
          colour: row.band === undefined ? '#939a94' : routePalette[row.band],
        }))
      : coordinates.value.map((row) => ({
          coordinates: row,
          colour: '#7052d6',
        }))
  )
  const currentReading = computed(() =>
    props.selectedTime === undefined
      ? undefined
      : nearbyReading(intensity.value.readings, props.selectedTime)
  )
  function title(key: string) {
    return key === 'power'
      ? 'Power'
      : key === 'heart_rate'
        ? 'Heart rate'
        : 'Pace'
  }
  function measurement(value: number) {
    if (colourMetric.value !== 'pace')
      return `${Math.round(value)} ${colourMetric.value === 'power' ? 'W' : 'bpm'}`
    const seconds = Math.round(
      value * 60 * (props.units === 'mi' ? 1.609344 : 1)
    )
    return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')} /${props.units || 'km'}`
  }
  function inspectRoute(event: LeafletMouseEvent) {
    if (props.compact || !map.value) return
    const object = map.value.leafletObject
    const target = object.latLngToContainerPoint(event.latlng)
    let best: Sample | undefined,
      distance = 44
    for (const fix of touchFixes.value) {
      const point = object.latLngToContainerPoint([fix.lat!, fix.lon!])
      const delta = Math.hypot(point.x - target.x, point.y - target.y)
      if (delta < distance) {
        distance = delta
        best = fix
      }
    }
    if (best) emit('select-time', best.t)
  }
  const { appConfig } = useApp()
  const expanded = ref(false),
    tileFailed = ref(false),
    map = ref<ILeafletObject | null>(null)
  const mapContainer = ref<HTMLElement | null>(null),
    expandButton = ref<HTMLButtonElement | null>(null)
  const options = computed<MapOptions>(() => ({
    scrollWheelZoom: false,
    dragging: !props.compact,
    touchZoom: !props.compact,
    doubleClickZoom: !props.compact,
    zoomControl: !props.compact,
    maxZoom: 19,
  }))
  const segments = computed(() => routeSegments(props.points, props.sampled))
  const fixes = computed(() => segments.value.flat())
  const touchFixes = computed(() =>
    segments.value.flatMap((row) =>
      row.filter(
        (_, i) =>
          i === 0 ||
          i === row.length - 1 ||
          i % Math.max(1, Math.ceil(row.length / 500)) === 0
      )
    )
  )
  const coordinates = computed<LatLngTuple[][]>(() =>
    segments.value.map((row) =>
      row
        .filter(
          (_, i) =>
            i === 0 ||
            i === row.length - 1 ||
            i % Math.max(1, Math.ceil(row.length / 1500)) === 0
        )
        .map((p) => [p.lat!, p.lon!])
    )
  )
  const first = computed(() => coordinates.value[0]?.[0])
  const bounds = computed<LatLngBoundsLiteral>(() => {
    const all = coordinates.value.flat()
    const lats = all.map((p) => p[0]),
      lons = all.map((p) => p[1])
    return [
      [Math.min(...lats), Math.min(...lons)],
      [Math.max(...lats), Math.max(...lons)],
    ]
  })
  const selected = computed<LatLngTuple | undefined>(() => {
    if (props.selectedTime === undefined) return
    const points = fixes.value
    if (!points.length) return
    let lo = 0,
      hi = points.length
    while (lo < hi) {
      const mid = (lo + hi) >>> 1
      if (points[mid].t < props.selectedTime) lo = mid + 1
      else hi = mid
    }
    const a = points[Math.max(0, lo - 1)],
      b = points[Math.min(points.length - 1, lo)]
    const nearest =
      Math.abs(a.t - props.selectedTime) <= Math.abs(b.t - props.selectedTime)
        ? a
        : b
    if (Math.abs(nearest.t - props.selectedTime) <= 30)
      return [nearest.lat!, nearest.lon!]
  })
  function fit() {
    map.value?.leafletObject.fitBounds(bounds.value, {
      padding: [20, 20],
      maxZoom: 17,
    })
  }
  let resizeObserver: ResizeObserver | undefined
  function mapReady() {
    fit()
    resizeObserver?.disconnect()
    resizeObserver = new ResizeObserver(() => {
      map.value?.leafletObject.invalidateSize({ pan: false })
      fit()
    })
    if (mapContainer.value) resizeObserver.observe(mapContainer.value)
  }
  onBeforeUnmount(() => resizeObserver?.disconnect())
  function keepFocusInMap(event: KeyboardEvent) {
    if (!expanded.value || event.key !== 'Tab') return
    const controls = Array.from(
      mapContainer.value?.querySelectorAll<HTMLElement>(
        'a[href], button, select, [tabindex="0"]'
      ) ?? []
    ).filter((element) => element.offsetParent !== null)
    const firstControl = controls[0],
      lastControl = controls[controls.length - 1]
    if (event.shiftKey && document.activeElement === firstControl) {
      event.preventDefault()
      lastControl?.focus()
    } else if (!event.shiftKey && document.activeElement === lastControl) {
      event.preventDefault()
      firstControl?.focus()
    }
  }
  watch(expanded, async () => {
    await nextTick()
    map.value?.leafletObject.invalidateSize()
    fit()
    expandButton.value?.focus()
  })
</script>
<style scoped>
  .activity-route-map {
    position: relative;
    height: 320px;
    border-radius: 16px;
    overflow: hidden;
    background: var(--r-soft);
    isolation: isolate;
  }
  .activity-route-map.compact {
    height: 220px;
    pointer-events: none;
  }
  .activity-route-map.no-route {
    height: auto;
    min-height: 44px;
    display: flex;
    align-items: center;
    background: transparent;
    color: var(--r-muted);
    font-size: 12px;
  }
  .activity-route-map.expanded {
    position: fixed;
    inset: 20px;
    height: auto;
    z-index: 3000;
    box-shadow: 0 0 0 100vmax #16251f99;
  }
  .expand-map {
    position: absolute;
    right: 12px;
    bottom: calc(var(--route-legend-height) + 26px);
    z-index: 1000;
    min-height: 44px;
    padding: 0 16px;
    background: var(--r-surface);
    color: var(--r-ink);
    border: 1px solid var(--r-line);
    border-radius: 24px;
    font-weight: 650;
  }
  .route-legend {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: var(--route-legend-height);
    padding: 4px 10px;
    box-sizing: border-box;
    background: var(--r-surface);
    border-top: 1px solid var(--r-line);
    font-size: 10px;
  }
  .route-scale {
    display: flex;
    align-items: center;
    gap: 7px;
  }
  .route-scale select {
    min-height: 44px;
    border: 0;
    background: transparent;
    color: var(--r-ink);
    font-weight: 650;
    font-size: 12px;
    padding-right: 6px;
  }
  .route-legend small {
    color: var(--r-muted);
    font-size: 10px;
  }
  .intensity-ramp {
    width: 54px;
    height: 5px;
    border-radius: 5px;
    background: linear-gradient(
      to right,
      var(--r-route-0),
      var(--r-route-1),
      var(--r-route-2),
      var(--r-route-3),
      var(--r-route-4)
    );
  }
  .route-reading {
    margin-left: auto;
    font-size: 12px;
    font-weight: 650;
  }
  .map-status {
    position: absolute;
    left: 10px;
    top: 10px;
    z-index: 1000;
    max-width: 70%;
    padding: 6px 10px;
    background: var(--r-surface);
    color: var(--r-ink);
    font-size: 11px;
    border-radius: 6px;
  }
  :deep(.leaflet-tile-pane) {
    filter: var(--map-filter);
  }
  :deep(.leaflet-bar a) {
    background: var(--r-surface);
    color: var(--r-ink);
    border-color: var(--r-line);
  }
  :deep(.leaflet-control-attribution) {
    background: var(--r-surface);
    color: var(--r-muted);
  }
  :deep(.leaflet-control-attribution a) {
    color: var(--r-muted);
  }
</style>
