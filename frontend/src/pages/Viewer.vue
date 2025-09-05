<template>
  <div class="viewer">
    <!-- 工具栏 -->
    <div class="toolbar">
      <label>大小：{{ radius }}px</label>
      <input type="range" min="20" max="300" v-model="radius" />
      <button @click="clearATop">清除</button>
      <button @click="restoreATop">复原</button>
      <button @click="confirmRegenerate" :disabled="generating">
        {{ generating ? '生成中...' : '重新生成' }}
      </button>
    </div>

    <!-- Canvas 容器 -->
    <div class="canvas-wrapper">
      <canvas ref="canvas"></canvas>

      <div class="arrow left" @click="prevImage" :class="{ disabled: currentIndex === 0 }">
        <svg viewBox="0 0 24 24" width="24" height="24">
          <path fill="white" d="M15.41 16.58L10.83 12l4.58-4.59L14 6l-6 6 6 6z"/>
        </svg>
      </div>

      <div class="arrow right" @click="nextImage" :class="{ disabled: currentIndex === images.length - 1 }">
        <svg viewBox="0 0 24 24" width="24" height="24">
          <path fill="white" d="M8.59 16.58L13.17 12 8.59 7.41 10 6l6 6-6 6z"/>
        </svg>
      </div>

    </div>

    <!-- 提示框 -->
    <div v-if="toast.show" class="toast" :class="toast.type">
      {{ toast.message }}
    </div>
  </div>
</template>


<script setup>
import { ref, onMounted, watch, onBeforeUnmount, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const canvas = ref(null)
const route = useRoute()
const router = useRouter()

// 图片相关
const images = JSON.parse(localStorage.getItem("images") || "[]")
const currentIndex = ref(Number(route.query.index) || 0)
const imgA = new Image()
const imgB = new Image()
const offCanvas = document.createElement('canvas')
const offCtx = offCanvas.getContext('2d')
const loaded = { a: false, b: false }

// 状态
const generating = ref(false)
const perspectiveMode = route.query.p === '1'
const lowDataMode = route.query.l === '1'
const toast = ref({ show: false, message: '', type: 'info' })
const isMobile = computed(() => window.innerWidth < 768)
const radius = ref(isMobile.value ? (perspectiveMode ? 180 : 100) : (perspectiveMode ? 300 : 150))

let scale = 1
let mousePos = null
let drawing = false

// ---------------- 翻页 ----------------
function prevImage() {
  if (currentIndex.value > 0) {
    currentIndex.value--
    const newPath = images[currentIndex.value]
    loadImages(newPath) // 直接加载图片
    router.replace({
      path: `/viewer/${encodeURIComponent(newPath)}`,
      query: { index: currentIndex.value, p: perspectiveMode ? 1 : 0, l: lowDataMode ? 1 : 0 }
    })
  }
}

function nextImage() {
  if (currentIndex.value < images.length - 1) {
    currentIndex.value++
    const newPath = images[currentIndex.value]
    loadImages(newPath) // 直接加载图片
    router.replace({
      path: `/viewer/${encodeURIComponent(newPath)}`,
      query: { index: currentIndex.value, p: perspectiveMode ? 1 : 0, l: lowDataMode ? 1 : 0 }
    })
  }
}

function handleKeydown(e) {
  if (e.key === 'ArrowLeft') {
    prevImage()
  } else if (e.key === 'ArrowRight') {
    nextImage()
  }
}


// ---------------- 图片加载 ----------------
async function loadImages(aPath) {
  if (!aPath) return
  const exts = ['jpg','jpeg','png','webp','bmp','gif','tiff']
  const regex = new RegExp(`a\\.(${exts.join('|')})$`, 'i')
  const bPath = aPath.replace(regex, 'b.$1')

  loaded.a = loaded.b = false
  offCtx.clearRect(0, 0, offCanvas.width, offCanvas.height)
  mousePos = null

  let aUrl = aPath + '?t=' + Date.now()
  let bUrl = bPath + '?t=' + Date.now()

  if (lowDataMode) {
    try {
      const res = await fetch(`/api/compress`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ aPath, bPath })
      })
      const data = await res.json()
      aUrl = data.aCompressed
      bUrl = data.bCompressed
    } catch (err) {
      console.warn('压缩失败，使用原图', err)
    }
  }

  imgA.onload = () => {
    loaded.a = true
    offCanvas.width = imgA.width
    offCanvas.height = imgA.height
    offCtx.clearRect(0,0,offCanvas.width,offCanvas.height)
    offCtx.drawImage(imgA,0,0)
    updateScale()
    redraw()
  }

  imgB.onload = () => {
    loaded.b = true
    updateScale()
    redraw()
  }

  imgB.onerror = () => {
    imgB.src = aUrl   // 用 A 图替代a
    updateScale()
    redraw()
    showToast("未找到 B 图")  // 提示用户
  }

  imgA.src = aUrl
  imgB.src = bUrl
}


