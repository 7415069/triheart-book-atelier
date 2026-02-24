<!-- src/components/shelf/ShelfRow.vue -->
<template>
  <div class="shelf-row-container">
    <div class="scroll-track">
      <slot></slot>
    </div>
  </div>
</template>

<style scoped>
.shelf-row-container {
  width: 100%;
  position: relative;
  /* 可选：加个上下padding防止阴影被切 */
  padding: 4px 0;
}

.scroll-track {
  display: flex;
  gap: 20px;
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: 10px; /* 留出滚动条空间或防止贴底 */

  /* 隐藏滚动条 (Chrome/Safari) */

  &::-webkit-scrollbar {
    display: none;
  }

  /* 隐藏滚动条 (Firefox) */
  scrollbar-width: none;

  /* 平滑滚动 */
  scroll-behavior: smooth;
  /* 允许惯性滚动 (iOS) */
  -webkit-overflow-scrolling: touch;
}

/* 强制内部卡片不换行且固定宽度 */
:deep(.book-card) {
  flex: 0 0 140px; /* 固定宽度 */
  width: 140px;
}

@media (max-width: 768px) {
  :deep(.book-card) {
    flex: 0 0 110px;
    width: 110px;
  }
}
</style>