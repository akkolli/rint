<template>
  <svg
    class="r-icon"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.7"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path :d="paths[name] || paths.move" />
  </svg>
</template>
<script setup lang="ts">
  defineProps<{ name: string }>()
  const paths: Record<string, string> = {
    sound: 'M11 5L6 9H3v6h3l5 4V5zm4 3a6 6 0 010 8m3-11a10 10 0 010 14',
    person: 'M12 12a4 4 0 100-8 4 4 0 000 8zM4 21v-2c0-6 16-6 16 0v2',
    bell: 'M18 8a6 6 0 00-12 0c0 8-3 8-3 10h18c0-2-3-2-3-10M10 22h4',
    chevron: 'M8 10l4 4 4-4',
    settings:
      'M12 8a4 4 0 100 8 4 4 0 000-8zM10 2h4l1 3 3 1 3-1 2 4-2 2v3l2 2-2 4-3-1-3 1-1 3h-4l-1-3-3-1-3 1-2-4 2-2v-3L1 9l2-4 3 1 3-1z',
    list: 'M8 6h12M8 12h12M8 18h12M3 6h.01M3 12h.01M3 18h.01',
    map: 'M9 3L2 6v15l7-3 6 3 7-3V3l-7 3-6-3zm0 0v15m6-12v15',
    sun: 'M12 8a4 4 0 100 8 4 4 0 000-8zM12 2v2m0 16v2M2 12h2m16 0h2M5 5l1 1m12 12 1 1M5 19l1-1M18 6l1-1',
    moon: 'M21 12.8A9 9 0 1111.2 3 7 7 0 0021 12.8z',
    globe:
      'M12 3a9 9 0 100 18 9 9 0 000-18zm0 0c-6 5-6 13 0 18 6-5 6-13 0-18zM3 12h18',
    logout: 'M10 4H4v16h6m-1-8h12m-4-4 4 4-4 4',
    feed: 'M3 10l9-7 9 7v10H3V10zm5 10v-7h8v7',
    move: 'M4 19h4l4-7 3 3h5M9 5l4 2 3 4h4M13 7l-4 4-5-1M16 3h.01',
    chart: 'M4 3v17h17M7 15l4-5 4 3 5-7',
    heart:
      'M20.8 4.6a5.5 5.5 0 00-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 00-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 000-7.8z',
    comment: 'M21 11a9 9 0 01-9 9H3l2-4a9 9 0 1116-5z',
    share: 'M12 16V3m-4 4 4-4 4 4M5 12v8h14v-8',
    plus: 'M12 5v14M5 12h14',
    arrow: 'M4 12h16m-6-6 6 6-6 6',
    shield: 'M12 3l8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3zm-4 9 3 3 5-6',
    watch: 'M8 7V3h8v4M8 17v4h8v-4M6 7h12v10H6zM12 9v4h3',
    upload: 'M12 16V4m-5 5 5-5 5 5M4 16v5h16v-5',
    check: 'M5 12l4 4L19 6',
    people:
      'M8 12a4 4 0 100-8 4 4 0 000 8zm-6 8v-2c0-4 12-4 12 0v2M16 4a4 4 0 010 8m1 3c4 0 5 1 5 5',
    trophy:
      'M7 3h10v6a5 5 0 01-10 0V3zm0 2H3v2c0 3 2 5 5 5m9-7h4v2c0 3-2 5-5 5M12 14v6m-4 1h8',
    clock: 'M12 3a9 9 0 100 18 9 9 0 000-18zm0 4v5l4 2',
  }
</script>
