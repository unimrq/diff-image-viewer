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

        <button class="action-btn" @click="generateThumbnails">重载缩略图</button>

        <!-- 列数选择 -->
        <div class="column-selector">
          <span>列数:</span>
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

// 移动端点击目录后，如果目录下有图片才收起侧边栏
async function handleMobileSelect(folder) {
  await handleSelect(folder)

  // 移动端 && 目录下有图片
  if (isMobile.value && currentImages.value.length > 0) {
    sidebarOpen.value = false
  }
}


// 获取当前后端 API 地址
function getApiBase() {
  const { protocol, hostname } = window.location
  const backendPort = 8000
  return `${protocol}//${hostname}:${backendPort}`
}

async function generateThumbnails() {
  const base = getApiBase()
  try {
    const res = await fetch(`${base}/resize`, {
      method: 'POST'
    })
    const data = await res.json()
    alert('任务已触发: ' + JSON.stringify(data))
  } catch (err) {
    console.error(err)
    alert('触发任务失败')
  }
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

/* 工具栏控件容器 */
.toolbar-controls {
  display: flex;
  align-items: center; /* 垂直居中所有子元素 */
  gap: 4px;
  height: 36px; /* 工具栏控件统一高度 */
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


/* toggle-switch 高度统一，文字居中 */
.toolbar-controls .toggle-switch {
  display: flex;
  align-items: center;
  height: 28px;
}
.toolbar-controls .toggle-switch .label-text {
  margin-left: 6px;
  line-height: 28px;
  color: white;
  font-size: 14px;
  font-family: inherit;
}

/* 列数选择容器和下拉框对齐 */
.toolbar-controls .column-selector {
  display: flex;
  align-items: center;
  height: 28px;
  gap: 8px;
}
.toolbar-controls .column-selector span {
  line-height: 28px;
  color: white;
  font-size: 14px;
  font-family: inherit;
}

/* 下拉框容器 */
.select-wrapper {
  position: relative;
  display: inline-block;
  width: 60px;
}

/* 下拉框样式 */
.select-wrapper select {
  width: 100%;
  height: 28px;
  line-height: 28px;
  padding: 0 8px;
  border: none;
  border-radius: 4px;
  appearance: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  color: black; /* 下拉文字黑色 */
  background-color: rgba(255,255,255,0.2);
  font-size: 14px;
  font-family: inherit;
}

/* 下拉箭头垂直居中 */
.select-wrapper .arrow {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  width: 12px;
  height: 6px;
  pointer-events: none;
  fill: white;
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

/* 移动端 sidebar */
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
/* toolbar 中按钮统一样式 */
.toolbar-controls button.action-btn {
  height: 32px;                 /* 与 toolbar 内控件高度匹配 */
  line-height: 32px;
  padding: 0 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #007acc;    /* toolbar 主色 */
  color: white;
  border-radius: 6px;           /* 更圆润 */
  border: none;
  font-size: 14px;
  font-family: inherit;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
}

.toolbar-controls button.action-btn:hover {
  background-color: #005fa3;    /* 深一点 hover */
}
</style>

