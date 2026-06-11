import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '@/views/Home.vue'
import Service from '@/views/Service.vue'
import ProductBind from '@/views/ProductBind.vue'
import ProductRepair from '@/views/ProductRepair.vue'
import ProgressQuery from '@/views/ProgressQuery.vue'
import CommonFaults from '@/views/CommonFaults.vue'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/service',
    name: 'Service',
    component: Service
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