<!-- src/views/portal/Index.vue -->
<template>
  <div class="portal-layout">
    <!-- 1. Header (固定高度，不参与滚动) -->
    <div class="layout-header">
      <PortalHeader/>
    </div>

    <!-- 2. Main Content (占据剩余空间，内部滚动) -->
    <div class="layout-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component"/>
        </transition>
      </router-view>
    </div>
  </div>
</template>

<script setup lang="ts">
import PortalHeader from '@/components/portal/Header.vue'
</script>

<style scoped>
.portal-layout {
  display: flex;
  flex-direction: column;
  height: 100vh; /* 占满视口高度 */
  overflow: hidden; /* 防止最外层出现滚动条 */
}

.layout-header {
  flex: 0 0 auto; /* 高度由内容撑开，不可压缩 */
  z-index: 100;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05); /* 阴影加在这里 */
}

.layout-main {
  flex: 1; /* 占据剩余所有空间 */
  overflow-y: auto; /* 核心：只有这里出垂直滚动条 */
  overflow-x: hidden;
  background-color: #f5f7fa; /* 统一背景色 */

  /* 优化滚动条样式 */

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-thumb {
    background: #d1d5db;
    border-radius: 3px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>