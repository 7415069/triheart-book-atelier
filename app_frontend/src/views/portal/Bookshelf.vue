<!-- src/views/portal/Bookshelf.vue -->
<template>
  <div class="square-page">
    <div class="page-container content-area">

      <!-- ============ 0. 个人书架区域 (包含骨架屏) ============ -->
      <div v-if="isLoggedIn && (personalLoading || hasPersonalData)" class="personal-section-wrapper fade-in">

        <div v-if="hasPersonalData" style="display: flex; gap: 20px; width: 100%;">
          <!-- 左侧：已购买书籍 -->
          <div v-if="myBooks.length > 0" class="personal-col">
            <div class="category-group-wrapper">
              <div class="group-header">
                <div class="title-left">
                  <div class="red-bar"></div>
                  <h3 class="shelf-title">已购买书籍</h3>
                </div>
                <div class="action-static">
                  共 {{ myBooks.length }} 本
                </div>
              </div>
              <div class="scroll-row">
                <BookCard
                    v-for="book in myBooks"
                    :key="book.modelId"
                    :book="book"
                    mode="public"
                    class="scroll-item"
                    @click="handleBookClick"
                />
              </div>
            </div>
          </div>

          <!-- 右侧：试读历史 -->
          <div v-if="historyBooks.length > 0" class="personal-col">
            <div class="category-group-wrapper">
              <div class="group-header">
                <div class="title-left">
                  <div class="red-bar"></div>
                  <h3 class="shelf-title">最近阅读</h3>
                </div>
                <div class="action-static">
                  最近 {{ historyBooks.length }} 本
                </div>
              </div>
              <div class="scroll-row">
                <BookCard
                    v-for="book in historyBooks"
                    :key="book.modelId"
                    :book="book"
                    mode="public"
                    class="scroll-item"
                    @click="handleBookClick"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- 可选：如果加载完了发现没数据，可以显示个简单的空状态，或者什么都不显示 -->
        <div v-else-if="!personalLoading" style="width: 100%; text-align: center; padding: 40px; color: #999;">
          <!-- 暂无阅读记录 -->
        </div>

      </div>

      <!-- 1. 一体化检索栏 -->
      <div class="toolbar-wrapper">
        <div class="search-combo-box">
          <div class="combo-item input-item">
            <el-input
                v-model="queryParams.keyword"
                placeholder="搜索书名..."
                size="large"
                clearable
                @keyup.enter="handleSearch"
                @clear="handleSearch"
            >
              <template #prefix>
                <el-icon>
                  <Search/>
                </el-icon>
              </template>
            </el-input>
          </div>

          <div class="combo-item select-item category-select">
            <el-select
                v-model="queryParams.category"
                placeholder="全部分类"
                size="large"
                clearable
                multiple
                collapse-tags
                collapse-tags-tooltip
                style="width: 180px"
                @change="handleSearch"
            >
              <el-option
                  v-for="item in categoryOptions"
                  :key="item.dicValue"
                  :label="item.dicLabel"
                  :value="item.dicValue"
              />
            </el-select>
          </div>

          <div class="combo-item select-item sort-select">
            <el-select v-model="queryParams.sort" placeholder="排序方式" size="large" style="width: 140px" @change="handleSearch">
              <template #prefix>
                <el-icon>
                  <Sort/>
                </el-icon>
              </template>
              <el-option v-for="item in sortOptions" :key="item.dicValue" :label="item.dicLabel" :value="item.dicValue"/>
            </el-select>
          </div>

          <div class="combo-item btn-item">
            <el-button type="primary" size="large" @click="handleSearch" class="main-btn">
              搜 索
            </el-button>
          </div>
        </div>
      </div>

      <!-- 2. 结果展示区 -->
      <div class="result-section" v-loading="loading">
        <template v-if="groupedResult.length > 0">
          <div
              v-for="group in groupedResult"
              :key="group.categoryCode"
              class="category-group-wrapper"
          >
            <ShelfGroup :title="group.categoryName">
              <template #actions>
                <div
                    v-if="group.books.length > PREVIEW_LIMIT"
                    class="action-toggle"
                    @click="toggleGroup(group.categoryCode)"
                >
                  <span v-if="!isGroupExpanded(group.categoryCode)">
                    展开 ({{ group.books.length }}) <el-icon><ArrowDown/></el-icon>
                  </span>
                  <span v-else class="expanded-text">
                    收起 <el-icon><ArrowUp/></el-icon>
                  </span>
                </div>
                <div v-else class="action-static">
                  共 {{ group.books.length }} 本
                </div>
              </template>

              <BookGrid class="book-grid">
                <BookCard
                    v-for="book in getVisibleBooks(group)"
                    :key="book.modelId"
                    :book="book"
                    mode="public"
                    @click="handleBookClick"
                />
              </BookGrid>
            </ShelfGroup>
          </div>

          <!-- [新增] 分页组件 -->
          <div class="pagination-container">
            <el-pagination
                v-model:current-page="queryParams.page"
                v-model:page-size="queryParams.size"
                :total="total"
                :page-sizes="[24,  48, 96, 192]"
                layout="->, total, sizes, prev, pager, next, jumper"
                background
                @size-change="handleSizeChange"
                @current-change="handlePageChange"
            />
          </div>
        </template>
        <!--
        <div v-else-if="!loading" class="empty-state">
          <div class="empty-icon">📚</div>
          <p>抱歉，没有找到相关书籍</p>
          <el-button @click="resetFilter">重置筛选</el-button>
        </div>
        -->
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {computed, onMounted, reactive, ref} from 'vue'
import {useRouter} from 'vue-router'
import {ArrowDown, ArrowUp, Search, Sort} from '@element-plus/icons-vue'
import {ElButton, ElIcon, ElInput, ElOption, ElPagination, ElSelect} from 'element-plus'
import BookGrid from '@/components/shelf/BookGrid.vue'
import BookCard from '@/components/shelf/BookCard.vue'
import ShelfGroup from '@/components/shelf/ShelfGroup.vue'
import type {UnifiedBookModel} from '@/types/book'
import {ShelfApi} from '@/api/shelf'
import {useUserStore} from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const PREVIEW_LIMIT = 10
const loading = ref(false)
const personalLoading = ref(userStore.isLoggedIn)

