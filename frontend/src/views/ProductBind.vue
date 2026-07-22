<template>
  <div class="product-bind">
    <van-nav-bar title="产品绑定" left-arrow @click-left="$router.back()" fixed :border="false" />

    <!-- 顶部 banner -->
    <div class="bind-banner">
      <div class="bind-banner-title">扫描产品二维码</div>
      <div class="bind-banner-sub">或将二维码对准摄像头扫描绑定</div>
      <van-button
        round
        block
        type="info"
        icon="scan"
        size="large"
        class="scan-btn"
        :loading="scanning"
        @click="onScan"
      >立即扫码</van-button>
    </div>

    <!-- 手动输入区（销售单 + 行项目号） -->
    <div class="manual-section">
      <div class="divider"><span>或输入销售单 + 行项目号</span></div>
      <van-cell-group inset>
        <van-field
          v-model="sapOrderNo"
          label="销售单号"
          placeholder="如 SO202607001"
          clearable
          :disabled="submitting"
        />
        <van-field
          v-model="sapLineItem"
          label="行项目号"
          type="number"
          placeholder="如 10"
          clearable
          :disabled="submitting"
        />
      </van-cell-group>
      <div class="submit-row">
        <van-button
          round
          block
          type="primary"
          :loading="submitting"
          :disabled="!canSubmit"
          @click="onManualBind"
        >绑定</van-button>
      </div>
    </div>

    <!-- 已绑定列表 -->
    <div class="bound-section">
      <div class="section-header">
        <span class="section-title">已绑定产品</span>
        <span class="section-count">共 {{ boundProducts.length }} 件</span>
      </div>

      <van-pull-refresh v-model="refreshing" @refresh="onRefresh" success-text="刷新成功">
        <div v-if="loading && boundProducts.length === 0" class="list-loading">
          <van-skeleton title :row="3" />
          <van-skeleton title :row="3" />
        </div>

        <van-empty
          v-else-if="boundProducts.length === 0"
          description="暂无绑定产品"
          image-size="80"
        >
          <van-button round type="info" size="small" @click="onScan" class="empty-btn">
            扫码绑定第一个产品
          </van-button>
        </van-empty>

        <div v-else class="bound-list">
          <van-cell-group v-for="p in boundProducts" :key="p.id" inset class="bound-card">
            <van-cell center>
              <template #title>
                <div class="bound-title">
                  <span class="bound-name">{{ p.product_name || p.model || '产品' }}</span>
                  <van-tag :type="p.bind_method === 'qrcode_sap' ? 'success' : 'primary'" size="mini">
                    {{ bindMethodLabel(p.bind_method) }}
                  </van-tag>
                </div>
              </template>
              <template #label>
                <div class="bound-meta">
                  <div v-if="p.sales_no">销售单：{{ p.sales_no }}</div>
                  <div v-if="p.sap_line_item !== null && p.sap_line_item !== undefined">
                    行项目：{{ p.sap_line_item }}
                  </div>
                  <div v-if="p.qr_code">二维码：{{ p.qr_code }}</div>
                </div>
              </template>
            </van-cell>
            <van-cell center title="绑定时间" :value="formatDate(p.bind_time)" />
            <van-cell center>
              <template #title><span class="op-text">操作</span></template>
              <template #right-icon>
                <van-button
                  size="mini"
                  type="danger"
                  plain
                  @click="onUnbind(p)"
                >解绑</van-button>
              </template>
            </van-cell>
          </van-cell-group>
        </div>
      </van-pull-refresh>
    </div>

    <div style="height: 60px;"></div>
  </div>
</template>

<script>
import { bindBySapOrder, bindBySerialNumber, getUserProducts, unbindProduct } from '@/api/products'
import { scanQRCode } from '@/utils/wechat'

