<template>
  <div id="notifications" class="view items-list-view">
    <header class="r-page-heading">
      <p class="r-eyebrow">YOUR COMMUNITY</p>
      <h1>Notifications</h1>
      <p>Encouragement, conversations and requests from your people.</p>
    </header>
    <div class="container items-list-container">
      <div
        id="notification-filters"
        class="filters-container"
        :class="{ hidden: hiddenFilters }"
      >
        <NotificationsFilters />
      </div>
      <div class="display-filters">
        <button
          @click="toggleFilters"
          :aria-expanded="!hiddenFilters"
          aria-controls="notification-filters"
        >
          <i
            :class="`fa fa-caret-${hiddenFilters ? 'down' : 'up'}`"
            aria-hidden="true"
          />
          <span>
            {{ $t(`workouts.${hiddenFilters ? 'DISPLAY' : 'HIDE'}_FILTERS`) }}
          </span>
        </button>
      </div>
      <div class="list-container">
        <Notifications />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref } from 'vue'
  import type { Ref } from 'vue'

  import Notifications from '@/components/Notifications/Notifications.vue'
  import NotificationsFilters from '@/components/Notifications/NotificationsFilters.vue'

  const hiddenFilters: Ref<boolean> = ref(true)

  function toggleFilters() {
    hiddenFilters.value = !hiddenFilters.value
  }
</script>