const isLoggedIn = computed(() => userStore.isLoggedIn)
const myBooks = ref<UnifiedBookModel[]>([])
const historyBooks = ref<UnifiedBookModel[]>([])
const hasPersonalData = computed(() => myBooks.value.length > 0 || historyBooks.value.length > 0)

// [新增] 总条数
const total = ref(0)

const queryParams = reactive({
  keyword: '',
  category: [] as string[],
  sort: '',
  // [新增] 分页参数
  page: 1,
  size: 12 // 默认为12，布局比较整齐 (3列或4列都好排)
})

const categoryOptions = ref<any[]>([])
const sortOptions = ref<any[]>([])

const expandedGroups = reactive(new Set<string>())
const bookList = ref<UnifiedBookModel[]>([])

const mapRelationsToBooks = (relations: any[]): UnifiedBookModel[] => {
  if (!Array.isArray(relations)) {
    return []
  }

  return relations.filter((item: any) => item.bookModel).map((item: any) => {
    const book = item.bookModel
    let progress = 0
    const totalPages = book.bookPageCount || 0
    const current = item.lastReadPageNo || 0

    if (totalPages > 0 && current > 0) {
      progress = Math.floor((current / totalPages) * 100)
      if (progress > 100) {
        progress = 100
      }
    }

    return {
      ...book,
      lastReadPage: current,
      lastReadTime: item.lastReadTime,
      purchaseStatus: item.purchaseStatus,
      progress: progress,

      bookCover: book.bookCover || ''
    }
  })
}

const loadPersonalData = async () => {
  if (!isLoggedIn.value) {
    return;
  }

  personalLoading.value = true
  try {
    const [purchasedRes, historyRes] = await Promise.all([
      ShelfApi.queryBookUserRelations({purchaseStatus: '1', size: 50}),
      ShelfApi.queryBookUserRelations({
        purchaseStatus: '0',
        isNotNullItems: ['lastReadTime'],
        sortItems: [{fieldName: 'lastReadTime', direction: 'DESC'}],
        size: 20
      })
    ])

    if (purchasedRes?.flag) {
      const list = purchasedRes.data?.content || []
      myBooks.value = mapRelationsToBooks(list)
    }

    if (historyRes?.flag) {
      const list = historyRes.data?.content || []
      historyBooks.value = mapRelationsToBooks(list)
    }

  } catch (e) {
    console.error('加载个人书架数据失败', e)
  } finally {
    setTimeout(() => {
      personalLoading.value = false
    }, 200)
  }
}

