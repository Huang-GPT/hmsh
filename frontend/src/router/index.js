import Vue from 'vue'
import VueRouter from 'vue-router'
import Service from '@/views/Service.vue'
import ProductBind from '@/views/ProductBind.vue'
import ProductRepair from '@/views/ProductRepair.vue'
import ProgressQuery from '@/views/ProgressQuery.vue'
import CommonFaults from '@/views/CommonFaults.vue'
import Home from '@/views/Home.vue'
import TerminalLogin from '@/views/Login.vue'
import AdminLayout from '@/views/admin/AdminLayout.vue'
import AdminLogin from '@/views/admin/AdminLogin.vue'
import AdminDashboard from '@/views/admin/AdminDashboard.vue'
import AdminOrders from '@/views/admin/AdminOrders.vue'
import AdminUsers from '@/views/admin/AdminUsers.vue'
import AdminProducts from '@/views/admin/AdminProducts.vue'
import AdminFaults from '@/views/admin/AdminFaults.vue'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'Service',
    component: Service
  },
  {
    path: '/user',
    name: 'UserCenter',
    component: Home
  },
  {
    path: '/login',
    name: 'TerminalLogin',
    component: TerminalLogin
  },
  {
    path: '/product/bind',
    name: 'ProductBind',
    component: ProductBind
  },
  {
    path: '/product/repair',
    name: 'ProductRepair',
    component: ProductRepair
  },
  {
    path: '/progress',
    name: 'ProgressQuery',
    component: ProgressQuery
  },
  {
    path: '/faults',
    name: 'CommonFaults',
    component: CommonFaults
  },
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: AdminLogin
  },
  {
    path: '/admin',
    component: AdminLayout,
    children: [
      { path: '', redirect: '/admin/dashboard' },
      { path: 'dashboard', name: 'AdminDashboard', component: AdminDashboard },
      { path: 'orders', name: 'AdminOrders', component: AdminOrders },
      { path: 'users', name: 'AdminUsers', component: AdminUsers },
      { path: 'products', name: 'AdminProducts', component: AdminProducts },
      { path: 'faults', name: 'AdminFaults', component: AdminFaults }
    ]
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

// 路由守卫：终端绑定/报修页面必须先登录
router.beforeEach((to, from, next) => {
  const tokenKey = 'hongmen_terminal_token'
  const needAuth = to.path === '/product/bind' || to.path === '/product/repair'
  if (needAuth && !localStorage.getItem(tokenKey)) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }
  next()
})

export default router