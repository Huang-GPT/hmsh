<template>
  <div class='admin-dealer-orders'>
    <h2 class='page-title'>工单售后</h2>
    <p class='page-sub'>监控所有经销商接单、处理、完成情况</p>

    <div class='filter-bar'>
      <select v-model='filterSp' class='filter-select' @change='loadOrders'>
        <option value=''>全部服务点</option>
        <option v-for='sp in servicePoints' :key='sp.id' :value='sp.id'>{{ sp.name }}</option>
      </select>
    </div>

    <van-tabs v-model='activeTab' @change='loadOrders' sticky>
      <van-tab title='待接单' name='dispatched' />
      <van-tab title='处理中' name='processing' />
      <van-tab title='已完成' name='completed' />
    </van-tabs>

    <div class='order-list'>
      <div v-for='o in orders' :key='o.id' class='order-card' @click='showDetail(o)'>
        <div class='card-header'>
          <span class='order-no'>{{ o.order_no }}</span>
          <van-tag :type='tagType(o.status)' size='medium'>{{ statusMap[o.status] || o.status }}</van-tag>
        </div>
        <div class='card-body'>
          <div class='row'><span class='k'>服务点</span><span class='v'>{{ o.service_point_name || '—' }}</span></div>
          <div class='row'><span class='k'>工程师</span><span class='v'>{{ o.assigned_engineer_name || '—' }} {{ o.assigned_engineer_phone || '' }}</span></div>
          <div class='row'><span class='k'>产品</span><span class='v'>{{ o.product_name || o.product_model || '—' }}</span></div>
          <div class='row'><span class='k'>客户</span><span class='v'>{{ o.contact_name }} {{ o.contact_phone }}</span></div>
          <div class='row'><span class='k'>预约时间</span><span class='v'>{{ o.appointment_date }} {{ o.appointment_period }}</span></div>
        </div>
      </div>
      <van-empty v-if='!loading && orders.length === 0' description='暂无工单' />
    </div>

    <van-dialog v-model='showDetailDialog' title='工单售后详情' :show-confirm-button='false' close-on-click-overlay>
      <div class='detail-dialog' v-if='currentOrder'>
        <div class='row'><span class='k'>工单号</span><span class='v'>{{ currentOrder.order_no }}</span></div>
        <div class='row'><span class='k'>状态</span><span class='v'>{{ statusMap[currentOrder.status] || currentOrder.status }}</span></div>
        <div class='row'><span class='k'>服务点</span><span class='v'>{{ currentOrder.service_point_name }}</span></div>
        <div class='row'><span class='k'>工程师</span><span class='v'>{{ currentOrder.assigned_engineer_name }} {{ currentOrder.assigned_engineer_phone }}</span></div>
        <div class='row'><span class='k'>产品</span><span class='v'>{{ currentOrder.product_name || currentOrder.product_model }}</span></div>
        <div class='row'><span class='k'>客户</span><span class='v'>{{ currentOrder.contact_name }} {{ currentOrder.contact_phone }}</span></div>
        <div class='row'><span class='k'>故障</span><span class='v'>{{ currentOrder.fault_type }}</span></div>
        <div class='row'><span class='k'>地址</span><span class='v'>{{ currentOrder.fault_address }}</span></div>
        <div class='row'><span class='k'>预约时间</span><span class='v'>{{ currentOrder.appointment_date }} {{ currentOrder.appointment_period }}</span></div>
        <div class='row'><span class='k'>创建</span><span class='v'>{{ currentOrder.created_at }}</span></div>
        <div class='action-btns' v-if="currentOrder.status === 'dispatched'">
          <van-button type='primary' block @click='adminAccept'>代为接单（填工程师）</van-button>
        </div>
      </div>
    </van-dialog>

    <van-dialog v-model='showAcceptDialog' title='总部代接单' show-cancel-button :before-close='onAcceptClose'>
      <div class='accept-dialog'>
        <div class='hint'>填写本次上门工程师的姓名和联系电话</div>
        <van-cell-group inset>
          <van-field v-model='engineerForm.name' label='工程师姓名' placeholder='请输入' maxlength='20' />
          <van-field v-model='engineerForm.phone' label='工程师电话' placeholder='11 位手机号' type='tel' maxlength='11' />
        </van-cell-group>
      </div>
    </van-dialog>
  </div>
