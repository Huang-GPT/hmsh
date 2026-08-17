<template>
  <div class="admin-dealer-orders">
    <h3>工单售后</h3>

    <!-- 顶部 KPI 卡片 -->
    <div class="kpi-row">
      <div class="kpi-card kpi-warn">
        <div class="kpi-num">{{ kpi.dispatched }}</div>
        <div class="kpi-label">待接单</div>
      </div>
      <div class="kpi-card kpi-info">
        <div class="kpi-num">{{ kpi.assigned_engineer + kpi.processing }}</div>
        <div class="kpi-label">处理中</div>
      </div>
      <div class="kpi-card kpi-success">
        <div class="kpi-num">{{ kpi.completed }}</div>
        <div class="kpi-label">已完成</div>
      </div>
      <div class="kpi-card kpi-muted">
        <div class="kpi-num">{{ kpi.closed + kpi.cancelled }}</div>
        <div class="kpi-label">关闭/撤销</div>
      </div>
    </div>

    <div class="toolbar">
      <div class="toolbar-row toolbar-top">
        <select v-if="!isSpUser" v-model="filterSp" class="filter-select" @change="loadOrders">
          <option value="">全部服务点</option>
          <option v-for="sp in servicePoints" :key="sp.id" :value="sp.id">{{ sp.name }}</option>
        </select>
        <div v-else class="sp-context">
          <van-icon name="location-o" />
          <span>当前服务点：<strong>{{ currentServicePointName || '（未分配）' }}</strong></span>
        </div>
        <van-button size="small" plain icon="replay" @click="loadOrders()">刷新</van-button>
      </div>
      <div class="toolbar-row toolbar-bottom">
        <span
          v-for="t in tabs"
          :key="t.name"
          :class="['filter-chip', { active: activeTab === t.name }]"
          @click="setTab(t.name)"
        >{{ t.label }} ({{ kpi[t.kpiKey] || 0 }})</span>
      </div>
    </div>

    <div class="table-wrap">
      <table class="order-table">
        <thead>
          <tr>
            <th>工单号</th>
            <th>用户</th>
            <th>产品</th>
            <th>客户名称</th>
            <th>经销商</th>
            <th>故障分类</th>
            <th>工程师姓名</th>
            <th>工程师电话</th>
            <th>状态</th>
            <th>创建时间</th>
            <th class="col-actions">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading && orders.length === 0">
            <td colspan="11" class="state-cell">加载中…</td>
          </tr>
          <tr v-else-if="orders.length === 0">
            <td colspan="11" class="state-cell">
              <div class="empty-cell">
                <div class="empty-icon">📋</div>
                <div class="empty-text">暂无工单</div>
              </div>
            </td>
          </tr>
          <tr
            v-for="o in orders"
            :key="o.id"
            @click="openDetail(o)"
            :class="{ 'row-pending': o.status === 'dispatched' }"
          >
            <td class="col-orderno" @click.stop="openDetail(o)">
              <a @click.stop="openDetail(o)"><code>{{ o.order_no }}</code></a>
              <div class="row-meta">{{ formatDateTime(o.created_at) }}</div>
            </td>
            <td>
              <div class="user-cell">
                <span class="user-name">{{ o.user_name || o.user_phone || ('用户#' + o.user_id) }}</span>
                <span class="user-phone">{{ o.user_phone || '—' }}</span>
              </div>
            </td>
            <td>
              <div class="prod-cell">
                <span class="prod-name">{{ o.product_name || o.product_model || '—' }}</span>
                <span class="prod-meta">二维码 {{ o.product_qr_code || '—' }}</span>
              </div>
            </td>
            <td>
              <span class="customer-cell" :class="{ 'cell-empty': !o.contact_name }">
                {{ o.contact_name || '—' }}
              </span>
            </td>
            <td>
              <span class="dealer-cell" :class="{ 'cell-empty': !o.service_point_name }">
                {{ o.service_point_name || '未分配' }}
              </span>
            </td>
            <td>
              <div class="fault-cell">
                <span class="fault-cat">{{ o.fault_category_name || '未分类' }}</span>
                <span class="fault-type">{{ o.fault_type || '—' }}</span>
              </div>
            </td>
            <td>
              <span :class="{ 'cell-empty': !o.assigned_engineer_name }">
                {{ o.assigned_engineer_name || '—' }}
              </span>
            </td>
            <td>
              <a v-if="o.assigned_engineer_phone" :href="`tel:${o.assigned_engineer_phone}`" class="ds-mono">{{ o.assigned_engineer_phone }}</a>
              <span v-else class="cell-empty">—</span>
            </td>
            <td>
              <van-tag :type="tagType(o.status)" size="mini">
                {{ statusMap[o.status] || o.status }}
              </van-tag>
            </td>
            <td class="col-time">
              <div>{{ formatDate(o.created_at) }}</div>
              <div class="row-meta">{{ formatTime(o.created_at) }}</div>
              <div v-if="o.appointment_date" class="row-meta appt-hint">
                <van-icon name="clock-o" /> {{ o.appointment_date }}
              </div>
            </td>
            <td class="col-actions" @click.stop>
              <a class="op-link primary" @click="openDetail(o)">详情</a>
              <a v-if="o.status === 'dispatched'" class="op-link success" @click="adminAccept(o)">代接单</a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ============ 详情 Drawer ============ -->
    <van-popup v-model:show="showDetail" position="right" :style="{ width: '94%', height: '100%' }" closeable>
      <div class="ds-drawer" v-if="currentOrder">
        <div class="ds-banner" :class="bannerClass(currentOrder.status)">
          <div class="ds-banner-row">
            <van-icon :name="statusIcon(currentOrder.status)" class="ds-banner-icon" />
            <span class="ds-banner-status">{{ statusMap[currentOrder.status] || currentOrder.status }}</span>
            <code class="ds-banner-orderno">{{ currentOrder.order_no }}</code>
          </div>
          <div class="ds-banner-meta">
            <span><van-icon name="clock-o" /> 创建 {{ formatDateTime(currentOrder.created_at) }}</span>
            <span v-if="currentOrder.updated_at"><van-icon name="replay" /> 更新 {{ formatDateTime(currentOrder.updated_at) }}</span>
          </div>
        </div>

        <!-- 报修人/联系人 -->
        <section class="ds-section">
          <header class="ds-title"><van-icon name="user-o" /> 报修信息</header>
          <div class="ds-grid">
            <div class="ds-key">用户</div>
            <div class="ds-val">{{ currentOrder.user_name || (currentOrder.user_phone || '—') }}</div>
            <div class="ds-key">用户手机</div>
            <div class="ds-val">
              <a v-if="currentOrder.user_phone" :href="`tel:${currentOrder.user_phone}`">{{ currentOrder.user_phone }}</a>
              <span v-else>—</span>
            </div>
            <div class="ds-key">联系人</div>
            <div class="ds-val">{{ currentOrder.contact_name || '—' }}</div>
            <div class="ds-key">联系电话</div>
            <div class="ds-val">
              <a v-if="currentOrder.contact_phone" :href="`tel:${currentOrder.contact_phone}`">{{ currentOrder.contact_phone }}</a>
              <span v-else>—</span>
            </div>
          </div>
        </section>

        <!-- 产品信息 -->
        <section class="ds-section">
          <header class="ds-title"><van-icon name="goods-collect-o" /> 产品信息</header>
          <div class="ds-grid">
            <div class="ds-key">产品名称</div>
            <div class="ds-val ds-emph">{{ currentOrder.product_name || currentOrder.product_model || '—' }}</div>
            <div class="ds-key">产品系列</div>
            <div class="ds-val">{{ currentOrder.product_family || '—' }}</div>
            <div class="ds-key">客户名</div>
            <div class="ds-val">{{ currentOrder.product_customer_name || '—' }}</div>
            <div class="ds-key">经销商</div>
            <div class="ds-val">{{ currentOrder.product_dealer_name || '—' }}</div>
            <div class="ds-key">序列号</div>
            <div class="ds-val ds-mono">{{ currentOrder.product_serial || '—' }}</div>
            <div class="ds-key">销售单号</div>
            <div class="ds-val ds-mono">{{ currentOrder.product_sales_no || '—' }}</div>
            <div class="ds-key">产品二维码</div>
            <div class="ds-val ds-mono">{{ currentOrder.product_qr_code || '—' }}</div>
          </div>
        </section>

        <!-- 故障信息 -->
        <section class="ds-section">
          <header class="ds-title"><van-icon name="warning-o" /> 故障信息</header>
          <div class="ds-grid">
            <div class="ds-key">故障分类</div>
            <div class="ds-val">
              <van-tag v-if="currentOrder.fault_category_name" type="primary" size="mini">{{ currentOrder.fault_category_name }}</van-tag>
              <span v-else class="ds-empty">未分类</span>
            </div>
            <div class="ds-key">故障概述</div>
            <div class="ds-val">
              <van-tag v-if="currentOrder.fault_type" type="warning" size="mini">{{ currentOrder.fault_type }}</van-tag>
              <span v-else class="ds-empty">—</span>
            </div>
            <div class="ds-key">详细描述</div>
            <div class="ds-val ds-block" :class="{ 'ds-empty': !currentOrder.fault_desc }">
              {{ currentOrder.fault_desc || '未填写描述' }}
            </div>
          </div>
        </section>

        <!-- 地址定位 -->
        <section class="ds-section">
          <header class="ds-title"><van-icon name="location-o" /> 地址定位</header>
          <div class="ds-grid">
            <div class="ds-key">故障地址</div>
            <div class="ds-val" :class="{ 'ds-empty': !currentOrder.fault_address }">
              {{ currentOrder.fault_address || '未填写' }}
            </div>
            <div v-if="currentOrder.fault_location_lat || currentOrder.fault_location_lng" class="ds-key">经纬度</div>
            <div v-if="currentOrder.fault_location_lat || currentOrder.fault_location_lng" class="ds-val ds-mono">
              <span v-if="currentOrder.fault_location_lat">{{ currentOrder.fault_location_lat }}</span>
              <span v-if="currentOrder.fault_location_lat && currentOrder.fault_location_lng">, </span>
              <span v-if="currentOrder.fault_location_lng">{{ currentOrder.fault_location_lng }}</span>
              <a v-if="currentOrder.fault_location_lat && currentOrder.fault_location_lng"
                 :href="amapUrl(currentOrder)" target="_blank" rel="noopener" class="ds-map-link">
                <van-icon name="guide-o" /> 地图
              </a>
            </div>
          </div>
        </section>

        <!-- 期望上门 -->
        <section class="ds-section">
          <header class="ds-title"><van-icon name="clock-o" /> 期望上门</header>
          <div class="ds-grid">
            <div class="ds-key">期望日期</div>
            <div class="ds-val" :class="{ 'ds-empty': !currentOrder.appointment_date }">
              {{ currentOrder.appointment_date || '尽快上门（未指定）' }}
            </div>
            <div class="ds-key">时段</div>
            <div class="ds-val">
              <van-tag v-if="currentOrder.appointment_period === 'AM'" type="primary" size="mini">上午</van-tag>
              <van-tag v-else-if="currentOrder.appointment_period === 'PM'" type="warning" size="mini">下午</van-tag>
              <span v-else class="ds-empty">未指定</span>
            </div>
          </div>
        </section>

        <!-- 服务分配 -->
        <section class="ds-section">
          <header class="ds-title"><van-icon name="manager-o" /> 服务分配</header>
          <div class="ds-grid">
            <div class="ds-key">服务点</div>
            <div class="ds-val" :class="{ 'ds-empty': !currentOrder.service_point_name }">
              {{ currentOrder.service_point_name || '未分配' }}
            </div>
            <div class="ds-key">工程师姓名</div>
            <div class="ds-val">
              <span class="ds-emph">{{ currentOrder.assigned_engineer_name || '—' }}</span>
            </div>
            <div class="ds-key">工程师电话</div>
            <div class="ds-val">
              <a v-if="currentOrder.assigned_engineer_phone" :href="`tel:${currentOrder.assigned_engineer_phone}`" class="ds-sub ds-mono">{{ currentOrder.assigned_engineer_phone }}</a>
              <span v-else class="ds-empty">—</span>
            </div>
          </div>
        </section>

        <!-- 关闭原因 -->
        <section v-if="currentOrder.reject_reason || currentOrder.cancel_reason" class="ds-section">
          <header class="ds-title"><van-icon name="close" /> 关闭原因</header>
          <div class="ds-grid">
            <div class="ds-key">{{ currentOrder.reject_reason ? '拒绝原因' : '撤销原因' }}</div>
            <div class="ds-val ds-block ds-danger">
              {{ currentOrder.reject_reason || currentOrder.cancel_reason }}
            </div>
          </div>
        </section>

        <!-- 现场图片 -->
        <section class="ds-section">
          <header class="ds-title">
            <van-icon name="photo-o" /> 现场图片
            <span v-if="currentOrder.images && currentOrder.images.length" class="ds-count">{{ currentOrder.images.length }} 张</span>
          </header>
          <div v-if="!currentOrder.images || currentOrder.images.length === 0" class="ds-empty-block">
            <van-icon name="photograph" /> 暂无现场图片
          </div>
          <div v-else class="ds-media-grid">
            <div v-for="(img, i) in currentOrder.images" :key="`img-${i}`" class="ds-media-item" @click="previewMedia(img)">
              <img :src="img" :alt="`图片${i+1}`" loading="lazy" />
            </div>
          </div>
        </section>

        <!-- 现场视频 -->
        <section v-if="currentOrder.videos && currentOrder.videos.length" class="ds-section">
          <header class="ds-title">
            <van-icon name="video-o" /> 现场视频
            <span class="ds-count">{{ currentOrder.videos.length }} 个</span>
          </header>
          <div class="ds-video-list">
            <a v-for="(v, i) in currentOrder.videos" :key="`v-${i}`" :href="v" target="_blank" rel="noopener" class="ds-video-item">
              <van-icon name="play-circle-o" /> 视频 {{ i+1 }}
            </a>
          </div>
        </section>

        <!-- 处理记录 -->
        <section class="ds-section">
          <header class="ds-title"><van-icon name="todo-list-o" /> 处理记录</header>
          <div v-if="!currentOrder.status_logs || currentOrder.status_logs.length === 0" class="ds-empty-block">
            <van-icon name="records" /> 暂无处理记录
          </div>
          <div v-else class="ds-timeline">
            <div v-for="log in currentOrder.status_logs" :key="log.id" class="ds-timeline-item">
              <div class="ds-dot" :class="logStatusClass(log.to_status)"></div>
              <div class="ds-timeline-content">
                <div class="ds-timeline-head">
                  <van-tag :type="logTagType(log.to_status)" size="mini">{{ statusMap[log.to_status] || log.to_status }}</van-tag>
                  <span class="ds-timeline-time">{{ formatDateTime(log.created_at) }}</span>
                </div>
                <div class="ds-timeline-operator">{{ log.operator_name || ('操作员#' + log.operator_id) }}</div>
                <div v-if="log.remark" class="ds-timeline-remark">{{ log.remark }}</div>
                <div v-if="log.images && log.images.length" class="ds-log-images">
                  <img v-for="(lg, gi) in log.images" :key="`lgi-${log.id}-${gi}`" :src="lg" @click="previewMedia(lg)" alt="现场图" />
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- 操作按钮 -->
        <div v-if="currentOrder.status === 'dispatched'" class="ds-action-bar">
          <div class="ds-action-primary">
            <van-button type="success" block @click="adminAccept(currentOrder)">总部代接单</van-button>
          </div>
        </div>
      </div>
    </van-popup>

    <!-- ============ 接单弹窗 ============ -->
    <van-dialog v-model:show="showAccept" title="总部代接单" show-cancel-button @confirm="submitAdminAccept">
      <div class="dialog-body">
        <div class="dialog-tip">填写本次上门工程师的姓名和手机号（11位）</div>
        <van-field v-model="engineerForm.name" label="工程师姓名" placeholder="请输入" maxlength="20" />
        <van-field v-model="engineerForm.phone" label="手机号" placeholder="11 位手机号" type="tel" maxlength="11" />
      </div>
    </van-dialog>

    <!-- 图片预览 -->
    <van-image-preview v-model:show="showImagePreview" :images="previewImages" />
  </div>
