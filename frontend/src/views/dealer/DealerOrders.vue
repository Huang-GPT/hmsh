<template>
  <div class='dealer-orders'>
    <van-nav-bar title='工单服务' left-arrow @click-left="$router.push('/admin/dashboard')" fixed />
    <van-tabs v-model='activeTab' @change='loadOrders' sticky offset-top="46px">
      <van-tab title='待接单' name='dispatched' />
      <van-tab title='处理中' name='processing' />
      <van-tab title='已完成' name='completed' />
    </van-tabs>
    <van-list v-model='loading' :finished='finished' finished-text='没有更多了' @load='loadOrders'>
      <div v-if='orders.length === 0 && !loading' class='empty-tip'>
        <van-empty :description='emptyText' />
      </div>
      <div
        v-for='o in orders'
        :key='o.id'
        class='order-card'
        @click='onCellClick(o)'
      >
        <div class='card-row-top'>
          <span class='order-no'>{{ o.order_no }}</span>
          <van-tag :type='tagType(o.status)' size='medium'>{{statusMap[o.status]}}</van-tag>
        </div>
        <div class='card-row'>
          <span class='ilbl'>客户：</span>
          <span class='ival'>{{ o.contact_name || '—' }} {{ o.contact_phone || '' }}</span>
        </div>
        <div class='card-row'>
          <span class='ilbl'>产品：</span>
          <span class='ival'>{{ o.product_name || o.product_model || '—' }}</span>
        </div>
        <div class='card-row'>
          <span class='ilbl'>故障：</span>
          <span class='ival ellipsis'>{{ o.fault_type || '—' }}</span>
        </div>
        <div v-if='o.assigned_engineer_name' class='card-row card-row-meta'>
          <van-icon name='manager-o' />
          <span>{{ o.assigned_engineer_name }}</span>
        </div>
      </div>
    </van-list>

    <van-dialog v-model='showAcceptDialog' title='接单' show-cancel-button :before-close='onAcceptClose'>
      <div class='accept-dialog'>
        <div class='hint'>请填写本次上门工程师的姓名和联系电话</div>
        <van-cell-group inset>
          <van-field v-model='engineerForm.name' label='工程师姓名' placeholder='请输入' maxlength='20' />
          <van-field v-model='engineerForm.phone' label='工程师电话' placeholder='11 位手机号' type='tel' maxlength='11' />
        </van-cell-group>
      </div>
    </van-dialog>

    <van-dialog v-model='showDetailDialog' title='工单详情' :show-confirm-button='false' close-on-click-overlay>
      <div class='detail-dialog' v-if='currentOrder'>
        <div class='row'><span class='k'>工单号</span><span class='v'>{{ currentOrder.order_no }}</span></div>
        <div class='row'><span class='k'>客户</span><span class='v'>{{ currentOrder.contact_name }} {{ currentOrder.contact_phone }}</span></div>
        <div class='row'><span class='k'>产品</span><span class='v'>{{ currentOrder.product_name || currentOrder.product_model }}</span></div>
        <div class='row'><span class='k'>故障</span><span class='v'>{{ currentOrder.fault_type }}</span></div>
        <div class='row'><span class='k'>地址</span><span class='v'>{{ currentOrder.fault_address }}</span></div>
        <div class='row'><span class='k'>预约时间</span><span class='v'>{{ currentOrder.appointment_date }} {{ currentOrder.appointment_period }}</span></div>
        <div class='row' v-if='currentOrder.assigned_engineer_name'><span class='k'>工程师</span><span class='v'>{{ currentOrder.assigned_engineer_name }} {{ currentOrder.assigned_engineer_phone }}</span></div>
        <div class='action-btns' v-if="(currentOrder.status === 'processing' || currentOrder.status === 'pending_confirm') && $hasPermission('order:complete')">
          <van-button type='success' block @click='confirmComplete'>标记完成</van-button>
        </div>
      </div>
    </van-dialog>
  </div>
