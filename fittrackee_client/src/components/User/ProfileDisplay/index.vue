<template>
  <AthleteHome v-if="$route.path === '/profile' && !isSuspended" />
  <div v-else id="user-profile">
    <header class="settings-heading">
      <router-link to="/profile">← You</router-link>
      <h1 class="r-page-title">Settings</h1>
    </header>
    <div class="box r-settings-layout">
      <UserProfileTabs :tabs="tabs" :selectedTab="tab" :edition="false" />
      <router-view :user="user"></router-view>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { computed, toRefs } from 'vue'
  import type { ComputedRef } from 'vue'

  import AthleteHome from '@/components/Rint/AthleteHome.vue'
  import UserProfileTabs from '@/components/User/UserProfileTabs.vue'
  import { AUTH_USER_STORE } from '@/store/constants'
  import type { IUserProfile } from '@/types/user'
  import { useStore } from '@/use/useStore'

  interface Props {
    user: IUserProfile
    tab: string
  }
  const props = defineProps<Props>()
  const { user, tab } = toRefs(props)

  const store = useStore()

  const isSuspended: ComputedRef<boolean> = computed(
    () => store.getters[AUTH_USER_STORE.GETTERS.IS_SUSPENDED]
  )
  const tabs = computed(() =>
    isSuspended.value
      ? [
          'PROFILE',
          'ACCOUNT',
          'PREFERENCES',
          'SPORTS',
          'EQUIPMENTS',
          'APPS',
          'MODERATION',
        ]
      : [
          'PROFILE',
          'ACCOUNT',
          'PREFERENCES',
          'SPORTS',
          'EQUIPMENTS',
          'APPS',
          'FOLLOW-REQUESTS',
          'BLOCKED-USERS',
          'NOTIFICATIONS',
          'MESSAGES',
          'MODERATION',
          'ARCHIVE-UPLOADS',
        ]
  )
</script>

<style lang="scss" scoped>
  @use '~@/scss/vars.scss' as *;

  .settings-heading {
    margin: 8px 0 24px;
  }
  .settings-heading a {
    display: inline-flex;
    align-items: center;
    min-height: 44px;
    font-size: 13px;
    color: var(--r-muted);
    text-decoration: none;
    margin-bottom: 12px;
  }
  #user-profile {
    margin: auto;
    width: 700px;
    @media screen and (max-width: $medium-limit) {
      width: 100%;
      margin: 0 auto 50px auto;
    }
  }
</style>
