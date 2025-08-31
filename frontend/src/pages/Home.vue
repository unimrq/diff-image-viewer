<template>
  <div class="toolbar">
    <h2>差分图片浏览器</h2>
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
</template>

<script setup>
import { ref, onMounted } from 'vue'
import FolderTree from '../components/FolderTree.vue'
import ImageGrid from '../components/ImageGrid.vue'

const folderTree = ref([])
const currentImages = ref([])   // 所有图片
const currentPath = ref('')
const columns = ref(6) // 默认列数
// 调用后端 API 获取目录内容
async function loadFolder(path = '') {
  const res = await fetch(`http://localhost:8000/api/list?dir=${encodeURIComponent(path)}`)
  const data = await res.json()
  return data.map(f => ({
    ...f,
    expanded: false,
    children: []
  }))
}

// 初始化根目录
onMounted(async () => {
  folderTree.value = await loadFolder('')
})

// 编码图片 URL，保证中文/空格不会被截断
function encodeImageURL(path) {
  return encodeURI(`http://localhost:8000/images/${path}`)
}

// 点击文件夹
async function handleSelect(folder) {
  currentPath.value = folder.path

  const allItems = await loadFolder(folder.path)

  // 懒加载子目录
  if (folder.type === 'folder' && folder.children.length === 0) {
    folder.children = allItems
      .filter(item => item.type === 'folder')
      .map(f => ({ ...f, expanded: false, children: [] }))
  }

  // 当前目录下的 a 图
  currentImages.value = allItems
    .filter(item => item.type === 'file' && item.name.endsWith('a.jpg'))
    .map(file => encodeImageURL(file.path))
}
</script>

<style scoped>
.container {
  display: flex;
  height: calc(100vh - 80px); /* Toolbar 高度 60px */
}
.sidebar {
  width: 250px;
  border-right: 1px solid #ddd;
  overflow-y: auto;
  padding: 10px 0px; /* 上下间距加大 */
}
.content {
  flex: 1;
  padding: 10px; /* 上下左右间距都加大 */
  overflow-y: auto;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px; /* 高度增加 */
  padding: 0 16px; /* 左右间距 */
  background: #007acc;
  color: white;
}
.toolbar h2 {
  margin: 0;
  font-size: 20px; /* 字体略大 */
}
.toolbar .settings {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  font-size: 20px; /* 图标字体略大 */
}
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
  appearance: none; /* 移除默认下拉箭头 */
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

</style>

