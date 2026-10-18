<template>
  <div
    id="workout"
    class="view"
    :class="{ 'stream-activity': workoutData.workout.with_stream }"
  >
    <div class="container">
      <div class="workout-container" v-if="sports.length > 0">
        <div v-if="workoutData.workout.id">
          <ActivityHero
            v-if="
              workoutData.workout.with_stream &&
              (!workoutData.workout.suspended || isWorkoutOwner)
            "
            :workout="workoutData.workout"
            :sport="sport"
            :is-owner="isWorkoutOwner"
          />
          <WorkoutUser v-else :user="workoutData.workout.user" />
          <div
            class="box suspended"
            v-if="workoutData.workout.suspended && !isWorkoutOwner"
          >
            {{ $t('workouts.SUSPENDED_BY_ADMIN') }}
          </div>
          <WorkoutDetail
            v-else-if="!workoutData.workout.with_stream"
            :workoutData="workoutData"
            :sport="sport"
            :authUser="authUser"
            :markerCoordinates="markerCoordinates"
            :displaySegment="displaySegment"
            :isWorkoutOwner="isWorkoutOwner"
            :cadenceUnit="cadenceUnit"
            :isRefreshing="isRefreshing"
          />
          <ActivityAnalysis
            v-if="
              !displaySegment &&
              (!workoutData.workout.suspended || isWorkoutOwner)
            "
            :workout-id="workoutData.workout.id"
            :sport-id="workoutData.workout.sport_id"
            :is-owner="isWorkoutOwner"
            :initial-visibility="workoutData.workout.workout_visibility"
            :initial-map-visibility="workoutData.workout.map_visibility"
          />
          <FeedActions
            v-if="
              workoutData.workout.with_stream &&
              (!workoutData.workout.suspended || isWorkoutOwner)
            "
            :workout="workoutData.workout"
            :configure-sharing="isWorkoutOwner"
            :hide-share="true"
          />
          <details
            v-if="
              workoutData.workout.with_stream &&
              (!workoutData.workout.suspended || isWorkoutOwner)
            "
            class="activity-manage"
            @toggle="manageOpen = ($event.target as HTMLDetailsElement).open"
          >
            <summary>Manage activity & original recording</summary>
            <WorkoutDetail
              v-if="manageOpen"
              :workoutData="workoutData"
              :sport="sport"
              :authUser="authUser"
              :markerCoordinates="markerCoordinates"
              :displaySegment="displaySegment"
              :isWorkoutOwner="isWorkoutOwner"
              :cadenceUnit="cadenceUnit"
              :isRefreshing="isRefreshing"
            />
          </details>
          <WorkoutChart
            v-if="
              workoutData.workout.with_analysis &&
              !workoutData.workout.with_stream
            "
            :workoutData="workoutData"
            :isRefreshing="isRefreshing"
            :authUser="authUser"
            :displaySegment="displaySegment"
            :sport="sport"
            :cadenceUnit="cadenceUnit"
            :isWorkoutOwner="isWorkoutOwner"
            @getCoordinates="updateCoordinates"
          />
          <WorkoutMediaGallery
            v-if="
              !displaySegment &&
              workoutData.workout.media_attachments.length > 0
            "
            :media-attachments="workoutData.workout.media_attachments"
            :media-visibility="workoutData.workout.media_visibility"
            :is-workout-owner="isWorkoutOwner"
            :workout-id="workoutData.workout.id"
          />
          <WorkoutContent
            v-if="
              !displaySegment &&
              (!workoutData.workout.with_stream ||
                workoutData.workout.description)
            "
            :workout-id="workoutData.workout.id"
            content-type="DESCRIPTION"
            :content="workoutData.workout.description"
            :loading="workoutData.loading"
            :disabled="isRefreshing"
            :allow-edition="isWorkoutOwner"
          />
          <details
            v-if="
              isWorkoutOwner &&
              !displaySegment &&
              workoutData.workout.with_stream &&
              !workoutData.workout.description
            "
            class="activity-manage"
          >
            <summary>Add a caption</summary>
            <WorkoutContent
              :workout-id="workoutData.workout.id"
              content-type="DESCRIPTION"
              :content="workoutData.workout.description"
              :loading="workoutData.loading"
              :disabled="isRefreshing"
              :allow-edition="true"
            />
          </details>
          <WorkoutSegments
            v-if="!displaySegment && workoutData.workout.segments.length > 1"
            :segments="workoutData.workout.segments"
            :useImperialUnits="displayOptions.useImperialUnits"
          />
          <details
            v-if="
              isWorkoutOwner &&
              !displaySegment &&
              workoutData.workout.with_stream &&
              !workoutData.workout.notes
            "
            class="activity-manage"
          >
            <summary>Private notes</summary>
            <WorkoutContent
              :workout-id="workoutData.workout.id"
              content-type="NOTES"
              :content="workoutData.workout.notes"
              :disabled="isRefreshing"
              :loading="workoutData.loading"
            />
          </details>
          <WorkoutContent
            v-else-if="isWorkoutOwner && !displaySegment"
            :workout-id="workoutData.workout.id"
            content-type="NOTES"
            :content="workoutData.workout.notes"
            :disabled="isRefreshing"
            :loading="workoutData.loading"
          />
          <Comments
            v-if="!displaySegment"
            :workoutData="workoutData"
            :disabled="isRefreshing"
            :auth-user="authUser"
          />
          <div id="bottom" />
        </div>
        <div v-else>
          <NotFound
            v-if="!workoutData.loading"
            :target="displaySegment ? 'SEGMENT' : 'WORKOUT'"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import {
    computed,
    nextTick,
    onBeforeMount,
    onUnmounted,
    onMounted,
    ref,
    toRefs,
    watch,
  } from 'vue'
  import type { ComputedRef, Ref } from 'vue'
  import { useRoute } from 'vue-router'

  import Comments from '@/components/Comment/Comments.vue'
  import NotFound from '@/components/Common/NotFound.vue'
  import ActivityHero from '@/components/Rint/ActivityHero.vue'
  import ActivityAnalysis from '@/components/Workout/ActivityAnalysis.vue'
  import FeedActions from '@/components/Workout/FeedActions.vue'
  import WorkoutDetail from '@/components/Workout/WorkoutDetail/index.vue'
  import WorkoutChart from '@/components/Workout/WorkoutDetail/WorkoutChart/index.vue'
  import WorkoutContent from '@/components/Workout/WorkoutDetail/WorkoutContent.vue'
  import WorkoutMediaGallery from '@/components/Workout/WorkoutDetail/WorkoutMediaGallery.vue'
  import WorkoutSegments from '@/components/Workout/WorkoutDetail/WorkoutSegments.vue'
  import WorkoutUser from '@/components/Workout/WorkoutDetail/WorkoutUser.vue'
  import useApp from '@/composables/useApp.ts'
  import useAuthUser from '@/composables/useAuthUser'
  import useScroll from '@/composables/useScroll.ts'
  import useSports from '@/composables/useSports'
  import { SPORTS_STORE, WORKOUTS_STORE } from '@/store/constants'
  import type { TCoordinates } from '@/types/map'
  import type { ISport } from '@/types/sports.ts'
  import type { IWorkoutData, IWorkoutPayload } from '@/types/workouts'
  import { useStore } from '@/use/useStore'
  import { getCadenceUnit } from '@/utils/workouts.ts'

  interface Props {
    displaySegment: boolean
  }
  const props = defineProps<Props>()
  const { displaySegment } = toRefs(props)

  const route = useRoute()
  const store = useStore()

  const { authUser } = useAuthUser()
  const { displayOptions } = useApp()
  const { getWorkoutSport, sports } = useSports()
  const { resetTimeout, scrollTo } = useScroll()

  const markerCoordinates: Ref<TCoordinates> = ref({
    latitude: null,
    longitude: null,
  })

  const workoutData: ComputedRef<IWorkoutData> = computed(
    () => store.getters[WORKOUTS_STORE.GETTERS.WORKOUT_DATA]
  )
  const isRefreshing: ComputedRef<boolean> = computed(
    () => workoutData.value.refreshLoading || workoutData.value.elevationLoading
  )
  const isWorkoutOwner: ComputedRef<boolean> = computed(
    () => authUser.value.username === workoutData.value.workout.user.username
  )
  const sport: ComputedRef<ISport | null> = computed(() =>
    getWorkoutSport(workoutData.value.workout)
  )
  const manageOpen = ref(false)
  const cadenceUnit: ComputedRef<string> = computed(() =>
    getCadenceUnit(sport.value?.label)
  )

  function updateCoordinates(coordinates: TCoordinates) {
    markerCoordinates.value = {
      latitude: coordinates.latitude,
      longitude: coordinates.longitude,
    }
  }

  watch(
    () => route.params.workoutId,
    async (newWorkoutId) => {
      if (newWorkoutId) {
        store.dispatch(WORKOUTS_STORE.ACTIONS.GET_WORKOUT_DATA, {
          workoutId: newWorkoutId,
        })
      }
    }
  )
  watch(
    () => route.params.segmentId,
    async (newSegmentId) => {
      if (route.params.workoutId) {
        const payload: IWorkoutPayload = {
          workoutId: route.params.workoutId,
        }
        if (newSegmentId) {
          payload.segmentId = newSegmentId
        }
        store.dispatch(WORKOUTS_STORE.ACTIONS.GET_WORKOUT_DATA, payload)
      }
    }
  )

  onBeforeMount(() => {
    const payload: IWorkoutPayload = { workoutId: route.params.workoutId }
    if (props.displaySegment) {
      payload.segmentId = route.params.segmentId
    }
    store.dispatch(WORKOUTS_STORE.ACTIONS.GET_WORKOUT_DATA, payload)
    if (sports.value.length === 0) {
      store.dispatch(SPORTS_STORE.ACTIONS.GET_SPORTS)
    }
  })
  onMounted(() => {
    nextTick(() => {
      if (route.hash) {
        scrollTo(route.hash.replace('#', ''), 300)
      }
    })
  })
  onUnmounted(() => {
    resetTimeout()
    store.commit(WORKOUTS_STORE.MUTATIONS.EMPTY_WORKOUT)
  })