export default {
  name: 'ProductBind',
  data() {
    return {
      sapOrderNo: '',
      sapLineItem: '',
      submitting: false,
      scanning: false,
      loading: true,
      refreshing: false,
      boundProducts: [],
    }
  },
  computed: {
    canSubmit() {
      return this.sapOrderNo.trim() && this.sapLineItem !== '' && this.sapLineItem !== null && !this.submitting
    },
  },
  created() {
    this.loadBoundProducts()
  },
  methods: {
  methods: {
    bindMethodLabel(m) {
      return { qrcode_sap: '扫码绑定', qrcode_product: '序列号绑定', manual: '手动绑定' }[m] || m
    },
    formatDate(d) {
      if (!d) return '—'
      return String(d).substring(0, 10)
    },
    async onScan() {
      this.scanning = true
      try {
        const result = await scanQRCode()
        // QR 格式约定：SAP订单号|行项目号，如 "SO202607001|10"
        const text = String(result || '').trim()
        if (!text) {
          this.$toast('扫码结果为空')
          return
        }
        const [orderNo, lineItem] = text.split('|').map(s => s && s.trim())
        if (orderNo && lineItem) {
          this.sapOrderNo = orderNo
          this.sapLineItem = lineItem
          await this.doBind(() => bindBySapOrder(orderNo, lineItem), '扫码')
        } else if (orderNo) {
          // 兼容：二维码内容直接就是序列号
          await this.doBind(() => bindBySerialNumber(orderNo), '扫码')
        } else {
          this.$toast('无法识别的二维码内容')
        }
      } catch (e) {
        const data = e && e.response && e.response.data
        this.$toast((data && data.error) || e.message || '扫码失败')
      } finally {
        this.scanning = false
      }
    },
    async onManualBind() {
      if (!this.canSubmit) return
      await this.doBind(() => bindBySapOrder(this.sapOrderNo.trim(), Number(this.sapLineItem)), '手动输入')
    },
    async doBind(apiCall, source) {
      this.submitting = true
      try {
        const res = await apiCall()
        this.$toast.success('绑定成功')
        this.sapOrderNo = ''
        this.sapLineItem = ''
        await this.loadBoundProducts()
      } catch (e) {
        const data = e && e.response && e.response.data
        const err = (data && data.error) || e.message || '绑定失败'
        if (e.response && e.response.status === 404) {
          this.$toast.fail(err + '（请先在管理后台录入）')
        } else if (e.response && e.response.status === 400 && /已绑定/.test(err)) {
          this.$toast.fail(err)
        } else {
          this.$toast.fail(err)
        }
        console.error(`[bind ${source}]`, data)
      } finally {
        this.submitting = false
      }
    },
    async onUnbind(p) {
      const ok = await this.$dialog.confirm({
        title: '确认解绑',
        message: `确定解绑产品 #${p.id}（${p.product_name || p.model || '未知'}）吗？`,
        confirmButtonText: '解绑',
      }).catch(() => false)
      if (!ok) return
      try {
        await unbindProduct(p.id)
        this.$toast.success('已解绑')
        await this.loadBoundProducts()
      } catch (e) {
        this.$toast('解绑失败')
      }
    },
    async loadBoundProducts() {
      try {
        const res = await getUserProducts()
        this.boundProducts = (res.data && res.data.products) || []
      } catch (e) {
        console.error('加载产品列表失败', e)
      } finally {
        this.loading = false
        this.refreshing = false
      }
    },
    async onRefresh() {
      this.refreshing = true
      await this.loadBoundProducts()
    },
  },
}
</script>

<style scoped>
.product-bind {
  min-height: 100vh;
  background: #f5f6f8;
  padding-top: 46px;
  padding-bottom: 20px;
}
.bind-banner {
  background: linear-gradient(135deg, #4a90e2, #1989fa);
  color: #fff;
  padding: 28px 20px 24px;
  text-align: center;
}
.bind-banner-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 4px;
}
.bind-banner-sub {
  font-size: 13px;
  opacity: 0.9;
  margin-bottom: 18px;
}
.scan-btn {
  background: #fff !important;
  color: #1989fa !important;
  border: none;
  font-weight: 600;
}
.manual-section {
  margin: 16px 0;
}
.divider {
  text-align: center;
  margin: 16px 0 12px;
  color: #999;
  font-size: 12px;
  position: relative;
}
.divider::before,
.divider::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 30%;
  height: 1px;
  background: #e5e7eb;
}
.divider::before { left: 0; }
.divider::after { right: 0; }
.divider span {
  background: #f5f6f8;
  padding: 0 12px;
}
.submit-row {
  padding: 12px 16px 0;
}
.bound-section {
  margin: 16px 0;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 0 16px 12px;
}
.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}
.section-count {
  font-size: 12px;
  color: #6b7280;
}
.list-loading {
  padding: 0 16px;
}
.bound-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 0 16px;
}
.bound-card {
  border-radius: 8px;
  overflow: hidden;
}
.bound-title {
  display: flex;
  align-items: center;
  gap: 8px;
}
.bound-name {
  font-weight: 600;
  color: #1f2937;
}
.bound-meta {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.6;
}
.op-text {
  font-size: 13px;
  color: #6b7280;
}
.empty-btn {
  margin-top: 12px;
}
</style>