</template>
<script>
import {
  getAllDealerOrders, getServicePoints, acceptOrderByText, getOrderDetail,
} from '@/api/admin'

export default {
  name: 'AdminDealerOrders',
  data() {
    return {
      activeTab: 'dispatched',
      filterSp: '',
      servicePoints: [],
      orders: [],
      loading: false,
      currentUser: null,
      currentServicePointName: '',
      isSpUser: false,
      currentUser: null,
      currentServicePointName: '',
      isSpUser: false,
      kpi: { dispatched: 0, assigned_engineer: 0, processing: 0, completed: 0, closed: 0, cancelled: 0 },

      showDetail: false,
      currentOrder: null,

      showAccept: false,
      engineerForm: { name: '', phone: '' },

      showImagePreview: false,
      previewImages: [],

      tabs: [
        { name: 'dispatched', label: '待接单', kpiKey: 'dispatched' },
        { name: 'processing', label: '处理中', kpiKey: 'processing' },
        { name: 'completed', label: '已完成', kpiKey: 'completed' },
      ],

      statusMap: {
        dispatched: '待接单',
        assigned_engineer: '已分配工程师',
        processing: '处理中',
        pending_confirm: '待确认',
        completed: '已完成',
        closed: '已关闭',
        cancelled: '已撤销',
        pending_accept: '待受理',
        pending_dispatch: '待派单',
      },
    }
  },
  watch: {
    activeTab() {
      this.loadOrders()
    },
  },
  async created() {
    this.loadCurrentUser()
    try {
      const spRes = await getServicePoints()
      const data = spRes.data || {}
      this.servicePoints = data.items || data.service_points || []
    } catch (e) { /* ignore */ }
    this.loadOrders()
  },
  methods: {
    setTab(name) {
      this.activeTab = name
    },
    loadCurrentUser() {
      try {
        const u = JSON.parse(localStorage.getItem('admin_user') || 'null')
        this.currentUser = u
        const isSp = u && (u.role === 'service_point' || u.role === 'service_point_admin')
        this.isSpUser = !!isSp
        if (isSp && u.service_point_id) {
          this.filterSp = String(u.service_point_id)
          this.currentServicePointName = u.service_point_name || ('服务点 #' + u.service_point_id)
        } else {
          this.currentServicePointName = ''
        }
      } catch (e) {
        this.currentUser = null
        this.isSpUser = false
      }
    },
    async loadOrders() {
      this.loading = true
      try {
        // 拉所有已派单的工单，统计 KPI 不限状态
        const res = await getAllDealerOrders({
          service_point_id: this.filterSp || undefined,
          status: this.activeTab === 'processing' ? 'assigned_engineer,processing' : this.activeTab,
        })
        this.orders = (res.data && res.data.orders) || []
        this.computeKpi()
      } catch (e) {
        this.orders = []
      } finally {
        this.loading = false
      }
    },
    async computeKpi() {
      // 拉全部已派单工单算 KPI（不管当前 tab）
      try {
        const res = await getAllDealerOrders({ service_point_id: this.filterSp || undefined })
        const all = (res.data && res.data.orders) || []
        const k = { dispatched: 0, assigned_engineer: 0, processing: 0, completed: 0, closed: 0, cancelled: 0 }
        for (const o of all) {
          if (k[o.status] !== undefined) k[o.status]++
        }
        this.kpi = k
      } catch (e) { /* ignore */ }
    },
    tagType(status) {
      const map = {
        dispatched: 'primary',
        assigned_engineer: 'primary',
        processing: 'cyan',
        pending_confirm: 'success',
        completed: 'success',
        closed: 'default',
        cancelled: 'danger',
      }
      return map[status] || 'default'
    },
    bannerClass(status) {
      return 'ds-banner-' + (status || 'dispatched')
    },
    statusIcon(status) {
      const map = {
        dispatched: 'logistics',
        assigned_engineer: 'manager-o',
        processing: 'setting-o',
        pending_confirm: 'certificate',
        completed: 'success',
        closed: 'close',
        cancelled: 'cross',
      }
      return map[status] || 'bell'
    },
    logTagType(status) {
      return this.tagType(status)
    },
    logStatusClass(status) {
      return 'ds-dot-' + (status || 'dispatched')
    },
    async openDetail(o) {
      // 拉详情（含 status_logs / images / videos）
      try {
        const res = await getOrderDetail(o.id)
        this.currentOrder = res.data && res.data.order ? res.data.order : o
      } catch (e) {
        this.currentOrder = o
      }
      this.showDetail = true
    },
    adminAccept(o) {
      this.currentOrder = o || this.currentOrder
      this.engineerForm = { name: '', phone: '' }
      this.showAccept = true
    },
    async submitAdminAccept() {
      const name = (this.engineerForm.name || '').trim()
      const phone = (this.engineerForm.phone || '').trim()
      if (!name) { this.$toast('请填写工程师姓名'); return }
      if (!/^1\d{10}$/.test(phone)) { this.$toast('请填写正确的 11 位手机号'); return }
      try {
        await acceptOrderByText(this.currentOrder.id, name, phone)
        this.$toast.success('已代为接单，工单进入处理中')
        this.showAccept = false
        this.showDetail = false
        this.loadOrders()
      } catch (e) {
        const err = (e && e.response && e.response.data && e.response.data.error) || '操作失败'
        this.$toast(err)
      }
    },
    previewMedia(url) {
      this.previewImages = [url]
      this.showImagePreview = true
    },
    amapUrl(order) {
      if (!order || !order.fault_location_lat || !order.fault_location_lng) return '#'
      return `https://uri.amap.com/marker?positionLng=${order.fault_location_lng}&positionLat=${order.fault_location_lat}&src=hmsh&name=故障定位`
    },
    formatDate(d) {
      if (!d) return '—'
      const s = String(d)
      return s.length >= 10 ? s.substring(0, 10) : s
    },
    formatTime(d) {
      if (!d) return '—'
      const s = String(d)
      return s.length >= 16 ? s.substring(11, 16) : s
    },
    formatDateTime(d) {
      if (!d) return '—'
      const s = String(d)
      return s.length >= 16 ? s.substring(0, 16).replace('T', ' ') : s
    },
  },
}
</script>
<style scoped>
.admin-dealer-orders {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  min-height: calc(100vh - 88px);
}
h3 {
  margin: 0 0 16px;
  font-size: 18px;
  color: #1f2937;
}

