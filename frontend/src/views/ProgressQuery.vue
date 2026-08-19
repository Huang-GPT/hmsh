<template>
  <div class="progress-query">
    <van-nav-bar
      title="进度查询"
      left-arrow
      :border="false"
      fixed
      @click-left="onBack"
    />
    <div class="pq-spacer" />

    <!-- 未登录提示 -->
    <div v-if="!loggedIn" class="login-tip">
      <van-empty description="请先登录后查看您的工单进度">
        <van-button round type="primary" size="small" @click="goLogin">
          立即登录
        </van-button>
      </van-empty>
    </div>

    <!-- 已登录：状态筛选 + 列表 -->
    <template v-else>
      <van-tabs v-model="activeStatus" sticky offset-top="46px" @change="onStatusChange">
        <van-tab title="全部" name="" />
        <van-tab title="待受理" name="pending_accept" />
        <van-tab title="待派单" name="pending_dispatch" />
        <van-tab title="处理中" name="processing" />
        <van-tab title="待确认" name="pending_confirm" />
        <van-tab title="已完成" name="completed" />
        <van-tab title="已关闭" name="closed" />
      </van-tabs>

      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-list
          v-model="loading"
          :finished="finished"
          finished-text="没有更多了"
          @load="loadOrders"
          :immediate-check="false"
        >
          <div v-if="orders.length === 0 && !loading" class="empty-block">
            <van-empty description="暂无工单" />
          </div>
          <div
            v-for="o in orders"
            :key="o.id"
            class="order-card"
            @click="goDetail(o.id)"
          >
            <div class="card-row card-row-top">
              <span class="order-no">{{ o.order_no }}</span>
              <van-tag :type="statusTagType(o.status)" size="medium">
                {{ o.status_cn || statusText[o.status] }}
              </van-tag>
            </div>
            <div class="card-row">
              <span class="lbl">产品：</span>
              <span class="val">{{ o.product_name || o.product_model || '—' }}</span>
            </div>
            <div class="card-row">
              <span class="lbl">故障：</span>
              <span class="val ellipsis">{{ o.fault_type || o.fault_category_name || '—' }}</span>
            </div>
            <div class="card-row card-row-bottom">
              <span class="meta">报修时间：{{ formatDate(o.created_at) }}</span>
              <span v-if="o.service_point_name" class="meta meta-r">
                <van-icon name="location-o" /> {{ o.service_point_name }}
              </span>
            </div>
          </div>
        </van-list>
      </van-pull-refresh>
    </template>

    <div class="bottom-menu">
      <van-tabbar v-model="activeMenu">
        <van-tabbar-item icon="service-o" to="/">品牌服务</van-tabbar-item>
        <van-tabbar-item icon="user-o" to="/user">我的</van-tabbar-item>
      </van-tabbar>
    </div>
  </div>
</template>

<script>
import { getMyOrders } from '@/api/workOrders'

export default {
  name: 'ProgressQuery',
  data() {
    return {
      activeMenu: 0,
      activeStatus: '',
      orders: [],
      loading: false,
      finished: false,
      refreshing: false,
      loggedIn: false,
      statusText: {
        pending_accept: '待受理',
        pending_dispatch: '待派单',
        dispatched: '已派单',
        assigned_engineer: '已分配工程师',
        processing: '处理中',
        pending_confirm: '待确认',
        completed: '已完成',
        closed: '已关闭',
        cancelled: '已撤销',
      },
    }
  },
  created() {
    this.loggedIn = !!this.getToken()
    if (this.loggedIn) {
      this.loadOrders(true)
    }
  },
  methods: {
    onBack() {
      if (window.history.length > 1) this.$router.back()
      else this.$router.replace('/')
    },
    goLogin() {
      this.$router.push({ path: '/login', query: { redirect: '/progress' } })
    },
    goDetail(id) {
      this.$router.push('/progress/' + id)
    },
    getToken() {
      try { return localStorage.getItem('hongmen_terminal_token') } catch { return null }
    },
    authHeaders() {
      const t = this.getToken()
      return t ? { Authorization: 'Bearer ' + t } : {}
    },
    statusTagType(s) {
      const map = {
        pending_accept: 'warning',
        pending_dispatch: 'warning',
        dispatched: 'primary',
        assigned_engineer: 'primary',
        processing: 'cyan',
        pending_confirm: 'cyan',
        completed: 'success',
        closed: 'default',
        cancelled: 'default',
      }
      return map[s] || 'default'
    },
    formatDate(s) {
      if (!s) return ''
      return String(s).replace('T', ' ').slice(0, 16)
    },
    async loadOrders(reset) {
      if (reset) {
        this.orders = []
        this.finished = false
      }
      this.loading = true
      try {
        const res = await getMyOrders(this.activeStatus || undefined, this.authHeaders())
        const list = (res.data && (res.data.orders || res.data.items)) || []
        this.orders = list
        this.finished = true
      } catch (e) {
        const code = e && e.response && e.response.status
        if (code === 401) {
          this.loggedIn = false
          this.$toast('登录已过期，请重新登录')
        } else {
          this.$toast('加载失败：' + ((e && e.response && e.response.data && e.response.data.error) || e.message))
        }
      } finally {
        this.loading = false
        this.refreshing = false
      }
    },
    onStatusChange(name) {
      this.loadOrders(true)
    },
    async onRefresh() {
      await this.loadOrders(true)
    },
  },
}
</script>

<style scoped>
.progress-query {
  min-height: 100vh;
  background: #f5f6f8;
  padding-top: 46px;
  padding-bottom: 60px;
}
.pq-spacer { height: 0; }
.login-tip {
  padding: 60px 16px;
}
.empty-block {
  padding: 40px 0;
}
.order-card {
  background: #fff;
  border-radius: 10px;
  margin: 12px 12px 0;
  padding: 14px 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  cursor: pointer;
  transition: transform .15s;
}
.order-card:active { transform: scale(0.99); }
.card-row {
  display: flex;
  align-items: center;
  line-height: 22px;
  font-size: 14px;
  color: #333;
  margin-top: 6px;
}
.card-row-top {
  justify-content: space-between;
  font-size: 15px;
  font-weight: 600;
  margin-top: 0;
}
.order-no { color: #222; }
.card-row-bottom {
  justify-content: space-between;
  margin-top: 10px;
  font-size: 12px;
  color: #999;
}
.lbl { color: #999; flex-shrink: 0; }
.val { color: #333; }
.val.ellipsis {
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  flex: 1; min-width: 0;
}
.meta-r { color: #1989fa; }
.bottom-menu {
  position: fixed; bottom: 0; left: 0; right: 0; z-index: 10;
}
</style>
