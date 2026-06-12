import Vue from 'vue'
import VueRouter from 'vue-router'
import Service from '@/views/Service.vue'
import ProductBind from '@/views/ProductBind.vue'
import ProductRepair from '@/views/ProductRepair.vue'
import ProgressQuery from '@/views/ProgressQuery.vue'
import CommonFaults from '@/views/CommonFaults.vue'
import Home from '@/views/Home.vue'

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
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

export default router