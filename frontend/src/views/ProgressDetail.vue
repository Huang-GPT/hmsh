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
        <div class="status-no">{{ order.order_no }}</div>
        <van-tag :type="statusTagType(order.status)" size="large">
          {{ order.status_cn || statusText[order.status] }}
        </van-tag>
      </div>

      <!-- 处理时间线 -->
      <div class="timeline-card">
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
      <div class="info-card">
        <div class="card-title"><van-icon name="goods-o" /> 产品信息</div>
        <van-cell title="产品名称" :value="order.product_name || order.product_model || '—'" />
        <van-cell title="产品型号" :value="order.product_model || '—'" />
        <van-cell v-if="order.product_serial" title="序列号" :value="order.product_serial" />
        <van-cell v-if="order.product_qr_code" title="产品码" :value="order.product_qr_code" />
        <van-cell v-if="order.product_sales_no" title="销售单号" :value="order.product_sales_no" />
        <van-cell v-if="order.product_customer_name" title="客户名称" :value="order.product_customer_name" />
        <van-cell v-if="order.product_dealer_name" title="经销商" :value="order.product_dealer_name" />
      </div>

      <!-- 故障信息 -->
      <div class="info-card">
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
      <div class="info-card" v-if="order.appointment_date || order.appointment_period">
        <div class="card-title"><van-icon name="calendar-o" /> 期望上门</div>
        <van-cell
          title="日期"
          :value="formatDate(order.appointment_date) + (order.appointment_period ? ' ' + periodText[order.appointment_period] : '')"
        />
      </div>

      <!-- 联系信息 -->
      <div class="info-card">
        <div class="card-title"><van-icon name="user-o" /> 联系信息</div>
        <van-cell title="联系人" :value="order.contact_name || '—'" />
        <van-cell title="联系电话" :value="order.contact_phone || '—'" />
        <van-cell v-if="order.user_name" title="报修账号" :value="order.user_name" />
      </div>

      <!-- 服务信息 -->
      <div class="info-card" v-if="order.service_point_name || order.engineer_name || order.assigned_engineer_name">
        <div class="card-title"><van-icon name="service-o" /> 服务信息</div>
        <van-cell v-if="order.service_point_name" title="服务点" :value="order.service_point_name" />
        <van-cell
          v-if="order.engineer_name || order.assigned_engineer_name"
          title="服务工程师"
          :value="(order.engineer_name || order.assigned_engineer_name) + (order.engineer_phone || order.assigned_engineer_phone ? ' ' + (order.engineer_phone || order.assigned_engineer_phone) : '')"
        />
      </div>

      <!-- 处理记录 -->
      <div class="info-card" v-if="logs.length">
        <div class="card-title"><van-icon name="records" /> 处理记录</div>
        <div v-for="log in logs" :key="log.id" class="log-item" :class="log.from_status === log.to_status ? 'log-note' : 'log-status'">
          <div class="log-meta">
            <span class="log-time">{{ formatDate(log.created_at) }}</span>
            <van-tag :type="log.from_status === log.to_status ? 'primary' : 'success'" size="mini">
              {{ log.from_status === log.to_status ? '备注' : statusText[log.to_status] || log.to_status_cn || log.to_status }}
            </van-tag>
          </div>
          <div class="log-op">{{ log.operator_name || '系统' }}</div>
          <div v-if="log.remark" class="log-remark">{{ log.remark }}</div>
          <div v-if="log.images && log.images.length" class="log-images">
            <van-image
              v-for="(img, i) in log.images"
              :key="i"
              :src="normalizeImageUrl(img)"
              width="60"
              height="60"
              fit="cover"
              radius="4"
              @click="previewLogImage(log, i)"
            />
          </div>
        </div>
      </div>

      <!-- 拒绝/取消原因 -->
      <div v-if="order.reject_reason" class="info-card">
        <div class="card-title"><van-icon name="close-circle-o" /> 拒绝原因</div>
        <div class="reject-text">{{ order.reject_reason }}</div>
      </div>
      <div v-if="order.cancel_reason" class="info-card">
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
  background: #f5f6f8;
  padding-top: 46px;
  padding-bottom: 32px;
}
.pd-spacer { height: 0; }
.loading-tip, .error-tip {
  padding: 60px 16px;
  text-align: center;
}
.status-card {
  background: linear-gradient(135deg, #1989fa 0%, #0f6fdb 100%);
  color: #fff;
  margin: 12px 12px 0;
  border-radius: 10px;
  padding: 18px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.status-no {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.5px;
}
.timeline-card, .info-card {
  background: #fff;
  margin: 12px 12px 0;
  border-radius: 10px;
  padding: 14px 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.card-title .van-icon { color: #1989fa; }
.step-status { font-size: 14px; color: #333; }
.step-time { font-size: 12px; color: #999; margin-top: 2px; }
.multiline { white-space: pre-wrap; word-break: break-all; line-height: 1.5; }
.image-block { padding: 8px 0; }
.image-label { color: #999; font-size: 13px; margin-bottom: 8px; }
.image-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.log-item {
  border-left: 3px solid #1989fa;
  padding: 8px 10px;
  margin: 8px 0;
  background: #f7f9fc;
  border-radius: 0 6px 6px 0;
}
.log-item.log-note {
  border-left-color: #1989fa;
  background: #eef5ff;
}
.log-item.log-status {
  border-left-color: #07c160;
  background: #f0fbf4;
}
.log-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}
.log-time { font-size: 12px; color: #999; }
.log-op { font-size: 13px; color: #666; margin-bottom: 2px; }
.log-remark {
  font-size: 14px;
  color: #333;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
}
.log-images {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}
.reject-text {
  color: #c45656;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
}
.action-bar {
  margin: 20px 16px 8px;
}
.action-bar-tip {
  text-align: center;
  color: #999;
  font-size: 12px;
  padding: 20px 16px;
}
</style>