</template>
<script>
import { getAllDealerOrders, getServicePoints, acceptOrderByText } from '@/api/admin'
export default {
  name: 'AdminDealerOrders',
  data() {
    return {
      activeTab: 'dispatched',
      filterSp: '',
      servicePoints: [],
      orders: [],
      loading: false,
      showDetailDialog: false,
      showAcceptDialog: false,
      currentOrder: null,
      engineerForm: { name: '', phone: '' },
      statusMap: {
        dispatched: '待接单',
        assigned_engineer: '已分配',
        processing: '处理中',
        pending_confirm: '待确认',
        completed: '已完成',
        closed: '已关闭',
        cancelled: '已撤销',
      },
    }
  },
  async created() {
    try {
      const spRes = await getServicePoints()
      this.servicePoints = (spRes.data || {}).items || (spRes.data || {}).service_points || (spRes.data || []).items || []
    } catch (e) { /* ignore */ }
    this.loadOrders()
  },
  methods: {
    tagType(s) {
      const m = {
        dispatched: 'primary',
        assigned_engineer: 'warning',
        processing: 'cyan',
        pending_confirm: 'success',
        completed: 'success',
        closed: 'default',
        cancelled: 'danger',
      }
      return m[s] || 'default'
    },
    async loadOrders() {
      this.loading = true
      try {
        const params = { status: this.activeTab }
        if (this.filterSp) params.service_point_id = this.filterSp
        const res = await getAllDealerOrders(params)
        this.orders = (res.data || {}).orders || []
      } catch (e) {
        this.$toast('加载失败')
        this.orders = []
      } finally { this.loading = false }
    },
    showDetail(o) {
      this.currentOrder = o
      this.showDetailDialog = true
    },
    adminAccept() {
      this.engineerForm = { name: '', phone: '' }
      this.showAcceptDialog = true
    },
    onAcceptClose(action) {
      if (action === 'confirm') {
        this.submitAdminAccept()
        return false
      }
      return true
    },
    async submitAdminAccept() {
      const name = (this.engineerForm.name || '').trim()
      const phone = (this.engineerForm.phone || '').trim()
      if (!name) { this.$toast('请填写工程师姓名'); return }
      if (!phone || phone.length < 7) { this.$toast('请填写正确的工程师电话'); return }
      try {
        await acceptOrderByText(this.currentOrder.id, name, phone)
        this.$toast.success('已代为接单，工单进入处理中')
        this.showAcceptDialog = false
        this.showDetailDialog = false
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
.admin-dealer-orders { padding: 0 16px 60px; }
.page-title { font-size: 22px; font-weight: 600; color: #323233; margin: 16px 0 4px; }
.page-sub { font-size: 13px; color: #969799; margin: 0 0 16px; }
.filter-bar { margin-bottom: 12px; }
.filter-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ebedf0;
  border-radius: 4px;
  font-size: 14px;
  background: #fff;
}
.order-list { margin-top: 12px; }
.order-card {
  background: #fff;
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  cursor: pointer;
}
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.order-no { font-weight: 600; color: #323233; font-size: 15px; }
.card-body .row { display: flex; padding: 4px 0; font-size: 13px; }
.card-body .row .k { width: 70px; color: #969799; flex-shrink: 0; }
.card-body .row .v { flex: 1; color: #323233; }
.detail-dialog { padding: 8px 16px; max-height: 60vh; overflow-y: auto; }
.detail-dialog .row { display: flex; padding: 6px 0; border-bottom: 1px solid #f7f7f7; font-size: 14px; }
.detail-dialog .row .k { width: 80px; color: #969799; flex-shrink: 0; }
.detail-dialog .row .v { flex: 1; color: #323233; word-break: break-all; }
.accept-dialog { padding: 16px; }
.accept-dialog .hint { font-size: 13px; color: #969799; margin-bottom: 12px; text-align: center; }
.action-btns { margin: 16px 0 8px; }
</style>
