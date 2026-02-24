// src/stores/user.ts
import {defineStore} from 'pinia'
import {computed, ref} from 'vue'
import {request, type Response} from 'brtech-fusion' // 假设你有一个封装好的 axios request

interface UserInfo {
  modelId: string;
  userName: string;
  userAvatar: string;
  userEmail: string;
  userPhone: string;
}

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')

  const userInfo = ref<UserInfo>()

  const userAvatar = ref<string>()
  const userName = ref<string>()

  const isLoggedIn = computed(() => !!token.value)

  async function handleLoginSuccess(newToken: string) {
    token.value = newToken
    localStorage.setItem('token', newToken)

    await fetchUserInfo()
  }

  async function fetchUserInfo() {
    if (!token.value) {
      return
    }
    try {
      const {data: response} = await request.post<Response<UserInfo>>('/auth/detail')
      if (response.flag && response.data) {
        userInfo.value = response.data;
        userName.value = response.data.userName
        if (userInfo.value?.userAvatar) {
          const formData = new FormData()
          formData.append('objectKey', userInfo.value.userAvatar)
          const {data: response} = await request.post<Response<string>>('/4a/user/storage/signedUrl/download', formData, {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            }
          })
          if (response.flag && response.data) {
            userAvatar.value = response.data
          }
        }
      }
    } catch (error) {
      console.error('获取用户信息失败', error)
    }
  }

  function logout() {
    token.value = ''
    userInfo.value = {
      modelId: '',
      userName: '',
      userAvatar: '',
      userEmail: '',
      userPhone: ''
    }
    localStorage.removeItem('token')
  }

  function initUser() {
    if (token.value) {
      fetchUserInfo().then(r => {
      })
    }
  }

  return {
    token,
    userAvatar,
    userName,
    userInfo,
    isLoggedIn,
    handleLoginSuccess,
    fetchUserInfo,
    logout,
    initUser
  }
})