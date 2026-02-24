<!-- src/components/portal/Header.vue -->
<template>
  <header class="header-wrapper">
    <div class="header-inner page-container">

      <!-- Brand -->
      <div class="brand" @click="router.push('/')">
        <img src="/static/logo.svg" class="brand-logo" alt="Logo"/>
        <span class="brand-text">三心书坊</span>
        <span class="brand-slogan hidden-xs">- 实现知识自由的铲子</span>
      </div>

      <!-- Desktop Nav Right -->
      <div class="nav-right desktop-only">
        <!-- 1. 未登录 -->
        <div v-if="!isLoggedIn" class="auth-btns">
          <el-button class="btn btn-outline" @click="handleLoginClick">登录</el-button>
        </div>

        <!-- 2. 已登录 User Profile -->
        <div v-else class="user-area">
          <el-icon class="bell-icon" :size="20">
            <Bell/>
          </el-icon>
          <div class="avatar-container">
            <!-- 使用 resolveCachedUrl 处理头像 -->
            <el-avatar :size="32" :src="resolveCachedUrl(userAvatar)" class="avatar-img"/>
            <span class="username">{{ displayName }}</span>
          </div>

          <!-- Dropdown (Hover) -->
          <div class="user-dropdown">
            <!-- 动态渲染菜单 -->
            <template v-for="action in userActions" :key="action.key">
              <template v-if="['portal', 'any'].includes(action.platform)">
                <div v-if="action.actionType === 'divider'" class="menu-divider"></div>
                <div v-else class="menu-item" @click="handleAction(action)" :class="{ 'highlight': action.key === 'bookshelf', 'danger-text': action.key === 'logout' }">
                  <el-icon v-if="action.icon" style="margin-right: 8px; vertical-align: middle;">
                    <component :is="iconMap[action.icon] || 'Operation'"/>
                  </el-icon>
                  <span>{{ action.title }}</span>
                </div>
              </template>
            </template>
          </div>
        </div>
      </div>

      <!-- Mobile Menu Button -->
      <div class="mobile-menu-btn mobile-only" @click="showMobileMenu = !showMobileMenu">
        <el-icon :size="24">
          <Menu/>
        </el-icon>
      </div>
    </div>

    <!-- Mobile Drawer -->
    <transition name="slide-down">
      <div v-if="showMobileMenu" class="mobile-drawer">
        <div v-if="!isLoggedIn" class="mobile-auth">
          <button class="btn btn-outline block" @click="handleLoginClick">登录</button>
        </div>

        <div v-else class="mobile-user">
          <div class="mobile-user-info">
            <el-avatar :size="40" :src="resolveCachedUrl(userAvatar)"/>
            <div>
              <div class="username">{{ displayName }}</div>
            </div>
          </div>
          <div class="mobile-links">
            <template v-for="action in userActions" :key="'m-' + action.key">
              <div v-if="action.actionType === 'divider'" style="border-bottom: 1px solid #f0f0f0; margin: 5px 0;"></div>
              <div v-else class="m-link" @click="handleAction(action)" :class="{ 'logout': action.key === 'logout' }">
                <el-icon v-if="action.icon" style="margin-right: 6px; font-size: 14px;">
                  <component :is="iconMap[action.icon] || 'Operation'"/>
                </el-icon>
                {{ action.title }}
              </div>
            </template>
          </div>
        </div>
      </div>
    </transition>

    <UserActionExecutor ref="userActionExecutorRef" @command="handleExecutorCommand"/>

  </header>
</template>

<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {useRouter} from 'vue-router'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import {Bell, Menu} from '@element-plus/icons-vue'
import {ElAvatar, ElButton, ElIcon} from 'element-plus'

import {useAuth, useFileStorage, UserActionExecutor} from 'brtech-fusion'

const router = useRouter()
const iconMap = ElementPlusIconsVue as Record<string, any>

const {isLoggedIn, userActions, userAvatar, displayName, checkLoginStatus, handleLogout, setLogoutLogic} = useAuth()

const {resolveCachedUrl} = useFileStorage()

const userActionExecutorRef = ref()
const showMobileMenu = ref(false)

const handleLoginClick = () => {
  showMobileMenu.value = false
  router.push('/login')
}

const handleExecutorCommand = (command: string) => {
  if (command === 'logout') {
    handleLogout() // 将自动执行已注册的门户退出策略
  }
}

