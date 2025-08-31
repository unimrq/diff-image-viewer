<template>
  <div>
    <!-- 瀑布流 -->
    <div class="masonry" :style="{ columnCount: columns }">
      <div v-for="img in images" :key="img" class="masonry-item">
        <img
          :src="img"
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
  columns: { type: Number, default: 6 }  // 接收父组件传来的列数
})
function openViewer(imgPath) {
  const encoded = encodeURIComponent(imgPath)
  window.open(`${window.location.origin}/viewer/${encoded}`, '_blank')
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
