<template>
  <div class="athlete-home">
    <header class="athlete-heading">
      <h1 class="r-page-title">You</h1>
      <router-link class="r-secondary" to="/profile/preferences"
        ><RintIcon name="settings" />Settings</router-link
      >
    </header>
    <UserHeader :user="authUser" :heading-level="2" />
    <div class="athlete-actions">
      <router-link class="r-secondary" to="/profile/edit"
        >Edit profile</router-link
      ><router-link class="r-secondary" :to="'/users/' + authUser.username"
        >View community profile <RintIcon name="arrow"
      /></router-link>
    </div>
    <nav class="athlete-links" aria-label="Your fitness library">
      <router-link to="/workouts"
        ><RintIcon name="list" /><span
          >Activities<small>{{ authUser.nb_workouts }} recorded</small></span
        ><RintIcon name="arrow" /></router-link
      ><router-link to="/migration"
        ><RintIcon name="watch" /><span
          >Imports &amp; data<small>Health, Strava &amp; exports</small></span
        ><RintIcon name="arrow"
      /></router-link>
    </nav>
    <div class="athlete-grid">
      <section>
        <div class="athlete-section-title">
          <h2>Recent activities</h2>
          <router-link to="/workouts"
            >View all <RintIcon name="arrow"
          /></router-link>
        </div>
        <UserWorkoutsList
          v-if="authUser.nb_workouts"
          :auth-user="authUser"
          :user="authUser"
        />
        <div v-else class="athlete-empty">
          <RintIcon name="move" />
          <h2>Your history starts here.</h2>
          <p>Import a workout or add your first activity.</p>
          <router-link class="r-primary" to="/migration"
            >Import workouts</router-link
          >
        </div>
      </section>
      <TrainingSnapshot />
    </div>
  </div>
</template>
<script setup lang="ts">
  import RintIcon from '@/components/Rint/RintIcon.vue'
  import TrainingSnapshot from '@/components/Rint/TrainingSnapshot.vue'
  import UserHeader from '@/components/User/ProfileDisplay/UserHeader.vue'
  import UserWorkoutsList from '@/components/User/ProfileDisplay/UserWorkoutsList.vue'
  import useAuthUser from '@/composables/useAuthUser'
  const { authUser } = useAuthUser()
</script>
<style scoped>
  .athlete-home {
    width: 100%;
    box-sizing: border-box;
    max-width: 1060px;
    margin: auto;
    padding: 36px 26px;
  }
  .athlete-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 26px;
  }
  .athlete-heading a {
    font-size: 13px;
    gap: 8px;
  }
  .athlete-home :deep(.r-profile-hero) {
    border: 0;
    border-radius: 0;
    background: transparent;
    padding: 0;
    margin: 0;
  }
  .athlete-home :deep(.r-profile-hero .r-eyebrow) {
    display: none;
  }
  .athlete-home :deep(.r-profile-hero .user-name) {
    font-size: 30px;
    margin-top: 0;
  }
  .athlete-home :deep(.profile-bio) {
    max-width: 520px;
    font-size: 14px;
  }
  .athlete-home :deep(.profile-stats) {
    padding-top: 18px;
    margin-top: 20px;
  }
  .athlete-actions {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin: 22px 0 28px;
  }
  .athlete-actions a {
    font-size: 12px;
    gap: 8px;
  }
  .athlete-actions svg {
    width: 16px;
  }
  .athlete-links {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    padding: 20px 0;
    border-top: 1px solid var(--r-line);
    border-bottom: 1px solid var(--r-line);
    margin-bottom: 32px;
  }
  .athlete-links a {
    display: flex;
    align-items: center;
    gap: 14px;
    min-height: 44px;
    color: var(--r-ink);
    text-decoration: none;
    font-size: 14px;
    font-weight: 650;
  }
  .athlete-links a > span {
    flex: 1;
  }
  .athlete-links a > svg:first-child {
    width: 24px;
    height: 24px;
    color: var(--r-action);
  }
  .athlete-links a > svg:last-child {
    width: 16px;
  }
  .athlete-links small {
    display: block;
    font-size: 12px;
    font-weight: 400;
    color: var(--r-muted);
    margin-top: 6px;
  }
  .athlete-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 280px;
    gap: 28px;
    align-items: start;
  }
  .athlete-section-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }
  .athlete-section-title h2 {
    font-size: 18px;
    margin: 0;
  }
  .athlete-section-title a {
    min-height: 44px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: var(--r-muted);
    text-decoration: none;
  }
  .athlete-section-title svg {
    width: 16px;
  }
  .athlete-home :deep(#user-workouts .section-title) {
    display: none;
  }
  .athlete-empty {
    padding: 28px;
    background: var(--r-surface);
    border: 1px solid var(--r-line);
    border-radius: 16px;
  }
  .athlete-empty p {
    color: var(--r-muted);
    line-height: 1.5;
  }
  @media (max-width: 1100px) {
    .athlete-grid {
      grid-template-columns: 1fr;
    }
    .athlete-grid > .training-snapshot {
      order: -1;
    }
  }
  @media (max-width: 600px) {
    .athlete-home {
      padding: 24px 6px;
    }
    .athlete-heading {
      margin-bottom: 24px;
    }
    .athlete-links {
      gap: 18px;
    }
    .athlete-links a {
      font-size: 12px;
      gap: 8px;
    }
    .athlete-links a > svg:last-child {
      display: none;
    }
    .athlete-links small {
      font-size: 10px;
      line-height: 1.4;
    }
    .athlete-home :deep(.r-profile-hero .user-name) {
      font-size: 26px;
    }
    .athlete-grid > .training-snapshot {
      display: none;
    }
  }
</style>
