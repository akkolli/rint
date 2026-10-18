<template>
  <header
    id="nav"
    class="r-nav"
    :class="{ 'r-nav--signed': isAuthenticated && !isAuthUserSuspended }"
  >
    <Modal
      v-if="displayModal"
      :title="$t('common.CONFIRMATION')"
      :message="$t('user.LOGOUT_CONFIRMATION')"
      :hide-error-message="true"
      @confirmAction="logout"
      @cancelAction="updateDisplayModal(false)"
      @keydown.esc="updateDisplayModal(false)"
    />
    <router-link
      class="r-wordmark"
      to="/"
      id="fittrackee-name"
      aria-label="Rint home"
      ><span aria-hidden="true">r.</span>rint</router-link
    >
    <div class="r-header-actions">
      <router-link
        v-if="isAuthenticated && !isAuthUserSuspended"
        class="r-icon-button"
        to="/notifications?status=unread"
        aria-label="Notifications"
        :class="{ unread: hasUnreadNotifications }"
        ><RintIcon name="bell"
      /></router-link>
      <details
        v-if="isAuthenticated"
        ref="accountMenu"
        class="r-account-menu"
        @keydown.esc="dismissMenu"
      >
        <summary aria-label="Account menu">
          <UserPicture :user="authUser" /><span>{{ authUser.username }}</span
          ><RintIcon name="chevron" />
        </summary>
        <div class="r-account-options">
          <router-link to="/profile" @click="closeMenu"
            ><RintIcon name="person" />Your profile</router-link
          >
          <router-link to="/migration" @click="closeMenu"
            ><RintIcon name="watch" />Imports &amp; your data</router-link
          >
          <router-link to="/profile/preferences" @click="closeMenu"
            ><RintIcon name="settings" />Settings &amp; privacy</router-link
          >
          <router-link
            v-if="authUserHasModeratorRights"
            to="/admin"
            @click="closeMenu"
            ><RintIcon name="shield" />Administration</router-link
          >
          <button @click="toggleTheme">
            <RintIcon name="sun" />{{
              darkTheme ? 'Light appearance' : 'Dark appearance'
            }}
          </button>
          <button
            :aria-pressed="interactionSounds"
            @click="toggleInteractionSounds"
          >
            <RintIcon name="sound" />Interaction sounds:
            {{ interactionSounds ? 'on' : 'off' }}
          </button>
          <Dropdown
            v-if="availableLanguages && appLanguage"
            :options="availableLanguages"
            :selected="appLanguage"
            @selected="updateLanguage"
            :buttonLabel="$t('user.LANGUAGE')"
            :listLabel="$t('user.LANGUAGE', 0)"
            :isMenuOpen="isMenuOpen"
            ><RintIcon name="globe" /><span>Language</span></Dropdown
          >
          <button @click="updateDisplayModal(true)">
            <RintIcon name="logout" />{{ $t('user.LOGOUT') }}
          </button>
        </div>
      </details>
      <template v-else>
        <button
          class="r-visitor-theme"
          @click="toggleTheme"
          :aria-label="`${$t('user.TOGGLE_THEME')} (${$t('user.PROFILE.THEME_MODE.VALUES.' + themeMode)})`"
          :title="$t('user.PROFILE.THEME_MODE.VALUES.' + themeMode)"
        >
          <RintIcon :name="darkTheme ? 'moon' : 'sun'" />
        </button>
        <Dropdown
          v-if="availableLanguages && appLanguage"
          :options="availableLanguages"
          :selected="appLanguage"
          @selected="updateLanguage"
          :buttonLabel="$t('user.LANGUAGE')"
          :listLabel="$t('user.LANGUAGE', 0)"
          :isMenuOpen="false"
          ><RintIcon name="globe"
        /></Dropdown>
        <router-link to="/login">Sign in</router-link
        ><router-link to="/register">Join Rint</router-link></template
      >
    </div>
    <aside v-if="isAuthenticated && !isAuthUserSuspended" class="r-sidebar">
      <nav class="r-primary-nav" aria-label="Primary navigation">
        <router-link
          v-for="item in destinations"
          :key="item.to"
          :to="item.to"
          :class="{ active: active(item.to), 'r-add-destination': item.short }"
          @click="closeMenu"
          ><RintIcon :name="item.icon" /><span class="r-nav-long">{{
            item.label
          }}</span
          ><span class="r-nav-short">{{
            item.short || item.label
          }}</span></router-link
        >
      </nav>
      <nav class="r-library-nav" aria-label="Your library">
        <p>YOUR LIBRARY</p>
        <router-link
          to="/workouts"
          :class="{ active: route.path === '/workouts' }"
          ><RintIcon name="list" />Activities</router-link
        >
        <router-link
          to="/workouts/map"
          :class="{ active: route.path === '/workouts/map' }"
          ><RintIcon name="map" />Activity map</router-link
        >
        <router-link to="/migration" :class="{ active: active('/migration') }"
          ><RintIcon name="watch" />Imports &amp; data</router-link
        >
      </nav>
      <div class="r-sidebar-bottom">
        <router-link to="/profile/preferences"
          ><RintIcon name="settings" />Settings &amp; privacy</router-link
        >
        <p>Open source</p>
      </div>
    </aside>
  </header>
