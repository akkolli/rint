<template>
  <div id="timeline">
    <div class="section-title">{{ $t('workouts.LATEST_WORKOUTS') }}</div>
    <div
      v-if="loading && workouts.length === 0"
      aria-label="Loading activities"
      role="status"
    >
      <WorkoutCard
        v-for="index in [...Array(initWorkoutsCount).keys()]"
        :user="authUser"
        :useImperialUnits="authUser.imperial_units"
        :dateFormat="dateFormat"
        :timezone="authUser.timezone"
        :key="index"
      />
    </div>
    <div v-else>
      <div v-if="error" class="feed-error" role="alert">
        <p>{{ error }}</p>
        <button class="r-secondary" @click="loadWorkouts(page + 1)">
          Try again
        </button>
      </div>
      <WorkoutCard
        v-for="workout in workouts"
        :workout="workout"
        :sport="
          workouts.length > 0
            ? sports.filter((s) => s.id === workout.sport_id)[0]
            : null
        "
        :user="workout.user"
        :useImperialUnits="authUser.imperial_units"
        :dateFormat="dateFormat"
        :timezone="authUser.timezone"
        :key="workout.id"
      />
      <NoWorkouts v-if="workouts.length === 0 && !error" />
      <div v-if="pagination.has_next" class="more-workouts">
        <button :disabled="loading" @click="loadMoreWorkouts">
          {{
            loading ? 'Loading activities…' : $t('workouts.LOAD_MORE_WORKOUT')
          }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, onBeforeMount, toRefs } from 'vue'

  import authApi from '@/api/authApi'
  import WorkoutCard from '@/components/Workout/WorkoutCard.vue'
  import NoWorkouts from '@/components/Workouts/NoWorkouts.vue'
  import useAuthUser from '@/composables/useAuthUser'
  import type { ISport } from '@/types/sports'
  import type { IAuthUserProfile } from '@/types/user'
  import type { IWorkout } from '@/types/workouts'
  import { defaultOrder } from '@/utils/workouts'

  const props = defineProps<{ sports: ISport[]; authUser: IAuthUserProfile }>()
  const { sports, authUser } = toRefs(props)
  const { dateFormat } = useAuthUser()
  const per_page = 5,
    initWorkoutsCount = 2
  const page = ref(0),
    workouts = ref<IWorkout[]>([])
  const pagination = ref({ has_next: false }),
    loading = ref(false),
    error = ref('')
  async function loadWorkouts(nextPage = 1) {
    if (loading.value || authUser.value.suspended_at) return
    loading.value = true
    error.value = ''
    try {
      const { data } = await authApi.get('timeline', {
        params: { page: nextPage, per_page, ...defaultOrder },
      })
      if (data.status !== 'success') throw new Error('Timeline unavailable')
      workouts.value =
        nextPage === 1
          ? data.data.workouts
          : [...workouts.value, ...data.data.workouts]
      pagination.value = data.pagination
      page.value = nextPage
    } catch {
      error.value = page.value
        ? 'More activities couldn’t load. Your place is saved.'
        : 'Your feed couldn’t load. Check your connection and try again.'
    } finally {
      loading.value = false
    }
  }
  function loadMoreWorkouts() {
    void loadWorkouts(page.value + 1)
  }
  onBeforeMount(() => loadWorkouts())
</script>

<style lang="scss" scoped>
  .feed-error {
    padding: 20px;
    border: 1px solid var(--r-line);
    background: var(--r-surface);
    border-radius: 14px;
    margin-bottom: 16px;
    font-size: 14px;
    line-height: 1.5;
  }
  #timeline {
    margin-bottom: 20px;

    .more-workouts {
      display: flex;
      justify-content: center;
    }
  }
</style>
