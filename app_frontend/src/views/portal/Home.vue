<!-- src/views/portal/Home.vue -->
<template>
  <div class="portal-home">
    <div class="page-container main-content">

      <!-- =========================================
           1. 平台愿景 (Hero Section)
           ========================================= -->
      <section class="common-section">
        <div class="section-header">
          <h2 class="section-title">平台愿景</h2>
        </div>

        <div class="section-card hero-card-layout">
          <!-- Left: Text -->
          <div class="hero-text-side">
            <h1 class="hero-slogan">
              做实现知识自由的铲子
            </h1>

            <div class="hero-rotate-container">
              <transition name="fade-slide" mode="out-in">
                <span :key="rotateIndex" class="rotate-item">
                  {{ currentRotateText }}
                </span>
              </transition>
            </div>

            <p class="hero-desc">用技术重塑阅读体验，连接最硬核的大脑与最渴求的灵魂。拒绝死记硬背，从“看不懂”到“会心一笑”； 拒绝“用爱发电”，让创作价值回归。</p>

            <div class="hero-actions">
              <!-- 只保留进入书坊 -->
              <button class="btn-primary" @click="router.push('/bookshelf')">
                进入书坊
              </button>
            </div>
          </div>

          <!-- Right: Visual (3D Book) -->
          <div class="hero-visual-side">
            <div class="mock-book-group">
              <div class="visual-book">
                <div class="vb-face-content">
                  <div class="vb-cover-title">
                    <span class="vb-main-text">知识自由</span>
                  </div>
                  <div class="vb-features">
                    <div class="vb-feat-item"><span class="feat-icon">🚀</span> 代码下载</div>
                    <div class="vb-feat-item"><span class="feat-icon">🎬</span> 视频伴读</div>
                    <div class="vb-feat-item"><span class="feat-icon">🔎</span> 术语高亮</div>
                    <div class="vb-feat-item"><span class="feat-icon">📝</span> 读书笔记</div>
                  </div>
                </div>
                <div class="vb-spine"></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- =========================================
           2. 致 创作者 (Author Features)
           ========================================= -->
      <section class="common-section">
        <div class="section-header">
          <h2 class="section-title">致 创作者</h2>
          <span class="section-subtitle">创作，是体面的劳动</span>
        </div>

        <div class="role-grid">
          <template v-if="config.authorFeatures?.list">
            <div v-for="(item, idx) in config.authorFeatures.list" :key="'a-' + idx" class="wr-feature-card">
              <div class="fc-icon">{{ item.icon }}</div>
              <h3 class="fc-title">{{ item.title }}</h3>
              <p class="fc-desc">{{ item.desc }}</p>
            </div>
          </template>
        </div>
      </section>

      <!-- =========================================
           3. 致 求索者 (Reader Features)
           ========================================= -->
      <section class="common-section">
        <div class="section-header">
          <h2 class="section-title">致 求索者</h2>
          <span class="section-subtitle">阅读，是享受的旅程</span>
        </div>

        <div class="role-grid">
          <template v-if="config.readerFeatures?.list">
            <div v-for="(item, idx) in config.readerFeatures.list" :key="'r-' + idx" class="wr-feature-card">
              <div class="fc-icon">{{ item.icon }}</div>
              <h3 class="fc-title">{{ item.title }}</h3>
              <p class="fc-desc">{{ item.desc }}</p>
            </div>
          </template>
        </div>
      </section>

      <!-- =========================================
           4. 平台信仰 (Credo)
           ========================================= -->
      <section class="common-section">
        <div class="section-header">
          <h2 class="section-title">平台信仰</h2>
        </div>

        <div class="section-card credo-layout">
          <div class="credo-diagram">
            <span class="cd-item">作者心</span>
            <span class="cd-line"></span>
            <span class="cd-item active">平台心</span>
            <span class="cd-line"></span>
            <span class="cd-item">读者心</span>
          </div>

          <div class="credo-value">心心心相印 · 互为共生</div>
          <h2 class="credo-text">初心 · 匠心 · 诚心</h2>
          <p class="credo-sub">不做流量的奴隶，只做有用的铲子</p>
        </div>
      </section>

    </div> <!-- End page-container -->

    <footer class="portal-footer">
      <div class="page-container">
        &copy; 2026 三心书坊. All Rights Reserved.
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import {computed, onMounted, onUnmounted, ref} from 'vue'
import {useRouter} from 'vue-router'
import {getHomeConfig} from '@/api/portal'

const router = useRouter()

