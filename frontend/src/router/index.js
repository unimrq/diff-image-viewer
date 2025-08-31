import { createRouter, createWebHistory } from 'vue-router'
import Home from '../pages/Home.vue'
import Viewer from '../pages/Viewer.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/viewer/:imgPath', component: Viewer, props: true }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
