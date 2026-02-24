<template>
  <div class="bookshelf-page">
    <PortalHeader/>

    <div class="page-container content-area">
      <h1 class="page-title">我的书架</h1>

      <!-- Tabs (Scrollable on mobile) -->
      <div class="tabs-wrapper">
        <div class="tabs">
          <div
              v-for="tab in tabs" :key="tab.key"
              class="tab"
              :class="{ active: currentTab === tab.key }"
              @click="currentTab = tab.key"
          >
            {{ tab.label }}
          </div>
        </div>
      </div>

      <!-- Grid -->
      <div class="shelf-grid">
        <div v-for="book in shelfBooks" :key="book.id" class="shelf-item" @click="continueRead(book)">
          <div class="shelf-cover">
            <div class="cover-placeholder" :style="{background: book.color}">
              {{ book.title }}
            </div>
            <!-- Progress -->
            <div v-if="book.progress > 0" class="progress-bar-bg">
              <div class="progress-bar-fill" :style="{ width: book.progress + '%' }"></div>
            </div>
          </div>

          <div class="shelf-info">
            <div class="shelf-title">{{ book.title }}</div>
            <div class="shelf-meta">
              <span class="status-text">{{ book.progress > 0 ? `进度 ${book.progress}%` : '未开始' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref} from 'vue'
import {useRouter} from 'vue-router'
import PortalHeader from '@/components/portal/Header.vue'

const router = useRouter()
const currentTab = ref('history')

const tabs = [
  {key: 'history', label: '最近阅读'},
  {key: 'purchased', label: '已购书籍'},
  {key: 'wishlist', label: '收藏心愿单'},
  {key: 'uploads', label: '我的上传'}
]

const shelfBooks = ref([
  {id: 'b1', title: 'Web3 修行手册', color: '#1e293b', progress: 35, lastPage: 25, bookId: 'book_001'},
  {id: 'b2', title: '算法导论图解版', color: '#9f1239', progress: 5, lastPage: 10, bookId: 'book_002'},
  {id: 'b3', title: 'Rust 高级编程', color: '#047857', progress: 0, lastPage: 0, bookId: 'book_003'},
  {id: 'b4', title: 'JavaScript 设计模式', color: '#555', progress: 100, lastPage: 320, bookId: 'book_004'},
])

const continueRead = (book: any) => {
  const page = book.lastPage || 1
  router.push(`/reader/${book.bookId}/${page}`)
}
</script>

<style scoped lang="scss">
.bookshelf-page {
  min-height: 100vh;
  background-color: #fafaf9;
}

.content-area {
  margin-top: 40px;
  margin-bottom: 60px;
}

.page-title {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 20px;
  color: var(--text-main);
}

/* Tabs */
.tabs-wrapper {
  width: 100%;
  overflow-x: auto;
  border-bottom: 1px solid var(--border);
  margin-bottom: 30px;
  /* Hide scrollbar */
  -ms-overflow-style: none;
  scrollbar-width: none;

  &::-webkit-scrollbar {
    display: none;
  }
}

.tabs {
  display: flex;
  white-space: nowrap;
}

.tab {
  padding: 12px 20px;
  cursor: pointer;
  font-size: 15px;
  color: var(--text-sub);
  border-bottom: 2px solid transparent;
  transition: all 0.2s;

  &.active {
    color: var(--primary);
    border-bottom-color: var(--primary);
    font-weight: 500;
  }
}

/* Shelf Grid */
.shelf-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 25px;
}

.shelf-item {
  cursor: pointer;
}

.shelf-cover {
  height: 240px;
  background: white;
  border-radius: 6px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-placeholder {
  color: white;
  font-weight: bold;
  font-size: 14px;
  text-align: center;
  padding: 15px;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-bar-bg {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: rgba(0, 0, 0, 0.1);
}

.progress-bar-fill {
  height: 100%;
  background: var(--primary);
}

.shelf-info {
  margin-top: 10px;
}

.shelf-title {
  font-size: 14px;
  font-weight: bold;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.shelf-meta {
  font-size: 12px;
  color: var(--text-sub);
  margin-top: 4px;
}

/* Mobile */
@media (max-width: 768px) {
  .content-area {
    margin-top: 20px;
  }
  .shelf-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
  }
  .shelf-cover {
    height: 200px;
  }
}
</style>