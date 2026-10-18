<template>
  <header class="activity-hero">
    <router-link class="back-link" to="/">← Feed</router-link>
    <div class="activity-meta">
      <span class="sport-badge"
        ><RintIcon name="move" />{{ sport?.label || 'Workout' }}</span
      ><time :datetime="workout.workout_date">{{
        new Date(workout.workout_date).toLocaleDateString(undefined, {
          month: 'long',
          day: 'numeric',
          year: 'numeric',
        })
      }}</time>
    </div>
    <h1>{{ workout.title || 'Your activity' }}</h1>
    <div class="activity-athlete">
      <router-link :to="'/users/' + workout.user.username">{{
        workout.user.username
      }}</router-link
      ><span>·</span
      ><VisibilityIcon :visibility="workout.workout_visibility" /><span>{{
        workout.workout_visibility === 'private'
          ? 'Only you'
          : workout.workout_visibility === 'followers_only'
            ? 'Followers'
            : 'Everyone'
      }}</span>
    </div>
    <router-link
      v-if="isOwner"
      class="hero-share"
      :to="`/workouts/${workout.id}#sharing`"
      ><RintIcon name="share" />Share</router-link
    >
  </header>
</template>
<script setup lang="ts">
  import RintIcon from '@/components/Rint/RintIcon.vue'
  import type { ISport } from '@/types/sports'
  import type { IWorkout } from '@/types/workouts'
  defineProps<{ workout: IWorkout; sport: ISport | null; isOwner: boolean }>()
</script>
<style scoped>
  .activity-hero {
    padding: 12px 0 0;
  }
  .back-link {
    display: inline-flex;
    align-items: center;
    min-height: 44px;
    text-decoration: none;
    font-size: 12px;
    color: var(--r-muted);
  }
  .activity-meta {
    display: flex;
    align-items: center;
    gap: 16px;
    font-size: 11px;
    color: var(--r-muted);
    margin-top: 0;
    flex-wrap: wrap;
  }
  .sport-badge {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    color: var(--r-ink);
    font-weight: 650;
  }
  h1 {
    font-size: clamp(25px, 3vw, 34px);
    letter-spacing: -1px;
    line-height: 1.15;
    margin: 6px 0;
    overflow-wrap: anywhere;
  }
  .activity-athlete {
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--r-muted);
    font-size: 12px;
  }
  .activity-athlete a {
    color: var(--r-ink);
    font-weight: 650;
    text-decoration: none;
  }
  .activity-hero :deep(.feed-actions) {
    margin-top: 12px;
    border-bottom: 1px solid var(--r-line);
    padding: 4px 0;
    justify-content: start;
  }
  .activity-hero :deep(.feed-actions button),
  .activity-hero :deep(.feed-actions a) {
    flex: 0 1 auto;
    min-width: 85px;
  }
</style>

<style scoped>
  @media (min-width: 701px) {
    .activity-hero {
      position: relative;
    }
    .activity-hero :deep(.feed-actions) {
      position: absolute;
      right: 0;
      top: 20px;
      margin: 0;
      border: 0;
      padding: 0;
    }
  }
  @media (max-width: 700px) {
    .back-link {
      min-height: 32px;
    }
    .activity-meta {
      margin-top: 0;
    }
    h1 {
      margin: 5px 0;
    }
    .activity-hero :deep(.feed-actions) {
      margin-top: 10px;
      min-height: 44px;
    }
  }
</style>

<style scoped>
  .activity-hero {
    position: relative;
  }
  .hero-share {
    position: absolute;
    right: 0;
    top: 12px;
    display: flex;
    gap: 7px;
    align-items: center;
    justify-content: center;
    min-height: 44px;
    padding: 0 12px;
    color: var(--r-ink);
    font-size: 12px;
    text-decoration: none;
    border: 1px solid var(--r-line);
    border-radius: 10px;
    background: var(--r-surface);
  }
  @media (max-width: 700px) {
    .hero-share {
      top: 8px;
    }
  }
</style>
