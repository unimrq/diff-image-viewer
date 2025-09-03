<template>
  <div>
    <!-- 瀑布流 -->
    <div class="masonry" :style="{ columnCount: columns }">
      <div v-for="img in images" :key="img" class="masonry-item">
          <img
            :src="getThumbnail(img)"
            loading="lazy"
            @click="openViewer(img)"
          />
    </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  images: Array,
  columns: { type: Number, default: 6 },  // 接收父组件传来的列数
  perspectiveMode: { type: Boolean, default: false },  // 接收透视模式
  lowDataMode: { type: Boolean, default: false }  // 省流模式
})

function openViewer(imgPath) {
  // imgPath 是相对 /images/... 的路径
  const encodedPath = encodeURIComponent(imgPath)   // 只编码路径
  const pmode = props.perspectiveMode ? 1 : 0
  const lmode = props.lowDataMode ? 1 : 0

  // query 参数单独拼接
  const url = `${window.location.origin}/viewer/${encodedPath}?p=${pmode}&l=${lmode}`
  window.open(url, "_blank")
}



function getThumbnail(imgUrl) {
  try {
    const base = window.location.origin  // 当前站点协议+host
    const url = new URL(imgUrl, base)
    const host = url.origin
    const relativePath = url.pathname.replace(/^\/images\//, "")
    return `${host}/thumbnails/${relativePath}`
  } catch (e) {
    console.error("URL 解析失败:", imgUrl, e)
    return imgUrl
  }
}



</script>

<style scoped>
.settings {
  margin-bottom: 10px;
}

.masonry {
  column-gap: 4px;
}

.masonry-item {
  break-inside: avoid;
  margin-bottom: 4px;
}

.masonry-item img {
  width: 100%;
  height: auto;
  display: block;
  border-radius: 2px;
  cursor: pointer;
}
</style>
