<!-- src/views/portal/OpenBookDetail.vue -->
<template>
  <div class="open-book-detail-page">
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading">
        <Loading/>
      </el-icon>
    </div>

    <div v-else-if="book" class="page-container detail-content">
      <div class="book-hero">
        <!-- 封面 -->
        <div class="hero-cover">
          <div class="cover-wrapper" :style="{ backgroundColor: book.bgColor || '#f0f0f0' }">
            <transition name="fade-img">
              <img v-if="realCoverUrl" :src="realCoverUrl" alt="cover"/>
            </transition>
            <span v-if="!realCoverUrl" class="placeholder">{{ book.bookTitle }}</span>
          </div>
        </div>

        <!-- 元数据 -->
        <div class="hero-meta">
          <div class="meta-top">
            <div class="license-badge" v-if="book.openSourceLicense">
              开源 · {{ book.openSourceLicense }}
            </div>
            <div class="license-badge" v-else>
              开源 · 免费分发
            </div>

            <h1 class="title">{{ book.bookTitle }}</h1>
            <h2 v-if="book.bookSubtitle" class="subtitle">{{ book.bookSubtitle }}</h2>

            <div class="specs-list">
              <div class="spec-item"><span class="label">作者</span><span class="value">{{ book.bookAuthor || '未知' }}</span></div>
              <div class="spec-item" v-if="book.bookTranslator"><span class="label">译者</span><span class="value">{{ book.bookTranslator }}</span></div>
              <div class="spec-item"><span class="label">页数</span><span class="value">{{ book.bookPageCount || '-' }} 页</span></div>
            </div>
          </div>

          <!-- 按钮区 -->
          <div class="btn-row">
            <button class="btn-pdf" @click="handlePdfRead">
              <el-icon>
                <Reading/>
              </el-icon>
              阅读/下载
            </button>
            <!--
            <el-tooltip placement="top" effect="dark" content="高度还原物理书籍阅读感 / 术语高亮 / 读书笔记 / 音视频伴读">
              <button class="btn-immersive" @click="handleImmersiveRead">
                <el-icon><MagicStick/></el-icon>
                沉浸式精读
              </button>
            </el-tooltip>
            -->
          </div>
        </div>
      </div>

      <!-- 简介 -->
      <div class="summary-section" v-if="book.bookSummary">
        <div class="summary-header">
          <h3 class="section-title">简介</h3>
          <div class="mini-back-btn" @click="handleBack">
            <el-icon>
              <ArrowLeft/>
            </el-icon>
            返回
          </div>
        </div>
        <p class="summary-text">{{ book.bookSummary }}</p>
      </div>
    </div>

    <div v-else class="error-container">书籍不存在或已下架</div>
  </div>
</template>

<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {ArrowLeft, Loading, Reading} from '@element-plus/icons-vue'
import {ElIcon, ElMessage} from 'element-plus'
import type {UnifiedBookModel} from '@/types/book'
import {ShelfApi} from '@/api/shelf'

const route = useRoute()
const router = useRouter()

const bookId = route.params.bookId as string
const loading = ref(true)
const book = ref<UnifiedBookModel | null>(null)
const realCoverUrl = ref('')

// 阅读：用浏览器打开 PDF
const handlePdfRead = async () => {
  try {
    const signedUrl = await ShelfApi.getOpenSourcePdfSignUrl(bookId)
    if (signedUrl) {
      window.open(signedUrl, '_blank')
    } else {
      ElMessage.error('获取下载地址失败')
    }
  } catch (e) {
    ElMessage.error('获取下载地址失败')
  }
}

// 沉浸式精读：跳转到详情页（包含价格和购买逻辑）
const handleImmersiveRead = () => {
  router.push(`/bookshelf/${bookId}`)
}

const handleBack = () => {
  router.push('/bookshelf')
}

onMounted(async () => {
  try {
    loading.value = true
    const bookData = await ShelfApi.getBookDetail(bookId)
    if (bookData) {
      book.value = bookData
      if (bookData.bookCover) {
        ShelfApi.getCoverSignUrl(bookData.modelId).then(url => realCoverUrl.value = url)
      }
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped lang="scss">
.open-book-detail-page {
  min-height: 100vh;
  background-color: #fff;
}

.detail-content {
  padding-top: 40px;
  padding-bottom: 60px;
}

.loading-container, .error-container {
  display: flex;
  justify-content: center;
  padding-top: 100px;
  color: #999;
  font-size: 16px;
}

.book-hero {
  display: flex;
  gap: 40px;
  margin-bottom: 40px;
}

.hero-cover {
  flex: 0 0 260px;

  .cover-wrapper {
    width: 100%;
    aspect-ratio: 2 / 3;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 15px 30px rgba(0, 0, 0, 0.15);
    display: flex;
    align-items: center;
    justify-content: center;
    color: rgba(255, 255, 255, 0.8);
    font-size: 20px;
    font-weight: bold;
    background-color: #f0f0f0;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }
}

.hero-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;

  .meta-top {
    flex-shrink: 0;
  }

  .license-badge {
    display: inline-flex;
    align-items: center;
    background: #f0fdf4;
    color: #16a34a;
    border: 1px solid #bbf7d0;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 16px;
    width: fit-content;
  }

  .title {
    font-size: 28px;
    font-weight: 800;
    color: #1a1a1a;
    margin: 0 0 8px 0;
    line-height: 1.3;
  }

  .subtitle {
    font-size: 18px;
    font-weight: 400;
    color: #666;
    margin: 0 0 20px 0;
  }

  .specs-list {
    margin-bottom: 28px;

    .spec-item {
      display: flex;
      font-size: 14px;
      margin-bottom: 8px;

      .label {
        width: 50px;
        color: #999;
      }

      .value {
        color: #333;
        font-weight: 500;
      }
    }
  }

  .btn-row {
    display: flex;
    gap: 16px;

    button {
      height: 48px;
      padding: 0 36px;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .btn-pdf {
      background: white;
      border: 2px solid #ddd;
      color: #333;

      &:hover {
        border-color: var(--primary);
        color: var(--primary);
        background: rgba(194, 65, 12, 0.04);
      }
    }

    .btn-immersive {
      background: var(--primary);
      color: white;
      border: none;
      box-shadow: 0 4px 12px rgba(194, 65, 12, 0.25);

      &:hover {
        background: var(--primary-hover);
        transform: translateY(-2px);
      }
    }
  }
}

.summary-section {
  margin-top: 10px;
  padding-top: 24px;
  border-top: 1px solid #eee;

  .summary-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }

  .section-title {
    font-size: 18px;
    font-weight: 700;
    color: #333;
    margin: 0;
    padding-left: 10px;
    border-left: 4px solid var(--primary);
  }

  .mini-back-btn {
    font-size: 13px;
    color: #666;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 4px;

    &:hover {
      color: var(--primary);
    }
  }

  .summary-text {
    font-size: 15px;
    color: #555;
    line-height: 1.8;
    text-align: justify;
    white-space: pre-wrap;
    margin: 0;
  }
}

@media (max-width: 768px) {
  .book-hero {
    flex-direction: column;
    gap: 24px;
  }

  .hero-cover {
    flex: unset;
    display: flex;
    justify-content: center;

    .cover-wrapper {
      width: 160px;
    }
  }

  .hero-meta {
    .btn-row {
      flex-direction: column;

      button {
        width: 100%;
        justify-content: center;
      }
    }
  }
}

.fade-img-enter-active {
  transition: opacity 0.5s ease;
}

.fade-img-enter-from {
  opacity: 0;
}
</style>