// 主动点击菜单退出
const handleAction = async (action: any) => {
  showMobileMenu.value = false

  if (action.key === 'logout') {
    try {
      if (userActionExecutorRef.value?.execute) {
        await userActionExecutorRef.value.execute(action)
      }
    } catch (e) {
      console.warn('Logout API failed', e)
    } finally {
      handleLogout() // 统一走底座，底座会走我们注册的逻辑
    }
    return
  }

  userActionExecutorRef.value?.execute(action)
}

onMounted(() => {
  setLogoutLogic(() => {
    router.replace('/')
  })

  // 2. 检查登录
  checkLoginStatus()
})
</script>

<style scoped lang="scss">
.header-wrapper {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border-light);
  height: var(--header-height);
  width: 100%;
}

.header-inner {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* Brand */
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;

  .brand-logo {
    height: 32px;
    width: auto;
  }

  .brand-text {
    font-size: 18px;
    font-weight: 800;
    color: var(--primary);
    white-space: nowrap;
  }

  .brand-slogan {
    font-size: 14px;
    color: var(--text-light);
    margin-left: 5px;
  }
}

/* Search Input */
.search-input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 20px;
  font-size: 13px;
  outline: none;
  background: #f9fafb;
  width: 200px;
  transition: all 0.3s;

  &:focus {
    width: 260px;
    border-color: var(--primary);
  }
}

/* Buttons */
.btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  font-size: 14px;
}

.btn-primary {
  background: var(--primary);
  color: white;
}

.btn-outline {
  border: 1px solid var(--border-color);
  background: white;
  color: var(--text-main);
}

.block {
  display: block;
  width: 100%;
  margin-bottom: 10px;
}

/* Desktop Right Area */
.nav-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.auth-btns {
  display: flex;
  gap: 10px;
}

/* User Area */
.user-area {
  position: relative;
  display: flex;
  align-items: center;
  gap: 15px;
  cursor: pointer;
  height: 100%;
}

.avatar-img {
  background: #f0f0f0;
}

.avatar-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Dropdown */
.user-dropdown {
  position: absolute;
  top: 50px;
  right: 0;
  width: 220px;
  background: white;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  opacity: 0;
  visibility: hidden;
  transform: translateY(10px);
  transition: all 0.2s;
  padding: 8px 0;
  z-index: 200;
}

.user-area:hover .user-dropdown {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  font-size: 14px;
  cursor: pointer;
  color: var(--text-main);
  transition: background-color 0.2s;

  &:hover {
    background: #f5f7fa;
    color: var(--primary);
  }

  &.highlight {
    color: var(--primary);
    font-weight: 500;
  }

  &.danger-text {
    color: #f56c6c;

    &:hover {
      background: #fef0f0;
    }
  }
}

.menu-divider {
  height: 1px;
  background-color: var(--border-light);
  margin: 4px 0;
}

.menu-header {
  padding: 10px 20px;
  border-bottom: 1px solid var(--border-light);
  margin-bottom: 5px;
}

.u-name {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 2px;
}

.menu-balance {
  font-size: 12px;
  color: var(--text-light);
}

/* Responsive Logic */
.mobile-only {
  display: none;
}

.desktop-only {
  display: flex;
}

@media (max-width: 768px) {
  .desktop-only {
    display: none;
  }
  .mobile-only {
    display: block;
    cursor: pointer;
    color: var(--text-main);
  }
  .hidden-xs {
    display: none;
  }

  /* Mobile Drawer */
  .mobile-drawer {
    position: absolute;
    top: var(--header-height);
    left: 0;
    width: 100%;
    background: white;
    border-bottom: 1px solid var(--border-light);
    padding: 20px;
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.05);
    box-sizing: border-box;
    z-index: 99;
  }
  .mobile-search {
    width: 100%;
    padding: 10px;
    margin-bottom: 20px;
    border: 1px solid #ddd;
    border-radius: 6px;
    box-sizing: border-box;
  }
  .mobile-user-info {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 20px;
  }
  .mobile-links .m-link {
    padding: 12px 0;
    border-top: 1px solid #f0f0f0;
    font-size: 15px;
    cursor: pointer;
    display: flex;
    align-items: center;
  }
  .mobile-links .m-link.logout {
    color: #f56c6c;
  }
}

.slide-down-enter-active, .slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from, .slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>