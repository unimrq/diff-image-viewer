<template>
  <div>
    <!-- 工具栏 -->
    <div class="toolbar">
      <h2>差分图片浏览器</h2>

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

    <!-- 主体布局 -->
    <div class="container">
      <!-- 左侧导航栏 -->
      <aside class="sidebar">
        <FolderTree :folders="folderTree" @select="handleSelect" />
      </aside>

      <!-- 右侧图片瀑布流 -->
      <main class="content">
        <ImageGrid :images="currentImages" :columns="columns" />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import FolderTree from '../components/FolderTree.vue'
import ImageGrid from '../components/ImageGrid.vue'

const folderTree = ref([])
const currentImages = ref([])
const currentPath = ref('')
const columns = ref(6)
const showA = ref(true)  // true 显示 a.jpg，false 显示 b.jpg

// 获取当前后端 API 地址，支持动态 IP/端口
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
})

// 编码图片 URL，保证中文/空格不会被截断
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

/* 开关样式 */
.toggle-switch {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}
.toggle-switch input {
  display: none;
}
.toggle-switch .slider {
  width: 36px;
  height: 18px;
  background-color: #ccc;       /* 未选中时灰色 */
  border-radius: 9px;
  position: relative;
  transition: 0.2s;
}
.toggle-switch input:checked + .slider {
  background-color: #00cc66;    /* 选中时绿色 */
}
.toggle-switch .slider::before {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  left: 1px;
  top: 1px;
  background-color: white;       /* 滑块保持白色，突出 */
  border-radius: 50%;
  transition: 0.2s;
}
.toggle-switch input:checked + .slider::before {
  transform: translateX(18px);
}

.toggle-switch .label-text {
  font-size: 14px;
  color: white;
  text-shadow: 0 0 2px rgba(0,0,0,0.5); /* 文字更清晰 */
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
.select-wrapper {
  position: relative;
  display: inline-block;
  width: 60px;
}
.select-wrapper select {
  width: 100%;
  padding: 4px 28px 4px 8px;
  border-radius: 4px;
  border: none;
  appearance: none;
  background-color: rgba(255, 255, 255, 0.2);
  color: black;
  font-size: 14px;
  cursor: pointer;
}
.select-wrapper select:focus {
  outline: none;
  background-color: rgba(255, 255, 255, 0.3);
}
.select-wrapper .arrow {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 10px;
  height: 6px;
  pointer-events: none;
  fill: white;
}

/* 主体布局 */
.container {
  display: flex;
  height: calc(100vh - 60px); /* 减去 toolbar 高度 */
}
.sidebar {
  width: 250px;
  border-right: 1px solid #ddd;
  overflow-y: auto;
  padding: 10px 0px;
}
.content {
  flex: 1;
  padding: 10px;
  overflow-y: auto;
}
</style>
