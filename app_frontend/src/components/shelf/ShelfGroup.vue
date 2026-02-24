<!-- src/components/shelf/ShelfGroup.vue -->
<template>
  <div class="shelf-group">
    <!-- 1. Header -->
    <div class="group-header">
      <h2 class="group-title">{{ title }}</h2>
      <div class="group-actions" v-if="$slots.actions">
        <slot name="actions"></slot>
      </div>
    </div>

    <!-- 2. Body (Grid) -->
    <div class="group-body">
      <slot></slot>
    </div>

    <!-- 3. Footer (新增：用于放展开按钮) -->
    <div class="group-footer" v-if="$slots.footer">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
}>()
</script>

<style scoped lang="scss">
.shelf-group {
  /* 移除 margin，由外部 wrapper 控制 */
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-color, #eee);
}

.group-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-main, #333);
  margin: 0;
  position: relative;
  padding-left: 12px;

  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 4px;
    height: 16px;
    background-color: var(--primary);
    border-radius: 2px;
  }
}

.group-actions {
  font-size: 14px;
  color: #666;
}

/* 新增 Footer 样式 */
.group-footer {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  padding-top: 10px;
  border-top: 1px dashed #f0f0f0;
}
</style>