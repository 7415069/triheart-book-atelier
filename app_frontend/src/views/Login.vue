<!-- src/views/LoginView.vue -->
<template>
  <div class="login-view-wrapper">
    <Login @login-success="handleLoginSuccess"/>
  </div>
</template>

<script setup lang="ts">
import {useRouter} from 'vue-router'
import {useUserStore} from '@/stores/user'
import {Login} from 'brtech-fusion'

const router = useRouter()
const userStore = useUserStore()

const handleLoginSuccess = async (token: string) => {
  console.log('登录成功，Token:', token)

  await userStore.handleLoginSuccess(token)

  const targetPath = window.history.state?.loginSuccessJumpToUrl

  if (targetPath) {
    await router.replace(targetPath)
  } else {
    await router.replace('/')
  }
}
</script>

<style scoped>
.login-view-wrapper {
  width: 100vw;
  height: 100vh;
  position: relative;
  z-index: 999;
}
</style>