// 仅保留配置数据，不再需要 books 列表
const config = ref<any>({
  authorFeatures: {list: []},
  readerFeatures: {list: []}
})

// 轮播文字
const rotateIndex = ref(0)
const rotateInterval = ref<any>(null)

const currentRotateText = computed(() => {
  const list = [
    '让创作 · 安心 · 省心 · 有利心',
    '使阅读 · 舒心 · 会心 · 能定心'
  ]
  return list[rotateIndex.value % list.length]
})

const resetInterval = () => {
  if (rotateInterval.value) {
    clearInterval(rotateInterval.value)
  }
  rotateInterval.value = setInterval(() => {
    rotateIndex.value++
  }, 5000)
}

onMounted(async () => {
  try {
    const configData = await getHomeConfig()
    if (configData) {
      config.value = configData
    }
  } catch (error) {
    console.error('Failed to load data, using mock:', error)
    // Mock 兜底数据
    config.value = {
      authorFeatures: {
        list: [
          {icon: '🛡️', title: '安心', desc: '独家矢量切片技术与加密流传输。你只管挥洒才华，我们做你最坚固的护城河。'},
          {icon: '⚡', title: '省心', desc: '支持全本 PDF 一键导入，1:1 像素级还原。告别繁琐排版，发布像呼吸一样自然。'},
          {icon: '💰', title: '利心', desc: '拒绝“用爱发电”。高比例分成与独立定价权，让每一行字符的价值都实实在在。'}
        ]
      },
      readerFeatures: {
        list: [
          {icon: '☕', title: '舒心', desc: '融合纸书的优雅与数字的便捷。PC 宽屏沉浸，移动端流式适配，你的数字书房。'},
          {icon: '💡', title: '会心', desc: '术语即点即查，难点视频弹窗伴读。拒绝死记硬背，从“看不懂”到“会心一笑”。'},
          {icon: '🧘', title: '定心', desc: '专属仪表盘记录每一个脚印。在碎片化的时代，帮你把心定下来，把书读进去。'}
        ]
      }
    }
  }
  resetInterval()
})

onUnmounted(() => {
  if (rotateInterval.value) {
    clearInterval(rotateInterval.value)
  }
})
</script>

<style scoped lang="scss">
/* 移除 header 相关的样式，因为已经移到 Layout 了 */
.portal-home {
  /* min-height 由 Layout 控制，这里不需要了 */
}

.main-content {
  padding-top: 40px;
  padding-bottom: 40px;
}

.common-section {
  margin-bottom: 60px;
}

/* === 通用组件 === */
.section-header {
  display: flex;
  align-items: flex-end; /* 底部对齐 */
  gap: 12px;
  margin-bottom: 20px;
}

.section-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  position: relative;
  padding-left: 12px;
  margin: 0;

  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 4px;
    height: 18px;
    background-color: var(--primary);
    border-radius: 2px;
  }
}

.section-subtitle {
  font-size: 14px;
  color: #999;
  padding-bottom: 2px;
}

.section-card {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.02);
  transition: box-shadow 0.3s ease;

  &:hover {
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.06);
  }
}

/* === 1. Hero Section === */
.hero-card-layout {
  padding: 50px 60px;
  min-height: 400px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 60px;
}

.hero-text-side {
  flex: 1;
  display: flex;
  flex-direction: column;
  z-index: 2;
  min-width: 300px;
}

.hero-rotate-container {
  height: 28px;
  margin-bottom: 16px;
  font-size: 16px;
  color: #999;
}

.hero-slogan {
  font-size: 40px;
  font-weight: 800;
  color: #1a1a1a;
  line-height: 1.2;
  margin: 0 0 16px 0;
  letter-spacing: -1px;
}

.hero-desc {
  font-size: 16px;
  color: #555;
  line-height: 1.6;
  max-width: 520px;
  margin-bottom: 30px;
  text-align: left;
  text-indent: 2em;
}

.hero-actions {
  display: flex;
  gap: 16px;
}

