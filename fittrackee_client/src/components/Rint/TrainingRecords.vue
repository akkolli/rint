<template>
  <section
    v-for="group in groups"
    :key="group.sport"
    class="benchmarks"
    :aria-label="`${group.label} all-time records`"
  >
    <h3 v-if="!sportId">{{ group.label }}</h3>
    <div class="benchmark-overview">
      <div class="benchmark-hero">
        <div>
          <p>
            <RintIcon name="trophy" />
            {{ effortDistance(chosen(group).distance_m) }} best
          </p>
          <strong>{{ duration(chosen(group).elapsed_s) }}</strong>
        </div>
        <div class="hero-pace">
          <b>{{
            duration(
              (chosen(group).elapsed_s / chosen(group).distance_m) * unitSize
            )
          }}</b
          ><small>/{{ unit }} · elapsed pace</small>
        </div>
      </div>
      <router-link class="benchmark-source" :to="link(chosen(group))"
        ><span
          ><b>{{ chosen(group).title }}</b
          ><time>{{ date(chosen(group).date) }}</time></span
        ><RintIcon name="arrow"
      /></router-link>
      <div v-if="group.rows.length > 1" class="benchmark-curve">
        <p>Best pace across distances</p>
        <div class="curve-surface">
          <svg
            viewBox="0 0 600 140"
            preserveAspectRatio="none"
            role="group"
            aria-label="Best pace by distance"
          >
            <line x1="24" y1="98" x2="576" y2="98" class="curve-grid" />
            <line x1="24" y1="32" x2="576" y2="32" class="curve-grid" />
            <path :d="curve(group.rows)" class="curve-line" />
            <g
              v-for="(best, i) in group.rows"
              :key="best.distance_m"
              role="button"
              tabindex="0"
              :aria-label="`Inspect ${effortDistance(best.distance_m)}: ${duration(best.elapsed_s)}`"
              @click="selected[group.sport] = best.distance_m"
              @keydown.enter="selected[group.sport] = best.distance_m"
              @keydown.space.prevent="selected[group.sport] = best.distance_m"
            >
              <rect
                :x="(i * 600) / group.rows.length"
                y="0"
                :width="600 / group.rows.length"
                height="140"
                fill="transparent"
              />
              <circle
                :cx="px(i, group.rows.length)"
                :cy="py(best, group.rows)"
                :r="best.distance_m === chosen(group).distance_m ? 6 : 3"
                class="curve-dot"
              />
            </g>
          </svg>
          <span class="curve-high">{{ paceBound(group.rows, true) }}</span>
          <span class="curve-low">{{ paceBound(group.rows, false) }}</span>
        </div>
        <div class="curve-labels">
          <span v-for="best in group.rows" :key="best.distance_m">{{
            effortDistance(best.distance_m)
          }}</span>
        </div>
      </div>
    </div>
    <div class="benchmark-labels">
      <span>Distance · source</span><span>Time · pace</span>
    </div>
    <router-link
      v-for="best in group.rows"
      :key="best.distance_m"
      class="benchmark-row"
      :to="link(best)"
    >
      <span class="benchmark-context"
        ><b>{{ effortDistance(best.distance_m) }}</b
        ><small>{{ best.title }}</small
        ><time>{{ date(best.date) }}</time></span
      >
      <span class="benchmark-result"
        ><strong>{{ duration(best.elapsed_s) }}</strong
        ><small
          >{{ duration((best.elapsed_s / best.distance_m) * unitSize) }} /{{
            unit
          }}</small
        ></span
      ><RintIcon name="chevron" />
    </router-link>
    <p class="benchmark-note">Elapsed time includes pauses.</p>
  </section>
</template>
<script setup lang="ts">
  import { computed, reactive } from 'vue'

  import RintIcon from '@/components/Rint/RintIcon.vue'
  import { effortDistance } from '@/utils/trainingHistory'
  interface Best {
    sport_id: number
    distance_m: number
    elapsed_s: number
    workout_id: string
    title: string
    date: string
  }
  interface Group {
    sport: number
    label: string
    rows: Best[]
  }
  const props = defineProps<{
    records: Best[]
    sports: { id: number; label: string }[]
    sportId: number
    unit: string
    unitSize: number
  }>()
  const selected = reactive<Record<number, number>>({})
  const groups = computed<Group[]>(() =>
    Array.from(new Set(props.records.map((r) => r.sport_id))).map((sport) => ({
      sport,
      label: props.sports.find((s) => s.id === sport)?.label || 'Workout',
      rows: props.records.filter((r) => r.sport_id === sport),
    }))
  )
  function chosen(group: Group) {
    return (
      group.rows.find((r) => r.distance_m === selected[group.sport]) ||
      group.rows.find((r) => r.distance_m === 5000) ||
      group.rows[group.rows.length - 1]
    )
  }
  function link(best: Best) {
    return {
      path: `/workouts/${best.workout_id}`,
      hash: `#effort-${best.distance_m}`,
    }
  }
  function date(raw: string) {
    return raw
      ? new Date(raw).toLocaleDateString(undefined, {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
        })
      : 'Recorded workout'
  }
  function duration(seconds: number) {
    const n = Math.round(seconds)
    return `${n >= 3600 ? `${Math.floor(n / 3600)}:` : ''}${String(Math.floor(n / 60) % 60).padStart(2, '0')}:${String(n % 60).padStart(2, '0')}`
  }
  function px(i: number, count: number) {
    return ((i + 0.5) / count) * 600
  }
  function paceBound(rows: Best[], upper: boolean) {
    const paces = rows.map((r) => r.elapsed_s / r.distance_m)
    return duration(
      (upper ? Math.max(...paces) : Math.min(...paces)) * props.unitSize
    )
  }
  function py(best: Best, rows: Best[]) {
    const paces = rows.map((r) => r.elapsed_s / r.distance_m)
    const lo = Math.min(...paces),
      hi = Math.max(...paces)
    return (
      98 -
      ((best.elapsed_s / best.distance_m - lo) / Math.max(0.01, hi - lo)) * 66
    )
  }
  function curve(rows: Best[]) {
    return rows
      .map(
        (best, i) => `${i ? 'L' : 'M'}${px(i, rows.length)},${py(best, rows)}`
      )
      .join(' ')
  }
