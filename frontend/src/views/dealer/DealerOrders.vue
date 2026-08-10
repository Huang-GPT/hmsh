<template>
  <div class='dealer-orders'>
    <van-nav-bar title='工单服务' left-arrow @click-left="$router.push('/admin/dashboard')" fixed />
    <van-tabs v-model='activeTab' @change='loadOrders' sticky>
      <van-tab title='待接单' name='dispatched' />
      <van-tab title='处理中' name='processing' />
      <van-tab title='已完成' name='completed' />
    </van-tabs>
    <van-list v-model='loading' :finished='finished' finished-text='没有更多了' @load='loadOrders'>
      <van-cell v-for='o in orders' :key='o.id' :title='o.order_no' :label="(o.product_name || o.product_model || '')" @click='onCellClick(o)'>
        <template #icon><van-tag :type='tagType(o.status)' size='small'>{{statusMap[o.status]}}</van-tag></template>
        <template #right-icon><span v-if='o.assigned_engineer_name' class='eng-name'>{{o.assigned_engineer_name}}</span></template>
      </van-cell>
    </van-list>
    <van-empty v-if='!loading && orders.length === 0' :description='emptyText' />

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
        <div class='action-btns' v-if="currentOrder.status === 'processing' || currentOrder.status === 'pending_confirm'">
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
        this.$toast.success('接单成功，工单已进入处理中')
        this.showAcceptDialog = false
        this.activeTab = 'processing'
        this.finished = false
        this.loadOrders()
      } catch (e) {
        const err = (e && e.response && e.response.data && e.response.data.error) || '接单失败'
        this.$toast(err)
      }
    },
    async confirmComplete() {
      try {
        await confirmCompletedApi(this.currentOrder.id, '经销商确认完成')
        this.$toast.success('已标记完成')
        this.showDetailDialog = false
        this.finished = false
        this.loadOrders()
      } catch (e) {
        const err = (e && e.response && e.response.data && e.response.data.error) || '操作失败'
        this.$toast(err)
      }
    }
  }
}
</script>
<style scoped>
.dealer-orders { background: #f5f5f5; min-height: 100vh; padding-bottom: 60px; }
.accept-dialog { padding: 16px; }
.accept-dialog .hint { font-size: 13px; color: #969799; margin-bottom: 12px; text-align: center; }
.detail-dialog { padding: 12px 16px; }
.detail-dialog .row { display: flex; padding: 8px 0; border-bottom: 1px solid #f2f2f2; font-size: 14px; }
.detail-dialog .row .k { width: 80px; color: #969799; flex-shrink: 0; }
.detail-dialog .row .v { flex: 1; color: #323233; word-break: break-all; }
.action-btns { margin: 16px 0 8px; }
.eng-name { font-size: 12px; color: #1989fa; }
</style>
