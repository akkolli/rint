<template>
  <div class="view progress-view">
    <div class="container">
      <header class="progress-header">
        <h1>Progress</h1>
      </header>
      <nav class="view-tabs" aria-label="Training view">
        <button
          v-for="tab in ['Week', 'Records', 'History']"
          :key="tab"
          :class="{ selected: section === tab }"
          :aria-pressed="section === tab"
          @click="section = tab"
        >
          {{ tab }}
        </button>
      </nav>
      <div class="section-heading">
        <h2>
          {{
            section === 'Records'
              ? 'All-time bests'
              : section === 'History'
                ? 'Workouts'
                : 'Weekly distance'
          }}
        </h2>
        <label class="sport-filter"
          ><span class="sr-only">Sport</span
          ><select v-model.number="sportId">
            <option :value="0">All sports</option>
            <option v-for="sport in sports" :key="sport.id" :value="sport.id">
              {{ sport.label }}
            </option>
          </select></label
        >
      </div>
      <p v-if="loading" role="status">Loading your training…</p>
      <p v-if="error" role="alert">
        {{ error }} <button @click="load">Try again</button>
      </p>
      <template v-if="!loading && !error">
        <template v-if="section === 'Week'">
          <section class="week-panel" aria-label="Weekly distance">
            <div class="week-summary">
              <div>
                <p>
                  {{
                    selected.week === weeks[7].week
                      ? 'This week · in progress'
                      : 'Week of ' + weekLabel(selected.week)
                  }}
                </p>
                <strong
                  >{{ (selected.distance_m / unitSize).toFixed(1) }}
                  <small>{{ unit }}</small></strong
                >
              </div>
              <div class="week-context">
                <b
                  >{{ selected.activities }}
                  {{ selected.activities === 1 ? 'workout' : 'workouts' }}</b
                ><span
                  >{{ (selected.elapsed_s / 3600).toFixed(1) }} hours
                  recorded</span
                ><span>Monday – Sunday</span>
              </div>
            </div>
            <div class="week-plot">
              <svg
                class="week-trend"
                viewBox="0 0 800 150"
                preserveAspectRatio="none"
                aria-hidden="true"
              >
                <path :d="weeklyTrend" />
                <circle
                  v-for="(week, i) in weeks"
                  :key="week.week"
                  :cx="(i + 0.5) * 100"
                  :cy="149 - (week.distance_m / maximum) * 149"
                  :r="week.week === selected.week ? 5 : 3"
                />
              </svg>
              <div
                class="week-bars"
                aria-label="Distance over the last eight weeks"
              >
                <button
                  v-for="week in weeks"
                  :key="week.week"
                  :class="{ selected: week.week === selected.week }"
                  @click="selectedWeek = week.week"
                  :aria-label="`Week of ${weekLabel(week.week)}: ${(week.distance_m / unitSize).toFixed(1)} ${unit}, ${week.activities} workouts`"
                  :aria-pressed="week.week === selected.week"
                >
                  <span class="bar-track"
                    ><span
                      :style="{
                        height: `${Math.max(1, (week.distance_m / maximum) * 100)}%`,
                      }" /></span
                  ><span>{{ weekLabel(week.week) }}</span>
                </button>
              </div>
            </div>
            <p class="helper">
              8 weeks
              <span v-if="previousWeek"
                >· Previous week
                {{ (previousWeek.distance_m / unitSize).toFixed(1) }}
                {{ unit }}</span
              >
            </p>
          </section>
          <button class="record-entry" @click="section = 'Records'">
            <RintIcon name="trophy" /><span
              ><strong>All-time bests</strong
              ><small>{{ records.length }} distances</small></span
            ><RintIcon name="arrow" />
          </button>
          <router-link
            class="library-link"
            :to="{
              path: '/workouts',
              query: sportId ? { sport_id: String(sportId) } : {},
            }"
            >Explore your workouts <RintIcon name="arrow"
          /></router-link>
        </template>
        <template v-else-if="section === 'Records'">
          <p v-if="analysisMessage" role="status" class="helper">
            {{ analysisMessage }}
          </p>
          <TrainingRecords
            :records="records"
            :sports="sports"
            :sport-id="sportId"
            :unit="unit"
            :unit-size="unitSize"
          />
          <p v-if="!records.length && !loading">
            No records yet. Continuous distance samples are required; summaries
            alone cannot verify an effort.
          </p>
          <button
            class="r-secondary refresh-records"
            :disabled="analyzing"
            @click="refreshEarlier"
          >
            {{ analyzing ? 'Preparing records…' : 'Refresh records' }}
          </button>
        </template>
        <template v-else>
          <p class="section-intro">
            Search, filter, and revisit your complete workout history.
          </p>
          <router-link
            class="library-link"
            :to="{
              path: '/workouts',
              query: sportId ? { sport_id: String(sportId) } : {},
            }"
            >Open activity library <RintIcon name="arrow"
          /></router-link>
          <section class="week-panel">
            <h3>
              Training year
              <select v-model.number="year" aria-label="Training year">
                <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
              </select>
            </h3>
            <div class="history-bars">
              <router-link
                v-for="month in months"
                :key="month.month"
                :to="monthLink(month.month)"
                ><span class="bar-track"
                  ><span
                    :style="{
                      height: `${(month.distance_m / maxMonth) * 100}%`,
                    }" /></span
                ><b>{{ (month.distance_m / unitSize).toFixed(1) }}</b
                ><span>{{ monthLabel(month.month) }}</span></router-link
              >
            </div>
            <p class="helper">
              {{ totalActivities }} workouts ·
              {{ (totalDistance / unitSize).toFixed(1) }} {{ unit }} · select a
              month to see its workouts.
            </p>
          </section>
        </template>
      </template>
    </div>
  </div>
