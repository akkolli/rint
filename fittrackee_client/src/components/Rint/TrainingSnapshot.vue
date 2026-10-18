<template>
  <section
    class="training-snapshot"
    :aria-label="
      runningSport
        ? 'Your weekly running distance'
        : 'Your weekly activity distance'
    "
    :aria-busy="loading"
  >
    <div class="snapshot-heading">
      <span
        ><span class="snapshot-live" aria-hidden="true" />This week
        <span class="snapshot-sport">{{
          runningSport ? 'Running' : 'All sports'
        }}</span></span
      >
      <router-link to="/progress" aria-label="Explore your training progress"
        ><span>View progress</span><RintIcon name="arrow"
      /></router-link>
    </div>
    <p v-if="loading" class="snapshot-status" role="status">
      Loading your training…
    </p>
    <div v-else-if="failed" class="snapshot-status">
      <p>Your training couldn’t load.</p>
      <button class="r-secondary" @click="load">Try again</button>
    </div>
    <div v-else class="snapshot-content">
      <div class="snapshot-primary">
        <div class="snapshot-distance">
          <strong>{{ (current.distance_m / unitSize).toFixed(1) }}</strong
          ><span>{{ unit }}</span>
        </div>
        <p class="snapshot-comparison">
          Last week
          <strong
            >{{ (weeks[6].distance_m / unitSize).toFixed(1) }}
            {{ unit }}</strong
          >
        </p>
      </div>
      <div class="snapshot-totals">
        <div>
          <RintIcon name="move" /><strong>{{ current.activities }}</strong
          ><span>{{
            current.activities === 1 ? 'activity' : 'activities'
          }}</span>
        </div>
        <div>
          <RintIcon name="clock" /><strong
            >{{ (current.elapsed_s / 3600).toFixed(1) }}<small>h</small></strong
          ><span>time recorded</span>
        </div>
      </div>
      <div class="snapshot-history">
        <div class="snapshot-chart-heading">
          <span>8-week distance</span><span>{{ unit }}</span>
        </div>
        <div
          class="snapshot-bars"
          aria-label="Distance over the last eight weeks"
        >
          <router-link
            v-for="week in weeks"
            :key="week.key"
            :to="weekLink(week.key)"
            :title="`${week.label}: ${(week.distance_m / unitSize).toFixed(1)} ${unit}`"
            :aria-label="`${week.label}: ${(week.distance_m / unitSize).toFixed(1)} ${unit}. View activities.`"
            :class="{ 'is-current': week.key === weekKey }"
          >
            <span class="snapshot-bar-track"
              ><span
                :style="{ height: `${(week.distance_m / maximum) * 100}%` }"
            /></span>
            <span class="snapshot-week-label">{{ week.label }}</span>
          </router-link>
        </div>
      </div>
    </div>
  </section>
</template>
<script setup lang="ts">
  import { computed, onMounted, ref } from 'vue'

  import authApi from '@/api/authApi'
  import RintIcon from '@/components/Rint/RintIcon.vue'
  import useAuthUser from '@/composables/useAuthUser'
  import useSports from '@/composables/useSports'
  import { dateKey, recentWeeks } from '@/utils/trainingHistory'
  import type { TrainingWeek } from '@/utils/trainingHistory'
  const { imperialUnits } = useAuthUser(),
    { sports } = useSports()
  const history = ref<TrainingWeek[]>([]),
    loading = ref(true),
    failed = ref(false)
  const runningSport = computed(
    () => sports.value.find((s) => s.label === 'Running')?.id || 0
  )
  const unit = computed(() => (imperialUnits.value ? 'mi' : 'km')),
    unitSize = computed(() => (imperialUnits.value ? 1609.344 : 1000))
  const weeks = computed(() =>
    recentWeeks(history.value, runningSport.value).map((r) => ({
      ...r,
      key: r.week,
      label: new Date(r.week + 'T12:00:00').toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
      }),
    }))
  )
  const current = computed(() => weeks.value[7]),
    weekKey = computed(() => current.value.key)
  const maximum = computed(() =>
    Math.max(1, ...weeks.value.map((r) => r.distance_m))
  )
  function weekLink(key: string) {
    const last = new Date(key + 'T12:00:00')
    last.setDate(last.getDate() + 6)
    return {
      path: '/workouts',
      query: {
        from: key,
        to: dateKey(last),
        ...(runningSport.value ? { sport_id: String(runningSport.value) } : {}),
      },
    }
  }
  async function load() {
    loading.value = true
    failed.value = false
    try {
      history.value = (
        await authApi.get('rint/history', {
          params: {
            period: 'week',
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          },
        })
      ).data.data
    } catch {
      failed.value = true
    } finally {
      loading.value = false
    }
  }
  onMounted(load)
