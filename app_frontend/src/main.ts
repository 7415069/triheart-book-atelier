// app_frontend/src/main.ts
import {createApp} from 'vue'
import {createPinia} from 'pinia'
import App from '@/App.vue'
import router from '@/router'

// 1. 引入底座插件 (包含 ElementPlus, AdminLayout, Crud组件等)
import BrtechFusion from 'brtech-fusion'
// 2. 引入聚合样式 (包含 ElementPlus 基础样式 + DarkMode + 底座自定义样式)
import 'brtech-fusion/style'
import '@/styles/portal.scss'

const app = createApp(App)

// 3. 注册状态管理 (业务侧控制)
app.use(createPinia())

// 4. 注册路由
app.use(router)

// 5. 一键安装底座
app.use(BrtechFusion, {
  apiPrefix: import.meta.env.VITE_API_BASE_URL,
  routePrefix: '/admin',
  loginPath: '/admin/login',
  homePath: '/admin',
})

app.mount('#app')