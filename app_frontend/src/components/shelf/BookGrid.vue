<!-- src/components/shelf/BookGrid.vue -->
<template>
  <div class="book-grid">
    <slot></slot>
  </div>
</template>

<style scoped>
.book-grid {
  display: grid;
  /* 核心：自动填充，最小宽度 160px，最大 1fr */
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));

  /* 间距 */
  gap: 30px 24px;

  width: 100%;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .book-grid {
    grid-template-columns: repeat(2, 1fr); /* 强制2列 */
    gap: 20px 15px;
  }
}
</style>