.btn-primary {
  padding: 10px 40px; /* 加宽一点，因为只有一个按钮 */
  border-radius: 30px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  background: #1a1a1a;
  color: white;
  border: none;

  &:hover {
    background: #000;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }
}

/* 3D Visual Book (保持不变) */
.hero-visual-side {
  flex: 0 0 400px;
  height: 300px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  perspective: 1000px;
}

.mock-book-group {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: gentleFloat 6s ease-in-out infinite;
}

.visual-book {
  width: 200px;
  height: 280px;
  background: linear-gradient(135deg, #2b2b2b 0%, #111 100%);
  border-radius: 4px 16px 16px 4px;
  position: relative;
  box-shadow: -20px 20px 40px rgba(0, 0, 0, 0.3);
  transform: rotateY(-20deg) rotateX(8deg);
  transform-style: preserve-3d;
  transition: transform 0.4s ease;

  &:hover {
    transform: rotateY(-10deg) rotateX(4deg) scale(1.02);
  }
}

.vb-spine {
  position: absolute;
  left: 0;
  top: 0;
  width: 20px;
  height: 100%;
  background: linear-gradient(to right, rgba(255, 255, 255, 0.1), transparent);
  z-index: 1;
  border-radius: 4px 0 0 4px;
}

.vb-face-content {
  position: relative;
  z-index: 2;
  width: 100%;
  height: 100%;
  padding: 30px;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.05);
  border-radius: 4px 16px 16px 4px;
}

.vb-cover-title {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.vb-main-text {
  font-size: 28px;
  font-weight: 800;
  color: #fff;
  letter-spacing: 6px;
  font-family: "Songti SC", serif;
}

.vb-features {
  width: 100%;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.vb-feat-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.03);
  padding: 8px 14px;
  border-radius: 8px;
  transition: all 0.2s;

  &:hover {
    background: rgba(255, 255, 255, 0.08);
    color: #fff;
    transform: translateX(4px);
  }
}

/* === 2 & 3. Role Grids (创作者/求索者) === */
/* 使用统一的 Grid 布局 */
.role-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.wr-feature-card {
  background: white;
  border-radius: 16px;
  padding: 32px 24px;
  text-align: center;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(0, 0, 0, 0.02);
  transition: all 0.3s;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.06);
  }
}

.fc-icon {
  font-size: 32px;
  margin: 0 auto 16px;
  background: #f8f8f8;
  width: 64px;
  height: 64px;
  line-height: 64px;
  border-radius: 50%;
}

.fc-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 10px;
  color: #333;
}

.fc-desc {
  font-size: 14px;
  color: #888;
  line-height: 1.6;
  text-align: left;
  text-indent: 2em;
}

/* === 4. Credo === */
.credo-layout {
  text-align: center;
  padding: 60px 40px;
  position: relative;
  overflow: hidden;

  &::before {
    content: "BELIEF";
    position: absolute;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 90px;
    color: rgba(0, 0, 0, 0.03);
    font-weight: 900;
    pointer-events: none;
  }
}

.credo-diagram {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 10px;
}

.cd-item {
  font-size: 14px;
  color: #bbb;
  text-transform: uppercase;
}

.cd-item.active {
  color: var(--primary);
  font-weight: 700;
}

.cd-line {
  width: 40px;
  height: 1px;
  background: #eee;
}

.credo-value {
  font-size: 18px;
  color: var(--primary);
  margin-bottom: 12px;
  letter-spacing: 4px;
}

.credo-text {
  font-size: 36px;
  font-weight: 400;
  color: #1a1a1a;
  margin: 0 0 24px 0;
  letter-spacing: 10px;
  font-family: "Songti SC", "SimSun", serif;
  white-space: nowrap;
  display: block;
}

.portal-footer {
  text-align: center;
  padding: 40px 0;
  color: #ccc;
  font-size: 12px;
  background: #f9f9f9;
  border-top: 1px solid #eee;
}

/* Animations */
.fade-slide-enter-active, .fade-slide-leave-active {
  transition: all 0.5s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

@keyframes gentleFloat {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

@media (max-width: 1024px) {
  .hero-card-layout {
    flex-direction: column-reverse;
    padding: 40px 24px;
    text-align: center;
    gap: 30px;
  }
  .hero-text-side {
    width: 100%;
    align-items: center;
  }
  .hero-slogan {
    font-size: 28px;
  }
  .hero-desc {
    font-size: 14px;
  }
  .hero-visual-side {
    flex: unset;
    width: 100%;
    height: 280px;
    margin-bottom: 10px;
  }
  .role-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  .credo-text {
    font-size: 24px;
    letter-spacing: 4px;
    margin-bottom: 16px;
  }
  .credo-diagram {
    gap: 8px;

    .cd-line {
      width: 20px;
    }

    .cd-item {
      font-size: 12px;
    }
  }
}

@media (max-width: 375px) {
  .credo-text {
    font-size: 20px;
    letter-spacing: 2px;
  }
}
</style>