</template>
<script setup lang="ts">
  import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
  import { useRoute } from 'vue-router'

  import authApi from '@/api/authApi'
  import RintIcon from '@/components/Rint/RintIcon.vue'
  import TrainingRecords from '@/components/Rint/TrainingRecords.vue'
  import useAuthUser from '@/composables/useAuthUser'
  import useSports from '@/composables/useSports'
  import { recentWeeks } from '@/utils/trainingHistory'
  import type { TrainingWeek } from '@/utils/trainingHistory'
  const { sports } = useSports(),
    { imperialUnits } = useAuthUser()
  const route = useRoute()
  const section = ref(route.query.view === 'records' ? 'Records' : 'Week'),
    sportId = ref(0),
    selectedWeek = ref('')
  const unit = computed(() => (imperialUnits.value ? 'mi' : 'km')),
    unitSize = computed(() => (imperialUnits.value ? 1609.344 : 1000))
  interface Month {
    month: string
    sport_id: number
    activities: number
    distance_m: number
    elapsed_s: number
  }
  interface Best {
    sport_id: number
    distance_m: number
    elapsed_s: number
    workout_id: string
    title: string
    date: string
  }
  const history = ref<Month[]>([]),
    weekRows = ref<TrainingWeek[]>([]),
    bests = ref<Best[]>([]),
    loading = ref(false),
    error = ref(''),
    analyzing = ref(false),
    analysisMessage = ref(''),
    pending = ref(0)
  let alive = true
  onBeforeUnmount(() => {
    alive = false
  })
  const year = ref(new Date().getFullYear())
  const years = computed(() => {
    const first = Math.min(
      new Date().getFullYear(),
      ...history.value.map((r) => Number(r.month.slice(0, 4)))
    )
    return Array.from(
      { length: new Date().getFullYear() - first + 1 },
      (_, i) => new Date().getFullYear() - i
    )
  })
  const weeks = computed(() => recentWeeks(weekRows.value, sportId.value))
  const selected = computed(
    () =>
      weeks.value.find((r) => r.week === selectedWeek.value) || weeks.value[7]
  )
  const maximum = computed(() =>
    Math.max(1, ...weeks.value.map((r) => r.distance_m))
  )
  const weeklyTrend = computed(() =>
    weeks.value
      .map(
        (week, i) =>
          `${i ? 'L' : 'M'}${(i + 0.5) * 100},${149 - (week.distance_m / maximum.value) * 149}`
      )
      .join(' ')
  )
  const previousWeek = computed(
    () =>
      weeks.value[
        weeks.value.findIndex((week) => week.week === selected.value.week) - 1
      ]
  )
  const records = computed(() =>
    bests.value
      .filter((r) => !sportId.value || r.sport_id === sportId.value)
      .sort((a, b) => a.distance_m - b.distance_m)
  )
  const months = computed(() =>
    Array.from({ length: 12 }, (_, i): Month => {
      const key = `${year.value}-${String(i + 1).padStart(2, '0')}-01`
      return history.value
        .filter(
          (r) =>
            r.month.slice(0, 7) === key.slice(0, 7) &&
            (!sportId.value || r.sport_id === sportId.value)
        )
        .reduce(
          (sum, r) => ({
            ...sum,
            distance_m: sum.distance_m + r.distance_m,
            activities: sum.activities + r.activities,
            elapsed_s: sum.elapsed_s + r.elapsed_s,
          }),
          {
            month: key,
            sport_id: 0,
            distance_m: 0,
            activities: 0,
            elapsed_s: 0,
          }
        )
    })
  )
  const maxMonth = computed(() =>
      Math.max(1, ...months.value.map((r) => r.distance_m))
    ),
    totalActivities = computed(() =>
      months.value.reduce((n, r) => n + r.activities, 0)
    ),
    totalDistance = computed(() =>
      months.value.reduce((n, r) => n + r.distance_m, 0)
    )
  function weekLabel(key: string) {
    return new Date(key + 'T12:00:00').toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
    })
  }
  function monthLabel(key: string) {
    return new Date(key + 'T12:00:00').toLocaleDateString(undefined, {
      month: 'short',
    })
  }
  function monthLink(key: string) {
    const end = new Date(
      Number(key.slice(0, 4)),
      Number(key.slice(5, 7)),
      0
    ).getDate()
    return {
      path: '/workouts',
      query: {
        from: key,
        to: key.slice(0, 8) + end,
        ...(sportId.value ? { sport_id: String(sportId.value) } : {}),
      },
    }
  }
  async function refreshEarlier() {
    if (analyzing.value) return
    analyzing.value = true
    analysisMessage.value = ''
    let cursor = 0,
      count = 0,
      failures = 0
    try {
      let more = true
      while (more && alive) {
        const { data } = await authApi.post('rint/bests/refresh', { cursor })
        cursor = data.data.cursor
        more = data.data.has_more
        count += data.data.processed
        failures += data.data.errors.length
        analysisMessage.value = `Preparing records · ${count} recordings reviewed`
        const b = await authApi.get('rint/bests')
        bests.value = b.data.data
      }
      analysisMessage.value = failures
        ? `${failures} recordings need another attempt. Completed records are shown.`
        : ''
    } catch {
      analysisMessage.value =
        'Preparation paused. Your completed records are saved; refresh to continue.'
    } finally {
      analyzing.value = false
    }
  }
  async function load() {
    loading.value = true
    error.value = ''
    try {
      const [h, w, b] = await Promise.all([
        authApi.get('rint/history'),
        authApi.get('rint/history', {
          params: {
            period: 'week',
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          },
        }),
        authApi.get('rint/bests'),
      ])
      history.value = h.data.data
      weekRows.value = w.data.data
      bests.value = b.data.data
      pending.value = b.data.coverage?.pending || 0
    } catch {
      error.value = 'Your training couldn’t load. Reconnect and try again.'
    } finally {
      loading.value = false
    }
  }
  onMounted(async () => {
    sportId.value =
      Number(route.query.sport_id) ||
      sports.value.find((s) => s.label === 'Running')?.id ||
      0
    await load()
    if (pending.value) await refreshEarlier()
  })
