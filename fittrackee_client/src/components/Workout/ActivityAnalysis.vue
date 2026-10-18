<template>
  <section
    v-if="analysis"
    class="activity-analysis"
    aria-label="Activity analysis"
  >
    <div class="activity-overview">
      <div class="metrics-overview">
        <h2 class="sr-only">Workout metrics</h2>
        <div class="summary-grid">
          <div>
            <small>Distance</small
            ><strong
              >{{ (analysis.summary.distance_m / unitSize).toFixed(2) }}
              <small>{{ units }}</small></strong
            >
          </div>
          <div>
            <small>Active time</small
            ><strong>{{ clock(analysis.summary.active_s) }}</strong>
          </div>
          <div>
            <small>Active pace</small
            ><strong
              >{{
                pace(
                  analysis.summary.distance_m
                    ? (analysis.summary.active_s * 1000) /
                        analysis.summary.distance_m
                    : null
                )
              }}
              <small>/{{ units }}</small></strong
            >
          </div>
        </div>
        <div class="metrics-context">
          <p class="time-context">
            <span class="heart-context"
              ><RintIcon name="heart" />{{
                analysis.summary.averages.heart_rate?.toFixed(0) || '—'
              }}
              bpm avg.</span
            >
            <span class="clock-context">
              <RintIcon name="clock" />
              {{ clock(analysis.summary.elapsed_s) }} elapsed <span>·</span>
              {{ clock(analysis.summary.paused_s) }} paused
            </span>
          </p>
          <label
            ><span class="sr-only">Units</span
            ><select v-model="units">
              <option value="km">km</option>
              <option value="mi">mi</option>
            </select></label
          >
        </div>
      </div>
      <RouteTrace
        class="analysis-route"
        :points="analysis.recording.points"
        :selected-time="cursorTime"
        :units="units"
        @select-time="selectMapTime"
        @metric-change="metric = $event"
      />
    </div>
    <nav class="analysis-tabs activity-sections" aria-label="Activity section">
      <button
        v-for="tab in ['Charts', 'Best efforts', 'Splits & laps']"
        :key="tab"
        :class="{ selected: panel === tab }"
        :aria-pressed="panel === tab"
        @click="panel = tab"
      >
        {{ tab }}
      </button>
    </nav>
    <div
      v-if="panel === 'Charts'"
      class="chart-panel"
      :style="{ '--chart-color': metricColor }"
    >
      <div class="chart-toolbar">
        <div class="metric-tabs" role="group" aria-label="Chart metric">
          <button
            v-for="m in metrics.filter((candidate) => available(candidate.key))"
            :key="m.key"
            :class="{ selected: metric === m.key }"
            :aria-pressed="metric === m.key"
            @click="metric = m.key"
          >
            {{ m.label }}
          </button>
        </div>
        <button v-if="zoomed" @click="zoomed = false">Reset zoom</button>
      </div>
      <div v-if="selectedRange" class="selection-context">
        <span
          >{{
            selectedEffort
              ? effortDistance(selectedEffort.distance_m) + ' effort'
              : 'Selected interval'
          }}
          · {{ clock(start) }}–{{ clock(end) }}</span
        >
        <button @click="clearSelection">Clear</button>
      </div>
      <div class="chart-reading" aria-live="polite">
        <strong
          ><span class="sr-only">{{ metricLabel }} </span>{{ cursorValue }}
          <small>{{ metricUnit }}</small></strong
        >
        <time>{{ clock(cursorTime) }}</time>
      </div>
      <div class="contextual-readings">
        <span v-for="reading in contextualReadings" :key="reading.key">
          <small :title="reading.label">{{
            reading.key === 'distance'
              ? 'At'
              : reading.key === 'heart_rate'
                ? 'HR'
                : reading.label
          }}</small>
          <b>{{ reading.value }}</b>
        </span>
      </div>
      <svg
        ref="chart"
        :viewBox="`0 0 ${chartWidth} 220`"
        class="stream-chart"
        role="slider"
        :aria-label="`${metricLabel} over elapsed time`"
        :aria-valuemin="domain[0]"
        :aria-valuemax="domain[1]"
        :aria-valuenow="cursorTime"
        :aria-valuetext="`${clock(cursorTime)}, ${cursorValue} ${metricUnit}`"
        @click="tapPlot"
        @keydown="inspectKey"
        tabindex="0"
        @pointerdown="scrub"
        @pointermove="scrub"
        @pointerup="finishScrub"
        @pointercancel="finishScrub"
        @lostpointercapture="finishScrub"
      >
        <defs>
          <linearGradient :id="`fill-${workoutId}`" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" :stop-color="metricColor" stop-opacity=".28" />
            <stop offset="1" :stop-color="metricColor" stop-opacity="0" />
          </linearGradient>
        </defs>
        <line
          v-for="y in [30, 80, 130, 180]"
          :key="y"
          x1="42"
          :x2="chartWidth - 10"
          :y1="y"
          :y2="y"
          stroke="var(--r-line)"
        />
        <text x="2" y="24" class="axis-text">{{ axisValue(bounds[1]) }}</text>
        <text x="2" y="184" class="axis-text">{{ axisValue(bounds[0]) }}</text>
        <rect
          v-if="selectedRange"
          :x="Math.max(42, x(start))"
          y="15"
          :width="
            Math.max(
              0,
              Math.min(chartWidth - 10, x(end)) - Math.max(42, x(start))
            )
          "
          height="170"
          :fill="metricColor"
          opacity=".1"
        />
        <path :d="area" :fill="`url(#fill-${workoutId})`" />
        <path
          :d="primaryPath"
          fill="none"
          :stroke="metricColor"
          stroke-width="2.5"
        />
        <path
          v-if="comparison"
          :d="comparisonPath"
          fill="none"
          stroke="#ce802e"
          stroke-width="2"
          stroke-dasharray="5 4"
        />
        <line
          :x1="x(cursorTime)"
          :x2="x(cursorTime)"
          y1="15"
          y2="185"
          stroke="var(--r-muted)"
          stroke-dasharray="3 3"
        />
        <circle
          v-if="cursorReading"
          :cx="x(cursorTime)"
          :cy="y(cursorReading.v)"
          r="4"
          :fill="metricColor"
          stroke="var(--r-surface)"
          stroke-width="2"
        />
        <text x="42" y="210" class="axis-text">{{ clock(domain[0]) }}</text>
        <text :x="chartWidth - 10" y="210" class="axis-text" text-anchor="end">
          {{ clock(domain[1]) }}
        </text>
      </svg>

      <div v-if="metric === 'pace'" class="pace-method">
        <span>{{
          clippedReadings && !fullPaceRange
            ? `${clippedReadings} slow readings beyond this scale`
            : '30-second pace'
        }}</span
        ><button @click="fullPaceRange = !fullPaceRange">
          {{ fullPaceRange ? 'Focus scale' : 'Full range' }}
        </button>
      </div>
      <details class="interval-details">
        <summary>Analyze an interval</summary>
        <div class="interval-controls">
          <label
            >Interval start · {{ clock(start)
            }}<input
              type="range"
              v-model.number="start"
              :min="analysis.summary.start"
              :max="end - 1" /></label
          ><label
            >Interval end · {{ clock(end)
            }}<input
              type="range"
              v-model.number="end"
              :min="start + 1"
              :max="analysis.summary.end" /></label
          ><button @click="selectInterval">Analyze interval</button>
        </div>
        <p v-if="selectedInterval" class="interval-result">
          Selected interval: {{ clock(selectedInterval.elapsed_s) }} ·
          {{ (selectedInterval.distance_m / unitSize).toFixed(2) }}
          {{ units }} · {{ pace(selectedInterval.pace_s_km) }} /{{ units
          }}<span v-for="(v, k) in selectedInterval.averages" :key="k">
            · {{ k.replace('_', ' ') }} {{ v.toFixed(0) }}</span
          >
        </p>
        <button @click="zoomed = !zoomed">
          {{ zoomed ? 'Reset zoom' : 'Zoom to selection' }}
        </button>
      </details>
    </div>

    <details v-if="panel === 'Charts'" @toggle="loadComparisonChoices">
      <summary>Compare another activity</summary>
      <label
        >Activity<select v-model="comparisonId" @change="loadComparison">
          <option value="">No comparison</option>
          <option v-for="w in choices" :key="w.id" :value="w.id">
            {{ w.title }}
          </option>
        </select></label
      >
      <p v-if="comparison">
        Solid line: this activity. Dashed amber: comparison. Both use elapsed
        time from the start.
      </p>
    </details>
    <section v-if="panel === 'Splits & laps'" class="split-panel">
      <nav class="analysis-tabs" aria-label="Analysis tables">
        <button
          v-for="tab in ['Splits', 'Device laps']"
          :key="tab"
          :class="{ selected: table === tab }"
          :aria-pressed="table === tab"
          @click="table = tab"
        >
          {{ tab }}
        </button>
      </nav>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>{{ table === 'Splits' ? 'Split' : 'Lap' }}</th>
              <th>Distance</th>
              <th>Elapsed</th>
              <th>Pace /{{ units }}</th>
              <th>HR</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in tableRows" :key="i">
              <th>
                <button
                  class="split-link"
                  @click="selectRange(row.start, row.end)"
                >
                  {{ row.name || i + 1
                  }}<small v-if="row.complete === false"> partial</small
                  ><span class="sr-only"> · inspect on chart</span>
                </button>
              </th>
              <td>{{ (row.distance_m / unitSize).toFixed(2) }} {{ units }}</td>
              <td>{{ clock(row.elapsed_s) }}</td>
              <td>{{ pace(row.pace_s_km) }}</td>
              <td>{{ row.averages.heart_rate?.toFixed(0) || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
    <section v-if="panel === 'Best efforts'" class="workout-efforts">
      <h2 class="sr-only">Best efforts</h2>
      <p class="scrub-hint">Elapsed time includes pauses.</p>
      <div class="effort-grid">
        <button
          v-for="effort in analysis.best_efforts"
          :key="effort.distance_m"
          @click="selectRange(effort.start, effort.end)"
        >
          <span class="effort-heading"
            ><b>{{ effortDistance(effort.distance_m) }}</b
            ><span
              v-if="
                isOwner &&
                personalBests.some(
                  (b) =>
                    b.sport_id === sportId &&
                    b.distance_m === effort.distance_m &&
                    Math.abs(b.elapsed_s - effort.elapsed_s) <= 0.01
                )
              "
              class="effort-record"
              ><RintIcon name="trophy" /> All-time best</span
            ></span
          >
          <strong>{{ clock(effort.elapsed_s) }}</strong
          ><span
            >{{ pace((effort.elapsed_s * 1000) / effort.distance_m) }} /{{
              units
            }}</span
          ><small>{{ clock(effort.start) }} – {{ clock(effort.end) }}</small>
        </button>
      </div>
      <router-link
        v-if="isOwner"
        :to="{
          path: '/progress',
          query: { view: 'records', sport_id: String(sportId || 0) },
        }"
        class="all-records-link"
        >View all-time records <RintIcon name="arrow"
      /></router-link>
    </section>
    <p v-if="panel === 'Splits & laps' && !tableRows.length">
      {{
        table === 'Device laps'
          ? 'This recording has no device laps.'
          : 'Distance splits are unavailable for this recording.'
      }}
    </p>
    <p v-if="panel === 'Best efforts' && !analysis.best_efforts.length">
      No qualifying sustained distance effort. Missing samples and indoor
      workouts without distance are never treated as records.
    </p>
    <details>
      <summary>How these numbers are calculated</summary>
      <p
        v-if="analysis.summary.active_energy_kcal !== undefined"
        class="eyebrow"
      >
        Active energy:
        {{ Math.round(analysis.summary.active_energy_kcal) }} kcal · reported by
        Health
      </p>
      <p
        v-if="analysis.summary.health_reported_active_s !== undefined"
        class="health-context"
      >
        Health active time:
        {{ clock(analysis.summary.health_reported_active_s) }}
      </p>

      <p>
        Elapsed time includes pauses. Moving time counts active, observed
        intervals with distance progress. Sensor averages are weighted by time
        and include only intervals with observations at both ends. Splits use
        interpolated distance crossings. Best efforts include pauses and exclude
        sampling gaps over 60 seconds. Method {{ analysis.method_version }}.
      </p>
      <ul>
        <li v-for="warning in analysis.warnings" :key="warning">
          {{ warning }}
        </li>
      </ul>
    </details>
    <details v-if="isOwner" class="ownership" id="sharing" ref="sharingPanel">
      <summary>Sharing & exports</summary>
      <div>
        <button @click="download('csv')">Export samples CSV</button
        ><button @click="download('json')">
          Export original streams + analysis
        </button>
      </div>
      <label
        >Activity visibility<select v-model="visibility">
          <option value="private">Only me</option>
          <option value="followers_only">Followers</option>
          <option value="public">Everyone</option>
        </select></label
      ><label
        >Route visibility<select v-model="mapVisibility">
          <option value="private">Only me</option>
          <option value="followers_only">Followers</option>
          <option value="public">Everyone</option>
        </select></label
      ><label
        >Protect start and finish (metres)<input
          v-model.number="privacyRadius"
          type="number"
          min="200"
          max="10000"
          step="100"
      /></label>
      <p>
        At least 200 m around both route endpoints stays hidden from other
        people. Photos are shared with the activity; their location metadata is
        removed during migration.
      </p>
      <button
        class="primary r-primary"
        :disabled="saving || !sharingLoaded"
        @click="share"
      >
        {{ saving ? 'Saving…' : 'Save sharing settings' }}</button
      ><button @click="copyLink">Copy activity link</button>
      <p role="status">{{ message }}</p>
    </details>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
  </section>
  <p v-else-if="loading" class="analysis-loading" role="status">
    Loading activity analysis…
  </p>
  <p v-else-if="error && isOwner" class="analysis-loading">{{ error }}</p>
</template>
<script setup lang="ts">
  import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
  import { useRoute } from 'vue-router'

  import authApi from '@/api/authApi'
  import RintIcon from '@/components/Rint/RintIcon.vue'
  import RouteTrace from '@/components/Rint/RouteTrace.vue'
  import useAuthUser from '@/composables/useAuthUser'
  import type { Analysis, Interval } from '@/types/rint'
  import {
    metricSeries,
    nearestValue,
    sampleEnvelope,
    seriesBounds,
  } from '@/utils/activityStream'
  import { effortDistance } from '@/utils/trainingHistory'
  const props = defineProps<{
    workoutId: string
    sportId?: number
    isOwner: boolean
    initialVisibility?: string
    initialMapVisibility?: string
  }>()
  const panel = ref('Charts'),
    selectedRange = ref(false),
    fullPaceRange = ref(false)
  const personalBests = ref<
    { sport_id: number; distance_m: number; elapsed_s: number }[]
  >([])
  const analysis = ref<Analysis | null>(null),
    comparison = ref<Analysis | null>(null),
    selectedInterval = ref<Interval | null>(null)
  const route = useRoute()
  const sharingPanel = ref<HTMLDetailsElement | null>(null)
  watch(
    [() => route.hash, sharingPanel],
    async ([hash, panel]) => {
      if (hash === '#sharing' && panel) {
        panel.open = true
        await nextTick()
        panel.scrollIntoView({ block: 'start', behavior: 'smooth' })
      }
    },
    { immediate: true }
  )
  const chart = ref<SVGSVGElement | null>(null),
    chartWidth = ref(800)
  let chartObserver: ResizeObserver | undefined
  watch(chart, (element) => {
    chartObserver?.disconnect()
    if (!element) return
    chartObserver = new ResizeObserver(([entry]) => {
      chartWidth.value = Math.max(250, entry.contentRect.width)
    })
    chartObserver.observe(element)
  })
  onBeforeUnmount(() => chartObserver?.disconnect())
  const saving = ref(false),
    sharingLoaded = ref(false)
  const { imperialUnits } = useAuthUser()
  const metricColor = computed(() =>
    metric.value === 'heart_rate'
      ? 'var(--r-heart)'
      : metric.value === 'power'
        ? 'var(--r-power)'
        : metric.value === 'elevation'
          ? 'var(--r-action)'
          : 'var(--r-violet)'
  )
  function axisValue(v: number) {
    return metric.value === 'pace' ? clock(v * 60) : v.toFixed(0)
  }
  const loading = ref(false),
    error = ref(''),
    message = ref(''),
    units = ref(imperialUnits.value ? 'mi' : 'km'),
    metric = ref('pace'),
    table = ref('Splits'),
    start = ref(0),
    end = ref(1),
    cursorTime = ref(0),
    zoomed = ref(false)
  const comparisonId = ref(''),
    choices = ref<{ id: string; title: string }[]>([]),
    visibility = ref(props.initialVisibility || 'private'),
    mapVisibility = ref(props.initialMapVisibility || 'private'),
    privacyRadius = ref(200)
  const metrics = [
    { key: 'pace', label: 'Pace', unit: 'min/km' },
    { key: 'heart_rate', label: 'Heart rate', unit: 'bpm' },
    { key: 'elevation', label: 'Elevation', unit: 'm' },
    { key: 'cadence', label: 'Cadence', unit: 'counts/min' },
    { key: 'power', label: 'Power', unit: 'W' },
  ]
  const unitSize = computed(() => (units.value === 'km' ? 1000 : 1609.344))
  const metricLabel = computed(
      () => metrics.find((m) => m.key === metric.value)?.label
    ),
    metricUnit = computed(() =>
      metric.value === 'pace'
        ? `min/${units.value}`
        : metrics.find((m) => m.key === metric.value)?.unit
    )
  function values(data: Analysis) {
    return data === analysis.value
      ? primaryValues.value
      : comparisonValues.value
  }
  const streams = computed(() =>
    Object.fromEntries(
      [...metrics.map((m) => m.key), 'd'].map((key) => [
        key,
        key === 'pace' && analysis.value?.recording.summary_only
          ? []
          : metricSeries(
              analysis.value?.recording.points || [],
              key,
              unitSize.value
            ),
      ])
    )
  )
  const primaryValues = computed(() => streams.value[metric.value] || [])
  const comparisonValues = computed(() =>
    metric.value === 'pace' && comparison.value?.recording.summary_only
      ? []
      : metricSeries(
          comparison.value?.recording.points || [],
          metric.value,
          unitSize.value
        )
  )
  function available(key: string) {
    if (key === 'pace' && analysis.value?.recording.summary_only) return false
    return Boolean(streams.value[key]?.length)
  }
  const domain = computed(() =>
    zoomed.value
      ? [start.value, end.value]
      : [analysis.value?.summary.start || 0, analysis.value?.summary.end || 1]
  )
  const bounds = computed(() => {
    const v = [
      ...(analysis.value ? values(analysis.value) : []),
      ...(comparison.value ? values(comparison.value) : []),
    ]
      .filter((p) => p.t >= domain.value[0] && p.t <= domain.value[1])
      .map((p) => p.v)
    return seriesBounds(
      v.map((v) => ({ t: 0, v, segment: 0 })),
      metric.value,
      fullPaceRange.value
    )
  })
  const clippedReadings = computed(
    () => primaryValues.value.filter((p) => p.v > bounds.value[1]).length
  )

  const x = (t: number) =>
    42 +
    ((t - domain.value[0]) / (domain.value[1] - domain.value[0])) *
      (chartWidth.value - 52)
  const y = (v: number) =>
    180 -
    ((Math.min(bounds.value[1], Math.max(bounds.value[0], v)) -
      bounds.value[0]) /
      (bounds.value[1] - bounds.value[0])) *
      155
  function pathFor(data: Analysis, fill = false) {
    const all = sampleEnvelope(
      values(data).filter(
        (p) => p.t >= domain.value[0] && p.t <= domain.value[1]
      )
    )
    return all
      .map((p, i, rows) => {
        const begins = !i || p.segment !== rows[i - 1].segment
        const ends = i === rows.length - 1 || p.segment !== rows[i + 1].segment
        const px = x(p.t).toFixed(2)
        return `${begins ? (fill ? `M${px},180 L` : 'M') : 'L'}${px},${y(p.v).toFixed(2)}${fill && ends ? ` L${px},180 Z` : ''}`
      })
      .join(' ')
  }
  const area = computed(() =>
    analysis.value ? pathFor(analysis.value, true) : ''
  )
  const primaryPath = computed(() =>
    analysis.value ? pathFor(analysis.value) : ''
  )
  const comparisonPath = computed(() =>
    comparison.value ? pathFor(comparison.value) : ''
  )
  const cursorReading = computed(() =>
    nearestValue(primaryValues.value, cursorTime.value)
  )
  const selectedEffort = computed(() =>
    analysis.value?.best_efforts.find(
      (effort) => effort.start === start.value && effort.end === end.value
    )
  )
  const contextualReadings = computed(() => {
    const rows = ['pace', 'heart_rate', 'power']
      .filter((key) => key !== metric.value && available(key))
      .map((key) => {
        const point = nearestValue(streams.value[key], cursorTime.value)
        const info = metrics.find((m) => m.key === key)!
        return {
          key,
          label: info.label,
          value: point
            ? key === 'pace'
              ? `${clock(point.v * 60)} /${units.value}`
              : `${point.v.toFixed(0)} ${info.unit}`
            : '—',
        }
      })
    const distance = nearestValue(streams.value.d, cursorTime.value)
    if (distance)
      rows.unshift({
        key: 'd',
        label: 'Distance',
        value: `${(distance.v / unitSize.value).toFixed(2)} ${units.value}`,
      })
    return rows
  })
  const cursorValue = computed(() => {
    if (!analysis.value) return '—'
    const p = cursorReading.value
    return p
      ? metric.value === 'pace'
        ? clock(p.v * 60)
        : p.v.toFixed(0)
      : '—'
  })
  const tableRows = computed(() =>
    !analysis.value
      ? []
      : table.value === 'Device laps'
        ? analysis.value.laps
        : units.value === 'km'
          ? analysis.value.splits_km
          : analysis.value.splits_mile
  )
  function clock(n: number) {
    const s = Math.round(n)
    const minutes = String(Math.floor(s / 60) % 60).padStart(2, '0')
    return (
      (s >= 3600 ? `${Math.floor(s / 3600)}:` : '') +
      minutes +
      ':' +
      String(s % 60).padStart(2, '0')
    )
  }
  function pace(n: number | null) {
    return n === null ? '—' : clock((n * unitSize.value) / 1000)
  }
  function explain(e: unknown) {
    return (
      (e as { response?: { data?: { message?: string } } }).response?.data
        ?.message || 'Unable to connect. Please try again.'
    )
  }
  watch(
    () => props.workoutId,
    async (id) => {
      loading.value = true
      error.value = ''
      analysis.value = null
      sharingLoaded.value = false
      if (props.isOwner) {
        authApi
          .get(`rint/activities/${id}/sharing`)
          .then(({ data }) => {
            if (id !== props.workoutId) return
            visibility.value = data.data.visibility
            mapVisibility.value = data.data.map_visibility
            privacyRadius.value = data.data.privacy_radius_m
            sharingLoaded.value = true
          })
          .catch((e) => {
            error.value = explain(e)
          })
      }
      try {
        analysis.value = (
          await authApi.get(`rint/activities/${id}/analysis`)
        ).data.data
        start.value = analysis.value!.summary.start
        end.value = analysis.value!.summary.end
        if (!available(metric.value))
          metric.value = metrics.find((m) => available(m.key))?.key || 'pace'
        cursorTime.value = primaryValues.value[0]?.t ?? start.value
        if (props.isOwner) {
          try {
            personalBests.value = (await authApi.get('rint/bests')).data.data
          } catch {
            personalBests.value = []
          }
        }
        await applyEffortLink()
      } catch (e) {
        error.value = explain(e)
      } finally {
        loading.value = false
      }
    },
    { immediate: true }
  )
  async function selectRange(from: number, to: number) {
    start.value = from
    end.value = to
    selectedRange.value = true
    zoomed.value = true
    panel.value = 'Charts'
    cursorTime.value =
      primaryValues.value.find((p) => p.t >= from && p.t <= to)?.t ?? from
    await nextTick()
    chart.value?.scrollIntoView({
      block: 'center',
      behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches
        ? 'auto'
        : 'smooth',
    })
  }
  async function applyEffortLink() {
    if (!route.hash.startsWith('#effort-')) return
    const effort = analysis.value?.best_efforts.find(
      (p) => p.distance_m === Number(route.hash.slice(8))
    )
    if (effort) await selectRange(effort.start, effort.end)
  }
  watch(() => route.hash, applyEffortLink)
  let dragging = false
  function selectMapTime(time: number) {
    panel.value = 'Charts'
    cursorTime.value = nearestValue(primaryValues.value, time)?.t ?? time
  }
  function clearSelection() {
    selectedRange.value = false
    zoomed.value = false
  }
  function tapPlot(e: MouseEvent) {
    selectPlot(e.clientX, e.currentTarget as SVGElement)
  }
  function inspectKey(e: KeyboardEvent) {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) return
    e.preventDefault()
    const time =
      e.key === 'Home'
        ? domain.value[0]
        : e.key === 'End'
          ? domain.value[1]
          : cursorTime.value + (e.key === 'ArrowRight' ? 10 : -10)
    cursorTime.value = Math.min(
      domain.value[1],
      Math.max(domain.value[0], time)
    )
  }
  function selectPlot(clientX: number, target: SVGElement) {
    const box = target.getBoundingClientRect()
    const time = Math.max(
      domain.value[0],
      Math.min(
        domain.value[1],
        domain.value[0] +
          ((((clientX - box.left) / box.width) * chartWidth.value - 42) /
            (chartWidth.value - 52)) *
            (domain.value[1] - domain.value[0])
      )
    )
    cursorTime.value = nearestValue(primaryValues.value, time)?.t ?? time
  }
  function scrub(e: PointerEvent) {
    if (e.type === 'pointerdown') {
      dragging = true
      ;(e.currentTarget as SVGElement).setPointerCapture(e.pointerId)
    }
    if (!dragging) return
    selectPlot(e.clientX, e.currentTarget as SVGElement)
  }
  function finishScrub() {
    dragging = false
  }
  async function selectInterval() {
    selectedRange.value = true
    try {
      selectedInterval.value = (
        await authApi.post(`rint/activities/${props.workoutId}/interval`, {
          start: start.value,
          end: end.value,
        })
      ).data.data
    } catch (e) {
      error.value = explain(e)
    }
  }
  async function loadComparisonChoices() {
    if (choices.value.length || !props.isOwner) return
    try {
      choices.value = (
        await authApi.get('workouts', { params: { per_page: 100 } })
      ).data.data.workouts.filter(
        (w: { id: string }) => w.id !== props.workoutId
      )
    } catch (e) {
      error.value = explain(e)
    }
  }
  async function loadComparison() {
    comparison.value = null
    if (!comparisonId.value) return
    try {
      comparison.value = (
        await authApi.get(`rint/activities/${comparisonId.value}/analysis`)
      ).data.data
    } catch (e) {
      error.value = explain(e)
    }
  }
  async function download(format: string) {
    try {
      const data = (
        await authApi.get(`rint/activities/${props.workoutId}/export`, {
          params: { format },
          responseType: 'blob',
        })
      ).data
      const url = URL.createObjectURL(data)
      const a = document.createElement('a')
      a.href = url
      a.download = `activity-${props.workoutId}.${format}`
      a.click()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (e) {
      error.value = explain(e)
    }
  }
  async function share() {
    saving.value = true
    message.value = ''
    try {
      await authApi.post(`rint/activities/${props.workoutId}/sharing`, {
        visibility: visibility.value,
        map_visibility: mapVisibility.value,
        privacy_radius_m: privacyRadius.value,
      })
      message.value =
        'Sharing settings saved. Your link follows these privacy settings.'
    } catch (e) {
      error.value = explain(e)
    } finally {
      saving.value = false
    }
  }
  async function copyLink() {
    try {
      await navigator.clipboard.writeText(
        `${location.origin}/workouts/${props.workoutId}`
      )
      message.value =
        'Link copied. Your privacy settings determine who can open it.'
    } catch {
      message.value = `${location.origin}/workouts/${props.workoutId}`
    }
  }
</script>
<style scoped>
  .activity-sections {
    display: flex;
    margin: 20px 0;
  }
  .activity-sections button {
    flex: 1;
    min-height: 44px;
  }
  .pace-method {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    font-size: 11px;
    color: var(--r-muted);
  }
  .pace-method button,
  .split-link {
    min-height: 44px;
    border: 0;
    background: transparent;
    color: var(--r-action);
    font-weight: 650;
  }
  .effort-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 14px;
  }
  .effort-grid > button {
    display: grid;
    gap: 12px;
    text-align: left;
    padding: 20px;
    border: 1px solid var(--r-line);
    border-radius: 18px;
    background: var(--r-surface);
    color: var(--r-ink);
  }
  .effort-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
  }
  .effort-grid strong {
    font-size: 32px;
    letter-spacing: -1px;
    font-variant-numeric: tabular-nums;
  }
  .effort-grid small,
  .effort-grid button > span:not(.effort-heading) {
    font-size: 12px;
    color: var(--r-muted);
  }
  .effort-record {
    font-size: 10px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    color: var(--r-power);
  }
  .all-records-link {
    display: inline-flex;
    gap: 10px;
    align-items: center;
    min-height: 44px;
    margin-top: 16px;
    font-weight: 650;
    color: var(--r-action);
  }

  .activity-analysis {
    margin: 18px 0;
    color: var(--r-ink);
  }
  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }
  h2 {
    font-size: 16px;
    letter-spacing: -0.8px;
    margin: 6px 0 12px;
  }
  .eyebrow {
    font-size: 10px;
    letter-spacing: 0.12em;
    color: var(--r-muted);
    font-weight: 700;
  }
  .summary-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 24px;
    padding: 12px 0 18px;
  }
  .summary-grid > div + div {
    border-left: 1px solid var(--r-line);
    padding-left: 24px;
  }
  .summary-grid small {
    display: block;
    color: var(--r-muted);
    font-size: 11px;
    margin-bottom: 8px;
  }
  .summary-grid strong {
    display: block;
    font-size: 32px;
    font-weight: 650;
    letter-spacing: -1px;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }
  .summary-grid strong small {
    display: inline;
    font-weight: 400;
    font-size: 12px;
    letter-spacing: 0;
  }
  .time-context {
    display: flex;
    align-items: center;
    gap: 9px;
    font-size: 12px;
    color: var(--r-muted);
    margin: 0 0 14px;
  }
  .time-context svg {
    width: 16px;
    height: 16px;
  }
  .health-context {
    font-size: 12px;
    color: var(--r-muted);
    line-height: 1.5;
    margin: 6px 0;
  }
  .chart-panel {
    background: var(--r-surface);
    border: 1px solid var(--r-line);
    border-radius: 14px;
    padding: 20px 24px 12px;
  }
  .chart-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }
  .metric-tabs {
    display: flex;
    gap: 6px;
    overflow: auto;
    scrollbar-width: thin;
  }
  .metric-tabs button {
    border: 0;
    min-width: max-content;
    padding: 10px 12px;
    background: transparent;
    color: var(--r-muted);
    border-radius: 100px;
    font-size: 12px;
  }
  .metric-tabs button.selected {
    background: var(--r-soft);
    color: var(--r-ink);
    font-weight: 700;
  }
  .metric-tabs button:disabled {
    opacity: 0.45;
  }
  button {
    min-height: 44px;
    box-shadow: none;
    border: 1px solid var(--r-line);
    border-radius: 100px;
    padding: 10px 16px;
    background: var(--r-surface);
    color: var(--r-ink);
    font-size: 12px;
    cursor: pointer;
  }
  button:disabled {
    opacity: 0.5;
  }
  .primary {
    background: var(--r-accent);
    color: #202719;
    border: 0;
  }
  .selection-context {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    width: 100%;
    font-size: 11px;
    color: var(--r-muted);
  }
  .selection-context button {
    border: 0;
    padding: 8px;
  }
  .contextual-readings {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 16px;
    margin-bottom: 8px;
    font-size: 12px;
    font-variant-numeric: tabular-nums;
  }
  .contextual-readings small {
    color: var(--r-muted);
    font-size: 11px;
    margin-right: 4px;
  }
  .chart-reading {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    margin: 14px 0 10px;
    font-variant-numeric: tabular-nums;
    align-items: center;
  }
  .chart-reading strong {
    font-size: 14px;
    font-weight: 650;
  }
  .chart-reading span {
    color: var(--chart-color);
    font-size: 14px;
    font-weight: 650;
  }
  .stream-chart {
    width: 100%;
    height: 220px;
    touch-action: pan-y;
    user-select: none;
  }
  .axis-text {
    font-size: 11px;
    fill: var(--r-muted);
  }
  .scrub-hint {
    font-size: 11px;
    color: var(--r-muted);
    text-align: center;
  }
  input[type='range'] {
    width: 100%;
    box-sizing: border-box;
    margin: 0;
    accent-color: var(--r-violet);
    min-height: 44px;
    padding: 0;
  }
  .interval-controls {
    display: flex;
    gap: 16px;
    align-items: center;
    flex-wrap: wrap;
  }
  .interval-controls label {
    flex: 1;
    min-width: 130px;
  }
  label {
    display: block;
    color: var(--r-muted);
    font-size: 11px;
    font-weight: 600;
  }
  select,
  input[type='number'] {
    display: block;
    margin-top: 8px;
    min-height: 44px;
    border: 1px solid var(--r-line);
    border-radius: 10px;
    padding: 10px;
    background: var(--r-surface);
    color: var(--r-ink);
    box-sizing: border-box;
    max-width: 100%;
  }
  .interval-result {
    background: var(--r-soft);
    border-radius: 10px;
    padding: 16px;
    font-size: 13px;
  }
  details {
    margin: 12px 0;
    line-height: 1.6;
    font-size: 13px;
  }
  summary {
    min-height: 44px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 600;
  }
  summary::after {
    content: '+';
    margin-left: auto;
    color: var(--r-muted);
    font-size: 20px;
  }
  details[open] > summary::after {
    content: '−';
  }
  .interval-details {
    border-top: 1px solid var(--r-line);
  }
  .route-details,
  .ownership {
    border-bottom: 1px solid var(--r-line);
    padding: 6px 0;
  }
  .analysis-tabs {
    display: flex;
    border-bottom: 1px solid var(--r-line);
    gap: 8px;
    margin-top: 32px;
  }
  .analysis-tabs button {
    background: transparent;
    border: 0;
    border-radius: 0;
    padding: 12px 16px;
    color: var(--r-muted);
  }
  .analysis-tabs .selected {
    border-bottom: 2px solid var(--r-ink);
    font-weight: 700;
    color: var(--r-ink);
  }
  .table-scroll {
    overflow: auto;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    font-variant-numeric: tabular-nums;
  }
  th,
  td {
    padding: 16px 12px;
    text-align: left;
    border-bottom: 1px solid var(--r-line);
    white-space: nowrap;
  }
  thead th {
    color: var(--r-muted);
    font-weight: 500;
    font-size: 11px;
  }
  tbody th {
    font-weight: 650;
  }
  tbody tr:hover {
    background: var(--r-soft);
  }
  th small {
    font-weight: 400;
    color: var(--r-muted);
  }
  .ownership summary {
    font-size: 17px;
    letter-spacing: -0.3px;
    flex-wrap: wrap;
  }
  .ownership summary span {
    font-size: 11px;
    color: var(--r-muted);
    font-weight: 400;
    letter-spacing: 0;
  }
  .ownership label {
    display: inline-block;
    margin: 16px 18px 10px 0;
  }
  .ownership p {
    color: var(--r-muted);
    font-size: 12px;
  }
  .ownership button {
    margin: 8px 8px 8px 0;
  }
  .error {
    color: var(--r-heart);
  }
  .analysis-loading {
    padding: 24px;
    color: var(--r-muted);
  }
  @media (max-width: 700px) {
    h2 {
      font-size: 21px;
    }
    header > label {
      font-size: 0;
    }
    header select {
      font-size: 11px;
      margin: 0;
      max-width: 110px;
    }
    .summary-grid {
      grid-template-columns: 1fr 1fr;
      gap: 22px 12px;
      padding: 12px 0 22px;
    }
    .summary-grid > div + div {
      border: 0;
      padding: 0;
    }
    .summary-grid strong {
      font-size: 30px;
    }
    .summary-grid small {
      font-size: 11px;
    }
    .chart-panel {
      padding: 14px 14px 8px;
      margin: 0 -4px;
    }
    .metric-tabs {
      gap: 0;
    }
    .metric-tabs button {
      padding: 10px;
      font-size: 11px;
    }
    .chart-reading {
      flex-wrap: wrap;
      margin: 22px 0 8px;
    }
    .chart-reading span {
      font-size: 13px;
    }
    .analysis-tabs {
      gap: 0;
    }
    .analysis-tabs button {
      flex: 1;
      padding: 12px 8px;
      font-size: 11px;
    }
    th,
    td {
      padding: 14px 10px;
      font-size: 12px;
    }
    .ownership label {
      display: block;
      margin: 16px 0;
    }
    .ownership select {
      width: 100%;
    }
    .ownership summary span {
      display: none;
    }
    .time-context {
      font-size: 11px;
      gap: 6px;
    }
  }
