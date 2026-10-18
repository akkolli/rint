<template>
  <div
    ref="host"
    class="route-trace"
    :class="{
      'route-trace--compact': !reserveSpace && !hasRoute,
      'route-trace--empty': compact && !loading && !hasRoute && !failed,
    }"
  >
    <ActivityRouteMap
      v-if="hasRoute"
      :points="samples"
      :sampled="!points"
      :compact="compact"
      :selected-time="selectedTime"
      :units="units"
      @select-time="emit('select-time', $event)"
      @metric-change="emit('metric-change', $event)"
    />
    <div v-else class="route-empty">
      <RintIcon :name="loading ? 'clock' : 'map'" />
      <span>{{
        loading
          ? 'Loading route…'
          : failed
            ? 'Route unavailable'
            : compact
              ? 'No route shared'
              : 'No route available'
      }}</span>
      <small v-if="!loading && !compact">{{
        failed
          ? 'Open the activity to try again.'
          : 'Indoor, without GPS, or protected by privacy settings. Your metrics still count.'
      }}</small>
    </div>
  </div>
</template>
<script setup lang="ts">
  import {
    computed,
    defineAsyncComponent,
    onBeforeUnmount,
    onMounted,
    ref,
    watch,
  } from 'vue'

  import authApi from '@/api/authApi'
  import RintIcon from '@/components/Rint/RintIcon.vue'
  import type { Sample } from '@/types/rint'
  import { routeSegments } from '@/utils/activityStream'
  const ActivityRouteMap = defineAsyncComponent(
    () => import('@/components/Rint/ActivityRouteMap.vue')
  )
  const props = defineProps<{
    workoutId?: string
    points?: Sample[]
    reserveSpace?: boolean
    compact?: boolean
    selectedTime?: number
    units?: string
  }>()
  const emit = defineEmits<{
    'select-time': [number]
    'metric-change': [string]
  }>()
  const host = ref<HTMLElement | null>(null),
    loaded = ref<Sample[]>([]),
    loading = ref(Boolean(props.workoutId && !props.points)),
    failed = ref(false)
  const samples = computed(() => props.points || loaded.value)
  const hasRoute = computed(
    () => routeSegments(samples.value, !props.points).length > 0
  )
  let observer: IntersectionObserver | undefined,
    generation = 0
  async function load() {
    if (props.points || !props.workoutId) return
    const current = ++generation
    loading.value = true
    failed.value = false
    try {
      const { data } = await authApi.get(
        'rint/activities/' + props.workoutId + '/preview'
      )
      if (current === generation) loaded.value = data.data.points
    } catch {
      if (current === generation) failed.value = true
    } finally {
      if (current === generation) loading.value = false
    }
  }
  onMounted(() => {
    observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          void load()
          observer?.disconnect()
        }
      },
      { rootMargin: '100px' }
    )
    if (host.value) observer.observe(host.value)
  })
  watch(
    () => props.workoutId,
    () => {
      loaded.value = []
      void load()
    }
  )
  onBeforeUnmount(() => {
    observer?.disconnect()
    generation++
  })
</script>
<style scoped>
  .route-trace {
    position: relative;
    min-height: 240px;
    background: var(--r-soft);
    border-radius: 16px;
    overflow: hidden;
  }
  .route-empty {
    min-height: inherit;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    gap: 10px;
    color: var(--r-muted);
    padding: 16px;
    text-align: center;
  }
  .route-empty .r-icon {
    width: 28px;
    height: 28px;
    color: var(--r-violet);
  }
  .route-empty span {
    font-size: 13px;
    font-weight: 600;
  }
  .route-empty small {
    font-size: 11px;
    max-width: 280px;
  }
  .route-trace--compact {
    min-height: 44px;
    background: transparent;
  }
  .route-trace--compact .route-empty {
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: flex-start;
    padding: 8px 0;
    text-align: left;
    gap: 8px;
  }
  .route-trace--compact .route-empty small {
    flex-basis: 100%;
    max-width: none;
    padding-left: 26px;
  }
  .route-trace--compact .r-icon {
    width: 18px;
    height: 18px;
  }
</style>
