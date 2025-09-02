<template>
  <div>
    <!-- 瀑布流 -->
    <div class="masonry" :style="{ columnCount: columns }">
      <div v-for="img in images" :key="img" class="masonry-item">
          <img
            :src="getThumbnail(img)"
            loading="lazy"
            @click="openViewer(img)"
            @dblclick="openViewer(img)"
          />
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  images: Array,
  columns: { type: Number, default: 6 },  // 接收父组件传来的列数
  perspectiveMode: { type: Boolean, default: false },  // 接收透视模式
  lowDataMode: { type: Boolean, default: false }  // 省流模式
})

function openViewer(imgPath) {
  const encoded = encodeURIComponent(imgPath)
  const pmode = props.perspectiveMode ? 1 : 0  // 转成数字或字符串
  const lmode = props.lowDataMode ? 1 : 0      // 省流模式
  window.open(`${window.location.origin}/viewer/${encoded}?p=${pmode}&l=${lmode}`, '_blank')
}



function getThumbnail(imgUrl) {
  try {
    const url = new URL(imgUrl)
    const host = url.origin       // 包含协议+IP+端口，例如 http://100.123.100.150:8000
    const relativePath = url.pathname.replace(/^\/images\//, "")
    return `${host}/thumbnails/${relativePath}`
  } catch (e) {
    console.error("URL 解析失败:", imgUrl)
    return imgUrl
  }
}


</script>

<style scoped>
.settings {
  margin-bottom: 10px;
}

.masonry {
  column-gap: 10px;
}

.masonry-item {
  break-inside: avoid;
  margin-bottom: 10px;
}

.masonry-item img {
  width: 100%;
  height: auto;
  display: block;
  border-radius: 4px;
  cursor: pointer;
}
</style>
