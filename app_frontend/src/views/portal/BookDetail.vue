<!-- src/views/portal/BookDetail.vue -->
<template>
  <div class="book-detail-page">
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading">
        <Loading/>
      </el-icon>
    </div>

    <div v-else-if="book" class="page-container detail-content">

      <!-- 2. Hero 区域 (三列布局) -->
      <div class="book-hero-grid">
        <!-- Col 1: 封面 -->
        <div class="hero-col-cover">
          <div class="cover-wrapper" :style="{ backgroundColor: book.bgColor || '#f0f0f0' }">
            <transition name="fade-img">
              <img v-if="realCoverUrl" :src="realCoverUrl" alt="cover"/>
            </transition>
            <span v-if="!realCoverUrl" class="placeholder">{{ book.bookTitle }}</span>
          </div>
        </div>

        <!-- Col 2: 元数据 -->
        <div class="hero-col-meta">
          <div class="meta-card">
            <div class="meta-header">
              <h1 class="title">{{ book.bookTitle }}</h1>
              <h2 v-if="book.bookSubtitle" class="subtitle">{{ book.bookSubtitle }}</h2>
              <div class="tags-row">
                <span class="tag category">{{ book.bookCategoryDisplay || '暂无分类' }}</span>
                <span v-for="t in book.tags" :key="t" class="tag promo">{{ t }}</span>
              </div>
              <div class="specs-list">
                <div class="spec-item"><span class="label">作者</span><span class="value">{{ book.bookAuthor || '未知' }}</span></div>
                <div class="spec-item" v-if="book.bookTranslator"><span class="label">译者</span><span class="value">{{ book.bookTranslator }}</span></div>
                <div class="spec-item"><span class="label">页数</span><span class="value">{{ book.bookPageCount || '-' }} 页</span></div>
                <div class="spec-item" v-if="book.bookIsbn"><span class="label">ISBN</span><span class="value">{{ book.bookIsbn }}</span></div>
              </div>
            </div>
            <div class="meta-footer">
              <div class="price-row">
                <template v-if="!isPurchased">
                  <div class="sale-price"><span class="symbol">¥</span>{{ book.bookSalePrice }}</div>
                  <div class="list-price" v-if="book.bookListPrice">原价 ¥{{ book.bookListPrice }}</div>
                </template>
                <div v-else class="purchased-tag">
                  <el-icon>
                    <CircleCheckFilled/>
                  </el-icon>
                  已拥有
                </div>
              </div>
              <div class="btn-row">
                <template v-if="isPurchased">
                  <el-tooltip content="使用 Chrome/Edge 浏览器，能获得更好的阅读体验" placement="top" effect="dark">
                    <button class="btn-main reading" @click="startReading">
                      <el-icon>
                        <Reading/>
                      </el-icon>
                      阅读
                    </button>
                  </el-tooltip>
                </template>
                <template v-else>
                  <button class="btn-main buy" @click="handleBuy"> 购买</button>
                  <el-tooltip content="使用 Chrome/Edge 浏览器，能获得更好的阅读体验" placement="top" effect="dark">
                    <button class="btn-sub" @click="startReading"> 试读</button>
                  </el-tooltip>
                </template>
                <template v-if="userStore.isLoggedIn">
                  <button class="btn-sub" @click="shareBook">分享</button>
                </template>
              </div>
            </div>
          </div>
        </div>

        <!-- Col 3: 简介 -->
        <div class="hero-col-summary">
          <div class="summary-card">
            <div class="summary-header">
              <h3 class="summary-title">简介</h3>
              <div class="mini-back-btn" @click="handleBack">
                <el-icon>
                  <ArrowLeft/>
                </el-icon>
                返回
              </div>
            </div>
            <div class="card-body">
              <p class="summary-text">{{ book.bookSummary || '暂无简介...' }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 3. 目录预览区 -->
      <div class="catalog-section" v-if="catalogItems.length > 0">
        <div class="section-header">
          <h3 class="section-title">目录</h3>
          <span class="section-hint">（点击图片查看高清大图）</span>
        </div>

        <!-- 可视区域：只渲染 calculated 出的那几张图，保证布局完美 -->
        <div class="static-preview-grid" ref="containerRef">
          <div
              v-for="(item, index) in visibleCatalogItems"
              :key="item.pageNo"
              class="preview-item-wrapper"
              :style="{ width: `${CARD_WIDTH}px` }"
          >
            <el-image
                class="real-catalog-img"
                :src="item.url || ''"
                fit="cover"
                loading="eager"
                :style="{ height: `${CARD_WIDTH * 1.414}px` }"
                @click="openViewer(index)"
            >
              <template #placeholder>
                <div class="image-slot loading-slot">
                  <el-icon class="is-loading">
                    <Loading/>
                  </el-icon>
                </div>
              </template>
              <template #error>
                <div class="image-slot error-slot">
                  <el-icon v-if="!item.url" class="is-loading">
                    <Loading/>
                  </el-icon>
                  <el-icon v-else>
                    <icon-picture/>
                  </el-icon>
                </div>
              </template>
            </el-image>
          </div>
        </div>

        <!-- 自定义 Viewer：翻页前先等 blob 就绪，彻底消除闪烁 -->
        <Teleport to="body">
          <div v-if="viewerVisible" class="custom-viewer" @click.self="onViewerClose">
            <!-- 关闭按钮 -->
            <button class="viewer-close" @click="onViewerClose">&#x2715;</button>

            <!-- 主体：左箭头 + 图片 + 右箭头 -->
            <div class="viewer-body">
              <button
                  class="viewer-arrow"
                  :disabled="viewerCurrentIndex <= 0 || viewerSwitching"
                  @click="viewerGo(viewerCurrentIndex - 1)"
              >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M13 4L7 10L13 16" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>

              <div class="viewer-canvas">
                <img v-if="viewerCurrentBlob" :src="viewerCurrentBlob" class="viewer-img" :class="{ 'viewer-img--loading': viewerSwitching }" alt=""/>
                <div v-else class="viewer-placeholder">
                  <el-icon class="is-loading">
                    <Loading/>
                  </el-icon>
                </div>
              </div>

              <button
                  class="viewer-arrow"
                  :disabled="viewerCurrentIndex >= catalogItems.length - 1 || viewerSwitching"
                  @click="viewerGo(viewerCurrentIndex + 1)"
              >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M7 4L13 10L7 16" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>

            <!-- 页码 -->
            <div class="viewer-counter">{{ viewerCurrentIndex + 1 }} / {{ catalogItems.length }}</div>
          </div>
        </Teleport>


      </div>

    </div>

    <div v-else class="error-container">书籍不存在或已下架</div>
    <PaymentDialog ref="paymentDialogRef" @success="onPaymentSuccess"/>
  </div>
</template>

<script setup lang="ts">
import {computed, onMounted, onUnmounted, ref} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {ArrowLeft, CircleCheckFilled, Loading, Picture as IconPicture, Reading} from '@element-plus/icons-vue'
import {ElIcon, ElImage, ElMessage, ElTooltip} from 'element-plus'
import type {UnifiedBookModel, UserBookRelation} from '@/types/book'
import {ShelfApi} from '@/api/shelf'
import {useUserStore} from '@/stores/user'
import {PaymentDialog, useFileStorage} from 'brtech-fusion'

const route = useRoute()
const router = useRouter()
const {resolveCachedUrl} = useFileStorage()
const userStore = useUserStore()

const bookId = route.params.bookId as string
const loading = ref(true)
const book = ref<UnifiedBookModel | null>(null)
const userBookRelation = ref<UserBookRelation | null>(null)
const realCoverUrl = ref('')

interface CatalogItem {
  pageNo: number;
  url: string
}

const catalogItems = ref<CatalogItem[]>([])


// ─── Blob 内存管理 ────────────────────────────────────────────────────────────
const blobUrlMap = new Map<number, string>()
const inflightMap = new Map<number, Promise<string | null>>()
let lastDownloadedIndex = -1

/**
 * 原子操作：下载单张 → blob → objectURL
 * 同一张图全局只有一个 fetch，命中缓存直接返回
 */
const fetchOnePage = (index: number): Promise<string | null> => {
  const item = catalogItems.value[index]
  if (!item) {
    return Promise.resolve(null)
  }

  if (blobUrlMap.has(item.pageNo)) {
    return Promise.resolve(blobUrlMap.get(item.pageNo)!)
  }
  if (inflightMap.has(item.pageNo)) {
    return inflightMap.get(item.pageNo)!
  }

  const promise = (async (): Promise<string | null> => {
    try {
      const signedUrl = await ShelfApi.getPageWebpUrl(bookId, item.pageNo)
      if (!signedUrl) {
        return null
      }
      const response = await fetch(signedUrl)
      if (!response.ok) {
        return null
      }
      const blob = await response.blob()
      const objectUrl = URL.createObjectURL(blob)
      blobUrlMap.set(item.pageNo, objectUrl)
      item.url = objectUrl
      lastDownloadedIndex = Math.max(lastDownloadedIndex, index)
      return objectUrl
    } catch (e) {
      console.error(`[Catalog] 下载第 ${item.pageNo} 页失败`, e)
      return null
    } finally {
      inflightMap.delete(item.pageNo)
    }
  })()

  inflightMap.set(item.pageNo, promise)
  return promise
}

/** 顺序串行下载 fromIndex ~ toIndex */
const fetchSequential = async (fromIndex: number, toIndex: number): Promise<void> => {
  const start = Math.max(fromIndex, 0)
  const end = Math.min(toIndex, catalogItems.value.length - 1)
  for (let i = start; i <= end; i++) {
    await fetchOnePage(i)
  }
}

// 核心配置
const CARD_WIDTH = 145  // 固定卡片宽度
const MIN_GAP = 20      // 最小间距

const containerRef = ref<HTMLElement | null>(null)
const maxVisibleCount = ref(0) // 默认为0，等待计算
const paymentDialogRef = ref();

const isPurchased = computed(() => userBookRelation.value?.purchaseStatus === '1')

// 计算最终要展示的列表（截取屏幕能放下的数量）
const visibleCatalogItems = computed(() => {
  if (maxVisibleCount.value <= 0) {
    return []
  }
  return catalogItems.value.slice(0, maxVisibleCount.value)
})

// ─── 自定义 Viewer 状态 ───────────────────────────────────────────────────────
const viewerVisible = ref(false)
const viewerCurrentIndex = ref(0)
const viewerCurrentBlob = ref<string | null>(null)
const viewerSwitching = ref(false)  // 翻页中（等待下载），用于禁用按钮 + 淡出效果

// 串行补位队列
let prefetchChain: Promise<void> = Promise.resolve()

const schedulePrefetch = (viewerIndex: number) => {
  const N = maxVisibleCount.value > 0 ? maxVisibleCount.value : 5
  const targetIndex = Math.min(viewerIndex + N, catalogItems.value.length - 1)
  if (targetIndex <= lastDownloadedIndex) {
    return
  }
  prefetchChain = prefetchChain.then(() =>
      fetchSequential(lastDownloadedIndex + 1, targetIndex)
  )
}

/**
 * 核心：切换到指定索引
 * 1. 标记 switching，禁用翻页按钮
 * 2. await fetchOnePage(index)，blob 就绪后再赋值给 viewerCurrentBlob
 * 3. img src 变化 → 浏览器渲染新图，全程不出现透明像素
 */
const viewerGo = async (index: number) => {
  if (index < 0 || index >= catalogItems.value.length) {
    return
  }
  if (viewerSwitching.value) {
    return
  }

  viewerSwitching.value = true
  viewerCurrentIndex.value = index
  const blob = await fetchOnePage(index)
  viewerCurrentBlob.value = blob
  viewerSwitching.value = false

  // 后台补位，不阻塞显示
  schedulePrefetch(index)
}

/** 点击缩略图打开 Viewer */
const openViewer = async (index: number) => {
  viewerCurrentBlob.value = null
  viewerCurrentIndex.value = index
  viewerVisible.value = true
  // 等目标 blob 就绪后再显示图片（Viewer 壳已打开，显示 loading）
  const blob = await fetchOnePage(index)
  viewerCurrentBlob.value = blob
  schedulePrefetch(index)
}

const onViewerClose = () => {
  viewerVisible.value = false
  viewerCurrentBlob.value = null
}

// ESC 关闭
const onKeydown = (e: KeyboardEvent) => {
  if (!viewerVisible.value) {
    return
  }
  if (e.key === 'Escape') {
    onViewerClose()
  }
  if (e.key === 'ArrowLeft') {
    viewerGo(viewerCurrentIndex.value - 1)
  }
  if (e.key === 'ArrowRight') {
    viewerGo(viewerCurrentIndex.value + 1)
  }
}

const shareBook = () => {

}
const startReading = async () => {
  let targetPage = 1

  if (userStore.isLoggedIn) {
    let oldRelation = await ShelfApi.getBookUserRelation(bookId)
    if (oldRelation === null) {
      oldRelation = await ShelfApi.createBookUserRelation(bookId, userStore.userInfo?.modelId || '')
    }
    if (oldRelation) {
      userBookRelation.value = oldRelation
    }
    targetPage = userBookRelation.value?.lastReadPageNo || 1
  }
  const routeData = router.resolve({
    name: 'TriHeartReader',
    params: {bookId: bookId, pageNo: targetPage}
  })
  window.open(routeData.href, '_blank')
}
const handleBuy = () => {
  if (!userStore.isLoggedIn) {
    ElMessage.info('购买书籍需要先登录账号')

    router.push({
      path: '/login',
      state: {
        loginSuccessJumpToUrl: route.fullPath
      }
    })
    return
  }
  if (!book.value) {
    return;
  }

  const snapshot = JSON.parse(JSON.stringify(book.value));
  paymentDialogRef.value.open({
    businessId: book.value.modelId,
    paySubject: `购买书籍 - ${book.value.bookTitle}`,
    amount: book.value.bookSalePrice,
    businessType: 'book_purchase',
    paySnapshot: snapshot
  });
}

const onPaymentSuccess = (paymentData: any) => {
  //isPurchased.value = true;
  ShelfApi.getBookUserRelation(bookId).then((relation) => {
    if (relation) {
      userBookRelation.value = relation
    }
  })
}
const handleBack = () => {
  if (window.history.length > 1) {
    router.back();
  } else {
    router.push('/square')
  }
}
/** 步骤1：页面加载，顺序串行下载前 N 张 */
const loadFirstScreen = async () => {
  const N = maxVisibleCount.value > 0 ? maxVisibleCount.value : 5
  await fetchSequential(0, N - 1)
}

// 计算能放几个的核心函数
const calcCapacity = () => {
  if (!containerRef.value) {
    return
  }
  const w = containerRef.value.clientWidth
  // 如果宽度获取失败（通常是DOM未稳定），给予默认值
  if (w === 0) {
    if (maxVisibleCount.value === 0) {
      maxVisibleCount.value = 5
    }
    return
  }
  // 公式：(总宽 + 间距) / (卡片宽 + 间距)
  const count = Math.floor((w + MIN_GAP) / (CARD_WIDTH + MIN_GAP))
  const finalCount = Math.min(count, catalogItems.value.length)

  if (finalCount > 0) {
    maxVisibleCount.value = finalCount
  }
}

let resizeObserver: ResizeObserver | null = null

onMounted(async () => {
  window.addEventListener('keydown', onKeydown)
  try {
    loading.value = true
    const tasks: Promise<any>[] = [ShelfApi.getBookDetail(bookId)]
    if (userStore.isLoggedIn) {
      tasks.push(ShelfApi.getBookUserRelation(bookId))
    }
    const [bookData, relationData] = await Promise.all(tasks)
    if (relationData) {
      userBookRelation.value = relationData
    }
    if (bookData) {
      book.value = bookData
      if (bookData.bookCover) {
        ShelfApi.getCoverSignUrl(bookData.modelId).then(url => realCoverUrl.value = url)
      }

      const startPage = (bookData as any).tocBeginPage || 1
      const endPage = (bookData as any).tocEndPage || Math.min(10, bookData.bookPageCount || 10)

      if (endPage >= startPage) {
        // 1. 初始化空数据
        for (let i = startPage; i <= endPage; i++) {
          catalogItems.value.push({pageNo: i, url: ''})
        }

        // 2. 等待 DOM 渲染，先算能放几个
        setTimeout(() => {
          calcCapacity()
          if (containerRef.value) {
            resizeObserver = new ResizeObserver(() => window.requestAnimationFrame(calcCapacity))
            resizeObserver.observe(containerRef.value)
          }

          // 3. 只下载首屏可见的几张，其余等用户打开 Viewer 再补位
          loadFirstScreen()

        }, 100)
      }
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
  // 释放所有 blob ObjectURL，防止 SPA 内存泄漏
  blobUrlMap.forEach((blobUrl) => URL.revokeObjectURL(blobUrl))
  blobUrlMap.clear()
})
</script>

<style scoped lang="scss">
.book-detail-page {
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

/* Grid */
.book-hero-grid {
  display: grid;
  grid-template-columns: 300px 1fr 1fr;
  gap: 40px;
  margin-bottom: 60px;
  align-items: stretch;
}

.hero-col-cover {
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
    font-size: 24px;
    font-weight: bold;
    background-color: #f0f0f0;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }
}

.hero-col-meta {
  .meta-card {
    background: #f8fafc;
    border-radius: 12px;
    padding: 10px;
    height: 100%;
    border: 1px solid #f1f5f9;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }

  .title {
    font-size: 20px;
    font-weight: 800;
    color: #2b2b2b;
    margin: 0 0 8px 0;
    line-height: 1.3;
  }

  .subtitle {
    font-size: 16px;
    font-weight: 400;
    color: #666;
    margin: 0 0 16px 0;
  }

  .tags-row {
    display: flex;
    gap: 8px;
    margin-bottom: 24px;

    .tag {
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 12px;

      &.category {
        background: #eff6ff;
        color: #1d4ed8;
      }

      &.promo {
        background: #fff1f2;
        color: #be123c;
      }
    }
  }

  .specs-list {
    margin-bottom: 20px;

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

  .meta-footer {
    margin-top: auto;

    .price-row {
      display: flex;
      align-items: baseline;
      gap: 10px;
      margin-bottom: 20px;

      .sale-price {
        font-size: 32px;
        color: var(--primary);
        font-weight: 800;

        .symbol {
          font-size: 18px;
        }
      }

      .list-price {
        font-size: 14px;
        color: #999;
        text-decoration: line-through;
      }

      .purchased-tag {
        color: #10b981;
        display: flex;
        align-items: center;
        gap: 5px;
        font-weight: 600;
      }
    }

    .btn-row {
      display: flex;
      gap: 15px;

      button {
        height: 44px;
        padding: 0 32px;
        border-radius: 6px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
        display: flex;
        align-items: center;
        gap: 6px;
      }

      .btn-main {
        background: var(--primary);
        color: white;
        border: none;
        box-shadow: 0 4px 10px rgba(194, 65, 12, 0.2);

        &:hover {
          background: var(--primary-hover);
          transform: translateY(-1px);
        }

        &.reading {
          background: #10b981;
          box-shadow: 0 4px 10px rgba(16, 185, 129, 0.2);
        }
      }

      .btn-sub {
        background: white;
        border: 1px solid #ddd;
        color: #333;

        &:hover {
          border-color: var(--primary);
          color: var(--primary);
          background: rgba(194, 65, 12, 0.05);
        }
      }
    }
  }
}

.hero-col-summary {
  height: 100%;
  min-height: 0;

  .summary-card {
    background: #f8fafc;
    border-radius: 12px;
    padding: 10px;
    height: 100%;
    border: 1px solid #f1f5f9;

    display: flex;
    flex-direction: column;

    .summary-header {
      border-bottom: 1px solid #e2e8f0;
      margin-bottom: 16px;
      padding-bottom: 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-shrink: 0;
    }

    .card-body {
      flex: 1;
      overflow-y: auto;
      min-height: 0;
      max-height: 380px;
      padding-right: 5px;

      &::-webkit-scrollbar {
        width: 10px;
      }

      &::-webkit-scrollbar-thumb {
        background-color: #cbd5e1;
        border-radius: 3px;
      }

      &::-webkit-scrollbar-track {
        background-color: transparent;
      }
    }

    .summary-title {
      font-size: 16px;
      font-weight: 700;
      color: #333;
      margin: 0;
      padding-left: 10px;
      border-left: 4px solid var(--primary);
      line-height: 1.2;
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
      font-size: 14px;
      color: #555;
      line-height: 1.8;
      text-align: justify;

      white-space: pre-wrap;
      margin: 0;
    }
  }
}

/* 目录区 */
.catalog-section {
  margin-top: 40px;
  padding-top: 30px;
  position: relative;

  .section-header {
    margin-bottom: 20px;
    display: flex;
    align-items: baseline;
    gap: 12px;

    .section-title {
      font-size: 20px;
      font-weight: 700;
      color: #333;
      margin: 0;
      padding-left: 10px;
      border-left: 4px solid var(--primary);
    }

    .section-hint {
      font-size: 12px;
      color: #999;
    }
  }
}

/* 新的静态 Grid 样式 */
.static-preview-grid {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  width: 100%;
  min-height: 200px;
  overflow: hidden;
  padding: 10px 2px 20px 2px;
}


.preview-item-wrapper {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;

  .real-catalog-img {
    width: 100%;
    /* 高度由 JS 内联样式控制 */
    border-radius: 4px;
    border: 1px solid #eee;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
    cursor: zoom-in;
    transition: all 0.3s;
    background-color: #fff;
    display: block;

    &:hover {
      transform: translateY(-5px);
      box-shadow: 0 10px 20px rgba(0, 0, 0, 0.12);
      border-color: var(--primary);
    }
  }

  .page-num {
    font-size: 12px;
    color: #999;
    text-align: center;
  }

  .img-skeleton, .image-slot {
    width: 100%;
    height: 100%;
    border-radius: 4px;
    background: #f5f7fa;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #ccc;
  }
}

.fade-img-enter-active {
  transition: opacity 0.5s ease;
}

.fade-img-enter-from {
  opacity: 0;
}

@media (max-width: 1024px) {
  .book-hero-grid {
    grid-template-columns: 200px 1fr;
  }
  .hero-col-summary {
    grid-column: 1 / -1;
    height: auto;
  }
}

/* ─── 自定义 Viewer（Teleport 到 body，必须用 :global）─────────────────────── */
:global(.custom-viewer) {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

/* 左箭头 + 图片区 + 右箭头，水平排列，垂直居中 */
:global(.viewer-body) {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  width: 100%;
  padding: 0 12px;
  box-sizing: border-box;
}

:global(.viewer-canvas) {
  max-width: 80vw;
  max-height: 85vh;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

:global(.viewer-img) {
  max-width: 80vw;
  max-height: 85vh;
  object-fit: contain;
  border-radius: 4px;
  transition: opacity 0.15s ease;
  display: block;
}

:global(.viewer-img--loading) {
  opacity: 0.4;
}

:global(.viewer-placeholder) {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 32px;
}

/* 左右箭头按钮 */
:global(.viewer-arrow) {
  flex-shrink: 0;
  width: 52px;
  height: 52px;
  background: rgba(255, 255, 255, 0.15);
  border: none;
  color: #fff;
  cursor: pointer;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: background 0.2s;
}

:global(.viewer-arrow:hover:not(:disabled)) {
  background: rgba(255, 255, 255, 0.3);
}

:global(.viewer-arrow:disabled) {
  opacity: 0.25;
  cursor: not-allowed;
}

/* 关闭按钮：右上角 absolute */
:global(.viewer-close) {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.15);
  border: none;
  color: #fff;
  cursor: pointer;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  padding: 0;
  transition: background 0.2s;
}

:global(.viewer-close:hover) {
  background: rgba(255, 255, 255, 0.3);
}

:global(.viewer-counter) {
  margin-top: 16px;
  color: rgba(255, 255, 255, 0.75);
  font-size: 14px;
  background: rgba(0, 0, 0, 0.4);
  padding: 4px 14px;
  border-radius: 20px;
  pointer-events: none;
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .detail-content {
    padding-top: 20px; /* 缩小顶部间距 */
  }

  .book-hero-grid {
    grid-template-columns: 1fr;
    gap: 24px;
    margin-bottom: 30px;
  }

  /* 1. 封面：居中并缩小，增加柔和阴影 */
  .hero-col-cover {
    display: flex;
    justify-content: center;

    .cover-wrapper {
      width: 160px; /* 稍微缩小一点 */
      border-radius: 6px;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2); /* 加深投影增强立体感 */
    }
  }

  /* 2. 元数据卡片：核心对齐区域 */
  .hero-col-meta {
    .meta-card {
      padding: 20px;
      background: #ffffff; /* 手机端使用纯白背景，更有呼吸感 */
      border: none;
      text-align: left; /* 核心：开启居中对齐 */
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    .title {
      font-size: 20px;
      line-height: 1.4;
      margin-bottom: 6px;
    }

    .subtitle {
      font-size: 14px;
      color: #777;
      margin-bottom: 12px;
    }

    /* 标签居中 */
    .tags-row {
      justify-content: flex-start;
      margin-bottom: 16px;
    }

    /* 规格列表：改为横向对齐的短语，并用分割线隔开 */
    .specs-list {
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-start;
      gap: 12px;
      margin-bottom: 0;

      .spec-item {
        margin-bottom: 0;
        font-size: 13px;
        color: #888;

        .label {
          width: auto; /* 移除固定宽度 */
          margin-right: 4px;

          &::after {
            content: ":";
          }
        }

        .value {
          color: #555;
          font-weight: 500;
        }
      }
    }

    /* 价格居中 */
    .meta-footer {
      width: 100%;

      .price-row {
        padding-left: 10px;
        justify-content: left;
        margin: 20px 0;

        .sale-price {
          font-size: 28px;
        }
      }

      /* 按钮组：平分宽度 */
      .btn-row {
        width: 100%;
        display: flex;
        gap: 10px;

        button {
          flex: 1; /* 核心：让两个按钮等宽 */
          height: 40px;
          padding: 0;
          justify-content: center;
          font-size: 15px;
        }
      }
    }
  }

  /* 3. 简介部分微调 */
  .hero-col-summary {
    .summary-card {
      padding: 16px;
      background: #fcfcfc;

      .summary-title {
        font-size: 15px;
      }

      .summary-text {
        font-size: 13px;
        line-height: 1.6;
        color: #666;
      }
    }
  }
}
</style>