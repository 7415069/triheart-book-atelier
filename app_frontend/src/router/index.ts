// src/router/index.ts
import {createRouter, createWebHistory} from 'vue-router'
import {getUiBasePath} from "brtech-fusion";

const router = createRouter({
  history: createWebHistory(getUiBasePath()),
  routes: [
    {
      path: '/reader/:bookId/:pageNo?',
      name: 'TriHeartReader',
      component: () => import('@/components/reader/v3/BookReader.vue'),
      meta: {
        title: '三心书坊 - 沉浸阅读',
        hidden: true,
        noLayout: true
      }
    },
    {
      path: '/',
      component: () => import('@/views/portal/Index.vue'), // 【核心修改】使用布局组件
      children: [
        {
          path: '', // 默认路径 /
          name: 'PortalHome',
          component: () => import('@/views/portal/Home.vue'),
          meta: {title: '三心书坊 - 实现知识自由的铲子'}
        },
        {
          path: 'bookshelf', // 路径 /square
          name: 'Bookshelf',
          component: () => import('@/views/portal/Bookshelf.vue'),
          meta: {title: '三心书坊 - 书架'}
        },
        {
          path: 'bookshelf/:bookId', // 路径 /book/:id
          name: 'BookDetail',
          component: () => import('@/views/portal/BookDetail.vue'),
          meta: {title: '三心书坊 - 书籍详情'}
        },
      ]
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: {title: '用户登录', hideHeader: true}
    },
    {
      path: '/admin/:pathMatch(.*)*',
      name: 'All',
      component: () => import('@/views/admin/Index.vue'),
      meta: {title: '三心书坊 - 实现知识自由的铲子', requiresAuth: true}
    },
  ]
})

export default router