const loadDictionaries = async () => {
  try {
    const dictMap = await ShelfApi.getShelfDictionaries()

    if (dictMap['book_category']) {
      categoryOptions.value = dictMap['book_category'].sort((a, b) => (a.dicSort || 0) - (b.dicSort || 0))
    }

    if (dictMap['book_sort']) {
      sortOptions.value = dictMap['book_sort'].sort((a, b) => (a.dicSort || 0) - (b.dicSort || 0))

      if (sortOptions.value.length > 0 && !queryParams.sort) {
        queryParams.sort = sortOptions.value[0].dicValue
      }
    }
  } catch (e) {
    console.error('加载字典配置失败', e)
    sortOptions.value = [{dicLabel: '默认排序', dicValue: 'updateTimestamp,DESC'}]
    queryParams.sort = 'updateTimestamp,DESC'
  }
}

const loadData = async () => {
  loading.value = true
  try {
    // [修改] 解构新的返回值 { list, total }
    const {list, total: totalCount} = await ShelfApi.searchBooks({
      keyword: queryParams.keyword,
      categories: queryParams.category,
      sort: queryParams.sort,
      page: queryParams.page,
      size: queryParams.size
    })
    bookList.value = list
    total.value = totalCount
  } finally {
    loading.value = false
  }
}

const groupedResult = computed(() => {
  const books = bookList.value
  const groups: Record<string, UnifiedBookModel[]> = {}

  books.forEach(book => {
    const catCode = book.bookCategory || 'other'
    if (!groups[catCode]) {
      groups[catCode] = []
    }
    groups[catCode].push(book)
  })

  const result: any[] = []

  categoryOptions.value.forEach(opt => {
    if (groups[opt.dicValue]) {
      result.push({
        categoryCode: opt.dicValue,
        categoryName: opt.dicLabel,
        books: groups[opt.dicValue]
      })
      delete groups[opt.dicValue]
    }
  })

  Object.keys(groups).forEach(key => {
    result.push({
      categoryCode: key,
      categoryName: key === 'other' ? '未分类' : '其他分类',
      books: groups[key]
    })
  })

  return result
})

const isGroupExpanded = (code: string) => expandedGroups.has(code)
const toggleGroup = (code: string) => {
  if (expandedGroups.has(code)) {
    expandedGroups.delete(code)
  } else {
    expandedGroups.add(code)
  }
}
const getVisibleBooks = (group: any) => {
  if (isGroupExpanded(group.categoryCode)) {
    return group.books
  }
  return group.books.slice(0, PREVIEW_LIMIT)
}

const handleSearch = () => {
  queryParams.page = 1 // 搜索条件变化时，重置回第一页
  loadData()
}

const resetFilter = () => {
  queryParams.keyword = ''
  queryParams.category = []
  if (sortOptions.value.length > 0) {
    queryParams.sort = sortOptions.value[0].dicValue
  } else {
    queryParams.sort = ''
  }
  handleSearch()
}

const handleBookClick = (book: UnifiedBookModel) => {
  router.push(`/bookshelf/${book.modelId}`)
}

const handlePageChange = (newPage: number) => {
  queryParams.page = newPage
  loadData()
  scrollToResult()
}

const handleSizeChange = (newSize: number) => {
  queryParams.size = newSize
  queryParams.page = 1
  loadData()
  scrollToResult()
}

const scrollToResult = () => {
  const resultSection = document.querySelector('.toolbar-wrapper')
  if (resultSection) {
    resultSection.scrollIntoView({behavior: 'smooth', block: 'start'})
  }
}

onMounted(async () => {
  await loadDictionaries()
  const promises: any = []
  if (isLoggedIn.value) {
    promises.push(loadPersonalData())
  }
  promises.push(loadData())
  await Promise.all(promises)
})
</script>

<style scoped lang="scss">
.square-page {
  min-height: 100vh;
  background-color: #f8fafc;
}

.content-area {
  padding-top: 30px;
  padding-bottom: 60px;
}

