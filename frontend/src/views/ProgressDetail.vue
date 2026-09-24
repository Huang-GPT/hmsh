<template>
  <div class="progress-detail">
    <van-nav-bar
      title="工单详情"
      left-arrow
      :border="false"
      fixed
      @click-left="onBack"
    />
    <div class="pd-spacer" />

    <div v-if="loading" class="loading-tip">
      <van-loading size="24">加载中...</van-loading>
    </div>

    <div v-else-if="loadError" class="error-tip">
      <van-empty :description="loadError">
        <van-button round type="primary" size="small" @click="loadDetail">重新加载</van-button>
      </van-empty>
    </div>

    <template v-else-if="order">
      <!-- 顶部状态卡 -->
      <div class="status-card">
        <div class="status-bg status-bg-1"></div>
        <div class="status-bg status-bg-2"></div>
        <div class="status-info">
          <div class="status-no">{{ order.order_no }}</div>
          <div class="status-meta">创建于 {{ formatDate(order.created_at) }}</div>
        </div>
        <van-tag :type="statusTagType(order.status)" size="large" class="status-tag">
          {{ order.status_cn || statusText[order.status] }}
        </van-tag>
      </div>

      <!-- 处理时间线 -->
      <div class="card">
        <div class="card-title">
          <van-icon name="clock-o" /> 处理进度
        </div>
        <van-steps direction="vertical" :active="timelineActive" active-color="#1989fa">
          <van-step v-for="(s, idx) in timelineSteps" :key="idx">
            <div class="step-status">{{ statusText[s.to_status] || s.to_status_cn || s.to_status }}</div>
            <div class="step-time">{{ formatDate(s.created_at) }}</div>
          </van-step>
        </van-steps>
      </div>

      <!-- 产品信息 -->
      <div class="card">
        <div class="card-title"><van-icon name="goods-o" /> 产品信息</div>
        <van-cell title="产品名称" :value="order.product_name || order.product_model || '—'" />
        <van-cell title="产品型号" :value="order.product_model || '—'" />
        <van-cell v-if="order.product_serial" title="序列号" :value="order.product_serial" />
        <van-cell v-if="order.product_qr_code" title="产品码" :value="order.product_qr_code" />
        <van-cell v-if="order.product_sales_no" title="销售单号" :value="order.product_sales_no" />
      </div>

      <!-- 故障信息 -->
      <div class="card">
        <div class="card-title"><van-icon name="warning-o" /> 故障信息</div>
        <van-cell title="故障分类" :value="order.fault_category_name || '—'" />
        <van-cell title="故障类型" :value="order.fault_type || '—'" />
        <van-cell v-if="order.fault_desc" title="故障描述">
          <template #default>
            <div class="multiline">{{ order.fault_desc }}</div>
          </template>
        </van-cell>
        <van-cell v-if="order.fault_address" title="故障地址" :value="order.fault_address" />
        <div v-if="order.images && order.images.length" class="image-block">
          <div class="image-label">现场图片</div>
          <div class="image-grid">
            <van-image
              v-for="(img, idx) in order.images"
              :key="idx"
              :src="normalizeImageUrl(img)"
              width="80"
              height="80"
              fit="cover"
              radius="6"
              @click="previewImage(idx)"
            />
          </div>
        </div>
      </div>

      <!-- 上门时间 -->
      <div class="card" v-if="order.appointment_date || order.appointment_period">
        <div class="card-title"><van-icon name="calendar-o" /> 期望上门</div>
        <van-cell
          title="日期"
          :value="formatDate(order.appointment_date) + (order.appointment_period ? ' ' + periodText[order.appointment_period] : '')"
        />
      </div>

      <!-- 服务信息 -->
      <div class="card" v-if="order.service_point_name || order.engineer_name || order.assigned_engineer_name">
        <div class="card-title"><van-icon name="service-o" /> 服务信息</div>
        <van-cell v-if="order.service_point_name" title="服务点" :value="order.service_point_name" />
        <van-cell
          v-if="order.engineer_name || order.assigned_engineer_name"
          title="服务工程师"
          :value="(order.engineer_name || order.assigned_engineer_name) + (order.engineer_phone || order.assigned_engineer_phone ? ' ' + (order.engineer_phone || order.assigned_engineer_phone) : '')"
        />
      </div>

      <!-- 拒绝/取消原因 -->
      <div v-if="order.reject_reason" class="card">
        <div class="card-title"><van-icon name="close-circle-o" /> 拒绝原因</div>
        <div class="reject-text">{{ order.reject_reason }}</div>
      </div>
      <div v-if="order.cancel_reason" class="card">
        <div class="card-title"><van-icon name="cross" /> 撤销原因</div>
        <div class="reject-text">{{ order.cancel_reason }}</div>
      </div>

      <!-- 操作按钮：撤销工单 -->
      <div v-if="order.status === 'pending_accept'" class="action-bar">
        <van-button block round type="danger" :loading="canceling" @click="onCancel">
          撤销工单
        </van-button>
      </div>
      <div v-else class="action-bar-tip">
        工单已进入处理流程，如需帮助请联系客服
      </div>
    </template>

    <!-- 图片预览 -->
    <van-image-preview
      v-model="showImagePreview"
      :images="previewImageList"
      :start-position="previewStart"
      closeable
    />
  </div>
</template>

<script>
import { getMyOrderDetail, cancelMyOrder } from '@/api/workOrders'

