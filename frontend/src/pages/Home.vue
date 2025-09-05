<template>
  <div>
    <!-- 工具栏 -->
    <div class="toolbar">
      <!-- 移动端菜单按钮 -->
      <button class="menu-btn" @click="toggleSidebar" v-if="isMobile">
        ☰
      </button>

      <!-- 桌面端显示标题 -->
      <h2>差分图片浏览器</h2>

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
            <span>显示图片A</span>
            <label class="toggle-switch">
              <input type="checkbox" v-model="showA">
              <span class="slider"></span>
            </label>
          </div>

          <!-- 2. 透视模式开关 -->
          <div class="panel-item">
            <span>透视模式</span>
            <label class="toggle-switch">
              <input type="checkbox" v-model="perspectiveMode">
              <span class="slider"></span>
            </label>
          </div>

          <!-- 3. 省流模式 -->
          <div class="panel-item">
            <span>省流模式</span>
            <label class="toggle-switch">
              <input type="checkbox" v-model="lowDataMode">
              <span class="slider"></span>
            </label>
          </div>

          <!-- 4. 列数选择 -->
          <div class="panel-item">
            <span>图片列数</span>
            <select v-model="columns">
              <option v-for="n in 12" :key="n" :value="n">{{ n }}</option>
            </select>
          </div>

          <!-- 5. 重载缩略图 -->
          <div class="panel-item">
            <span>图片扫描</span>
            <button class="action-btn" @click="generateThumbnails">执行</button>
          </div>

          <!-- 6. 密码登录 -->
          <div class="panel-item" >
            <span>访问密码</span>
            <button class="action-btn" @click="tryLogin">登录</button>
          </div>

          <div style="display: flex; width: 100%; margin-top: -8px; margin-left: 24px; align-items: center;">
            <input
              v-model="password"
              maxlength="8"
              class="password-input-underline"
              placeholder="请输入密码"
              style="margin-right: 8px;"
            />
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
import { ref, onMounted, watch, computed, onBeforeUnmount } from 'vue'
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

// 密码 & token
const password = ref('')
const authToken = ref(localStorage.getItem("authToken") || "")

// ------------------ 登录鉴权 ------------------
async function tryLogin() {
  try {
    const res = await fetch(`/api/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: password.value })
    })
    const data = await res.json()
    if (data.success) {
      authToken.value = data.token
      localStorage.setItem("authToken", data.token)
      alert("登录成功")
      window.location.reload()
    } else {
      alert("密码错误")
    }
  } catch (err) {
    console.error(err)
    alert("登录失败")
  }
}

async function authedFetch(url, options = {}) {
  if (!authToken.value) throw new Error("未登录")
  return fetch(url, {
    ...options,
    headers: {
      ...(options.headers || {}),
      Authorization: `Bearer ${authToken.value}`
    }
  })
}

// ------------------ 功能 ------------------
function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}

async function handleMobileSelect(folder) {
  await handleSelect(folder)
  if (isMobile.value && currentImages.value.length > 0) {
    sidebarOpen.value = false
  }
}

async function generateThumbnails() {
  try {
    const res = await authedFetch(`/api/resize`, { method: 'POST' })
    const data = await res.json()
    alert('任务已触发')
  } catch (err) {
    console.error(err)
    alert('触发任务失败')
  }
}

async function loadFolder(path = "") {
  try {
    const res = await authedFetch(`/api/list?dir=${encodeURIComponent(path)}`)
    const data = await res.json()
    return data.map(f => ({ ...f, expanded: false, children: [] }))
  } catch (e) {
    console.warn("未登录或无权限")
    return []
  }
}

function handleBack(e) {
  if (isMobile.value) {
    if (!sidebarOpen.value) {
      e.preventDefault()
      sidebarOpen.value = true
      history.pushState(null, "", location.href)
    }
  }
}

onMounted(async () => {
  if (authToken.value) {
    folderTree.value = await loadFolder('')
  }
  window.addEventListener('resize', onResize)
  history.pushState(null, "", location.href)
  window.addEventListener("popstate", handleBack)
})

onBeforeUnmount(() => {
  window.removeEventListener("popstate", handleBack)
})

function onResize() {
  if (!isMobile.value) sidebarOpen.value = false
  columns.value = isMobile.value ? 2 : 5
}

function encodeImageURL(path) {
  return encodeURI(`/images/${path}`)
}

async function updateImages() {
  if (!currentPath.value) return
  const allItems = await loadFolder(currentPath.value)
  const suffix = showA.value ? 'a' : 'b'
  const regex = new RegExp(`${suffix}\\.(jpg|jpeg|png|webp)$`, 'i')
  currentImages.value = allItems
    .filter(item => item.type === 'file' && regex.test(item.name))
    .map(file => encodeImageURL(file.path))
}

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

// ------------------ 本地存储 ------------------
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
  margin: 0;               /* 去掉默认外边距 */
  font-size: 20px;
  line-height: 1;          /* 避免行高撑大 */
  display: flex;
  align-items: center;     /* 让里面的文字也居中 */
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
  transform: translateY(-2px);  /* 微调位置 */
}

/* 设置按钮 */
.settings-btn {
  font-size: 24px;
  font-weight: 700;   /* 加粗，可根据需要调整 400/500/600/700 */
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 4px;
}
.settings-btn:hover {
  color: #ddd;
}

/* 输入框样式 */
.password-input {
  width: 120px;
  height: 28px;
  padding: 0 6px;
  font-size: 14px;
  border: 1px solid #ccc;
  border-radius: 4px;
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
  width: 350px;
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
  font-size: 24px;
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
  position: relative;      /* 为伪元素定位做准备 */
  padding-left: 24px;      /* 给小圆点留位置 */
  margin: 8px 0;           /* 每项之间垂直间距相等 */
}

/* 在每项前加一个圆点 */
.panel-item::before {
  content: "";
  width: 12px;              /* 圆点大小 */
  height: 12px;
  border-radius: 50%;      /* 圆形 */
  background-color: #424242; /* 蓝色圆点，可以换色 */
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%); /* 垂直居中 */
}

.password-input-underline {
  width: 90%;
  padding: 4px 0;
  font-size: 14px;
  border: none;
  border-bottom: 2px solid #ccc; /* 下划线颜色 */
  outline: none;
  background: transparent;
  color: black;
}

.password-input-underline:focus {
  border-bottom-color: #007acc; /* 聚焦时下划线颜色 */
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