// ---------------- 监听 ----------------
watch(() => route.params.imgPath, (p) => loadImages(p), { immediate: true })
watch(
  () => currentIndex.value,
  (idx) => {
    if (images.length > 0) {
      loadImages(images[idx])
    }
  },
  { immediate: true }
)

// ---------------- Canvas ----------------
function getXY(e) {
  if (!canvas.value || !imgA.width || !imgB.width) return { x: 0, y: 0 }

  const rect = canvas.value.getBoundingClientRect()

  // 计算绘制 imgA 的缩放比例（和 redraw 保持一致）
  const scaleX = canvas.value.width / imgA.width
  const scaleY = canvas.value.height / imgA.height
  const scale = Math.min(scaleX, scaleY)

  // 居中偏移
  const offsetX = (canvas.value.width - imgA.width * scale) / 2
  const offsetY = (canvas.value.height - imgA.height * scale) / 2

  return {
    x: (e.clientX - rect.left - offsetX) / scale,
    y: (e.clientY - rect.top - offsetY) / scale
  }
}


function redraw() {
  if (!canvas.value || !loaded.a || !loaded.b) return
  const c = canvas.value
  const ctx = c.getContext('2d')
  ctx.clearRect(0, 0, c.width, c.height)

  const offsetX = (c.width - imgA.width * scale) / 2
  const offsetY = (c.height - imgA.height * scale) / 2
  const drawWidth = offCanvas.width * scale
  const drawHeight = offCanvas.height * scale
  // 底图 B —— 按照 A 的尺寸缩放
  ctx.drawImage(imgB, offsetX, offsetY, imgA.width * scale, imgA.height * scale)

  // 顶图 A
  ctx.drawImage(offCanvas, offsetX, offsetY, drawWidth, drawHeight)


  // 透视模式裁剪圆圈
  if (perspectiveMode && mousePos) {
    ctx.save()
    ctx.beginPath()
    ctx.arc(mousePos.x * scale + offsetX, mousePos.y * scale + offsetY, radius.value, 0, Math.PI * 2)
    ctx.clip()
    ctx.drawImage(imgB, offsetX, offsetY, drawWidth, drawHeight)  // 使用和 offCanvas 一样的尺寸
    ctx.restore()
  }


  // 鼠标提示圆圈
  if (mousePos) {
    ctx.save()
    ctx.beginPath()
    ctx.arc(mousePos.x * scale + offsetX, mousePos.y * scale + offsetY, radius.value, 0, Math.PI * 2)
    ctx.fillStyle = perspectiveMode ? 'rgba(0,0,0,0.1)' : 'rgba(0,0,0,0.3)'
    ctx.fill()
    ctx.restore()
  }

}


function updateScale() {
  if (!canvas.value || !imgA.width || !imgA.height) return
  const toolbarHeight = canvas.value.parentElement.querySelector('.toolbar')?.offsetHeight || 50
  const maxWidth = window.innerWidth
  const maxHeight = window.innerHeight - toolbarHeight

  // 用 A 图的尺寸作为基准
  scale = Math.min(maxWidth / imgA.width, maxHeight / imgA.height)

  canvas.value.width = imgA.width * scale
  canvas.value.height = imgA.height * scale
}


// ---------- 初始化事件 ----------
function initCanvasEvents() {
  const c = canvas.value
  if (!c) return

  // ---------- 桌面端 ----------
  c.addEventListener('mousedown', () => drawing = true)
  c.addEventListener('mouseup', () => drawing = false)
  c.addEventListener('mouseleave', () => drawing = false)

  c.addEventListener('mousemove', e => {
    handleDraw(getXY(e))
  })

  // ---------- 移动端 ----------
  c.addEventListener('touchstart', e => {
    e.preventDefault()   // 防止滚动
    drawing = true
    const touch = e.touches[0]
    handleDraw(getXY(touch))
  }, { passive: false })

  c.addEventListener('touchmove', e => {
    e.preventDefault()
    if (!drawing) return
    const touch = e.touches[0]
    handleDraw(getXY(touch))
  }, { passive: false })

  c.addEventListener('touchend', e => {
    drawing = false
    mousePos = null
    redraw()
  })
}

function handleDraw(pos) {
  mousePos = pos
  if (!drawing || !loaded.a || !loaded.b) {
    redraw()
    return
  }

  if (!perspectiveMode) {
    offCtx.save()
    offCtx.globalCompositeOperation = 'destination-out'
    offCtx.beginPath()
    // 直接使用 pos 坐标
    offCtx.arc(pos.x, pos.y, radius.value / scale, 0, Math.PI * 2)
    offCtx.fill()
    offCtx.restore()
  }

  redraw()
}


function clearATop() { offCtx.clearRect(0,0,offCanvas.width,offCanvas.height); redraw() }
function restoreATop() { offCtx.clearRect(0,0,offCanvas.width,offCanvas.height); offCtx.drawImage(imgA,0,0); redraw() }

