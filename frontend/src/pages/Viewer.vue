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
  const rect = canvas.value.getBoundingClientRect()
  const scaleX = canvas.value.width / rect.width
  const scaleY = canvas.value.height / rect.height
  return { x: (e.clientX - rect.left) * scaleX, y: (e.clientY - rect.top) * scaleY }
}

function redraw() {
  const c = canvas.value
  const ctx = c.getContext('2d')
  if (!loaded.a || !loaded.b) return

  ctx.clearRect(0, 0, c.width, c.height)
  // 底层 b 图
  ctx.drawImage(imgB, 0, 0, imgB.width * scale, imgB.height * scale)
  // 顶层 a 图
  ctx.drawImage(offCanvas, 0, 0, offCanvas.width * scale, offCanvas.height * scale)

  // 半透明提示圆
  if (mousePos) {
    ctx.save()
    ctx.beginPath()
    ctx.arc(mousePos.x, mousePos.y, radius.value, 0, Math.PI * 2)
    ctx.fillStyle = 'rgba(0,0,0,0.3)'
    ctx.fill()
    ctx.restore()
  }
}

function initCanvasEvents() {
  const c = canvas.value

  c.addEventListener('mousedown', () => drawing = true)
  c.addEventListener('mouseup', () => drawing = false)
  c.addEventListener('mouseleave', () => drawing = false)

  c.addEventListener('mousemove', e => {
    const { x, y } = getXY(e)
    mousePos = { x, y }

    if (drawing && loaded.a && loaded.b) {
      offCtx.save()
      offCtx.globalCompositeOperation = 'destination-out'
      offCtx.beginPath()
      offCtx.arc(x / scale, y / scale, radius.value, 0, Math.PI * 2)
      offCtx.fill()
      offCtx.restore()
    }

    redraw()
  })
}

function clearATop() {
  offCtx.clearRect(0, 0, offCanvas.width, offCanvas.height)
  redraw()
}

function restoreATop() {
  offCtx.clearRect(0, 0, offCanvas.width, offCanvas.height)
  offCtx.drawImage(imgA, 0, 0)
  redraw()
}

function updateScale() {
  const c = canvas.value
  if (!imgB.width || !imgB.height) return
  const toolbarHeight = 50
  const ch = window.innerHeight - toolbarHeight
  scale = ch / imgB.height
  c.width = imgB.width * scale
  c.height = imgB.height * scale
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

watch(
  () => route.params.imgPath,
  (p) => loadImages(p),
  { immediate: true }
)

onMounted(() => {
  initCanvasEvents()
  window.addEventListener('resize', () => {
    updateScale()
    redraw()
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', () => {
    updateScale()
    redraw()
  })
})
</script>

<style scoped>
.viewer {
  display: flex;
  flex-direction: column;
  height: 100vh;
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
}
canvas {
  flex: 1;
  display: block;
  margin: auto;
  cursor: crosshair;
}
</style>
