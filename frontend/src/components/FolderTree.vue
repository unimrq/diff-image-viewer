<template>
  <ul>
    <li v-for="folder in folders" :key="folder.name">
      <!-- 给 div 添加 folder-item 类 -->
      <div class="folder-item" @click="toggle(folder)">
        📁 {{ folder.name }}
      </div>
      <FolderTree
        v-if="folder.children && folder.expanded"
        :folders="folder.children"
        @select="select"
      />
    </li>
  </ul>
</template>

<script setup>
import { defineEmits } from 'vue'

const props = defineProps({
  folders: { type: Array, required: true }
})
const emit = defineEmits(['select'])

function toggle(folder) {
  folder.expanded = !folder.expanded
  if (folder.expanded && folder.children.length === 0) {
    emit('select', folder)
  }
}

function select(folder) {
  emit('select', folder)
}
</script>

<style scoped>
ul {
  list-style: none;
  padding-left: 10px;
  margin: 0;
}
li {
  margin: 0;
}
.folder-item {
  padding: 8px 0px;   /* 上下左右间距加大 */
  margin-bottom: 2px;   /* 项目间隔 */
  cursor: pointer;
  border-radius: 4px;
}
.folder-item:hover {
  background-color: #f0f0f0;
}
</style>
