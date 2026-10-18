<template>
  <article
    class="timeline-workout workout-card"
    :aria-busy="!workout.id"
    @click="openCard"
  >
    <div class="box">
      <header class="workout-card-title">
        <router-link
          class="card-avatar"
          :to="{ path: '/users/' + encodeURIComponent(user.username) }"
          :aria-label="`View ${user.username}’s profile`"
          ><UserPicture :user="user"
        /></router-link>
        <div class="card-heading">
          <router-link
            v-if="workout.id"
            class="workout-title"
            :to="{ name: 'Workout', params: { workoutId: workout.id } }"
            @click="$emit('workoutLinkClicked')"
            >{{ workout.title || sport?.label || 'Activity' }}</router-link
          >
          <div v-else class="card-skeleton" aria-label="Loading activity" />
          <div class="card-meta">
            <span class="card-author">{{ user.username }}</span>
            <time v-if="workout.workout_date" :datetime="workoutDateWithTZ">
              {{
                formatDistance(new Date(workout.workout_date), new Date(), {
                  addSuffix: true,
                  locale,
                })
              }}
              · {{ sport?.label || 'Workout' }}
            </time>
          </div>
        </div>
        <VisibilityIcon
          v-if="workout.workout_visibility"
          :visibility="workout.workout_visibility"
        />
      </header>
      <div
        class="workout-data"
        :class="{ 'four-metrics': metricCount === 4 }"
        :style="{ '--metric-count': metricCount }"
        @click="navigateToWorkout(workout)"
        role="link"
        tabindex="0"
        @keydown.enter="navigateToWorkout(workout)"
        @keydown.space.prevent="navigateToWorkout(workout)"
        aria-label="Open activity metrics"
      >
        <div class="metric-distance">
          <small>Distance</small
          ><strong
            ><Distance
              v-if="workout.id && workout.distance !== null"
              :distance="workout.distance"
              :digits="2"
              unitFrom="km"
              :useImperialUnits="useImperialUnits"
            /><span v-else>—</span></strong
          >
        </div>
        <div>
          <small>{{ timeLabel }}</small
          ><strong>{{
            formatWorkoutDuration(workout.moving ?? workout.duration)
          }}</strong>
        </div>
        <div v-if="motionMetric" class="metric-pace">
          <small>{{ motionMetric.label }}</small>
          <strong
            ><b class="metric-value">{{ motionMetric.value }}</b
            ><span class="metric-unit">{{ motionMetric.unit }}</span></strong
          >
        </div>
        <div
          :class="{ 'metric-heart': workout.ave_hr }"
          v-if="
            workout.ave_hr ||
            (workout.ascent !== null && workout.ascent !== undefined)
          "
        >
          <small>{{ workout.ave_hr ? 'Avg. HR' : 'Elevation' }}</small
          ><strong v-if="workout.ave_hr"
            >{{ Math.round(workout.ave_hr) }}
            <span class="metric-unit">bpm</span></strong
          ><strong v-else
            ><Distance
              v-if="workout.ascent !== null && workout.ascent !== undefined"
              :distance="workout.ascent"
              :digits="0"
              unitFrom="m"
              :useImperialUnits="useImperialUnits"
            /><span v-else>—</span></strong
          >
        </div>
      </div>
      <router-link
        v-if="
          workout.with_stream &&
          workout.with_geometry !== false &&
          !workout.media_attachments?.length
        "
        class="route-link"
        :to="{ name: 'Workout', params: { workoutId: workout.id } }"
        @click="$emit('workoutLinkClicked')"
        ><RouteTrace :workout-id="workout.id" compact reserve-space
      /></router-link>
      <StaticMap
        v-else-if="
          workout.map && workout.with_file && !workout.media_attachments?.length
        "
        :workout="workout"
        @workoutLinkClicked="$emit('workoutLinkClicked')"
      />
      <div v-if="workout.media_attachments?.length" class="media-attachments">
        <router-link
          v-for="media in workout.media_attachments.slice(0, 3)"
          :key="media.id"
          :to="'/workouts/' + workout.id + '#photos'"
          :aria-label="media.description || 'Activity photo'"
          ><img
            :src="media.meta.thumbnail_url"
            :alt="media.description || 'Activity photo'"
            loading="lazy"
        /></router-link>
      </div>
      <FeedActions
        v-if="workout.id"
        :workout="workout"
        :metric-columns="metricCount"
      />
    </div>
  </article>
