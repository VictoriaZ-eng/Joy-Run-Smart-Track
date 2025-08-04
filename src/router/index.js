import { createRouter, createWebHistory } from 'vue-router'
import Marathon from '@/views/marathon.vue' // 修改路径以匹配你的实际文件位置

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/marathon',        // 路由路径
      name: 'Marathon',         // 路由名称
      component: Marathon       // 关联组件
    }
  ]
})

export default router

