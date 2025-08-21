import { createRouter, createWebHistory } from 'vue-router'
import Marathon from '@/views/marathon.vue' 
import Traffic_search  from '@/views/traffic_search.vue'
import AI_search  from '@/views/AI_search.vue'
import Routeplan from '@/views/routeplan.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/marathon',        // 路由路径
      name: 'Marathon',         // 路由名称
      component: Marathon       // 关联组件
    },
    {
      path: '/traffic_search',        // 路由路径
      name: 'Traffic_search',         // 路由名称
      component: Traffic_search       // 关联组件
    },
    {
      path: '/AI_search',        // 路由路径
      name: 'AI_search',         // 路由名称
      component: AI_search       // 关联组件
    },
    {
      path: '/routeplan',        // 路由路径
      name: 'Routeplan',         // 路由名称
      component: Routeplan       // 关联组件
    },
  ]
})

export default router