</template>
<script setup lang="ts">
  import { formatDistance } from 'date-fns'
  import { computed, toRefs } from 'vue'

  import StaticMap from '@/components/Common/StaticMap.vue'
  import RouteTrace from '@/components/Rint/RouteTrace.vue'
  import UserPicture from '@/components/User/UserPicture.vue'
  import FeedActions from '@/components/Workout/FeedActions.vue'
  import useApp from '@/composables/useApp'
  import router from '@/router'
  import type { ISport } from '@/types/sports'
  import type { IUserProfile } from '@/types/user'
  import type { IWorkout } from '@/types/workouts'
  import { formatDate } from '@/utils/dates'
  import {
    formatDuration,
    formatWorkoutDuration,
    workoutDurationSeconds,
  } from '@/utils/duration'
  import { sportsWithPace } from '@/utils/sports'

  function openCard(event: MouseEvent) {
    const target = event.target as HTMLElement
    if (target.closest('a,button,input,summary,[role="link"]')) return
    if (props.workout.id) navigateToWorkout(props.workout)
  }
  interface Props {
    user: IUserProfile
    useImperialUnits: boolean
    dateFormat: string
    timezone: string
    workout?: IWorkout
    sport?: ISport | null
  }
  const props = withDefaults(defineProps<Props>(), {
    workout: () => ({}) as IWorkout,
    sport: () => ({}) as ISport,
  })
  const { dateFormat, sport, timezone, user, useImperialUnits, workout } =
    toRefs(props)

  const { locale } = useApp()

  const emit = defineEmits(['workoutLinkClicked'])

  const timeLabel = computed(() =>
    workout.value.moving != null ? 'Moving time' : 'Elapsed time'
  )
  const motionMetric = computed(() => {
    const distance = workout.value.distance
    const seconds = workoutDurationSeconds(
      workout.value.moving ?? workout.value.duration
    )
    if (
      !distance ||
      !Number.isFinite(distance) ||
      distance <= 0 ||
      seconds === null ||
      seconds < 1
    )
      return null
    const moving = workout.value.moving != null
    const usePace =
      sportsWithPace.includes(sport.value?.label || '') ||
      sport.value?.label === 'Indoor Running'
    return usePace
      ? {
          label: moving ? 'Moving pace' : 'Elapsed pace',
          value: formatDuration(
            Math.round(
              (seconds / distance) * (useImperialUnits.value ? 1.609344 : 1)
            )
          ),
          unit: useImperialUnits.value ? '/mi' : '/km',
        }
      : {
          label: moving ? 'Moving speed' : 'Avg. speed',
          value: (
            ((distance / seconds) * 3600) /
            (useImperialUnits.value ? 1.609344 : 1)
          ).toFixed(1),
          unit: useImperialUnits.value ? 'mph' : 'km/h',
        }
  })
  const metricCount = computed(
    () =>
      2 +
      (motionMetric.value ? 1 : 0) +
      (workout.value.ave_hr ||
      (workout.value.ascent !== null && workout.value.ascent !== undefined)
        ? 1
        : 0)
  )
  const workoutDateWithTZ = computed(() =>
    formatDate(workout.value.workout_date, timezone.value, dateFormat.value)
  )

  function navigateToWorkout(workout: IWorkout) {
    if (workout.id) {
      router.push({
        name: 'Workout',
        params: { workoutId: workout.id },
      })
      emit('workoutLinkClicked')
    }
  }
</script>

