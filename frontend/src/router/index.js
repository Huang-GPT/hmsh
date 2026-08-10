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
  { path: '/faults', name: 'CommonFaults', component: CommonFaults },
  { path: '/admin/login', name: 'AdminLogin', component: AdminLogin },
  { path: '/admin', component: AdminLayout, children: [
    { path: '', redirect: '/admin/dashboard' },
    { path: 'dashboard', name: 'AdminDashboard', component: AdminDashboard },
    { path: 'orders', name: 'AdminOrders', component: AdminOrders },
    { path: 'users', name: 'AdminUsers', component: AdminUsers },
    { path: 'products', name: 'AdminProducts', component: AdminProducts },
    { path: 'bindings', name: 'AdminBindings', component: AdminBindings },
    { path: 'faults', name: 'AdminFaults', component: AdminFaults }
  ]},
  { path: '/dealer', component: AdminLayout, children: [
    { path: '', redirect: '/dealer/orders' },
    { path: 'orders', name: 'DealerOrders', component: DealerOrders }
  ]}
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

export default router
