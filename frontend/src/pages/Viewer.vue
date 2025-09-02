<template>
  <div class="viewer">
    <!-- 工具栏 -->
    <div class="toolbar">
      <label>橡皮擦大小：{{ radius }}px</label>
      <input type="range" min="5" max="100" v-model="radius" />
      <button @click="clearATop">清除 a 图</button>
      <button @click="restoreATop">复原 a 图</button>
      <button @click="regenerate" :disabled="generating">  {{ generating ? '生成中...' : '重新生成' }}</button>
    </div>
    <!-- 差分 Canvas -->
    <canvas ref="canvas"></canvas>
    <!-- 提示框 -->
    <div v-if="toast.show" class="toast" :class="toast.type">
      {{ toast.message }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'

const canvas = ref(null)
const route = useRoute()

const imgA = new Image()
const imgB = new Image()
const offCanvas = document.createElement('canvas')
const offCtx = offCanvas.getContext('2d')
const loaded = { a: false, b: false }
const generating = ref(false)
const radius = ref(50)
let scale = 1
let mousePos = null
let drawing = false

// 提示框状态
const toast = ref({
  show: false,
  message: '',
  type: 'info'
})

function getXY(e) {
  if (!canvas.value || !imgB.width || !imgB.height) return { x: 0, y: 0 }

  const rect = canvas.value.getBoundingClientRect()
  const scaleX = canvas.value.width / rect.width
  const scaleY = canvas.value.height / rect.height

  const offsetX = (canvas.value.width - imgB.width * scale) / 2
  const offsetY = (canvas.value.height - imgB.height * scale) / 2

  return {
    x: (e.clientX - rect.left) * scaleX - offsetX,
    y: (e.clientY - rect.top) * scaleY - offsetY
  }
}

function redraw() {
  if (!canvas.value || !loaded.a || !loaded.b) return
  const c = canvas.value
  const ctx = c.getContext('2d')
  ctx.clearRect(0, 0, c.width, c.height)

  const offsetX = (c.width - imgB.width * scale) / 2
  const offsetY = (c.height - imgB.height * scale) / 2

  // 绘制底图 B
  ctx.drawImage(imgB, offsetX, offsetY, imgB.width * scale, imgB.height * scale)
  // 绘制顶图 A
  ctx.drawImage(offCanvas, offsetX, offsetY, offCanvas.width * scale, offCanvas.height * scale)

  // 鼠标半透明圆
  if (mousePos) {
    ctx.save()
    ctx.beginPath()
    ctx.arc(mousePos.x + offsetX, mousePos.y + offsetY, radius.value, 0, Math.PI * 2)
    ctx.fillStyle = 'rgba(0,0,0,0.3)'
    ctx.fill()
    ctx.restore()
  }
}

function updateScale() {
  if (!canvas.value || !imgB.width || !imgB.height) return

  const toolbarHeight = canvas.value.parentElement.querySelector('.toolbar')?.offsetHeight || 50
  const maxWidth = window.innerWidth
  const maxHeight = window.innerHeight - toolbarHeight

  const imgW = imgB.width
  const imgH = imgB.height

  scale = Math.min(maxWidth / imgW, maxHeight / imgH)

  canvas.value.width = imgW * scale
  canvas.value.height = imgH * scale
}

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

// ---------- 抽离的绘制函数 ----------
function handleDraw(pos) {
  if (!pos) return
  mousePos = pos

  if (drawing && loaded.a && loaded.b) {
    offCtx.save()
    offCtx.globalCompositeOperation = 'destination-out'
    offCtx.beginPath()
    offCtx.arc(pos.x / scale, pos.y / scale, radius.value / scale, 0, Math.PI * 2)
    offCtx.fill()
    offCtx.restore()
  }

  redraw()
}


function clearATop() {
  if (!offCtx) return
  offCtx.clearRect(0, 0, offCanvas.width, offCanvas.height)
  redraw()
}

function restoreATop() {
  if (!offCtx) return
  offCtx.clearRect(0, 0, offCanvas.width, offCanvas.height)
  offCtx.drawImage(imgA, 0, 0)
  redraw()
}

function loadImages(aPath) {
  const bPath = aPath.replace(/a(\.jpg|\.png)$/i, 'b$1')
  loaded.a = false
  loaded.b = false
  offCtx.clearRect(0, 0, offCanvas.width, offCanvas.height)
  mousePos = null

  imgA.onload = () => {
    loaded.a = true
    offCanvas.width = imgA.width
    offCanvas.height = imgA.height
    offCtx.clearRect(0, 0, offCanvas.width, offCanvas.height)
    offCtx.drawImage(imgA, 0, 0)
    updateScale()
    redraw()
  }

  imgB.onload = () => {
    loaded.b = true
    updateScale()
    redraw()
  }

  imgA.src = aPath + '?t=' + Date.now()
  imgB.src = bPath + '?t=' + Date.now()
}

watch(() => route.params.imgPath, (p) => loadImages(p), { immediate: true })

onMounted(() => {
  initCanvasEvents()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
})

function onResize() {
  updateScale()
  redraw()
}

function showToast(message, type = 'info', duration = 3000) {
  toast.value = { show: true, message, type }
  if (duration > 0) {
    setTimeout(() => {
      toast.value.show = false
    }, duration)
  }
}


async function regenerate() {
  if (generating.value) return
    generating.value = true

  const aPath = route.params.imgPath   // a 图路径
  const bPath = aPath.replace(/a(\.jpg|\.png)$/i, 'b$1')  // 对应的 b 图路径

  try {
    const backendUrl = `http://${window.location.hostname}:8000/regenerate`

    const res = await fetch(backendUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        aPath: aPath,
        bPath: bPath
      })
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

function pollTaskStatus(taskId, bPath) {
  const backendUrl = `http://${window.location.hostname}:8000/task_status/${taskId}`
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
  padding: 5px 10px;
  gap: 10px;
  background: #444;
  color: white;
  flex-shrink: 0;
  margin: 0;
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
</style>