<style scoped>
  .timeline-workout {
    margin-bottom: 12px;
  }
  .timeline-workout .box {
    box-sizing: border-box;
    margin: 0;
    border: 1px solid var(--r-line);
    border-radius: 16px;
    box-shadow: var(--r-shadow);
    transition: border-color 180ms ease;
    overflow: hidden;
    padding: 0;
    display: block;
    background: var(--r-surface);
  }
  .workout-card-title {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px 4px;
  }
  .card-avatar {
    display: grid;
    place-items: center;
    flex: 0 0 44px;
    width: 44px;
    height: 44px;
    text-decoration: none;
  }
  .card-avatar :deep(.user-picture) {
    min-width: 30px;
    padding: 0;
  }
  .card-avatar :deep(img) {
    width: 30px;
    height: 30px;
  }
  .card-avatar :deep(.no-picture) {
    font-size: 30px;
  }
  .card-heading {
    flex: 1;
    min-width: 0;
  }
  .workout-title {
    display: block;
    font-size: 18px;
    line-height: 1.25;
    letter-spacing: -0.4px;
    font-weight: 700;
    color: var(--r-ink);
    text-decoration: none;
    overflow-wrap: anywhere;
  }
  .workout-title:hover {
    text-decoration: underline;
  }
  .card-meta {
    display: flex;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 2px 8px;
    margin-top: 3px;
    color: var(--r-muted);
    font-size: 11px;
    line-height: 1.3;
  }
  .card-author {
    font-weight: 600;
  }
  .workout-data {
    display: grid;
    grid-template-columns: repeat(var(--metric-count), minmax(0, 1fr));
    gap: 8px;
    padding: 10px 16px 14px;
    cursor: pointer;
  }
  .workout-data > div {
    min-width: 0;
  }
  .workout-data small {
    display: block;
    color: var(--r-muted);
    font-size: 11px;
    line-height: 1.3;
    margin-bottom: 3px;
  }
  .workout-data strong {
    display: flex;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 4px;
    font-size: 23px;
    line-height: 1.2;
    letter-spacing: -0.5px;
    font-weight: 650;
    font-variant-numeric: tabular-nums;
  }
  .metric-distance strong {
    color: var(--r-distance);
  }
  .metric-pace strong {
    color: var(--r-violet);
  }
  .metric-heart strong {
    color: var(--r-heart);
  }
  .timeline-workout .box:hover {
    border-color: color-mix(in srgb, var(--r-muted) 50%, var(--r-line));
  }
  .metric-value {
    font: inherit;
  }
  .workout-data .metric-unit,
  .workout-data :deep(.unit) {
    font-size: 11px;
    letter-spacing: 0;
    color: var(--r-muted);
    font-weight: 400;
  }
  .workout-data :deep(.distance) {
    font-size: inherit;
    font-weight: inherit;
    color: inherit;
  }
  .route-link {
    display: block;
    text-decoration: none;
    color: var(--r-ink);
  }
  .route-link:has(.route-trace--empty) {
    display: none;
  }
  .route-link :deep(.route-trace) {
    min-height: 150px;
    border-radius: 0;
  }
  .route-link :deep(.activity-route-map.compact) {
    height: 150px;
    border-radius: 0;
  }
  .media-attachments {
    display: flex;
    gap: 2px;
  }
  .media-attachments a {
    flex: 1;
    min-width: 0;
  }
  .media-attachments img {
    width: 100%;
    height: 160px;
    object-fit: cover;
    display: block;
  }
  .card-skeleton {
    height: 20px;
    background: var(--r-soft);
    border-radius: 4px;
    max-width: 75%;
  }
  @media (max-width: 700px) {
    .workout-data strong {
      font-size: 20px;
      gap: 2px;
    }
    .workout-data .metric-unit,
    .workout-data :deep(.unit) {
      font-size: 10px;
    }
    .workout-card-title {
      padding: 10px 12px 2px;
    }
    .workout-data {
      padding: 8px 12px 12px;
    }
  }
  @media (max-width: 350px) {
    .workout-data.four-metrics {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      row-gap: 8px;
    }
  }
</style>
