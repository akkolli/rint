<template>
  <div class="user-picture">
    <img
      v-if="authUserPictureUrl !== ''"
      class="profile-user-img"
      :alt="$t('user.USER_PICTURE')"
      :src="authUserPictureUrl"
    />
    <div v-else class="no-picture" :aria-label="user.username">
      <span class="r-initials" aria-hidden="true">{{
        user.username?.slice(0, 2).toUpperCase() || 'R'
      }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { computed, toRefs } from 'vue'

  import type { IUserLightProfile, IUserProfile } from '@/types/user'
  import { getApiUrl } from '@/utils'

  interface Props {
    user: IUserProfile | IUserLightProfile
  }
  const props = defineProps<Props>()
  const { user } = toRefs(props)

  const authUserPictureUrl = computed(() =>
    user.value.picture
      ? `${getApiUrl()}users/${user.value.username}/picture?${Date.now()}`
      : ''
  )
</script>

<style lang="scss">
  .user-picture {
    display: flex;
    justify-content: center;
    align-items: center;
    min-width: 30%;
    line-height: 1.2em;
    img {
      border-radius: 50%;
      height: 90px;
      width: 90px;
    }
    .r-initials {
      display: grid;
      place-items: center;
      width: 1em;
      height: 1em;
      border-radius: 50%;
      background: var(--r-soft);
      color: var(--r-action);
      font-size: 0.38em;
      width: 2.63em;
      height: 2.63em;
      font-weight: 750;
      letter-spacing: -0.04em;
      overflow: hidden;
    }
    .r-initials::first-letter {
      font-size: inherit;
    }
    .no-picture {
      color: var(--app-a-color);
      font-size: 5.5em;
    }
  }
</style>
