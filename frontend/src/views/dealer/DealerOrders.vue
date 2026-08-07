<template>
  <div class='dealer-orders'>
    <van-nav-bar title='经销商工单' left-arrow @click-left="$router.push('/admin/dashboard')" fixed />
    <van-tabs v-model='activeTab' @change='loadOrders' sticky>
      <van-tab title='待分配' name='dispatched' />
      <van-tab title='处理中' name='processing' />
      <van-tab title='已完成' name='completed' />
    </van-tabs>
    <van-list v-model='loading' :finished='finished' finished-text='没有更多了' @load='loadOrders'>
      <van-cell v-for='o in orders' :key='o.id' :title='o.order_no' :label="(o.product_name || o.product_model || '')" @click='showDetail(o)'>
        <template #icon><van-tag :type='tagType(o.status)' size='small'>{{statusMap[o.status]}}</van-tag></template>
        <template #right-icon><span v-if='o.assigned_engineer_name' class='eng-name'>{{o.assigned_engineer_name}}</span></template>
      </van-cell>
    </van-list>
    <van-empty v-if='!loading && orders.length === 0' description='暂无工单' />
  </div>
</template>
<script>
import { getServicePointOrders, assignEngineerByText, confirmCompletedApi } from '@/api/admin'
export default {
  name: 'DealerOrders',
  data() {
    return {
      activeTab: 'dispatched', orders: [], loading: false, finished: false,
      showAssignDialog: false, showDetailDialog: false, currentOrder: null,
      engineerForm: { name: '', phone: '' },
      statusMap: { 'dispatched': '已派单', 'assigned_engineer': '已分配', 'processing': '处理中', 'pending_confirm': '待确认', 'completed': '已完成' }
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
        if (this.activeTab === 'dispatched') this.orders = allOrders.filter(o => o.status === 'dispatched')
        else if (this.activeTab === 'processing') this.orders = allOrders.filter(o => ['assigned_engineer','processing','pending_confirm'].includes(o.status))
        else this.orders = allOrders.filter(o => o.status === 'completed')
        this.finished = true
      } catch (e) { this.$toast('加载失败') } finally { this.loading = false }
    },
    showDetail(o) { this.currentOrder = o; this.showDetailDialog = true },
    async submitAssign() {
      if (!this.engineerForm.name || !this.engineerForm.phone) { this.$toast('请填写完整信息'); return }
      try { await assignEngineerByText(this.currentOrder.id, this.engineerForm.name, this.engineerForm.phone); this.$toast.success('分配成功'); this.showAssignDialog = false; this.loadOrders() }
      catch (e) { const err = (e && e.response && e.response.data && e.response.data.error) || '操作失败'; this.$toast(err) }
    },
    async confirmComplete() {
      try { await confirmCompletedApi(this.currentOrder.id, '经销商确认完成'); this.$toast.success('已确认完成'); this.showDetailDialog = false; this.loadOrders() }
      catch (e) { this.$toast('操作失败') }
    }
  }
}
</script>
<style scoped>
.dealer-orders { background: #f5f5f5; min-height: 100vh; padding-bottom: 20px; }
.assign-dialog, .detail-dialog { padding: 16px; }
.assign-dialog h4 { margin: 0 0 16px; text-align: center; font-size: 16px; color: #323233; }
.dialog-btns { display: flex; flex-direction: column; gap: 8px; margin-top: 16px; }
.action-btns { margin: 12px 0; }
.eng-name { font-size: 12px; color: #1989fa; }
</style>