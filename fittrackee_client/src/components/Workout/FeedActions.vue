<template>
  <div
    class="feed-actions"
    :class="{
      'without-share': hideShare,
      'metric-aligned': metricColumns,
      'four-columns': metricColumns === 4,
    }"
  >
    <button
      :aria-label="`${liked ? 'Unlike' : 'Like'} activity (${likes} likes)`"
      :aria-pressed="liked"
      :disabled="busy"
      @click.stop="toggleLike"
    >
      <RintIcon name="heart" />
      <span>{{ liked ? 'Liked' : 'Like' }}</span>
      <span v-if="likes > 0" class="like-count">{{ likes }}</span>
    </button>
    <router-link :to="`/workouts/${workout.id}#bottom`"
      ><RintIcon name="comment" /> Comment</router-link
    >
    <button
      v-if="!hideShare"
      class="share-action"
      aria-label="Share activity"
      title="Share"
      @click.stop="share"
    >
      <RintIcon name="share" />
      <span>Share</span>
    </button>
    <span role="status" v-if="message">{{ message }}</span>
  </div>
</template>
<script setup lang="ts">
  import { ref, watch } from 'vue'

  import authApi from '@/api/authApi'
  import RintIcon from '@/components/Rint/RintIcon.vue'
  import router from '@/router'
  import type { IWorkout } from '@/types/workouts'
  import {
    prepareFeedback,
    playAppreciation,
  } from '@/utils/interactionFeedback'
  const props = defineProps<{
    workout: IWorkout
    configureSharing?: boolean
    hideShare?: boolean
    metricColumns?: number
  }>()
  const liked = ref(props.workout.liked),
    likes = ref(props.workout.likes_count || 0),
    busy = ref(false),
    message = ref('')
  watch(
    () => props.workout.liked,
    (v) => (liked.value = v)
  )
  watch(
    () => props.workout.likes_count,
    (v) => (likes.value = v || 0)
  )
  async function toggleLike() {
    prepareFeedback()
    busy.value = true
    message.value = ''
    try {
      await authApi.post(
        `workouts/${props.workout.id}/like${liked.value ? '/undo' : ''}`
      )
      liked.value = !liked.value
      likes.value += liked.value ? 1 : -1
      if (liked.value) playAppreciation()
    } catch {
      message.value = 'Unable to save your like. Please try again.'
    } finally {
      busy.value = false
    }
  }
  async function share() {
    if (props.configureSharing) {
      await router.push({
        path: '/workouts/' + props.workout.id,
        hash: '#sharing',
      })
      return
    }
    const url = `${location.origin}/workouts/${props.workout.id}`
    try {
      if (navigator.share)
        await navigator.share({ title: props.workout.title, url })
      else {
        await navigator.clipboard.writeText(url)
        message.value = 'Link copied. Activity privacy still applies.'
      }
    } catch (e) {
      if ((e as Error).name !== 'AbortError') message.value = url
    }
  }
</script>
<style scoped>
  .feed-actions {
    box-sizing: border-box;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    align-items: center;
    gap: 4px;
    padding: 0 4px;
    border-top: 1px solid var(--r-line);
  }
  .feed-actions.without-share {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .feed-actions.metric-aligned {
    gap: 8px;
    padding-inline: 16px;
  }
  .feed-actions.four-columns {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
  .four-columns > a {
    grid-column: span 2;
  }
  button,
  a {
    box-sizing: border-box;
    display: inline-flex;
    gap: 5px;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: 0;
    box-shadow: none;
    margin: 0;
    color: var(--r-muted);
    padding: 0 4px;
    font-size: 12px;
    min-height: 44px;
    min-width: 44px;
    text-decoration: none;
    border-radius: 10px;
    cursor: pointer;
    width: 100%;
  }
  .r-icon {
    width: 18px;
    height: 18px;
    flex-shrink: 0;
  }
  .metric-aligned > button,
  .metric-aligned > a {
    justify-content: flex-start;
    padding-inline: 0;
  }
  .like-count {
    font-variant-numeric: tabular-nums;
  }
  button:hover,
  a:hover {
    background: var(--r-soft);
  }
  button[aria-pressed='true'] {
    color: var(--r-heart);
  }
  button[aria-pressed='true'] svg {
    fill: var(--r-heart);
    animation: appreciation 240ms ease-out;
  }
  span[role='status'] {
    grid-column: 1 / -1;
    box-sizing: border-box;
    font-size: 11px;
    padding: 8px;
    color: var(--r-muted);
    width: 100%;
  }
  @keyframes appreciation {
    50% {
      transform: scale(1.18);
    }
  }
  @media (max-width: 700px) {
    .feed-actions.metric-aligned {
      padding-inline: 12px;
    }
  }
  @media (max-width: 350px) {
    .feed-actions.four-columns {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
    .four-columns > a {
      grid-column: auto;
    }
  }
</style>
