<template>
  <div>
    <!-- 工具栏 -->
    <div class="toolbar">
      <!-- 移动端菜单按钮 -->
      <button class="menu-btn" @click="toggleSidebar" v-if="isMobile">
        ☰
      </button>

      <!-- 桌面端显示标题 -->
      <h2 v-if="!isMobile">差分图片浏览器</h2>

      <div class="toolbar-controls">
        <!-- 切换开关 -->
        <label class="toggle-switch">
          <input type="checkbox" v-model="showA">
          <span class="slider"></span>
          <span class="label-text">{{ showA ? '显示a' : '显示b' }}</span>
        </label>

        <!-- 列数选择 -->
        <div class="column-selector">
          <span>图片列数:</span>
          <div class="select-wrapper">
            <select v-model="columns">
              <option v-for="n in 12" :key="n" :value="n">{{ n }}</option>
            </select>
            <svg class="arrow" viewBox="0 0 10 6">
              <path d="M0 0 L5 6 L10 0 Z" fill="currentColor"/>
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- 半透明遮罩 -->
    <div v-if="isMobile && sidebarOpen" class="overlay" @click="sidebarOpen = false"></div>

    <!-- 主体布局 -->
    <div class="container">
      <!-- 左侧导航栏 -->
      <aside
        class="sidebar"
        :class="{ open: sidebarOpen || !isMobile }"
      >
        <FolderTree
          :folders="folderTree"
          @select="handleMobileSelect"
        />
      </aside>

      <!-- 右侧图片瀑布流 -->
      <main class="content">
        <ImageGrid :images="currentImages" :columns="columns" />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import FolderTree from '../components/FolderTree.vue'
import ImageGrid from '../components/ImageGrid.vue'

const folderTree = ref([])
const currentImages = ref([])
const currentPath = ref('')
const showA = ref(true)
const sidebarOpen = ref(false)

// 响应式判断是否为移动端
const isMobile = computed(() => window.innerWidth < 768)

// 列数根据屏幕自动设置
const columns = ref(isMobile.value ? 2 : 5)

// 切换侧边栏
function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}

// 移动端点击目录后自动收起
function handleMobileSelect(folder) {
  handleSelect(folder)
  if (isMobile.value) sidebarOpen.value = false
}

// 获取当前后端 API 地址
function getApiBase() {
  const { protocol, hostname } = window.location
  const backendPort = 8000
  return `${protocol}//${hostname}:${backendPort}`
}

// 调用后端 API 获取目录内容
async function loadFolder(path = '') {
  const base = getApiBase()
  const res = await fetch(`${base}/api/list?dir=${encodeURIComponent(path)}`)
  const data = await res.json()
  return data.map(f => ({ ...f, expanded: false, children: [] }))
}

// 初始化根目录
onMounted(async () => {
  folderTree.value = await loadFolder('')
  window.addEventListener('resize', onResize)
})

// 监听窗口 resize
function onResize() {
  if (!isMobile.value) sidebarOpen.value = false
  columns.value = isMobile.value ? 2 : 5
}

// 编码图片 URL
function encodeImageURL(path) {
  const base = getApiBase()
  return encodeURI(`${base}/images/${path}`)
}

// 根据切换开关刷新图片
async function updateImages() {
  if (!currentPath.value) return
  const allItems = await loadFolder(currentPath.value)
  const suffix = showA.value ? 'a.jpg' : 'b.jpg'
  currentImages.value = allItems
    .filter(item => item.type === 'file' && item.name.endsWith(suffix))
    .map(file => encodeImageURL(file.path))
}

// 点击文件夹
async function handleSelect(folder) {
  currentPath.value = folder.path

  const allItems = await loadFolder(folder.path)
  if (folder.type === 'folder' && folder.children.length === 0) {
    folder.children = allItems
      .filter(item => item.type === 'folder')
      .map(f => ({ ...f, expanded: false, children: [] }))
  }

  await updateImages()
}

// 监听开关切换，自动刷新
watch(showA, () => {
  updateImages()
})
</script>


<style scoped>
/* 工具栏样式 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
  padding: 0 16px;
  background: #007acc;
  color: white;
}
.toolbar h2 {
  margin: 0;
  font-size: 20px;
}
.toolbar-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 移动端菜单按钮 */
.menu-btn {
  font-size: 24px;
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  margin-right: 8px;
}

/* 半透明遮罩 */
.overlay {
  position: fixed;
  top: 60px;
  left: 0;
  width: 100%;
  height: calc(100vh - 60px);
  background-color: rgba(0,0,0,0.4);
  z-index: 900;
}

/* 主体布局 */
.container {
  display: flex;
  height: calc(100vh - 60px);
}
.sidebar {
  width: 250px;
  border-right: 1px solid #ddd;
  overflow-y: auto;
  padding: 10px 0;
  background: #f9f9f9;
  transition: transform 0.3s;
}
.sidebar.open {
  transform: translateX(0);
}
/* 列数选择 */
.column-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: white;
}
.column-selector span {
  font-weight: 500;
}

/* 下拉框容器 */
.select-wrapper {
  position: relative;
  display: inline-block;
  width: 60px;
}

/* 隐藏原生箭头 */
.select-wrapper select {
  width: 100%;
  padding: 4px 24px 4px 8px; /* 右侧留空间给自定义箭头 */
  border-radius: 4px;
  border: none;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  background-color: rgba(255, 255, 255, 0.2);
  color: black;
  font-size: 14px;
  cursor: pointer;
}
.select-wrapper select:focus {
  outline: none;
  background-color: rgba(255, 255, 255, 0.3);
}

/* 自定义箭头 */
.select-wrapper .arrow {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  width: 12px;   /* 小巧箭头 */
  height: 6px;
  pointer-events: none;
  fill: white;
}

@media (max-width: 767px) {
  .sidebar {
    position: fixed;
    top: 60px;
    left: 0;
    height: calc(100vh - 60px);
    width: 100%;
    z-index: 1000;
    transform: translateX(-100%);
  }
  .sidebar.open {
    transform: translateX(0);
  }
}

/* 内容区域 */
.content {
  flex: 1;
  padding: 10px;
  overflow-y: auto;
}
</style>
