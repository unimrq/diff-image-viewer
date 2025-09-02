<template>
  <div class="viewer">
    <img :src="decodedImgPath" />
  </div>
</template>

<script setup>
const props = defineProps({ imgPath: String })
const decodedImgPath = decodeURIComponent(props.imgPath)
</script>

<style scoped>
html, body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
}

.viewer {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100vw;      /* 占满整个屏幕宽度 */
  height: 100vh;     /* 占满整个屏幕高度 */
  margin: 0;
  padding: 0;
  background: black;
  overflow: hidden;  /* 防止滚动条 */
}

.viewer img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain; /* 保持比例，完整显示 */
  display: block;      /* 去掉默认 img 行内间距 */
}

</style>
