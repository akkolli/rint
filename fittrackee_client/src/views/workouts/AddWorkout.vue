<template>
  <div id="add-workout" class="view">
    <div class="container add-container">
      <header>
        <p class="r-eyebrow">KEEP YOUR HISTORY TOGETHER</p>
        <h1 class="r-page-title">Add an activity</h1>
        <p class="r-page-subtitle">
          Bring in a recording, connect Apple Health or log an effort.
        </p>
      </header>
      <div class="add-sources">
        <router-link to="/migration?source=health"
          ><span class="source-symbol"><RintIcon name="heart" /></span
          ><span
            ><strong>Apple Health</strong
            ><small>Watch history &amp; automatic sync</small></span
          ><RintIcon name="arrow"
        /></router-link>
        <router-link to="/migration?source=strava"
          ><span class="source-symbol"><RintIcon name="upload" /></span
          ><span
            ><strong>Move from Strava</strong
            ><small>Import your account export</small></span
          ><RintIcon name="arrow"
        /></router-link>
      </div>
      <h2 class="upload-heading">Upload a recording or add manually</h2>
      <WorkoutEdition
        :authUser="authUser"
        :sports="sports"
        :isCreation="true"
        :loading="workoutData.loading"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import type { ComputedRef } from 'vue'

  import RintIcon from '@/components/Rint/RintIcon.vue'
  import WorkoutEdition from '@/components/Workout/WorkoutEdition.vue'
  import useAuthUser from '@/composables/useAuthUser'
  import useSports from '@/composables/useSports'
  import { WORKOUTS_STORE } from '@/store/constants'
  import type { IWorkoutData } from '@/types/workouts'
  import { useStore } from '@/use/useStore'

  const store = useStore()

  const { authUser } = useAuthUser()
  const { sports } = useSports()

  const workoutData: ComputedRef<IWorkoutData> = computed(
    () => store.getters[WORKOUTS_STORE.GETTERS.WORKOUT_DATA]
  )
</script>

<style scoped>
  #add-workout .add-container {
    display: block;
    max-width: 960px;
    width: 100%;
    box-sizing: border-box;
    padding: 36px 28px;
  }
  .add-container header {
    margin-bottom: 28px;
  }
  .add-container header .r-eyebrow {
    margin: 0 0 10px;
  }
  .add-sources {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 32px;
  }
  .add-sources a {
    padding: 22px;
    display: flex;
    align-items: center;
    gap: 14px;
    text-decoration: none;
    color: var(--r-ink);
    background: var(--r-surface);
    border: 1px solid var(--r-line);
    border-radius: 14px;
  }
  .source-symbol {
    padding: 12px;
    display: flex;
    background: var(--r-soft);
    border-radius: 12px;
    color: var(--r-action);
  }
  .add-sources a > span:nth-child(2) {
    flex: 1;
  }
  .add-sources strong {
    font-size: 16px;
  }
  .add-sources small {
    display: block;
    font-size: 12px;
    color: var(--r-muted);
    line-height: 1.5;
    margin-top: 6px;
  }
  .add-sources a > svg {
    width: 16px;
  }
  .upload-heading {
    font-size: 18px;
    margin-bottom: 20px;
  }
  .add-container :deep(.card-title) {
    display: none;
  }
  @media (max-width: 600px) {
    #add-workout .add-container {
      padding: 24px 16px;
    }
    .add-sources {
      grid-template-columns: 1fr;
      gap: 10px;
    }
    .add-sources a {
      padding: 18px;
    }
  }
</style>
