<template>
  <div class="admin-dashboard">
    <!-- 顶部 KPI 卡片 -->
    <div class="stats-grid">
      <div class="stat-card stat-warn">
        <div class="stat-value">{{ stats.total_orders || 0 }}</div>
        <div class="stat-label">工单总数</div>
      </div>
      <div class="stat-card stat-warning">
        <div class="stat-value">{{ stats.pending_orders || 0 }}</div>
        <div class="stat-label">待处理</div>
      </div>
      <div class="stat-card stat-success">
        <div class="stat-value">{{ stats.completed_orders || 0 }}</div>
        <div class="stat-label">已完成</div>
      </div>
      <div class="stat-card stat-info">
        <div class="stat-value">{{ stats.today_orders || 0 }}</div>
        <div class="stat-label">今日新增</div>
      </div>
    </div>

    <div class="section">
      <div class="section-header">
        <h4 class="section-title">
          <van-icon name="chart-trending-o" /> 工单状态分布
        </h4>
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
        <h4 class="section-title">
          <van-icon name="todo-list-o" /> 最近工单
        </h4>
        <van-button size="small" plain type="primary" to="/admin/orders">查看全部</van-button>
      </div>
      <van-cell-group v-if="recentOrders.length">
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
      <van-empty v-else description="暂无工单" />
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
.admin-dashboard {
  max-width: 1400px;
}

/* ===== KPI 卡片 ===== */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}
.stat-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-md);
  padding: var(--space-5) var(--space-4);
  text-align: center;
  box-shadow: var(--shadow-card);
  transition: all var(--transition-base);
  position: relative;
  overflow: hidden;
}
.stat-card:hover {
  box-shadow: var(--shadow-hover);
  transform: translateY(-1px);
}
.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--card-color, var(--color-primary));
}
.stat-card.stat-warn {
  --card-color: var(--color-primary);
}
.stat-card.stat-warning {
  --card-color: var(--color-warning);
}
.stat-card.stat-success {
  --card-color: var(--color-success);
}
.stat-card.stat-info {
  --card-color: var(--color-info);
}
.stat-value {
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  color: var(--card-color, var(--color-text));
  line-height: 1.2;
}
.stat-label {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  margin-top: var(--space-1);
}

/* ===== Section 通用 ===== */
.section {
  background: var(--color-bg-card);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  margin-bottom: var(--space-4);
  box-shadow: var(--shadow-card);
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-divider);
}
.section-title {
  margin: 0;
  color: var(--color-text);
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.section-title .van-icon {
  color: var(--color-primary);
}

/* ===== 状态列表 ===== */
.status-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}
.status-item {
  background: var(--color-bg-muted);
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-4);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  transition: all var(--transition-base);
}
.status-item:hover {
  background: var(--brand-50);
}
.status-name {
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
}
.status-count {
  font-weight: var(--font-bold);
  color: var(--color-primary);
  font-size: var(--text-md);
}
</style>