</style>

<style scoped>
  .activity-analysis {
    margin: 10px 0;
  }
  .metrics-overview {
    position: relative;
  }
  .metrics-context {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: center;
    gap: 8px;
    padding-bottom: 8px;
  }
  .metrics-context label {
    font-size: 12px;
  }
  .metrics-overview select {
    min-height: 44px;
    margin: 0;
    padding: 6px;
    font-size: 12px;
  }
  .summary-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 14px;
    padding: 8px 0 10px;
  }
  .summary-grid > div + div {
    padding-left: 14px;
  }
  .summary-grid strong {
    font-size: 29px;
  }
  .summary-grid small {
    margin-bottom: 4px;
    font-size: 12px;
  }
  .time-context {
    flex-wrap: wrap;
    gap: 6px 14px;
    margin: 0;
    line-height: 1.4;
  }
  .time-context > span {
    display: inline-flex;
    align-items: center;
    gap: 5px;
  }
  .heart-context {
    color: var(--r-heart);
  }
  .analysis-route {
    min-height: 0;
  }
  .analysis-route :deep(.activity-route-map:not(.expanded)) {
    height: 224px;
  }
  .activity-sections {
    margin: 10px 0 8px;
  }
  .split-panel .analysis-tabs {
    margin: 0 0 8px;
  }
  .split-panel tbody th {
    padding: 0 12px;
  }
  .split-panel tbody td {
    padding: 8px 12px;
  }
  .chart-panel {
    padding: 10px 12px 8px;
    margin: 0;
  }
  .chart-reading {
    margin: 8px 0 4px;
  }
  .chart-reading strong {
    font-size: 25px;
    color: var(--chart-color);
    letter-spacing: -0.6px;
  }
  .chart-reading small {
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0;
  }
  .chart-reading time {
    font-size: 13px;
    color: var(--r-muted);
  }
  .contextual-readings {
    gap: 6px 12px;
  }
  .contextual-readings > span {
    white-space: nowrap;
  }

  .effort-grid {
    display: block;
    border-top: 1px solid var(--r-line);
  }
  .effort-grid > button {
    width: 100%;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 4px 12px;
    border: 0;
    border-bottom: 1px solid var(--r-line);
    border-radius: 0;
    background: transparent;
    padding: 12px 0;
    min-height: 64px;
  }
  .effort-heading {
    grid-column: 1;
    grid-row: 1;
    justify-content: flex-start;
    flex-wrap: wrap;
  }
  .effort-grid strong {
    grid-column: 2;
    grid-row: 1;
    font-size: 25px;
    text-align: right;
  }
  .effort-grid button > span:not(.effort-heading) {
    grid-column: 2;
    grid-row: 2;
    text-align: right;
  }
  .effort-grid button > small {
    grid-column: 1;
    grid-row: 2;
    align-self: center;
  }
  @media (max-width: 700px) {
    .summary-grid {
      gap: 10px;
      padding: 8px 0;
    }
    .summary-grid > div + div {
      padding-left: 10px;
      border-left: 1px solid var(--r-line);
    }
    .summary-grid strong {
      font-size: clamp(22px, 6.5vw, 27px);
      letter-spacing: -0.7px;
      white-space: normal;
    }
    .summary-grid strong small {
      font-size: 11px;
    }
    .summary-grid small {
      font-size: 11px;
    }
    .analysis-route :deep(.activity-route-map:not(.expanded)) {
      height: 204px;
    }
    .chart-reading {
      margin: 6px 0 4px;
    }
    .metric-tabs button {
      min-height: 44px;
      padding: 6px 9px;
      font-size: 12px;
    }
    .chart-toolbar {
      flex-wrap: wrap;
      gap: 4px;
    }
    .metric-tabs {
      flex-wrap: wrap;
      overflow: visible;
      gap: 2px;
    }
    .chart-toolbar > button {
      margin-left: auto;
      padding: 6px 10px;
    }
    .time-context {
      font-size: 11px;
    }
  }
  @media (min-width: 1000px) {
    .activity-analysis {
      display: grid;
      grid-template-columns: minmax(0, 1.4fr) minmax(270px, 1fr);
      column-gap: 24px;
      row-gap: 10px;
      align-items: start;
    }
    .activity-analysis > * {
      grid-column: 1 / -1;
    }
    .activity-overview {
      display: contents;
    }
    .metrics-overview {
      grid-column: 1;
      grid-row: 1;
    }
    .analysis-route {
      grid-column: 2;
      grid-row: 1 / span 3;
      align-self: stretch;
      max-height: 540px;
    }
    .analysis-route :deep(.activity-route-map:not(.expanded)) {
      height: 100%;
      min-height: 420px;
    }
    .activity-sections {
      grid-column: 1;
      grid-row: 2;
      margin: 0;
    }
    .chart-panel,
    .workout-efforts,
    .split-panel {
      grid-column: 1;
      grid-row: 3;
    }
    .chart-panel {
      min-width: 0;
    }
    .summary-grid strong {
      font-size: 27px;
    }
  }
</style>