</script>

<style lang="scss" scoped>
  @use '~@/scss/vars.scss' as *;
  #workout {
    display: flex;
    .container {
      width: 100%;
      padding: 0;
      .workout-container {
        width: 100%;

        .user-header {
          align-items: center;
          ::v-deep(.user-picture) {
            img {
              height: 50px;
              width: 50px;
            }
            .no-picture {
              font-size: 3em;
            }
          }
          ::v-deep(.user-details) {
            flex-direction: row;
          }
        }
      }
      .workout-loading {
        height: $app-height;
        width: 100%;
        .loading {
          display: flex;
          align-items: center;
          height: 100%;
        }
      }
    }
  }
</style>

<style scoped>
  #workout > .container {
    display: block;
    max-width: 960px;
    box-sizing: border-box;
    width: 100%;
    padding: 0 28px;
  }
  .activity-manage {
    margin: 24px 0;
    border-top: 1px solid var(--r-line);
  }
  .activity-manage > summary {
    display: flex;
    align-items: center;
    min-height: 56px;
    cursor: pointer;
    color: var(--r-muted);
    font-size: 13px;
  }
  .activity-manage > summary::after {
    content: '+';
    margin-left: auto;
    font-size: 22px;
  }
  .activity-manage[open] > summary::after {
    content: '−';
  }
  #workout.stream-activity :deep(#workout-content .card) {
    background: transparent;
    border: 0;
    border-top: 1px solid var(--r-line);
    border-radius: 0;
    margin: 0;
    padding: 20px 0;
    box-shadow: none;
  }
  #workout.stream-activity :deep(#workout-content .card-title),
  #workout.stream-activity :deep(#workout-content .card-content) {
    border: 0;
    padding: 0;
  }
  #workout.stream-activity :deep(#workout-content .card-title) {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    margin-bottom: 8px;
  }
  #workout.stream-activity :deep(#workout-content .card-content) {
    color: var(--r-muted);
    font-size: 14px;
    line-height: 1.6;
  }
  #workout.stream-activity :deep(#workout-content .icon-button) {
    min-width: 44px;
    min-height: 44px;
  }
  #workout.stream-activity :deep(.workout-comments > .card) {
    margin: 24px 0;
    padding: 24px;
    border-radius: 20px;
    border: 1px solid var(--r-line);
    box-shadow: none;
  }
  #workout.stream-activity :deep(.workout-comments .card-title) {
    padding: 0 0 16px;
    font-size: 22px;
    letter-spacing: -0.6px;
    border: 0;
  }
  #workout.stream-activity :deep(.workout-comments .card-content) {
    padding: 0;
  }
  #workout.stream-activity :deep(.workout-comments .no-comments) {
    font-style: normal;
    color: var(--r-muted);
  }
  #workout.stream-activity :deep(.workout-comments .add-comment-button button),
  #workout.stream-activity :deep(.workout-comments .comment-buttons button) {
    min-height: 44px;
    padding: 10px 18px;
    border-radius: 99px;
  }
  #workout.stream-activity :deep(.workout-comments .add-comment-button button),
  #workout.stream-activity :deep(.workout-comments .comment-buttons .confirm) {
    background: var(--r-accent);
    border-color: var(--r-accent);
    color: var(--r-accent-ink);
    font-weight: 650;
  }
  @media (max-width: 700px) {
    #workout > .container {
      padding: 0 16px;
    }
  }
</style>