function onResize() {
  updateScale()  // 根据新的窗口大小调整 canvas 尺寸
  redraw()       // 重绘图像
}

function showToast(message, type = 'info', duration = 8000) {
  toast.value = { show: true, message, type }
  if (duration > 0) {
    setTimeout(() => {
      toast.value.show = false
    }, duration)
  }
}

onMounted(() => {
  initCanvasEvents()
  window.addEventListener('resize', onResize)
  window.addEventListener('keydown', handleKeydown)  // ← 添加键盘监听
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  window.removeEventListener('keydown', handleKeydown) // ← 移除监听
})

// ---------- 重新生成 ----------
function pollTaskStatus(taskId, bPath) {
  const backendUrl = `http://${window.location.hostname}:8000/api/task_status/${taskId}`
  const interval = setInterval(async () => {
    try {
      const res = await fetch(backendUrl)
      const data = await res.json()
      const status = data.status

      if (status === 'done') {
        clearInterval(interval)
        showToast('生成完成！', 'success')
        // 强制刷新 b 图
        imgB.src = bPath + '?t=' + Date.now()
        generating.value = false
      } else if (status.startsWith('error')) {
        clearInterval(interval)
        showToast(`生成失败：${status}`, 'error')
        generating.value = false
      }
    } catch (err) {
      clearInterval(interval)
      showToast(`查询任务状态出错：${err.message}`, 'error')
      generating.value = false
    }
  }, 2000) // 每 2 秒查询一次
}


async function regenerate() {
  if (generating.value) return
  generating.value = true

  const aPath = route.params.imgPath      // a 图路径
  const bPath = aPath.replace(/a(\.jpg|\.png)$/i, 'b$1')  // 对应的 b 图路径

  try {
    // 使用 Vite 代理，直接调用相对路径
    const res = await fetch('/api/regenerate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ aPath, bPath })
    })

    if (!res.ok) {
      const errText = await res.text()
      showToast(`失败：${errText}`, 'error')
      generating.value = false
      return
    }

    const data = await res.json()
    if (data.status !== 'accepted') {
      showToast(`提交任务失败：${data.detail || '未知错误'}`, 'error')
      generating.value = false
      return
    }

    showToast('任务已提交，正在生成...', 'info')
    pollTaskStatus(data.task_id, bPath)

  } catch (err) {
    showToast(`请求出错：${err.message}`, 'error')
    generating.value = false
  }
}

function confirmRegenerate(){ if(confirm("确定要重新生成吗？")) regenerate() }
</script>


<style scoped>
.viewer {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  margin: 0;
  padding: 0;
  background: #333;
  overflow: hidden;
}

.toolbar {
  display: flex;
  align-items: center;
  padding: 6px 10px;
  gap: 10px;
  background: #444;
  color: white;
  flex-shrink: 0;
  font-size: 14px;
  line-height: 1.6;
  min-height: 42px;
}

.toolbar label {
  white-space: nowrap;
  font-size: 13px;
}

.toolbar input[type="range"] {
  flex: 1;
  max-width: 100px;
  height: 26px;
}

.toolbar button {
  padding: 4px 8px;
  font-size: 13px;
  border: none;
  border-radius: 4px;
  background: #666;
  color: white;
}

.toolbar button:disabled {
  opacity: 0.5;
}

/* -------- 桌面端优化 -------- */
@media (min-width: 768px) {
  .toolbar {
    padding: 10px 16px;       /* 高度更大 */
    gap: 16px;
    font-size: 16px;          /* 字体放大 */
    min-height: 54px;         /* toolbar 更高 */
  }

  .toolbar label {
    font-size: 15px;
  }

  .toolbar input[type="range"] {
    max-width: 180px;         /* 滑块更长 */
    height: 32px;             /* 更高 */
  }

  .toolbar button {
    padding: 6px 12px;
    font-size: 15px;
  }
}

canvas {
  display: block;
  margin: auto;
  cursor: crosshair;
}
/* 提示框样式 */
.toast {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 20px;
  border-radius: 6px;
  color: white;
  font-size: 14px;
  opacity: 0.9;
}
.toast.success {
  background: #4caf50;
}
.toast.error {
  background: #f44336;
}
.toast.info {
  background: #2196f3;
}

.canvas-wrapper {
  position: relative;
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}

.arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(0,0,0,0.3);
  display: flex;
  justify-content: center;
  align-items: center; /* ✅ 完全居中 */
  cursor: pointer;
  user-select: none;
  z-index: 20;
}

.arrow svg {
  display: block;   /* 防止 inline 元素偏移 */
  width: 36px;               /* 放大箭头 */
  height: 36px;
}

.arrow.left {
  left: 10px;
}

.arrow.right {
  right: 10px;
}

.arrow.disabled {
  opacity: 0.3;
  pointer-events: none;
}


</style>
