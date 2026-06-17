<template>
  <div class="admin-dashboard">
    <h3>工作台</h3>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_orders || 0 }}</div>
        <div class="stat-label">工单总数</div>
      </div>
      <div class="stat-card pending">
        <div class="stat-value">{{ stats.pending_orders || 0 }}</div>
        <div class="stat-label">待处理</div>
      </div>
      <div class="stat-card success">
        <div class="stat-value">{{ stats.completed_orders || 0 }}</div>
        <div class="stat-label">已完成</div>
      </div>
      <div class="stat-card today">
        <div class="stat-value">{{ stats.today_orders || 0 }}</div>
        <div class="stat-label">今日新增</div>
      </div>
    </div>

    <div class="section">
      <div class="section-header">
        <h4>工单状态分布</h4>
      </div>
      <div class="status-list">
        <div class="status-item" v-for="(count, status) in statusStats" :key="status">
          <span class="status-name">{{ statusMap[status] || status }}</span>
          <span class="status-count">{{ count }}</span>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="section-header">
        <h4>最近工单</h4>
        <van-button size="small" plain to="/admin/orders">查看全部</van-button>
      </div>
      <van-cell-group>
        <van-cell
          v-for="order in recentOrders"
          :key="order.id"
          :title="order.order_no"
          :label="order.fault_type + ' - ' + order.contact_name"
          :value="statusMap[order.status]"
          is-link
          @click="$router.push('/admin/orders')"
        />
      </van-cell-group>
      <van-empty v-if="recentOrders.length === 0" description="暂无工单" />
    </div>
  </div>
</template>

<script>
import { getStatistics, getStatisticsByStatus, getAllOrders } from '@/api/admin'

export default {
  name: 'AdminDashboard',
  data() {
    return {
      stats: {},
      statusStats: {},
      recentOrders: [],
      statusMap: {
        'pending_accept': '待受理',
        'pending_dispatch': '待派单',
        'dispatched': '已派单',
        'assigned_engineer': '已分配工程师',
        'processing': '处理中',
        'pending_confirm': '待确认',
        'completed': '已完成',
        'closed': '已关闭',
        'cancelled': '已撤销'
      }
    }
  },
  created() {
    this.loadData()
  },
  methods: {
    async loadData() {
      try {
        const [statsRes, statusRes, ordersRes] = await Promise.all([
          getStatistics(),
          getStatisticsByStatus(),
          getAllOrders()
        ])
        this.stats = statsRes.data
        this.statusStats = statusRes.data
        this.recentOrders = (ordersRes.data.orders || []).slice(0, 5)
      } catch (e) {
        console.error(e)
      }
    }
  }
}
</script>

<style scoped>
.admin-dashboard h3 {
  margin: 0 0 20px 0;
  color: #333;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}
.stat-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.stat-card.pending { border-top: 3px solid #ff976a; }
.stat-card.success { border-top: 3px solid #07c160; }
.stat-card.today { border-top: 3px solid #1989fa; }
.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}
.stat-label {
  font-size: 13px;
  color: #999;
  margin-top: 8px;
}
.section {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.section-header h4 {
  margin: 0;
  color: #333;
}
.status-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.status-item {
  background: #f5f5f5;
  border-radius: 6px;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.status-name {
  color: #666;
  font-size: 13px;
}
.status-count {
  font-weight: bold;
  color: #1976d2;
}
</style>