</template>
<script setup lang="ts">
  import { computed, ref } from 'vue'
  import type { ComputedRef, Ref } from 'vue'
  import { useRoute } from 'vue-router'

  import RintIcon from '@/components/Rint/RintIcon.vue'
  import UserPicture from '@/components/User/UserPicture.vue'
  import useApp from '@/composables/useApp'
  import useAuthUser from '@/composables/useAuthUser'
  import {
    AUTH_USER_STORE,
    NOTIFICATIONS_STORE,
    ROOT_STORE,
  } from '@/store/constants'
  import type { IDropdownOption } from '@/types/forms'
  import type { TLanguage } from '@/types/locales'
  import { useStore } from '@/use/useStore'
  import {
    interactionSounds,
    toggleInteractionSounds,
  } from '@/utils/interactionFeedback'
  import { availableLanguages } from '@/utils/locales'

  const emit = defineEmits(['menuInteraction'])

  const route = useRoute()
  const destinations = [
    { to: '/', label: 'Feed', icon: 'feed' },
    { to: '/progress', label: 'Progress', icon: 'chart' },
    { to: '/workouts/add', label: 'Add activity', short: 'Add', icon: 'plus' },
    { to: '/users', label: 'People', icon: 'people' },
    { to: '/profile', label: 'You', icon: 'person' },
  ]
  function active(path: string) {
    return path === '/'
      ? route.path === '/'
      : route.path === path || route.path.startsWith(path + '/')
  }
  const store = useStore()

  const { appLanguage, darkMode, darkTheme } = useApp()
  const themeMode = computed(() =>
    darkMode.value === null ? 'DEFAULT' : darkMode.value ? 'DARK' : 'LIGHT'
  )
  const {
    authUser,
    isAuthenticated,
    isAuthUserSuspended,
    authUserHasModeratorRights,
  } = useAuthUser()

  const isMenuOpen: Ref<boolean> = ref(false)
  const displayModal: Ref<boolean> = ref(false)

  const hasUnreadNotifications: ComputedRef<boolean> = computed(
    () => store.getters[NOTIFICATIONS_STORE.GETTERS.UNREAD_STATUS]
  )

  const accountMenu = ref<HTMLDetailsElement | null>(null)
  function dismissMenu() {
    closeMenu()
    accountMenu.value?.querySelector('summary')?.focus()
  }
  function closeMenu() {
    if (accountMenu.value) accountMenu.value.open = false
    isMenuOpen.value = false
    emit('menuInteraction', false)
  }
  function updateLanguage(option: IDropdownOption) {
    store.dispatch(
      ROOT_STORE.ACTIONS.UPDATE_APPLICATION_LANGUAGE,
      option.value as TLanguage
    )
  }
  function logout() {
    store.dispatch(AUTH_USER_STORE.ACTIONS.LOGOUT)
    displayModal.value = false
  }
  function updateDisplayModal(display: boolean) {
    closeMenu()
    displayModal.value = display
  }
  function toggleTheme() {
    store.commit(ROOT_STORE.MUTATIONS.UPDATE_DARK_MODE, !darkTheme.value)
  }
</script>