</script>
<style scoped>
  .progress-view {
    min-height: 0;
    background: var(--r-paper);
    color: var(--r-ink);
  }
  .container {
    display: block;
    box-sizing: border-box;
    max-width: 960px;
    width: 100%;
    margin: auto;
    padding: 16px 20px 28px;
  }
  h1 {
    font-size: 30px;
    letter-spacing: -1.5px;
    margin: 0 0 12px;
  }
  .eyebrow {
    font-size: 10px;
    letter-spacing: 1.4px;
    color: var(--r-muted);
    font-weight: 750;
  }
  .view-tabs {
    display: flex;
    gap: 4px;
    background: var(--r-soft);
    padding: 4px;
    border-radius: 28px;
    margin-bottom: 12px;
  }
  .view-tabs button {
    flex: 1;
    min-height: 44px;
    background: transparent;
    border: 0;
    border-radius: 24px;
    color: var(--r-muted);
    font-size: 15px;
  }
  .view-tabs .selected {
    background: var(--r-surface);
    color: var(--r-ink);
    font-weight: 700;
  }
  .section-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 10px;
  }
  h2 {
    font-size: 20px;
    letter-spacing: -0.7px;
    margin: 0;
  }
  .sport-filter select {
    max-width: 170px;
    min-height: 44px;
    border: 0;
    background: transparent;
    color: var(--r-ink);
  }
  .week-panel {
    padding: 16px;
    border: 1px solid var(--r-line);
    border-radius: 16px;
    background: var(--r-surface);
  }
  .week-summary {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
  }
  .week-summary p {
    margin: 0 0 6px;
    font-weight: 650;
  }
  .week-summary strong {
    display: block;
    font-size: 42px;
    letter-spacing: -2px;
    font-variant-numeric: tabular-nums;
    line-height: 1;
  }
  .week-summary small {
    font-size: 20px;
    color: var(--r-muted);
    letter-spacing: 0;
    font-weight: 450;
  }
  .week-context {
    display: grid;
    gap: 4px;
    text-align: right;
    font-size: 12px;
    color: var(--r-muted);
  }
  .week-context b {
    color: var(--r-ink);
  }
  .week-bars,
  .history-bars {
    display: grid;
    grid-template-columns: repeat(8, minmax(0, 1fr));
    gap: 8px;
    margin-top: 0;
  }
  .week-bars {
    gap: 0;
  }
  .week-bars button {
    padding: 0 4px;
  }
  .week-plot {
    position: relative;
    margin-top: 12px;
  }
  .week-trend {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 130px;
    pointer-events: none;
    z-index: 1;
    overflow: visible;
  }
  .week-trend path {
    fill: none;
    stroke: var(--r-violet);
    stroke-width: 2.5;
    vector-effect: non-scaling-stroke;
  }
  .week-trend circle {
    fill: var(--r-violet);
  }
  .week-bars button,
  .history-bars a {
    display: grid;
    gap: 10px;
    min-width: 0;
    padding: 0;
    border: 0;
    background: none;
    font-size: 10px;
    color: var(--r-muted);
    text-align: center;
    text-decoration: none;
  }
  .bar-track {
    height: 130px;
    display: flex;
    align-items: flex-end;
    border-bottom: 1px solid var(--r-line);
  }
  .week-bars button {
    padding: 0 4px;
  }
  .bar-track > span {
    display: block;
    width: 100%;
    background: var(--r-violet);
    opacity: 0.25;
    border-radius: 4px 4px 0 0;
  }
  .selected .bar-track > span {
    opacity: 0.5;
  }
  .helper {
    font-size: 12px;
    line-height: 1.5;
    color: var(--r-muted);
    margin: 18px 0 0;
  }
  .record-entry {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 26px 0;
    width: 100%;
    background: none;
    border: 0;
    border-bottom: 1px solid var(--r-line);
    text-align: left;
    color: var(--r-ink);
  }
  .record-entry > .r-icon:first-child {
    width: 28px;
    height: 28px;
    color: var(--r-power);
  }
  .record-entry span {
    display: grid;
    gap: 6px;
    flex: 1;
  }
  .record-entry strong {
    font-size: 20px;
  }
  .record-entry small {
    font-size: 13px;
    color: var(--r-muted);
  }
  .library-link {
    display: inline-flex;
    align-items: center;
    gap: 12px;
    min-height: 44px;
    margin: 18px 0;
    color: var(--r-ink);
    font-weight: 650;
    text-decoration: none;
  }
  .section-intro {
    color: var(--r-muted);
    line-height: 1.6;
    margin-bottom: 26px;
    max-width: 640px;
  }
  .record-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 16px;
  }
  .record-card {
    display: flex;
    flex-direction: column;
    padding: 22px;
    gap: 12px;
    border: 1px solid var(--r-line);
    border-radius: 20px;
    background: var(--r-surface);
    color: var(--r-ink);
    text-decoration: none;
  }
  .record-icons {
    display: flex;
    justify-content: space-between;
    color: var(--r-power);
  }
  .record-icons .r-icon:last-child {
    color: var(--r-muted);
  }
  .record-card h3 {
    font-size: 17px;
    margin: 4px 0 0;
  }
  .record-card > strong {
    font-size: 38px;
    letter-spacing: -1px;
    font-variant-numeric: tabular-nums;
  }
  .record-sport,
  .record-pace {
    font-size: 12px;
    color: var(--r-muted);
  }
  .record-origin {
    display: grid;
    gap: 8px;
    border-top: 1px solid var(--r-line);
    padding-top: 14px;
    font-size: 12px;
    margin-top: auto;
  }
  .record-origin time {
    color: var(--r-muted);
  }
  .refresh-records {
    margin-top: 22px;
  }
  .history-bars {
    grid-template-columns: repeat(12, minmax(0, 1fr));
  }
  .history-bars .bar-track {
    height: 130px;
  }
  @media (max-width: 600px) {
    h1 {
      font-size: 30px;
    }
    h2 {
      font-size: 21px;
    }
    .sport-filter select {
      max-width: 115px;
      font-size: 13px;
    }
    .week-panel {
      padding: 18px;
    }
    .week-summary strong {
      font-size: 44px;
    }
    .record-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }
    .record-card {
      padding: 16px;
    }
    .record-card > strong {
      font-size: 31px;
    }
    .history-bars {
      gap: 4px;
      font-size: 9px;
    }
  }
</style>