</script>
<style scoped>
  .benchmarks {
    padding: 14px;
    background: var(--r-surface);
    border: 1px solid var(--r-line);
    border-radius: 18px;
    margin-bottom: 16px;
  }
  h3 {
    margin: 0 0 14px;
  }
  .benchmark-hero {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
  }
  .benchmark-hero p {
    display: flex;
    gap: 6px;
    align-items: center;
    margin: 0 0 6px;
    color: var(--r-power);
    font-size: 12px;
    font-weight: 650;
  }
  .benchmark-hero strong {
    font-size: 34px;
    font-variant-numeric: tabular-nums;
    letter-spacing: -1.5px;
  }
  .hero-pace {
    display: grid;
    text-align: right;
    gap: 5px;
  }
  .hero-pace b {
    color: var(--r-violet);
    font-size: 22px;
  }
  small,
  time {
    font-size: 11px;
    color: var(--r-muted);
  }
  .benchmark-source {
    display: flex;
    gap: 12px;
    justify-content: space-between;
    align-items: center;
    min-height: 44px;
    text-decoration: none;
    color: var(--r-ink);
    margin: 4px 0;
  }
  .benchmark-source span {
    display: grid;
    gap: 5px;
  }
  .benchmark-source b {
    font-size: 14px;
  }
  .benchmark-curve p {
    font-size: 12px;
    color: var(--r-muted);
    margin: 6px 0 4px;
  }
  .curve-surface svg {
    width: 100%;
    height: 80px;
    overflow: visible;
  }
  .r-icon {
    width: 18px;
    height: 18px;
    flex: 0 0 18px;
  }
  .benchmark-context,
  .benchmark-source span {
    min-width: 0;
  }
  .benchmark-context small,
  .benchmark-source b {
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }
  .curve-surface {
    position: relative;
    padding-right: 40px;
  }
  .curve-high,
  .curve-low {
    position: absolute;
    right: 0;
    color: var(--r-muted);
    font-size: 10px;
    font-variant-numeric: tabular-nums;
  }
  .curve-high {
    top: 14px;
  }
  .curve-low {
    top: 50px;
  }
  .curve-labels {
    display: flex;
    padding-right: 40px;
    font-size: 11px;
    color: var(--r-muted);
  }
  .curve-labels span {
    flex: 1;
    text-align: center;
  }
  svg text {
    font-size: 14px;
    fill: var(--r-muted);
  }
  .curve-grid {
    stroke: var(--r-line);
    stroke-width: 1;
  }
  .curve-line {
    fill: none;
    stroke: var(--r-violet);
    stroke-width: 2.5;
    vector-effect: non-scaling-stroke;
  }
  .curve-dot {
    fill: var(--r-violet);
  }
  g {
    cursor: pointer;
  }
  g:focus {
    outline: 2px solid var(--r-violet);
  }
  .benchmark-labels,
  .benchmark-row {
    display: flex;
    justify-content: space-between;
    gap: 12px;
  }
  .benchmark-labels {
    margin-top: 10px;
    font-size: 10px;
    color: var(--r-muted);
  }
  .benchmark-row {
    align-items: center;
    padding: 8px 0;
    min-height: 44px;
    border-bottom: 1px solid var(--r-line);
    color: var(--r-ink);
    text-decoration: none;
  }
  .benchmark-context {
    display: grid;
    gap: 4px;
    min-width: 0;
  }
  .benchmark-context small {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .benchmark-result {
    display: grid;
    gap: 4px;
    text-align: right;
    margin-left: auto;
    flex-shrink: 0;
    font-variant-numeric: tabular-nums;
  }
  .benchmark-result strong {
    font-size: 23px;
    letter-spacing: -0.5px;
  }
  .benchmark-row .r-icon {
    width: 12px;
    flex-shrink: 0;
  }
  .benchmark-note {
    margin: 12px 0 0;
    font-size: 11px;
    color: var(--r-muted);
  }
  @media (min-width: 900px) {
    .benchmark-overview {
      display: grid;
      grid-template-columns: 1fr 1.4fr;
      column-gap: 24px;
    }
    .benchmark-hero {
      grid-column: 1;
      grid-row: 1;
    }
    .benchmark-source {
      grid-column: 1;
      grid-row: 2;
    }
    .benchmark-curve {
      grid-column: 2;
      grid-row: 1 / span 2;
    }
    .benchmarks {
      max-width: none;
    }
  }
</style>
