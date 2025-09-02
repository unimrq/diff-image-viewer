<template>
  <div>
    <!-- 工具栏 -->
    <div class="toolbar">
      <!-- 移动端菜单按钮 -->
      <button class="menu-btn" @click="toggleSidebar" v-if="isMobile">
        ☰
      </button>

      <!-- 桌面端显示标题 -->
      <h2 >差分图片浏览器</h2>

      <!-- 设置按钮 -->
      <button class="settings-btn" @click="settingsOpen = true">⚙</button>
    </div>

    <!-- 设置弹窗 -->
    <div v-if="settingsOpen" class="settings-overlay" @click.self="settingsOpen = false">
      <div class="settings-panel">
        <div class="panel-header">
          <span>设置</span>
          <button class="close-btn" @click="settingsOpen = false">×</button>
        </div>

        <div class="panel-body">
          <!-- 1. 显示a/b开关 -->
          <div class="panel-item">
            <span>1. 显示图片a</span>
            <label class="toggle-switch">
              <input type="checkbox" v-model="showA" >
              <span class="slider"></span>
            </label>
          </div>

            <!-- 2. 透视模式开关 -->
          <div class="panel-item">
            <span>2. 透视模式</span>
            <label class="toggle-switch">
              <input type="checkbox" v-model="perspectiveMode">
              <span class="slider"></span>
            </label>
          </div>

          <div class="panel-item">
            <span>3. 省流模式</span>
            <label class="toggle-switch">
              <input type="checkbox" v-model="lowDataMode">
              <span class="slider"></span>
            </label>
          </div>

          <!-- 4. 列数选择 -->
          <div class="panel-item">
            <span>4. 图片列数</span>
            <select v-model="columns">
              <option v-for="n in 12" :key="n" :value="n">{{ n }}</option>
            </select>
          </div>

          <!-- 5. 重载缩略图 -->
          <div class="panel-item">
            <span>5. 重载缩略图</span>
            <button class="action-btn" @click="generateThumbnails">执行</button>
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
        <ImageGrid 
          :images="currentImages" 
          :columns="columns" 
          :perspectiveMode="perspectiveMode" 
          :lowDataMode="lowDataMode"
        />
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
const sidebarOpen = ref(false)
const settingsOpen = ref(false)


// 响应式判断是否为移动端
const isMobile = computed(() => window.innerWidth < 768)


const showA = ref(localStorage.getItem('showA') === 'false' ? false : true)
const perspectiveMode = ref(localStorage.getItem('perspectiveMode') === 'true')
const columns = ref(Number(localStorage.getItem('columns')) || (isMobile.value ? 2 : 5))
const lowDataMode = ref(localStorage.getItem('lowDataMode') === 'true')

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

watch(showA, (val) => {
  localStorage.setItem('showA', val)
  updateImages()
})

watch(perspectiveMode, (val) => {
  localStorage.setItem('perspectiveMode', val)
})

watch(columns, (val) => {
  localStorage.setItem('columns', val)
})

// 监听变化并存储到 localStorage
watch(lowDataMode, (val) => {
  localStorage.setItem('lowDataMode', val)
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
  align-items: center;
  gap: 8px;
  height: 36px;
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

/* 设置按钮 */
.settings-btn {
  font-size: 24px;
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 4px;
}
.settings-btn:hover {
  color: #ddd;
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
.content {
  flex: 1;
  padding: 10px;
  overflow-y: auto;
}

/* 设置弹窗 */
.settings-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0,0,0,0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}
.settings-panel {
  background: #fff;
  border-radius: 10px;
  width: 280px;
  box-shadow: 0 8px 20px rgba(0,0,0,0.25);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: slideIn 0.2s ease;
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  font-weight: 600;
  font-size: 16px;
  border-bottom: 1px solid #eee;
}
.close-btn {
  border: none;
  background: none;
  font-size: 18px;
  cursor: pointer;
  color: #555;
}
.close-btn:hover { color: #000; }
.panel-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 14px;
}

/* 每一项：左文字右控件 */
.panel-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 滑块和下拉框统一样式 */
.panel-item input[type="range"],
.panel-item select,
.panel-item .action-btn {
  width: 40px;
  height: 28px;
  line-height: 28px;
  font-size: 14px;
  font-family: inherit;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 下拉框样式 */
select {
  padding: 0 6px;
  border-radius: 4px;
  border: 1px solid #ccc;
  background-color: #fff;
  color: black;
  appearance: none;
  cursor: pointer;
}

/* 滑块样式 */
input[type="range"] {
  -webkit-appearance: none;
  background: #ccc;
  border-radius: 4px;
}
input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  background: #007acc;
  border-radius: 50%;
  cursor: pointer;
  border: none;
}

/* 执行按钮 */
.action-btn {
  background-color: #007acc;  /* 蓝色背景 */
  color: white;               /* 白色文字 */
  font-size: 14px;            /* 字体大小，可根据需要调整 */
  border: none;               /* 去掉边框 */
  border-radius: 6px;         /* 圆角 */
  cursor: pointer;            /* 鼠标手型 */
  padding: 6px 4px;          /* 内边距 */
  text-align: center;
  transition: background-color 0.2s, transform 0.1s; /* 平滑过渡 */
}

.action-btn:hover {
  background-color: #005fa3;  /* hover 深蓝色 */
}



/* toggle-switch */
.toggle-switch {
  display: flex;
  align-items: center;
  cursor: pointer;
}
.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
  position: absolute;
}
.toggle-switch .slider {
  width: 40px;
  height: 20px;
  background-color: #ccc;
  border-radius: 10px;
  position: relative;
  transition: 0.2s;
}
.toggle-switch input:checked + .slider {
  background-color: #007acc;
}
.toggle-switch .slider::before {
  content: "";
  position: absolute;
  width: 16px;
  height: 16px;
  left: 2px;
  top: 2px;
  background: white;
  border-radius: 50%;
  transition: 0.2s;
}
.toggle-switch input:checked + .slider::before {
  transform: translateX(20px);
}

/* 弹窗动画 */
@keyframes slideIn {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}

</style>

