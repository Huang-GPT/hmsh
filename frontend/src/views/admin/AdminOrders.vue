<template>
  <div class="admin-orders">
    <h3>工单管理</h3>

    <!-- 顶部 KPI 卡片 -->
    <div class="kpi-row">
      <div class="kpi-card kpi-warn">
        <div class="kpi-num">{{ kpi.pending_accept + kpi.pending_dispatch }}</div>
        <div class="kpi-label">待处理</div>
      </div>
      <div class="kpi-card kpi-info">
        <div class="kpi-num">{{ kpi.processing + kpi.dispatched + kpi.assigned_engineer }}</div>
        <div class="kpi-label">处理中</div>
      </div>
      <div class="kpi-card kpi-success">
        <div class="kpi-num">{{ kpi.completed }}</div>
        <div class="kpi-label">已完成</div>
      </div>
      <div class="kpi-card kpi-muted">
        <div class="kpi-num">{{ kpi.cancelled + kpi.closed }}</div>
        <div class="kpi-label">关闭/撤销</div>
      </div>
    </div>

    <div class="toolbar">
      <div class="toolbar-row toolbar-top">
        <van-search
          v-model="keyword"
          placeholder="搜索 工单号/用户/手机/产品/故障"
          @search="loadOrders(1)"
          shape="round"
          class="search-box"
        />
      </div>
      <div class="toolbar-row toolbar-bottom">
        <span
          v-for="f in statusFilters"
          :key="f.value"
          :class="['filter-chip', { active: statusFilter === f.value }]"
          @click="setStatusFilter(f.value)"
        >{{ f.label }}</span>
        <van-button size="small" plain icon="replay" @click="loadOrders()">刷新</van-button>
      </div>
    </div>

    <div class="table-wrap">
      <table class="order-table">
        <thead>
          <tr>
            <th>工单号</th>
            <th>用户</th>
            <th>产品</th>
            <th>故障分类</th>
            <th>状态</th>
            <th>创建时间</th>
            <th class="col-actions">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading && orders.length === 0">
            <td colspan="7" class="state-cell">加载中…</td>
          </tr>
          <tr v-else-if="orders.length === 0">
            <td colspan="7" class="state-cell">
              <div class="empty-cell">
                <div class="empty-icon">📋</div>
                <div class="empty-text">暂无工单</div>
              </div>
            </td>
          </tr>
          <tr
            v-for="o in orders"
            :key="o.id"
            @click="showDetail(o)"
            :class="{ 'row-pending': isPending(o.status) }"
          >
            <td class="col-orderno">
              <code>{{ o.order_no }}</code>
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
                <span v-if="o.product_qr_code" class="prod-serial">{{ o.product_qr_code }}</span>
              </div>
            </td>
            <td>
              <div class="fault-cell">
                <van-tag v-if="o.fault_category_name" size="mini" type="primary" class="mr-1">{{ o.fault_category_name }}</van-tag>
                <van-tag size="mini" type="warning">{{ o.fault_type || '—' }}</van-tag>
              </div>
            </td>
            <td>
              <van-tag :type="tagType(o.status)" size="mini">
                {{ statusMap[o.status] || o.status }}
              </van-tag>
              <div v-if="o.engineer_name" class="row-meta">→ {{ o.engineer_name }}</div>
            </td>
            <td class="col-time">
              <div>{{ formatDate(o.created_at) }}</div>
              <div class="row-meta">{{ formatTime(o.created_at) }}</div>
            </td>
            <td class="col-actions" @click.stop>
              <a class="op-link primary" @click="showDetail(o)">详情</a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="pagination">
      <span class="pagination-info">
        共 <strong>{{ total }}</strong> 条 ·
        第 {{ page }} / {{ totalPages }} 页 ·
        每页 {{ pageSize }} 条
      </span>
      <div class="pagination-buttons">
        <van-button size="mini" :disabled="page <= 1" @click="changePage(-1)">上一页</van-button>
        <van-button size="mini" :disabled="page >= totalPages" @click="changePage(1)">下一页</van-button>
      </div>
    </div>

    <!-- ============ 工单详情 ============ -->
    <van-popup v-model:show="showDetail" position="right" :style="{ width: '90%', height: '100%' }" closeable>
      <div class="detail-drawer" v-if="currentOrder">
        <div class="drawer-header">
          <div class="dh-title">
            <span class="dh-orderno">{{ currentOrder.order_no }}</span>
            <van-tag :type="tagType(currentOrder.status)" size="medium" class="ml-1">
              {{ statusMap[currentOrder.status] }}
            </van-tag>
          </div>
          <div class="dh-meta">
            <span>创建于 {{ formatDateTime(currentOrder.created_at) }}</span>
          </div>
        </div>

        <van-cell-group inset>
          <van-cell title="报修用户">
            <template #value>
              <div class="cell-value-stack">
                <span class="cv-main">{{ currentOrder.user_name || '—' }}</span>
                <span class="cv-sub">{{ currentOrder.user_phone || '—' }}</span>
              </div>
            </template>
          </van-cell>
          <van-cell title="报修产品">
            <template #value>
              <div class="cell-value-stack">
                <span class="cv-main">{{ currentOrder.product_name || currentOrder.product_model || '—' }}</span>
                <span v-if="currentOrder.product_serial" class="cv-sub">序列: {{ currentOrder.product_serial }}</span>
                <span v-if="currentOrder.product_qr_code" class="cv-sub">二维码: {{ currentOrder.product_qr_code }}</span>
                <span v-if="currentOrder.product_sales_no" class="cv-sub">销售单: {{ currentOrder.product_sales_no }}</span>
              </div>
            </template>
          </van-cell>
          <van-cell title="故障分类">
            <template #value>
              <div class="cell-value-stack">
                <span class="cv-main">
                  <van-tag v-if="currentOrder.fault_category_name" type="primary" size="mini" class="mr-1">
                    {{ currentOrder.fault_category_name }}
                  </van-tag>
                  <van-tag type="warning" size="mini">{{ currentOrder.fault_type || '—' }}</van-tag>
                </span>
              </div>
            </template>
          </van-cell>
          <van-cell title="故障描述">
            <template #value>
              <div class="desc-text">{{ currentOrder.fault_desc || '—' }}</div>
            </template>
          </van-cell>
          <van-cell v-if="currentOrder.fault_address" title="故障地址" :value="currentOrder.fault_address" />
          <van-cell v-if="currentOrder.appointment_date" title="期望时间">
            <template #value>
              <span class="cv-main">{{ currentOrder.appointment_date }}</span>
              <span v-if="currentOrder.appointment_period === 'AM'" class="cv-sub">上午</span>
              <span v-else-if="currentOrder.appointment_period === 'PM'" class="cv-sub">下午</span>
            </template>
          </van-cell>
          <van-cell title="联系信息">
            <template #value>
              <div class="cell-value-stack">
                <span class="cv-main">{{ currentOrder.contact_name }}</span>
                <a :href="`tel:${currentOrder.contact_phone}`" class="cv-sub">{{ currentOrder.contact_phone }}</a>
              </div>
            </template>
          </van-cell>
          <van-cell v-if="currentOrder.service_point_name" title="服务点" :value="currentOrder.service_point_name" />
          <van-cell v-if="currentOrder.engineer_name" title="工程师">
            <template #value>
              <div class="cell-value-stack">
                <span class="cv-main">{{ currentOrder.engineer_name }}</span>
                <a v-if="currentOrder.engineer_phone" :href="`tel:${currentOrder.engineer_phone}`" class="cv-sub">{{ currentOrder.engineer_phone }}</a>
              </div>
            </template>
          </van-cell>
          <van-cell v-if="currentOrder.reject_reason" title="拒绝原因">
            <template #value><span style="color:#ee0a24">{{ currentOrder.reject_reason }}</span></template>
          </van-cell>
          <van-cell v-if="currentOrder.cancel_reason" title="撤销原因">
            <template #value><span style="color:#ee0a24">{{ currentOrder.cancel_reason }}</span></template>
          </van-cell>
          <van-cell title="创建时间" :value="formatDateTime(currentOrder.created_at)" />
        </van-cell-group>

        <!-- 图片 / 视频 -->
        <div v-if="hasMedia(currentOrder)" class="media-section">
          <div class="ms-title">现场图片 / 视频</div>
          <div v-if="currentOrder.images && currentOrder.images.length" class="media-grid">
            <div
              v-for="(img, i) in currentOrder.images"
              :key="`img-${i}`"
              class="media-item"
              @click="previewMedia(img)"
            >
              <img :src="img" :alt="`图片${i+1}`" loading="lazy" />
            </div>
          </div>
          <div v-if="currentOrder.videos && currentOrder.videos.length" class="video-list">
            <video
              v-for="(v, i) in currentOrder.videos"
              :key="`vid-${i}`"
              :src="v"
              controls
              preload="metadata"
              class="video-item"
            />
          </div>
        </div>

        <!-- 状态流转日志 -->
        <div class="log-section">
          <div class="ls-title">处理记录</div>
          <div v-if="!currentOrder.status_logs || currentOrder.status_logs.length === 0" class="ls-empty">暂无处理记录</div>
          <div v-else class="ls-list">
            <div v-for="log in currentOrder.status_logs" :key="log.id" class="ls-item">
              <div class="ls-dot"></div>
              <div class="ls-content">
                <div class="ls-head">
                  <span class="ls-status">{{ statusMap[log.to_status] || log.to_status }}</span>
                  <span class="ls-time">{{ formatDateTime(log.created_at) }}</span>
                </div>
                <div class="ls-operator">{{ log.operator_name || ('操作员#' + log.operator_id) }}</div>
                <div v-if="log.remark" class="ls-remark">{{ log.remark }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 操作区 -->
        <div v-if="canAct(currentOrder)" class="action-bar">
          <van-button
            v-if="currentOrder.status === 'pending_accept'"
            type="primary"
            block
            @click="acceptOrder"
          >受理工单</van-button>
          <van-button
            v-if="currentOrder.status === 'pending_accept' || currentOrder.status === 'pending_dispatch'"
            type="info"
            block
            @click="showDispatchDialog"
          >分配服务点</van-button>
          <van-button
            v-if="currentOrder.status === 'dispatched'"
            type="info"
            block
            @click="showAssignEngineerDialog"
          >分配工程师</van-button>
          <van-button
            v-if="currentOrder.status === 'assigned_engineer'"
            type="warning"
            block
            @click="startProcessing"
          >开始处理</van-button>
          <van-button
            v-if="currentOrder.status === 'processing'"
            type="success"
            block
            @click="completeOrder"
          >处理完成（待客户确认）</van-button>
          <van-button
            v-if="currentOrder.status === 'pending_confirm'"
            type="success"
            block
            @click="confirmCompleted"
          >确认完成</van-button>
          <van-button
            v-if="currentOrder.status === 'pending_accept' || currentOrder.status === 'pending_dispatch'"
            type="danger"
            plain
            block
            @click="rejectOrder"
          >拒绝工单</van-button>
          <van-button
            type="default"
            plain
            block
            @click="showDetail = false"
          >关闭</van-button>
        </div>
      </div>
    </van-popup>

    <!-- ============ 分配服务点 ============ -->
    <van-dialog v-model:show="showDispatch" title="分配服务点" show-cancel-button @confirm="confirmDispatch">
      <div class="dialog-body">
        <div class="dialog-tip">选择处理该工单的服务点</div>
        <select v-model="dispatchForm.service_point_id" class="select-input">
          <option :value="null">请选择</option>
          <option v-for="sp in servicePoints" :key="sp.id" :value="sp.id">{{ sp.name }}</option>
        </select>
        <van-field
          v-model="dispatchForm.remark"
          label="备注"
          placeholder="选填"
          maxlength="100"
        />
      </div>
    </van-dialog>

    <!-- ============ 分配工程师 ============ -->
    <van-dialog v-model:show="showAssignEngineer" title="分配工程师" show-cancel-button @confirm="confirmAssignEngineer">
      <div class="dialog-body">
        <div class="dialog-tip">服务点: {{ currentOrder && currentOrder.service_point_name }}</div>
        <select v-model="dispatchForm.engineer_id" class="select-input">
          <option :value="null">请选择工程师</option>
          <option v-for="e in engineers" :key="e.id" :value="e.id">{{ e.name }} {{ e.phone ? '(' + e.phone + ')' : '' }}</option>
        </select>
        <van-field
          v-model="dispatchForm.remark"
          label="备注"
          placeholder="选填"
          maxlength="100"
        />
      </div>
    </van-dialog>

    <!-- 图片预览 -->
    <van-image-preview v-model:show="showImagePreview" :images="previewImages" />
  </div>
</template>

<script>
import {
  getAllOrders, getOrderDetail,
  getServicePoints, getEngineers,
  acceptOrderApi, dispatchOrder, assignEngineer,
  startProcessingOrder, completeOrderApi, confirmCompletedApi, rejectOrder,
} from '@/api/admin'

export default {
  name: 'AdminOrders',
  data() {
    return {
      orders: [],
      keyword: '',
      statusFilter: 'all',
      page: 1,
      pageSize: 30,
      total: 0,
      loading: false,
      kpi: { pending_accept: 0, pending_dispatch: 0, dispatched: 0, assigned_engineer: 0, processing: 0, pending_confirm: 0, completed: 0, closed: 0, cancelled: 0 },

      showDetail: false,
      currentOrder: null,

      servicePoints: [],
      engineers: [],
      showDispatch: false,
      showAssignEngineer: false,
      dispatchForm: { service_point_id: null, engineer_id: null, remark: '' },

      showImagePreview: false,
      previewImages: [],

      statusMap: {
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
  computed: {
    totalPages() {
      return Math.max(1, Math.ceil(this.total / this.pageSize))
    },
    statusFilters() {
      return [
        { value: 'all', label: '全部' },
        { value: 'pending', label: '待处理' },
        { value: 'progress', label: '处理中' },
        { value: 'pending_confirm', label: '待确认' },
        { value: 'completed', label: '已完成' },
        { value: 'closed', label: '已关闭' },
      ]
    },
  },
  watch: {
    statusFilter() {
      this.loadOrders(1)
    },
  },
  created() {
    this.loadOrders()
    this.loadServicePoints()
  },
  methods: {
    isPending(status) {
      return ['pending_accept', 'pending_dispatch'].includes(status)
    },
    tagType(status) {
      const map = {
        pending_accept: 'warning',
        pending_dispatch: 'orange',
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
    setStatusFilter(v) {
      this.statusFilter = v
    },
    hasMedia(o) {
      return (o.images && o.images.length) || (o.videos && o.videos.length)
    },
    canAct(o) {
      return !['completed', 'closed', 'cancelled'].includes(o.status)
    },
    previewMedia(url) {
      if (!url) return
      const all = (this.currentOrder.images || []).filter(Boolean)
      this.previewImages = all.length ? all : [url]
      this.showImagePreview = true
    },

    async loadOrders(targetPage) {
      if (targetPage) this.page = targetPage
      this.loading = true
      try {
        const params = {
          keyword: this.keyword,
          page: this.page,
          page_size: this.pageSize,
        }
        if (this.statusFilter && this.statusFilter !== 'all') {
          if (this.statusFilter === 'pending') {
            params.status = 'pending_accept,pending_dispatch'
          } else if (this.statusFilter === 'progress') {
            params.status = 'dispatched,assigned_engineer,processing'
          } else {
            params.status = this.statusFilter
          }
        }
        const res = await getAllOrders(params)
        const data = res.data || {}
        this.orders = data.items || data.orders || []
        this.total = data.total || this.orders.length
        if (data.kpi) this.kpi = { ...this.kpi, ...data.kpi }
      } catch (e) {
        console.error(e)
      } finally {
        this.loading = false
      }
    },
    changePage(delta) {
      const next = this.page + delta
      if (next < 1 || next > this.totalPages) return
      this.page = next
      this.loadOrders()
    },
    async loadServicePoints() {
      try {
        const res = await getServicePoints()
        this.servicePoints = (res.data && (res.data.items || res.data.service_points)) || []
      } catch (e) { console.error(e) }
    },
    async loadEngineers(servicePointId) {
      try {
        const res = await getEngineers({ service_point_id: servicePointId })
        this.engineers = (res.data && (res.data.items || res.data.engineers)) || []
      } catch (e) { console.error(e) }
    },

    async showDetail(order) {
      this.currentOrder = order
      this.showDetail = true
      // 拉详情以获取 status_logs / 图片完整 URL 等
      try {
        const res = await getOrderDetail(order.id)
        const data = res.data || {}
        if (data.order) this.currentOrder = data.order
        else Object.assign(this.currentOrder, data)
        // 加载该服务点的工程师列表
        if (this.currentOrder.service_point_id) {
          this.loadEngineers(this.currentOrder.service_point_id)
        }
      } catch (e) {
        console.warn('工单详情加载失败', e)
      }
    },

    // ===== 操作 =====
    async acceptOrder() {
      try {
        await acceptOrderApi(this.currentOrder.id, this.currentOrder.contact_phone)
        this.$toast.success('已受理')
        this.currentOrder.status = 'pending_dispatch'
        this.loadOrders()
      } catch (e) {
        this.$toast((e && e.response && e.response.data && e.response.data.error) || '操作失败')
      }
    },
    showDispatchDialog() {
      if (!this.servicePoints.length) this.loadServicePoints()
      this.dispatchForm = { service_point_id: null, engineer_id: null, remark: '' }
      this.showDispatch = true
    },
    async confirmDispatch() {
      if (!this.dispatchForm.service_point_id) {
        this.$toast('请选择服务点')
        return false
      }
      try {
        await dispatchOrder(this.currentOrder.id, this.dispatchForm.service_point_id, this.dispatchForm.remark)
        this.$toast.success('已派单')
        this.showDispatch = false
        this.showDetail = false
        this.loadOrders()
      } catch (e) {
        this.$toast((e && e.response && e.response.data && e.response.data.error) || '操作失败')
        return false
      }
      return true
    },
    async showAssignEngineerDialog() {
      if (!this.currentOrder.service_point_id) {
        this.$toast('请先分配服务点')
        return false
      }
      await this.loadEngineers(this.currentOrder.service_point_id)
      this.dispatchForm = { service_point_id: this.currentOrder.service_point_id, engineer_id: null, remark: '' }
      this.showAssignEngineer = true
    },
    async confirmAssignEngineer() {
      if (!this.dispatchForm.engineer_id) {
        this.$toast('请选择工程师')
        return false
      }
      try {
        await assignEngineer(this.currentOrder.id, this.dispatchForm.engineer_id, this.dispatchForm.remark)
        this.$toast.success('已分配工程师')
        this.showAssignEngineer = false
        this.showDetail = false
        this.loadOrders()
      } catch (e) {
        this.$toast((e && e.response && e.response.data && e.response.data.error) || '操作失败')
        return false
      }
      return true
    },
    async startProcessing() {
      try {
        await startProcessingOrder(this.currentOrder.id, '')
        this.$toast.success('已开始处理')
        this.currentOrder.status = 'processing'
        this.loadOrders()
      } catch (e) {
        this.$toast((e && e.response && e.response.data && e.response.data.error) || '操作失败')
      }
    },
    async completeOrder() {
      try {
        await completeOrderApi(this.currentOrder.id, '')
        this.$toast.success('已处理完成，等待客户确认')
        this.currentOrder.status = 'pending_confirm'
        this.loadOrders()
      } catch (e) {
        this.$toast((e && e.response && e.response.data && e.response.data.error) || '操作失败')
      }
    },
    async confirmCompleted() {
      try {
        await confirmCompletedApi(this.currentOrder.id, '')
        this.$toast.success('已确认完成')
        this.currentOrder.status = 'completed'
        this.loadOrders()
      } catch (e) {
        this.$toast((e && e.response && e.response.data && e.response.data.error) || '操作失败')
      }
    },
    async rejectOrder() {
      const reason = window.prompt('请输入拒绝原因')
      if (!reason) return
      try {
        await rejectOrder(this.currentOrder.id, reason)
        this.$toast.success('已拒绝')
        this.currentOrder.status = 'cancelled'
        this.loadOrders()
        this.showDetail = false
      } catch (e) {
        this.$toast((e && e.response && e.response.data && e.response.data.error) || '操作失败')
      }
    },
  },
}
</script>

<style scoped>
.admin-orders {
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
  color: #1f2937;
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
.video-list {
  margin-top: 10px;
}
.video-item {
  width: 100%;
  border-radius: 6px;
  background: #000;
  margin-bottom: 8px;
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
</style>