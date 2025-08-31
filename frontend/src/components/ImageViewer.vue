<template>
  <div class="viewer">
    <img :src="decodedImgPath" />
  </div>
</template>

<script setup>
import { defineProps } from 'vue'
const props = defineProps({ imgPath: String })
const decodedImgPath = decodeURIComponent(props.imgPath)
</script>

<style scoped>
.viewer {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: black;
}
.viewer img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}
</style>
