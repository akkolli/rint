<template>
  <div id="users" class="view" v-if="authUser.username">
    <div class="container">
      <header class="r-page-heading">
        <p class="r-eyebrow">YOUR COMMUNITY</p>
        <h1 class="r-page-title">People</h1>
        <p class="r-page-subtitle">
          Find friends and follow the efforts that inspire you.
        </p>
      </header>
      <UsersList :authUser="authUser" />
    </div>
  </div>
</template>

<script setup lang="ts">
  import UsersList from '@/components/Users/UsersList.vue'
  import useAuthUser from '@/composables/useAuthUser'

  const { authUser } = useAuthUser()
</script>