</script>
<style scoped>
  .training-snapshot {
    background: linear-gradient(115deg, #183d3e, #152b37);
    color: #f3f8f8;
    border: 1px solid #335552;
    border-radius: 20px;
    padding: 18px 24px 22px;
    overflow: hidden;
  }
  .snapshot-heading,
  .snapshot-heading > span,
  .snapshot-heading a {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .snapshot-heading {
    justify-content: space-between;
    font-size: 12px;
    font-weight: 600;
  }
  .snapshot-live {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #d4f36b;
    box-shadow: 0 0 0 4px #d4f36b12;
  }
  .snapshot-sport {
    color: #c0d4d9;
    font-weight: 400;
    border-left: 1px solid #557075;
    padding-left: 10px;
  }
  .snapshot-heading a {
    color: #d4f36b;
    text-decoration: none;
    min-height: 44px;
    margin-block: -8px;
    font-size: 11px;
  }
  .snapshot-heading a svg {
    width: 16px;
  }
  .snapshot-content {
    display: grid;
    grid-template-columns: 1fr 1fr 1.35fr;
    gap: 24px;
    align-items: center;
    margin-top: 18px;
  }
  .snapshot-distance {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }
  .snapshot-distance > strong {
    font-size: clamp(44px, 5vw, 64px);
    letter-spacing: -3px;
    line-height: 1;
    font-weight: 650;
    font-variant-numeric: tabular-nums;
  }
  .snapshot-distance > span {
    font-size: 18px;
    color: #d4f36b;
  }
  .snapshot-comparison {
    font-size: 11px;
    color: #b7cdd0;
    margin: 10px 0 0;
  }
  .snapshot-comparison strong {
    font-weight: 500;
    color: #edf3f6;
    margin-left: 3px;
  }
  .snapshot-totals {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    border-left: 1px solid #ffffff20;
    padding-left: 24px;
  }
  .snapshot-totals > div {
    display: flex;
    flex-direction: column;
    align-items: start;
    gap: 5px;
  }
  .snapshot-totals svg {
    width: 16px;
    height: 16px;
    color: #9cbbb9;
    margin-bottom: 5px;
  }
  .snapshot-totals strong {
    font-size: 25px;
    font-weight: 550;
    letter-spacing: -0.6px;
    font-variant-numeric: tabular-nums;
  }
  .snapshot-totals small {
    font-size: 12px;
    font-weight: 400;
    color: #b7cdd0;
    margin-left: 3px;
  }
  .snapshot-totals span {
    font-size: 10px;
    color: #b7cdd0;
    white-space: nowrap;
  }
  .snapshot-chart-heading {
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    color: #b7cdd0;
    margin-bottom: 8px;
  }
  .snapshot-bars {
    display: flex;
    gap: 7px;
  }
  .snapshot-bars a {
    flex: 1;
    min-width: 0;
    text-align: center;
    text-decoration: none;
    color: #b7cdd0;
    font-size: 9px;
    display: flex;
    flex-direction: column;
    gap: 7px;
    min-height: 44px;
  }
  .snapshot-bar-track {
    height: 58px;
    display: flex;
    align-items: end;
    background: #ffffff05;
    border-bottom: 1px solid #78918e;
    border-radius: 3px 3px 0 0;
  }
  .snapshot-bar-track > span {
    width: 100%;
    border-radius: 3px 3px 0 0;
    background: #729893;
    min-height: 1px;
    transition: background 160ms ease;
  }
  .is-current .snapshot-bar-track > span {
    background: #d4f36b;
  }
  .snapshot-bars a:hover .snapshot-bar-track > span {
    background: #e4f9aa;
  }
  .snapshot-week-label {
    white-space: nowrap;
  }
  .snapshot-status {
    font-size: 13px;
    color: #d4e1d8;
    min-height: 80px;
  }
  @media (max-width: 1100px) {
    .snapshot-content {
      grid-template-columns: 1fr 1fr;
    }
    .snapshot-history {
      grid-column: 1 / -1;
    }
    .snapshot-bar-track {
      height: 42px;
    }
  }
  @media (max-width: 700px) {
    .training-snapshot {
      padding: 16px 18px;
      border-radius: 18px;
    }
    .snapshot-content {
      gap: 16px;
      margin-top: 18px;
    }
    .snapshot-distance > strong {
      font-size: 44px;
      letter-spacing: -2px;
    }
    .snapshot-totals {
      gap: 12px;
      padding-left: 16px;
    }
    .snapshot-totals svg {
      display: none;
    }
    .snapshot-totals strong {
      font-size: 22px;
    }
    .snapshot-bar-track {
      height: 28px;
    }
    .snapshot-chart-heading {
      margin-bottom: 6px;
    }
    .snapshot-heading a span {
      display: none;
    }
    .snapshot-heading a {
      width: 44px;
      justify-content: flex-end;
    }
  }
  @media (max-width: 350px) {
    .snapshot-totals {
      gap: 8px;
      padding-left: 10px;
    }
    .snapshot-totals span {
      white-space: normal;
    }
    .snapshot-week-label {
      font-size: 8px;
    }
  }
</style>
