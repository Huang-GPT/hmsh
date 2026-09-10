import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import Vant from 'vant'
import 'vant/lib/index.css'
import { hasPermission, hasAnyPermission, refreshPermissionCache } from '@/utils/permissions'

Vue.use(Vant)
Vue.config.productionTip = false

// 全局权限助手：模板里可用 v-if="$hasPermission('order:accept')"
Vue.prototype.$hasPermission = hasPermission
Vue.prototype.$hasAnyPermission = hasAnyPermission
Vue.prototype.$refreshPermissionCache = refreshPermissionCache

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')