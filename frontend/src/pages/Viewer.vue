<template>
  <div class="viewer">
    <!-- 工具栏 -->
    <div class="toolbar">
      <label>橡皮擦大小：{{ radius }}px</label>
      <input type="range" min="5" max="100" v-model="radius" />
      <button @click="clearATop">清除 a 图</button>
      <button @click="restoreATop">复原 a 图</button>
    </div>
    <!-- 差分 Canvas -->
    <canvas ref="canvas"></canvas>
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

const radius = ref(50)
let scale = 1
let mousePos = null
let drawing = false

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
</style>
