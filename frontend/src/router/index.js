import Vue from 'vue'
import VueRouter from 'vue-router'
import Service from '@/views/Service.vue'
import ProductBind from '@/views/ProductBind.vue'
import ProductRepair from '@/views/ProductRepair.vue'
import ProgressQuery from '@/views/ProgressQuery.vue'
import ProgressDetail from '@/views/ProgressDetail.vue'
import CommonFaults from '@/views/CommonFaults.vue'
import Home from '@/views/Home.vue'
import TerminalLogin from '@/views/Login.vue'
import AdminLayout from '@/views/admin/AdminLayout.vue'
import AdminLogin from '@/views/admin/AdminLogin.vue'
import AdminDashboard from '@/views/admin/AdminDashboard.vue'
import AdminOrders from '@/views/admin/AdminOrders.vue'
import AdminRoles from '@/views/admin/AdminRoles.vue'
import AdminServicePoints from '@/views/admin/AdminServicePoints.vue'
import AdminUsers from '@/views/admin/AdminUsers.vue'
import AdminProducts from '@/views/admin/AdminProducts.vue'
import AdminBindings from '@/views/admin/AdminBindings.vue'
import AdminFaults from '@/views/admin/AdminFaults.vue'
import DealerOrders from '@/views/dealer/DealerOrders.vue'

Vue.use(VueRouter)

const routes = [
  { path: '/', name: 'Service', component: Service },
  { path: '/user', name: 'UserCenter', component: Home },
  { path: '/login', name: 'TerminalLogin', component: TerminalLogin },
  { path: '/product/bind', name: 'ProductBind', component: ProductBind },
  { path: '/product/repair', name: 'ProductRepair', component: ProductRepair },
  { path: '/progress', name: 'ProgressQuery', component: ProgressQuery },
  { path: '/progress/:id', name: 'ProgressDetail', component: ProgressDetail },
  { path: '/faults', name: 'CommonFaults', component: CommonFaults },
  { path: '/admin/login', name: 'AdminLogin', component: AdminLogin },

  // 管理后台 — 所有 /admin/* 都要登录；子路由声明需要的 permission code
  { path: '/admin', component: AdminLayout, meta: { requireAuth: true }, children: [
    { path: '', redirect: '/admin/dashboard' },
    { path: 'dashboard',         name: 'AdminDashboard',     component: AdminDashboard,    meta: { permission: 'dashboard:view' } },
    { path: 'orders',            name: 'AdminOrders',        component: AdminOrders,       meta: { permission: 'order:view' } },
    { path: 'dealer-orders',     name: 'AdminDealerOrders',  component: () => import('@/views/admin/AdminDealerOrders.vue'), meta: { permission: 'dealer_order:view' } },
    { path: 'users',             name: 'AdminUsers',         component: AdminUsers,        meta: { permission: 'user:view' } },
    { path: 'products',          name: 'AdminProducts',      component: AdminProducts,     meta: { permission: 'product:view' } },
    { path: 'bindings',          name: 'AdminBindings',      component: AdminBindings,     meta: { permission: 'binding:view' } },
    { path: 'faults',            name: 'AdminFaults',        component: AdminFaults,       meta: { permission: 'fault:view' } },
    { path: 'service-points',    name: 'AdminServicePoints', component: AdminServicePoints, meta: { permission: 'service_point:view' } },
    { path: 'roles',             name: 'AdminRoles',         component: AdminRoles,        meta: { permission: 'role:view' } }
  ]},

  // 经销商视图（也是用 AdminLayout 当壳，但侧边栏菜单过滤逻辑会按 service_point_admin 走）
  { path: '/dealer', component: AdminLayout, meta: { requireAuth: true, dealerScope: true }, children: [
    { path: '', redirect: '/dealer/orders' },
    { path: 'orders', name: 'DealerOrders', component: DealerOrders, meta: { permission: 'dealer_order:view' } }
  ]}
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

// ---------- 全局守卫：登录态 + 路由级 permission 检查 ----------
router.beforeEach((to, from, next) => {
  // 1) /admin/login 永远放行
  if (to.path === '/admin/login') {
    return next()
  }

  const userRaw = localStorage.getItem('admin_user')
  const user = userRaw ? safeParse(userRaw) : null
  const token = localStorage.getItem('admin_token') || (user && user.token) || ''

  // 2) /admin/* / /dealer/* 都要登录
  const needAuth = to.matched.some(r => r.meta && r.meta.requireAuth)
  if (needAuth && !token) {
    return next({ path: '/admin/login', query: { redirect: to.fullPath } })
  }

  // 3) 检查路由 meta.permission
  const required = to.meta && to.meta.permission
  if (required) {
    const perms = (user && Array.isArray(user.permissions)) ? user.permissions : []
    if (!perms.includes(required)) {
      // 没权限 — 不让进；跳回 dashboard
      console.warn(`[router] denied: ${to.path} requires ${required}, user has:`, perms)
      return next({ path: '/admin/dashboard', query: { denied: required } })
    }
  }

  return next()
})

function safeParse(s) {
  try { return JSON.parse(s) } catch (e) { return null }
}

export default router