.personal-section-wrapper {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;

  min-height: 270px;

  position: relative;

  .personal-col {
    flex: 1;
    min-width: 0;
  }
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;

  .title-left {
    display: flex;
    align-items: center;

    .red-bar {
      width: 4px;
      height: 18px;
      background-color: var(--el-color-danger, #f56c6c);
      margin-right: 10px;
      border-radius: 2px;
    }

    .shelf-title {
      font-size: 18px;
      font-weight: 600;
      color: #333;
      margin: 0;
    }
  }
}

.scroll-row {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 10px;
  scroll-behavior: smooth;

  &::-webkit-scrollbar {
    height: 6px;
  }

  &::-webkit-scrollbar-thumb {
    background-color: #e0e0e0;
    border-radius: 3px;
  }

  &::-webkit-scrollbar-track {
    background-color: transparent;
  }

  .scroll-item {
    flex: 0 0 auto;
    width: 140px;
  }
}

.toolbar-wrapper {
  background: white;
  padding: 20px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  margin-bottom: 30px;
  border: 1px solid rgba(0, 0, 0, 0.02);
}

.search-combo-box {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.combo-item {
  &.input-item {
    flex: 1;
    min-width: 200px;
  }

  &.main-btn {
    min-width: 100px;
    font-weight: bold;
    font-size: 16px;
  }
}

.category-group-wrapper {
  margin-bottom: 20px;
  background: #fff;
  padding: 20px 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);

  :deep(.shelf-group) {
    margin-bottom: 0;
  }
}

.book-grid {
  display: grid !important;
  grid-template-columns: repeat(auto-fill, 140px) !important;
  gap: 24px 24px;
  justify-content: flex-start;
}

@media (max-width: 768px) {
  .book-grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)) !important;
    gap: 15px;
    justify-content: center;
  }
}

.fade-in {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.action-toggle {
  cursor: pointer;
  font-size: 13px;
  color: var(--primary);
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  border-radius: 15px;
  background-color: rgba(194, 65, 12, 0.08);
  transition: all 0.2s;
  user-select: none;

  &:hover {
    background-color: rgba(194, 65, 12, 0.15);
  }

  .expanded-text {
    color: #666;
  }
}

.action-static {
  font-size: 13px;
  color: #999;
  background: #f5f5f5;
  padding: 2px 10px;
  border-radius: 12px;
}

.empty-state {
  padding: 60px 0;
  text-align: center;
  color: #999;

  .empty-icon {
    font-size: 48px;
    margin-bottom: 16px;
  }
}

/* [新增] 分页容器样式 */
.pagination-container {
  display: flex;
  justify-content: center;
  padding: 30px 0 10px 0;
  background: transparent;
}

:deep(.el-input__wrapper), :deep(.el-select__wrapper) {
  border-radius: 8px !important;
  background-color: #f9fafb !important;
  box-shadow: none !important;
  border: 1px solid #f0f0f2 !important;
  transition: all 0.2s;

  &:hover {
    border-color: var(--primary) !important;
  }

  &.is-focus {
    border-color: var(--primary) !important;
    background-color: #fff !important;
    box-shadow: 0 0 0 1px var(--primary) inset !important;
  }
}

@media (max-width: 768px) {
  .toolbar-wrapper {
    padding: 12px;
    margin-bottom: 16px;
  }

  .search-combo-box {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 8px !important;
    width: 100%;
  }

  .combo-item.input-item {
    width: 100% !important;
    flex: none !important;
  }

  .combo-item.select-item {
    flex: 1 !important;
    display: flex;
    min-width: 0;

    :deep(.el-select) {
      width: 100% !important;
    }

    :deep(.el-select__wrapper) {
      width: 100% !important;
      box-sizing: border-box;
    }
  }

  .combo-item.btn-item {
    width: 100% !important;
    margin-top: 4px;
  }

  .main-btn {
    width: 100% !important;
    height: 42px !important;
    background-color: var(--primary) !important;
    border: none !important;
    letter-spacing: 8px !important;
    font-weight: bold;
  }

  .pagination-container {
    padding: 20px 0;

    :deep(.el-pagination) {
      .el-pagination__total,
      .el-pagination__sizes,
      .el-pagination__jump {
        display: none !important;
      }

      button, .el-pager li {
        min-width: 30px;
        height: 30px;
        line-height: 30px;
        font-size: 13px;
      }

      .el-pagination__rightwrapper {
        flex: 1;
        display: flex;
        justify-content: center;
      }
    }
  }
}
</style>