</template>
<script>
import { getServicePointOrders, acceptOrderByText, confirmCompletedApi } from '@/api/admin'
export default {
  name: 'DealerOrders',
  data() {
    return {
      activeTab: 'dispatched', orders: [], loading: false, finished: false,
      showAcceptDialog: false, showDetailDialog: false, currentOrder: null,
      engineerForm: { name: '', phone: '' },
      statusMap: { 'dispatched': '已派单', 'assigned_engineer': '已分配', 'processing': '处理中', 'pending_confirm': '待确认', 'completed': '已完成' },
      emptyText: '暂无工单',
    }
  },
  created() { this.loadOrders() },
  methods: {
    tagType(s) { const m = { dispatched: 'primary', assigned_engineer: 'warning', processing: 'cyan', pending_confirm: 'success', completed: 'success' }; return m[s] || 'default' },
    async loadOrders() {
      if (this.finished) return
      this.loading = true
      try {
        const res = await getServicePointOrders()
        const allOrders = (res.data || {}).orders || []
        if (this.activeTab === 'dispatched') {
          this.orders = allOrders.filter(o => o.status === 'dispatched')
          this.emptyText = '暂无待接单工单'
        } else if (this.activeTab === 'processing') {
          this.orders = allOrders.filter(o => ['processing','pending_confirm'].includes(o.status))
          this.emptyText = '暂无处理中工单'
        } else {
          this.orders = allOrders.filter(o => o.status === 'completed')
          this.emptyText = '暂无已完成工单'
        }
        this.finished = true
      } catch (e) { this.$toast('加载失败') } finally { this.loading = false }
    },
    onCellClick(o) {
      this.currentOrder = o
      if (o.status === 'dispatched') {
        this.engineerForm = { name: '', phone: '' }
        this.showAcceptDialog = true
      } else {
        this.showDetailDialog = true
      }
    },
    onAcceptClose(action) {
      if (action === 'confirm') {
        this.submitAccept()
        return false
      }
      return true
    },
    async submitAccept() {
      const name = (this.engineerForm.name || '').trim()
      const phone = (this.engineerForm.phone || '').trim()
      if (!name) { this.$toast('请填写工程师姓名'); return }
      if (!phone || phone.length < 7) { this.$toast('请填写正确的工程师电话'); return }
      try {
        await acceptOrderByText(this.currentOrder.id, name, phone)
        this.$toast.success('接单成功')
        this.showAcceptDialog = false
        this.loadOrders()
      } catch (e) {
        this.$toast((e && e.response && e.response.data && e.response.data.error) || '接单失败')
      }
    },
    async confirmComplete() {
      try {
        await confirmCompletedApi(this.currentOrder.id, '')
        this.$toast.success('已标记完成')
        this.showDetailDialog = false
        this.loadOrders()
      } catch (e) {
        this.$toast((e && e.response && e.response.data && e.response.data.error) || '操作失败')
      }
    },
  },
}
</script>
<style scoped>
.dealer-orders {
  min-height: 100vh;
  background: var(--color-bg-page);
  padding-top: var(--nav-bar-height);
}

/* ===== 列表卡片 ===== */
.order-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-md);
  margin: var(--space-3) var(--space-4);
  padding: var(--space-4);
  box-shadow: var(--shadow-card);
  cursor: pointer;
  transition: all var(--transition-base);
}
.order-card:active {
  transform: scale(0.99);
  box-shadow: var(--shadow-hover);
}
.card-row-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-2);
}
.order-no {
  font-family: ui-monospace, monospace;
  font-weight: var(--font-semibold);
  font-size: var(--text-md);
  color: var(--color-text);
}
.card-row {
  display: flex;
  align-items: center;
  font-size: var(--text-base);
  color: var(--color-text);
  margin-top: var(--space-1);
  line-height: 1.5;
}
.card-row-meta {
  font-size: var(--text-sm);
  color: var(--color-primary);
  margin-top: var(--space-2);
}
.card-row-meta .van-icon {
  margin-right: var(--space-1);
}
.ilbl {
  color: var(--color-text-tertiary);
  flex-shrink: 0;
  margin-right: var(--space-1);
}
.ival {
  color: var(--color-text);
}
.ival.ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

/* ===== Empty ===== */
.empty-tip {
  padding: var(--space-10) 0;
}

/* ===== Dialogs ===== */
.accept-dialog {
  padding: var(--space-3) var(--space-4);
}
.accept-dialog .hint {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-3);
}
.detail-dialog {
  padding: var(--space-4);
  font-size: var(--text-base);
}
.detail-dialog .row {
  display: flex;
  padding: var(--space-2) 0;
  border-bottom: 1px dashed var(--color-divider);
}
.detail-dialog .row:last-child {
  border-bottom: none;
}
.detail-dialog .k {
  width: 80px;
  flex-shrink: 0;
  color: var(--color-text-tertiary);
}
.detail-dialog .v {
  flex: 1;
  color: var(--color-text);
  word-break: break-all;
}
.action-btns {
  margin-top: var(--space-4);
}
</style>