/* ===== KPI ===== */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}
.kpi-card {
  border-radius: 8px;
  padding: 14px 16px;
  color: #fff;
  text-align: center;
}
.kpi-warn { background: linear-gradient(135deg, #ff976a, #ee0a24); }
.kpi-info { background: linear-gradient(135deg, #4a90e2, #1989fa); }
.kpi-success { background: linear-gradient(135deg, #07c160, #04a655); }
.kpi-muted { background: linear-gradient(135deg, #909399, #606266); }
.kpi-num {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
}
.kpi-label {
  font-size: 12px;
  opacity: 0.9;
  margin-top: 2px;
}

/* ===== toolbar ===== */
.toolbar {
  margin-bottom: 12px;
}
.toolbar-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.search-box {
  flex: 1;
  min-width: 280px;
}
.filter-chip {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 14px;
  background: #f3f4f6;
  font-size: 13px;
  color: #4b5563;
  cursor: pointer;
}
.filter-chip:hover { background: #e5e7eb; }
.filter-chip.active {
  background: #1989fa;
  color: white;
}

/* ===== table ===== */
.table-wrap {
  overflow-x: auto;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}
.order-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.order-table th {
  background: #f9fafb;
  padding: 10px 8px;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
  white-space: nowrap;
}
.order-table td {
  padding: 10px 8px;
  border-bottom: 1px solid #f3f4f6;
  color: #4b5563;
  vertical-align: middle;
}
.order-table tbody tr {
  cursor: pointer;
}
.order-table tbody tr:hover td {
  background: #f9fafb;
}
.order-table tbody tr.row-pending td:first-child {
  border-left: 3px solid #ee0a24;
}
.col-orderno code {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: ui-monospace, monospace;
  font-size: 12px;
  color: #1989fa;
  text-decoration: underline;
  text-decoration-color: rgba(25,137,250,0.35);
  text-underline-offset: 2px;
}
.col-orderno a {
  color: inherit;
  text-decoration: none;
}
.col-time {
  font-family: ui-monospace, monospace;
  font-size: 12px;
}
.row-meta {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 2px;
}
.user-cell,
.prod-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.customer-cell,
.dealer-cell {
  display: inline-block;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: middle;
}
.cell-empty {
  color: #c8c9cc;
  font-style: italic;
}
.user-name,
.prod-name {
  font-weight: 500;
  color: #1f2937;
}
.user-phone,
.prod-serial {
  font-size: 11px;
  color: #9ca3af;
}
.fault-cell .mr-1 {
  margin-right: 4px;
}
.col-actions {
  white-space: nowrap;
}
.op-link {
  color: #1989fa;
  cursor: pointer;
  margin-right: 8px;
  font-size: 13px;
}
.op-link:hover { text-decoration: underline; }
.op-link.primary { color: #1989fa; }
.op-link.danger { color: #ee0a24; }
.state-cell {
  text-align: center !important;
  padding: 60px !important;
  color: #9ca3af;
  font-size: 13px;
}
.empty-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.empty-icon {
  font-size: 48px;
  opacity: 0.5;
}
.empty-text {
  font-size: 14px;
  color: #6b7280;
}
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 4px 0;
}
.pagination-info {
  font-size: 13px;
  color: #6b7280;
}
.pagination-info strong {
  color: #1989fa;
  margin: 0 2px;
}
.pagination-buttons {
  display: flex;
  gap: 8px;
}

/* ===== Drawer ===== */
.detail-drawer {
  padding: 20px 16px 80px;
  background: #f5f6f8;
  min-height: 100vh;
  overflow-y: auto;
}
.drawer-header {
  background: #fff;
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 12px;
}
.dh-title {
  display: flex;
  align-items: center;
  gap: 8px;
}
.dh-orderno {
  font-family: ui-monospace, monospace;
  font-weight: 600;
  font-size: 15px;
  color: #1f2937;
}
.dh-meta {
  margin-top: 6px;
  font-size: 12px;
  color: #9ca3af;
}

.cell-value-stack {
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-width: 240px;
  text-align: right;
}
.cv-main {
  font-weight: 500;
  color: #1f2937;
}
.cv-sub {
  font-size: 12px;
  color: #9ca3af;
}
.desc-text {
  white-space: pre-wrap;
  color: #4b5563;
  line-height: 1.6;
  text-align: right;
  max-width: 240px;
}

/* ===== Media ===== */
.media-section {
  background: #fff;
  border-radius: 8px;
  padding: 14px 16px;
  margin-top: 12px;
}
.ms-title {
  font-weight: 600;
  font-size: 14px;
  color: #374151;
  margin-bottom: 10px;
}
.media-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.media-item {
  aspect-ratio: 1;
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
  background: #f3f4f6;
}
.media-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.media-video {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #f9fafb;
  border-radius: 6px;
  color: #1989fa;
  text-decoration: none;
  margin-bottom: 8px;
  word-break: break-all;
  font-size: 13px;
}
.media-video .mv-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #1989fa;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
}
.ls-images {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  margin-top: 6px;
}
.ls-images img {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  border-radius: 4px;
  cursor: pointer;
}
.ls-coord a {
  color: #1989fa;
  text-decoration: underline;
}

/* ===== Log ===== */
.log-section {
  background: #fff;
  border-radius: 8px;
  padding: 14px 16px;
  margin-top: 12px;
}
.ls-title {
  font-weight: 600;
  font-size: 14px;
  color: #374151;
  margin-bottom: 10px;
}
.ls-empty {
  text-align: center;
  color: #9ca3af;
  font-size: 12px;
  padding: 10px 0;
}
.ls-list {
  position: relative;
}
.ls-item {
  display: flex;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px dashed #f3f4f6;
  position: relative;
}
.ls-item:last-child { border-bottom: none; }
.ls-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #1989fa;
  margin-top: 6px;
  flex-shrink: 0;
}
.ls-content {
  flex: 1;
}
.ls-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.ls-status {
  font-weight: 500;
  color: #1f2937;
  font-size: 13px;
}
.ls-time {
  font-size: 11px;
  color: #9ca3af;
  font-family: ui-monospace, monospace;
}
.ls-operator {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}
.ls-remark {
  margin-top: 4px;
  background: #f9fafb;
  padding: 6px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #4b5563;
}

/* ===== Action Bar ===== */
.action-bar {
  position: fixed;
  bottom: 0;
  right: 0;
  width: 90%;
  background: #fff;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-shadow: 0 -2px 8px rgba(0,0,0,0.04);
  z-index: 100;
}

/* ===== Dialog ===== */
.dialog-body {
  padding: 12px 16px;
}
.dialog-tip {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 10px;
}
.select-input {
  width: 100%;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 8px;
  font-size: 13px;
  background: #fff;
  margin-bottom: 12px;
}
.ml-1 { margin-left: 4px; }

/* ===== 标准化字段展示（占位 + 样式） ===== */
.cv-empty {
  color: #c8c9cc;
  font-style: italic;
}
.reason-text {
  color: #ee0a24;
  font-weight: 500;
}
.fault-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.fault-cat {
  font-size: 11px;
  color: #1989fa;
  font-weight: 500;
}
.fault-type {
  font-size: 12px;
  color: #4b5563;
}
.prod-meta {
  font-size: 11px;
  color: #9ca3af;
  font-family: ui-monospace, monospace;
  margin-top: 2px;
}
.appt-hint {
  color: #1989fa;
  font-size: 11px;
  display: flex;
  align-items: center;
  gap: 2px;
  margin-top: 2px;
}

/* ===== 现场图片（带空态） ===== */
.media-empty {
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
  padding: 20px 0;
}
.ms-count {
  font-size: 12px;
  color: #6b7280;
  margin-left: 6px;
  font-weight: normal;
}

/* ===== 处理记录时间轴（彩色状态点） ===== */
.ls-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #1989fa;
  margin-top: 6px;
  flex-shrink: 0;
  position: relative;
}
.ls-dot::before {
  content: '';
  position: absolute;
  top: 12px;
  left: 50%;
  width: 2px;
  height: 30px;
  background: #f0f0f0;
  transform: translateX(-50%);
}
.ls-item:last-child .ls-dot::before { display: none; }
.ls-dot.dot-info     { background: #ff976a; }
.ls-dot.dot-warning  { background: #ff976a; }
.ls-dot.dot-primary  { background: #1989fa; }
.ls-dot.dot-cyan     { background: #25aeae; }
.ls-dot.dot-success  { background: #07c160; }
.ls-dot.dot-muted    { background: #c8c9cc; }
.ls-dot.dot-danger   { background: #ee0a24; }

/* ===== 行业标准抽屉 ===== */
.ds-drawer {
  padding: 0 0 96px;
  background: #f4f6f8;
  min-height: 100vh;
  overflow-y: auto;
  font-size: 13px;
  color: #1f2937;
}
.ds-banner {
  padding: 18px 16px 14px;
  color: #fff;
  background: linear-gradient(135deg, #4a90b2, #1989fa);
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}
.ds-banner-pending_accept    { background: linear-gradient(135deg, #ff976a, #ee7700); }
.ds-banner-pending_dispatch  { background: linear-gradient(135deg, #ffb84d, #ff976a); }
.ds-banner-dispatched        { background: linear-gradient(135deg, #4a90b2, #1989fa); }
.ds-banner-assigned_engineer { background: linear-gradient(135deg, #1989fa, #0e6fd1); }
.ds-banner-processing        { background: linear-gradient(135deg, #25aeae, #1989fa); }
.ds-banner-pending_confirm   { background: linear-gradient(135deg, #07c160, #04a655); }
.ds-banner-completed         { background: linear-gradient(135deg, #04a655, #03884e); }
.ds-banner-closed            { background: linear-gradient(135deg, #909399, #606266); }
.ds-banner-cancelled         { background: linear-gradient(135deg, #ee0a24, #c8050d); }
.ds-banner-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
}
.ds-banner-icon {
  font-size: 22px;
  flex-shrink: 0;
}
.ds-banner-status {
  font-size: 16px;
  font-weight: 600;
}
.ds-banner-orderno {
  margin-left: auto;
  font-family: ui-monospace, monospace;
  font-size: 12px;
  background: rgba(255,255,255,0.18);
  padding: 3px 8px;
  border-radius: 4px;
  color: #fff;
}
.ds-banner-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  opacity: 0.92;
}
.ds-banner-meta .van-icon {
  vertical-align: -1px;
  margin-right: 2px;
}
.ds-section {
  background: #fff;
  margin: 0 12px 12px;
  border-radius: 10px;
  padding: 14px 16px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}
.ds-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f2f5;
}
.ds-title .van-icon {
  color: #1989fa;
  font-size: 16px;
}
.ds-count {
  margin-left: 6px;
  font-size: 12px;
  color: #6b7280;
  font-weight: normal;
}
.ds-grid {
  display: grid;
  grid-template-columns: 84px 1fr;
  row-gap: 10px;
  column-gap: 12px;
  align-items: start;
}
.ds-key {
  color: #6b7280;
  font-size: 12px;
  line-height: 22px;
}
.ds-val {
  color: #1f2937;
  font-size: 13px;
  line-height: 22px;
  word-break: break-all;
}
.ds-val a {
  color: #1989fa;
  text-decoration: none;
}
.ds-val a:hover { text-decoration: underline; }
.ds-emph {
  color: #1f2937;
  font-weight: 500;
}
.ds-sub {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}
.ds-mono {
  font-family: ui-monospace, monospace;
  font-size: 12px;
  color: #4b5563;
}
.ds-empty {
  color: #c8c9cc;
  font-style: italic;
}
.ds-block {
  white-space: pre-wrap;
  background: #f9fafb;
  padding: 8px 10px;
  border-radius: 6px;
  border-left: 3px solid #1989fa;
  line-height: 1.6;
  grid-column: 2 / 3;
}
.ds-danger {
  color: #ee0a24;
  border-left-color: #ee0a24;
  font-weight: 500;
}
.ds-map-link {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  margin-left: 8px;
  padding: 2px 8px;
  background: #1989fa;
  color: #fff !important;
  border-radius: 4px;
  font-size: 12px;
}
.ds-map-link:hover { background: #0e6fd1; }
.ds-empty-block {
  text-align: center;
  color: #9ca3af;
  padding: 16px 0;
  font-size: 13px;
}
.ds-empty-block .van-icon {
  display: block;
  font-size: 28px;
  margin-bottom: 4px;
  opacity: 0.6;
}
.ds-media-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.ds-media-item {
  aspect-ratio: 1;
  border-radius: 6px;
  overflow: hidden;
  background: #f3f4f6;
  cursor: pointer;
  border: 1px solid #f0f2f5;
}
.ds-media-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.ds-video-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.ds-video-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #f9fafb;
  border-radius: 6px;
  color: #1989fa;
  font-size: 13px;
  border: 1px solid #eef2f7;
}
.ds-video-item:hover { background: #f0f7ff; }
.ds-video-item .van-icon { font-size: 18px; }
.ds-timeline {
  position: relative;
  padding-left: 4px;
}
.ds-timeline-item {
  display: flex;
  gap: 10px;
  padding: 8px 0 14px;
  position: relative;
}
.ds-timeline-item:last-child { padding-bottom: 0; }
.ds-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #1989fa;
  margin-top: 5px;
  flex-shrink: 0;
  position: relative;
  box-shadow: 0 0 0 3px #fff, 0 0 0 4px #f0f2f5;
}
.ds-dot::before {
  content: '';
  position: absolute;
  top: 14px;
  left: 50%;
  width: 2px;
  height: calc(100% + 6px);
  background: #f0f2f5;
  transform: translateX(-50%);
}
.ds-timeline-item:last-child .ds-dot::before { display: none; }
.ds-dot.dot-warning  { background: #ff976a; }
.ds-dot.dot-primary  { background: #1989fa; }
.ds-dot.dot-cyan     { background: #25aeae; }
.ds-dot.dot-success  { background: #07c160; }
.ds-dot.dot-muted    { background: #c8c9cc; }
.ds-dot.dot-danger   { background: #ee0a24; }
.ds-timeline-content { flex: 1; min-width: 0; }
.ds-timeline-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.ds-timeline-time {
  margin-left: auto;
  font-size: 11px;
  color: #9ca3af;
  font-family: ui-monospace, monospace;
}
.ds-timeline-operator {
  font-size: 12px;
  color: #6b7280;
}
.ds-timeline-remark {
  margin-top: 4px;
  background: #f9fafb;
  padding: 6px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #4b5563;
  line-height: 1.6;
}
.ds-log-images {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  margin-top: 6px;
}
.ds-log-images img {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  border-radius: 4px;
  cursor: pointer;
}
.ds-action-bar {
  position: sticky;
  bottom: 0;
  left: 0;
  right: 0;
  background: #fff;
  padding: 10px 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-shadow: 0 -2px 8px rgba(0,0,0,0.05);
  z-index: 10;
}
.ds-action-primary {
  display: flex;
  gap: 8px;
}
.ds-action-primary .van-button { flex: 1; }
.ds-action-secondary {
  display: flex;
  gap: 8px;
}
.ds-action-secondary .van-button { flex: 1; }


/* ===== DealerOrders 特有样式 ===== */
.sp-context {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #e8f4ff;
  border-radius: 14px;
  font-size: 13px;
  color: #1989fa;
}
.sp-context strong { color: #1f2937; margin-left: 2px; }
.filter-select {
  flex: 1;
  min-width: 180px;
  padding: 6px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 14px;
  background: #fff;
  color: #1f2937;
  cursor: pointer;
}
.appt-hint {
  color: #1989fa;
}
.op-link {
  display: inline-block;
  margin-right: 8px;
  padding: 2px 4px;
  cursor: pointer;
  font-size: 13px;
  text-decoration: none;
}
.op-link:hover {
  text-decoration: underline;
}
.op-link.primary {
  color: #1989fa;
}
.op-link.success {
  color: #07c160;
}
.dialog-body {
  padding: 16px;
}
.dialog-tip {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 12px;
  text-align: center;
}

</style>

