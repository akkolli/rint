<template>
  <div id="dashboard" class="view" v-if="authUser.username && sports.length">
    <div class="r-dashboard">
      <header class="daily-header">
        <div>
          <p class="r-eyebrow">Your training, at a glance</p>
          <h1 class="r-page-title">Overview<span class="title-dot">.</span></h1>
        </div>
        <router-link class="r-secondary" to="/users"
          ><RintIcon name="people" /><span>Find people</span></router-link
        >
      </header>
      <PrivacyPolicyToAccept
        v-if="authUser.accepted_privacy_policy !== true"
        :is-privacy-updated="authUser.accepted_privacy_policy === false"
      />
      <TrainingSnapshot />
      <div class="dashboard-grid">
        <section class="feed-column" aria-label="Social feed">
          <div class="feed-heading">
            <h2>Activity feed</h2>
            <span>Latest first</span>
          </div>
          <Timeline :sports="sports" :authUser="authUser" />
        </section>
        <aside class="training-column">
          <section class="quick-library">
            <h2>Your library</h2>
            <router-link to="/migration"
              ><span class="quick-icon"><RintIcon name="watch" /></span
              ><span
                >Bring your history<small
                  >Apple Health, Strava or a recording</small
                ></span
              ><RintIcon name="arrow" /></router-link
            ><router-link to="/workouts"
              ><span class="quick-icon"><RintIcon name="list" /></span
              ><span
                >All your activities<small
                  >{{ authUser.nb_workouts }} efforts, in one place</small
                ></span
              ><RintIcon name="arrow"
            /></router-link>
          </section>
          <section class="training-tools">
            <h2>Training calendar</h2>
            <UserCalendar :sports="sports" :user="authUser" />
          </section>
        </aside>
      </div>
    </div>
    <div id="bottom" />
  </div>
  <div v-else class="app-loading"><Loader /></div>
</template>
<script setup lang="ts">
  import { onBeforeMount } from 'vue'

  import Timeline from '@/components/Dashboard/Timeline.vue'
  import UserCalendar from '@/components/Dashboard/UserCalendar/index.vue'
  import PrivacyPolicyToAccept from '@/components/PrivacyPolicyToAccept.vue'
  import RintIcon from '@/components/Rint/RintIcon.vue'
  import TrainingSnapshot from '@/components/Rint/TrainingSnapshot.vue'
  import useAuthUser from '@/composables/useAuthUser'
  import useSports from '@/composables/useSports'
  import { AUTH_USER_STORE } from '@/store/constants'
  import { useStore } from '@/use/useStore'
  const store = useStore(),
    { authUser } = useAuthUser(),
    { sports } = useSports()
  onBeforeMount(() =>
    store.dispatch(AUTH_USER_STORE.ACTIONS.GET_USER_PROFILE, {})
  )
</script>
<style scoped>
  .r-dashboard {
    max-width: 1160px;
    margin: auto;
    padding: 28px 32px 40px;
  }
  .daily-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    margin-bottom: 22px;
  }
  .daily-header .r-eyebrow {
    margin: 0 0 8px;
    font-size: 10px;
    letter-spacing: 0.14em;
  }
  .title-dot {
    color: var(--r-distance);
  }
  .daily-header .r-secondary {
    font-size: 12px;
    gap: 8px;
  }
  .dashboard-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 260px;
    gap: 28px;
    align-items: start;
    margin-top: 28px;
  }
  .feed-column {
    min-width: 0;
  }
  h2 {
    font-size: 15px;
    letter-spacing: -0.3px;
    margin: 0;
  }
  .feed-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 14px;
    min-height: 24px;
  }
  .feed-heading > span {
    font-size: 11px;
    color: var(--r-muted);
  }
  .feed-column :deep(#timeline > .section-title) {
    display: none;
  }
  .training-column {
    display: flex;
    flex-direction: column;
    gap: 28px;
  }
  .quick-library h2,
  .training-tools h2 {
    margin-bottom: 14px;
  }
  .quick-library a {
    display: flex;
    align-items: center;
    gap: 10px;
    min-height: 70px;
    border-bottom: 1px solid var(--r-line);
    text-decoration: none;
    color: var(--r-ink);
    font-size: 12px;
    font-weight: 600;
  }
  .quick-library a > span:nth-child(2) {
    flex: 1;
  }
  .quick-library small {
    display: block;
    color: var(--r-muted);
    font-size: 11px;
    font-weight: 400;
    margin-top: 5px;
    line-height: 1.4;
  }
  .quick-library a > svg {
    width: 16px;
    transition: transform 180ms ease;
  }
  .quick-library a:hover > svg {
    transform: translateX(3px);
  }
  .quick-icon {
    padding: 9px;
    border-radius: 12px;
    background: var(--r-soft);
    color: var(--r-distance);
    display: flex;
  }
  .training-tools :deep(.box) {
    background: transparent;
    border: 0;
    padding: 0;
    margin: 0;
  }
  .training-tools :deep(.section-title) {
    display: none;
  }
  @media (min-width: 901px) and (max-width: 1150px) {
    .r-dashboard {
      padding: 24px;
    }
    .dashboard-grid {
      grid-template-columns: minmax(0, 1fr) 220px;
      gap: 20px;
    }
  }
  @media (max-width: 700px) {
    .r-dashboard {
      padding: 16px 16px 24px;
    }
    .daily-header {
      margin-bottom: 16px;
    }
    .daily-header .r-eyebrow {
      font-size: 9px;
      letter-spacing: 0.1em;
    }
    .daily-header .r-secondary {
      padding: 0 12px;
    }
    .dashboard-grid {
      display: block;
      margin-top: 22px;
    }
    .training-column {
      display: none;
    }
  }
</style>
