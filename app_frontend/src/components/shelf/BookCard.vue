<!-- src/components/shelf/BookCard.vue -->
<template>
  <div
      class="book-card"
      :class="[`mode-${mode}`]"
      @click="handleClick"
  >
    <!-- 1. 封面区域 -->
    <div class="card-cover-wrapper">
      <!-- 封面图容器 -->
      <div
          class="cover-image"
          :style="{ backgroundColor: book.bgColor || '#e2e8f0' }"
      >
        <!-- 【核心修改】使用 realCoverUrl，并增加渐显动画 -->
        <transition name="fade-img">
          <img
              v-if="realCoverUrl"
              :src="realCoverUrl"
              alt="cover"
              loading="lazy"
          />
        </transition>

        <!-- 图片未加载时显示的文字占位 -->
        <div v-if="!realCoverUrl" class="cover-placeholder">
          {{ book.bookTitle }}
        </div>

        <!-- 遮罩层 -->
        <div class="cover-overlay">
          <span class="action-text">
            {{ mode === 'public' ? '查看详情' : '继续阅读' }}
          </span>
        </div>
      </div>

      <!-- 角标 -->
      <div class="badges">
        <!-- 模式A: 公共广场 -->
        <template v-if="mode === 'public'">
          <span v-if="book.tags && book.tags.length" class="badge-tag market-tag">{{ book.tags[0] }}</span>
          <span v-else-if="book.bookCategoryDisplay" class="badge-tag category-tag">{{ book.bookCategoryDisplay }}</span>
        </template>

        <!-- 模式B: 个人书架 -->
        <template v-if="mode === 'personal'">
          <span v-if="bookStatusText === '已读'" class="badge-tag status-finished">已读完</span>
          <span v-else-if="!book.isPurchased" class="badge-tag status-trial">试读</span>
        </template>
      </div>
    </div>

    <!-- 2. 信息区域 -->
    <div class="card-info">
      <h3 class="book-title" :title="book.bookTitle">{{ book.bookTitle }}</h3>
      <p class="book-author">{{ book.bookAuthor }}</p>

      <!-- 3. 底部状态栏 -->
      <div class="card-footer">

        <!-- 模式A: 显示价格 -->
        <div v-if="mode === 'public'" class="footer-public">
          <span class="price-text" :class="{ 'free': isFree }">
            {{ priceDisplay }}
          </span>
          <span v-if="showListPrice" class="list-price">
            ¥{{ book.bookListPrice }}
          </span>
        </div>

        <!-- 模式B: 显示进度 -->
        <div v-if="mode === 'personal'" class="footer-personal">
          <div class="progress-track">
            <div class="progress-bar" :style="{ width: (progressPercent || 0) + '%' }"></div>
          </div>
          <span class="progress-text">{{ progressPercent || 0 }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {computed, onMounted, ref, watch} from 'vue'
import type {UnifiedBookModel} from '@/types/book'
import {ShelfApi} from '@/api/shelf'

const props = defineProps<{
  book: UnifiedBookModel
  mode: 'public' | 'personal'
}>()

const emit = defineEmits(['click'])

// 1. 基础逻辑：计算阅读状态文案
const bookStatusText = computed(() => {
  if (props.mode === 'public') {
    return '';
  }

  const current = props.book.lastReadPageNo ?? 0;
  // 适配 UnifiedBookModel 的平铺结构
  const total = props.book.bookPageCount ?? 0;

  if (!props.book.lastReadTime || current === 0) {
    return '未读';
  }
  if (total > 0 && current >= total) {
    return '已读';
  }
  return '在读';
})

// 2. 基础逻辑：计算进度百分比
const progressPercent = computed(() => {
  const current = props.book.lastReadPageNo ?? 0;
  const total = props.book.bookPageCount ?? 0;
  if (total === 0) {
    return 0;
  }
  return Math.min(Math.floor((current / total) * 100), 100);
})

// 3. 基础逻辑：判断是否已购买
// 注意：后端返回的 purchaseStatus 通常是字符串 '1' 或 '0'
const isPurchased = computed(() => props.book.purchaseStatus === '1')

// --- 原有逻辑保留 ---
const realCoverUrl = ref('')
const loadCover = async () => {
  realCoverUrl.value = ''
  const rawCover = props.book.bookCover
  if (rawCover) {
    if (rawCover.startsWith('http')) {
      realCoverUrl.value = rawCover
    } else {
      const signed = await ShelfApi.getCoverSignUrl(props.book.modelId)
      realCoverUrl.value = signed
    }
  }
}

watch(() => props.book.bookCover, loadCover)
onMounted(loadCover)

const isFree = computed(() => !props.book.bookSalePrice || props.book.bookSalePrice === 0)
const priceDisplay = computed(() => isFree.value ? '免费' : `¥${props.book.bookSalePrice?.toFixed(2)}`)
const showListPrice = computed(() => {
  const list = props.book.bookListPrice
  const sale = props.book.bookSalePrice
  return list !== undefined && sale !== undefined && list > sale
})

const handleClick = () => emit('click', props.book)
</script>

<style scoped lang="scss">
.book-card {
  width: 100%;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease;

  &:hover {
    .cover-overlay {
      opacity: 1;
    }

    .book-title {
      color: var(--primary);
    }
  }
}

.card-cover-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 2 / 3;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.04);
  margin-bottom: 10px;
  background-color: #f8f9fa;
}

.cover-image {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

/* 【新增】图片渐显动画 */
.fade-img-enter-active {
  transition: opacity 0.5s ease;
}

.fade-img-enter-from {
  opacity: 0;
}

.cover-placeholder {
  padding: 10px;
  font-size: 14px;
  font-weight: bold;
  color: #999;
  text-align: center;
  line-height: 1.4;
}

.cover-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.action-text {
  color: white;
  background: rgba(0, 0, 0, 0.6);
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  backdrop-filter: blur(4px);
}

.badges {
  position: absolute;
  top: 6px;
  right: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.badge-tag {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
  color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.market-tag {
  background: #f56c6c;
}

.category-tag {
  background: #3b82f6;
}

.status-finished {
  background: #67c23a;
}

.status-trial {
  background: #909399;
}

.card-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.book-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin: 0 0 4px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.book-author {
  font-size: 12px;
  color: #999;
  margin: 0 0 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-footer {
  margin-top: auto;
}

.footer-public {
  display: flex;
  align-items: baseline;
  gap: 6px;

  .price-text {
    font-size: 14px;
    font-weight: 700;
    color: var(--primary);

    &.free {
      color: #67c23a;
    }
  }

  .list-price {
    font-size: 12px;
    color: #ccc;
    text-decoration: line-through;
  }
}

.footer-personal {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-track {
  flex: 1;
  height: 4px;
  background-color: #eee;
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background-color: var(--primary);
  border-radius: 2px;
}

.progress-text {
  font-size: 11px;
  color: #999;
  font-family: monospace;
}
</style>