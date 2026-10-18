<template>
  <section class="r-profile-hero">
    <div class="user-header">
      <div class="follows-you" v-if="user.follows === 'true'">
        {{ $t('user.RELATIONSHIPS.FOLLOWS_YOU') }}
      </div>
      <div
        class="follows-you"
        v-else-if="
          user.username === authUser.username &&
          !$route.path.startsWith('/profile')
        "
      >
        {{ $t('user.YOU') }}
      </div>
      <UserPicture :user="user" />
      <div class="user-details">
        <p class="r-eyebrow">
          {{
            user.username === authUser.username
              ? 'YOUR PROFILE'
              : 'YOUR COMMUNITY'
          }}
        </p>
        <component :is="`h${headingLevel || 1}`" class="user-name">{{
          user.username
        }}</component>
        <p v-if="user.location" class="profile-location">{{ user.location }}</p>
        <p v-if="user.bio" class="profile-bio">{{ user.bio }}</p>
      </div>
      <div class="user-role" v-if="role">
        {{ $t(role) }}
      </div>
      <div class="rss-feed" v-if="route.name === 'User'">
        <a
          :href="userWorkoutAtomFeedURL"
          target="_blank"
          rel="noopener noreferrer"
          :title="$t('workouts.PUBLIC_WORKOUTS_ATOM_FEED')"
        >
          <i class="fa fa-rss" aria-hidden="true"></i>
        </a>
      </div>
    </div>
    <UserStats :user="user" class="profile-stats" />
    <AlertMessage
      message="user.ACCOUNT_SUSPENDED_AT"
      :param="suspensionDate"
      v-if="'suspended_at' in user && user.suspended_at !== null"
    >
      <template
        #additionalMessage
        v-if="displayMakeAppeal || displayReportLink"
      >
        <router-link
          to="/profile/suspension"
          class="appeal-link"
          v-if="displayMakeAppeal"
        >
          {{ $t('user.APPEAL') }}
        </router-link>
        <i18n-t keypath="common.SEE_REPORT" v-if="displayReportLink">
          <router-link :to="`/admin/reports/${user.suspension_report_id}`">
            {{ user.suspension_report_id }}
          </router-link>
        </i18n-t>
      </template>
    </AlertMessage>
  </section>
</template>

<script setup lang="ts">
  import { computed, type ComputedRef, toRefs } from 'vue'
  import { useRoute } from 'vue-router'

  import UserPicture from '@/components/User/UserPicture.vue'
  import UserStats from '@/components/User/UserStats.vue'
  import useApp from '@/composables/useApp'
  import useAuthUser from '@/composables/useAuthUser'
  import type { IUserProfile } from '@/types/user'
  import { getApiUrl } from '@/utils'
  import { formatDate } from '@/utils/dates'

  interface Props {
    user: IUserProfile
    headingLevel?: 1 | 2
  }
  const props = defineProps<Props>()
  const { user } = toRefs(props)

  const route = useRoute()

  const { appLanguage, displayOptions } = useApp()
  const { authUser, authUserHasModeratorRights } = useAuthUser()

  const suspensionDate: ComputedRef<string | null> = computed(() =>
    user.value.suspended_at
      ? formatDate(
          user.value.suspended_at,
          displayOptions.value.timezone,
          displayOptions.value.dateFormat
        )
      : ''
  )
  const displayMakeAppeal: ComputedRef<boolean> = computed(
    () =>
      user.value.suspended_at !== null &&
      route.name !== 'AuthUserAccountSuspension' &&
      user.value.username === authUser?.value.username
  )
  const displayReportLink: ComputedRef<boolean> = computed(
    () =>
      authUserHasModeratorRights.value &&
      user.value.suspension_report_id !== undefined
  )
  const role: ComputedRef<string> = computed(() =>
    user.value.role !== 'user' ? `user.ROLES.${user.value.role}` : ''
  )
  const userWorkoutAtomFeedURL: ComputedRef<string> = computed(() =>
    getuserWorkoutAtomFeedURL()
  )

  function getuserWorkoutAtomFeedURL() {
    const apiUrl = getApiUrl().replace('/api/', '')
    const feedUrl = `${apiUrl}/users/${user.value.username}/workouts.atom`
    const lang = appLanguage.value === 'en' ? '' : `?lang=${appLanguage.value}`
    const imperialUnits = displayOptions.value.useImperialUnits
      ? `${lang ? '&' : '?'}imperial_units=true`
      : ''
    return `${feedUrl}${lang}${imperialUnits}`
  }
</script>

<style lang="scss" scoped>
  .r-profile-hero {
    position: relative;
    padding: 28px;
    border-radius: 24px;
    background: var(--r-surface);
    border: 1px solid var(--r-line);
  }
  .user-header {
    display: flex;
    align-items: center;
    gap: 24px;
  }
  .user-details {
    flex: 1;
    min-width: 0;
  }
  .user-name {
    margin: 4px 0 8px;
    font-size: clamp(28px, 5vw, 40px);
    font-weight: 750;
    letter-spacing: -1px;
    overflow-wrap: anywhere;
  }
  .profile-location,
  .profile-bio {
    color: var(--r-muted);
    margin: 8px 0;
    line-height: 1.5;
    white-space: pre-wrap;
  }
  .follows-you {
    position: absolute;
    top: 16px;
    right: 20px;
    font-size: 11px;
    color: var(--r-action);
    background: var(--r-soft);
    padding: 4px 8px;
    border-radius: 20px;
  }
  .rss-feed {
    position: absolute;
    right: 20px;
    bottom: 24px;
  }
  .profile-stats {
    margin-top: 24px;
    padding-top: 20px;
    border-top: 1px solid var(--r-line);
    display: flex;
    gap: 32px;
  }
  :deep(.user-stat) {
    flex-direction: column;
    gap: 6px;
  }
  :deep(.stat-number) {
    font-size: 24px;
    padding: 0;
  }
  :deep(.stat-label) {
    color: var(--r-muted);
    font-size: 12px;
    padding: 0;
  }
  :deep(.user-picture img) {
    height: 72px;
    width: 72px;
    border-radius: 50%;
  }
  :deep(.user-picture .no-picture) {
    font-size: 72px;
    color: var(--r-action);
  }
  @media (max-width: 600px) {
    .r-profile-hero {
      padding: 22px;
    }
    .user-header {
      gap: 16px;
    }
    .profile-stats {
      gap: 24px;
    }
    :deep(.user-picture img) {
      width: 56px;
      height: 56px;
    }
    :deep(.user-picture .no-picture) {
      font-size: 56px;
    }
  }
</style>