export default {
  name: 'ProgressDetail',
  data() {
    return {
      orderId: null,
      order: null,
      logs: [],
      loading: false,
      loadError: '',
      canceling: false,
      showImagePreview: false,
      previewImageList: [],
      previewStart: 0,
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
      periodText: {
        morning: '上午',
        afternoon: '下午',
        evening: '晚上',
      },
    }
  },
  computed: {
    timelineSteps() {
      const statusChanges = (this.logs || []).filter(l => l.from_status !== l.to_status)
      return statusChanges.slice().reverse()
    },
    timelineActive() {
      return Math.max(0, this.timelineSteps.length - 1)
    },
  },
  created() {
    this.orderId = this.$route.params.id
    if (!this.orderId) {
      this.loadError = '工单号缺失'
      return
    }
    this.loadDetail()
  },
  methods: {
    onBack() {
      if (window.history.length > 1) this.$router.back()
      else this.$router.replace('/progress')
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
    normalizeImageUrl(url) {
      if (!url) return ''
      if (/^https?:\/\//.test(url) || url.startsWith('data:')) return url
      if (url.startsWith('/')) return window.location.origin + url
      var idx = url.lastIndexOf('/')
      var file = idx >= 0 ? url.substring(idx + 1) : url
      return window.location.origin + '/api/uploads/' + file
    },
    async loadDetail() {
      this.loading = true
      this.loadError = ''
      try {
        const res = await getMyOrderDetail(this.orderId, this.authHeaders())
        const data = res.data || {}
        this.order = data.order || null
        this.logs = Array.isArray(data.logs) ? data.logs : []
      } catch (e) {
        const code = e && e.response && e.response.status
        if (code === 401) {
          this.loadError = '登录已过期，请重新登录'
        } else if (code === 403) {
          this.loadError = '无权查看此工单'
        } else if (code === 404) {
          this.loadError = '工单不存在'
        } else {
          this.loadError = '加载失败：' + ((e && e.response && e.response.data && e.response.data.error) || e.message)
        }
        this.order = null
      } finally {
        this.loading = false
      }
    },
    previewImage(idx) {
      if (!this.order || !this.order.images) return
      this.previewImageList = this.order.images.map(u => ({ url: this.normalizeImageUrl(u) }))
      this.previewStart = idx
      this.showImagePreview = true
    },
    previewLogImage(log, idx) {
      if (!log.images) return
      this.previewImageList = log.images.map(u => ({ url: this.normalizeImageUrl(u) }))
      this.previewStart = idx
      this.showImagePreview = true
    },
    async onCancel() {
      try {
        await this.$dialog.confirm({ title: '确认撤销', message: '撤销后无法恢复，是否继续？' })
      } catch (e) {
        return
      }
      this.canceling = true
      try {
        await cancelMyOrder(this.orderId, this.authHeaders())
        this.$toast.success('撤销申请已提交')
        this.loadDetail()
      } catch (e) {
        this.$toast((e && e.response && e.response.data && e.response.data.error) || '撤销失败')
      } finally {
        this.canceling = false
      }
    },
  },
}
</script>

<style scoped>
.progress-detail {
  min-height: 100vh;
  background: var(--color-bg-page);
  padding-top: var(--nav-bar-height);
  padding-bottom: 32px;
}
.pd-spacer { height: 0; }
.loading-tip, .error-tip {
  padding: 60px var(--space-4);
  text-align: center;
}

/* ===== 顶部状态卡 ===== */
.status-card {
  position: relative;
  background: linear-gradient(135deg, var(--brand-400), var(--brand-600));
  color: #fff;
  margin: var(--space-3) var(--space-4) 0;
  border-radius: var(--radius-md);
  padding: var(--space-5) var(--space-4);
  display: flex;
  justify-content: space-between;
  align-items: center;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(25, 137, 250, 0.18);
}
.status-bg {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.10);
}
.status-bg-1 {
  width: 160px; height: 160px;
  top: -60px; right: -40px;
}
.status-bg-2 {
  width: 100px; height: 100px;
  bottom: -40px; left: -30px;
  background: rgba(255, 255, 255, 0.06);
}
.status-info {
  position: relative;
  flex: 1;
}
.status-no {
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  letter-spacing: 0.5px;
  font-family: ui-monospace, monospace;
}
.status-meta {
  font-size: var(--text-sm);
  opacity: 0.85;
  margin-top: var(--space-1);
}
.status-tag {
  position: relative;
  font-weight: var(--font-semibold);
}

/* ===== 信息卡 ===== */
.card {
  background: var(--color-bg-card);
  margin: var(--space-3) var(--space-4) 0;
  border-radius: var(--radius-md);
  padding: var(--space-4);
  box-shadow: var(--shadow-card);
}
.card-title {
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  margin-bottom: var(--space-3);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.card-title .van-icon {
  color: var(--color-primary);
}
.step-status {
  font-size: var(--text-base);
  color: var(--color-text);
}
.step-time {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  margin-top: var(--space-1);
}
.multiline {
  white-space: pre-wrap;
  word-break: break-all;
  line-height: 1.5;
}
.image-block {
  padding: var(--space-2) 0;
}
.image-label {
  color: var(--color-text-tertiary);
  font-size: var(--text-sm);
  margin-bottom: var(--space-2);
}
.image-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
.reject-text {
  color: var(--color-danger);
  font-size: var(--text-base);
  line-height: 1.5;
  white-space: pre-wrap;
}
.action-bar {
  margin: var(--space-5) var(--space-4) var(--space-2);
}
.action-bar-tip {
  text-align: center;
  color: var(--color-text-tertiary);
  font-size: var(--text-sm);
  padding: var(--space-5) var(--space-4);
}
</style>