<style scoped>
  .r-visitor-theme {
    display: grid;
    place-items: center;
    min-width: 44px;
    min-height: 44px;
    border: 0;
    background: transparent;
    color: var(--r-ink);
  }
  .r-nav {
    height: 76px;
    display: flex;
    align-items: center;
    padding: 0 32px;
    gap: 32px;
    border-bottom: 1px solid var(--r-line);
    background: var(--r-surface);
  }
  .r-wordmark {
    display: flex;
    align-items: center;
    gap: 11px;
    color: var(--r-ink);
    text-decoration: none;
    font-size: 28px;
    font-weight: 850;
    letter-spacing: -1.6px;
    width: 152px;
    flex-shrink: 0;
  }
  .r-wordmark > span {
    display: grid;
    place-items: center;
    width: 34px;
    height: 34px;
    border-radius: 11px;
    background: var(--r-accent);
    color: #202719;
    font-style: italic;
    font-size: 27px;
    padding-right: 3px;
    box-sizing: border-box;
  }
  .r-header-actions {
    display: flex;
    align-items: center;
    gap: 18px;
    margin-left: auto;
  }
  .r-icon-button {
    width: 44px;
    height: 44px;
    display: grid;
    place-items: center;
    color: var(--r-ink);
    position: relative;
  }
  .unread::after {
    content: '';
    position: absolute;
    top: 8px;
    right: 9px;
    width: 7px;
    height: 7px;
    border: 2px solid var(--r-surface);
    background: var(--r-violet);
    border-radius: 50%;
  }
  .r-account-menu {
    position: relative;
  }
  .r-account-menu summary {
    min-height: 44px;
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    list-style: none;
    font-size: 13px;
    font-weight: 600;
  }
  .r-account-menu summary::-webkit-details-marker {
    display: none;
  }
  .r-account-menu summary > span {
    max-width: 160px;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .r-account-menu :deep(.user-picture) {
    min-width: 32px;
  }
  .r-account-menu :deep(.user-picture img) {
    width: 32px;
    height: 32px;
  }
  .r-account-menu :deep(.no-picture) {
    font-size: 32px;
  }
  .r-account-options {
    position: absolute;
    right: 0;
    top: 52px;
    width: 256px;
    padding: 8px;
    z-index: 1100;
    border: 1px solid var(--r-line);
    background: var(--r-surface);
    border-radius: 14px;
    box-shadow: 0 12px 40px #17211c1a;
  }
  .r-account-options a,
  .r-account-options > button {
    display: flex;
    align-items: center;
    gap: 12px;
    min-height: 44px;
    padding: 0 12px;
    border: 0;
    border-radius: 8px;
    text-decoration: none;
    color: var(--r-ink);
    background: transparent;
    font-size: 14px;
    width: 100%;
    box-sizing: border-box;
  }
  .r-account-options a:hover,
  .r-account-options > button:hover {
    background: var(--r-soft);
  }
  .r-account-options :deep(.dropdown-button) {
    display: flex;
    align-items: center;
    gap: 12px;
    min-height: 44px;
  }
  .r-sidebar {
    position: fixed;
    top: 77px;
    bottom: 0;
    left: 0;
    width: 216px;
    box-sizing: border-box;
    border-right: 1px solid var(--r-line);
    padding: 28px 18px 20px;
    background: var(--r-surface);
    display: flex;
    flex-direction: column;
    z-index: 900;
  }
  .r-primary-nav,
  .r-library-nav {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }
  .r-sidebar a {
    display: flex;
    gap: 14px;
    align-items: center;
    min-height: 48px;
    padding: 0 16px;
    text-decoration: none;
    font-size: 14px;
    font-weight: 550;
    color: var(--r-muted);
    border-radius: 10px;
    transition:
      background 160ms ease,
      color 160ms ease;
  }
  .r-sidebar a:hover {
    color: var(--r-ink);
    background: var(--r-soft);
  }
  .r-sidebar a.active {
    background: var(--r-soft);
    color: var(--r-ink);
    font-weight: 750;
    box-shadow: inset 3px 0 var(--r-distance);
  }
  .r-sidebar .r-add-destination {
    margin: 6px 0;
    color: var(--r-ink);
  }
  .r-add-destination svg {
    background: var(--r-accent);
    color: #202719;
    border-radius: 50%;
    padding: 5px;
    margin: -5px;
  }
  .r-nav-short {
    display: none;
  }
  .r-library-nav {
    margin-top: 32px;
    border-top: 1px solid var(--r-line);
    padding-top: 20px;
  }
  .r-library-nav p {
    font-size: 10px;
    letter-spacing: 1.4px;
    font-weight: 700;
    color: var(--r-muted);
    padding: 0 16px;
    margin: 0 0 8px;
  }
  .r-sidebar-bottom {
    margin-top: auto;
    padding-top: 24px;
  }
  .r-sidebar-bottom a {
    font-size: 12px;
  }
  .r-sidebar-bottom p {
    font-size: 10px;
    color: var(--r-muted);
    padding: 0 16px;
  }
  @media (min-width: 901px) {
    .r-nav--signed {
      position: sticky;
      top: 0;
      z-index: 950;
    }
  }
  @media (max-width: 900px) {
    .r-nav {
      height: 62px;
      padding: 0 20px;
      gap: 12px;
    }
    .r-wordmark {
      width: auto;
      font-size: 26px;
    }
    .r-wordmark > span {
      width: 30px;
      height: 30px;
      font-size: 24px;
      border-radius: 9px;
    }
    .r-account-menu summary > span,
    .r-account-menu summary > svg,
    .r-library-nav,
    .r-sidebar-bottom {
      display: none;
    }
    .r-header-actions {
      gap: 8px;
    }
    .r-sidebar {
      top: auto;
      right: 0;
      width: 100%;
      bottom: 0;
      padding: 5px 8px calc(5px + env(safe-area-inset-bottom));
      border-top: 1px solid var(--r-line);
      border-right: 0;
    }
    .r-primary-nav {
      flex-direction: row;
      justify-content: space-around;
      gap: 0;
    }
    .r-primary-nav a {
      flex: 1;
      flex-direction: column;
      gap: 5px;
      min-height: 55px;
      padding: 6px 0;
      box-sizing: border-box;
      border-radius: 0;
      font-size: 10px;
      font-weight: 650;
    }
    .r-primary-nav a.active {
      background: transparent;
      color: var(--r-ink);
      box-shadow: none;
    }
    .r-primary-nav a.active svg {
      color: var(--r-action);
      stroke-width: 2.4;
    }
    .r-primary-nav .r-add-destination {
      margin: 0;
    }
    .r-primary-nav .r-add-destination svg {
      margin: -3px 0 1px;
      padding: 3px;
    }
    .r-nav-long {
      display: none;
    }
    .r-nav-short {
      display: inline;
    }
  }
</style>
