<template>
  <div class="admin-orders">
    <h3>工单管理</h3>

    <div class="filter-bar">
      <van-search v-model="keyword" placeholder="搜索工单号/联系人/手机号" @search="loadOrders" shape="round" />
      <van-dropdown-menu>
        <van-dropdown-item v-model="statusFilter" :options="statusOptions" @change="loadOrders" />
      </van-dropdown-menu>
    </div>

    <van-cell-group class="order-list">
      <van-cell
        v-for="order in orders"
        :key="order.id"
        :title="order.order_no"
        :label="order.product_model + ' | ' + order.fault_type"
        :value="statusMap[order.status]"
        is-link
        @click="showDetail(order)"
      >
        <template #right-icon>
          <van-tag :type="tagType(order.status)" size="medium">{{ statusMap[order.status] }}</van-tag>
        </template>
      </van-cell>
    </van-cell-group>

    <van-empty v-if="orders.length === 0" description="暂无工单" />

    <!-- 工单详情弹窗 -->
    <van-dialog v-model="showDetailDialog" title="工单详情" :show-cancel-button="false" confirm-button-text="关闭">
      <div class="order-detail" v-if="currentOrder">
        <van-cell-group>
          <van-cell title="工单号" :value="currentOrder.order_no" />
          <van-cell title="产品型号" :value="currentOrder.product_model" />
          <van-cell title="序列号" :value="currentOrder.product_serial" />
          <van-cell title="故障类型" :value="currentOrder.fault_type" />
          <van-cell title="故障描述" :value="currentOrder.fault_desc" />
          <van-cell title="联系人" :value="currentOrder.contact_name" />
          <van-cell title="联系电话" :value="currentOrder.contact_phone" />
          <van-cell title="创建时间" :value="currentOrder.created_at" />
        </van-cell-group>

        <div class="action-section" v-if="currentOrder.status !== 'completed' && currentOrder.status !== 'closed' && currentOrder.status !== 'cancelled'">
          <h4>操作</h4>
          <van-button v-if="currentOrder.status === 'pending_accept' || currentOrder.status === 'pending_dispatch'" type="primary" size="small" @click="showAssignDialog">分配工单</van-button>
          <van-button v-if="currentOrder.status === 'dispatched'" type="primary" size="small" @click="showAssignDialog">分配工程师</van-button>
          <van-button v-if="currentOrder.status === 'assigned_engineer'" type="warning" size="small" @click="startProcessing">开始处理</van-button>
          <van-button v-if="currentOrder.status === 'processing'" type="success" size="small" @click="completeOrder">处理完成</van-button>
          <van-button v-if="currentOrder.status === 'pending_confirm'" type="info" size="small" @click="confirmCompleted">确认完成</van-button>
          <van-button type="danger" plain size="small" @click="rejectCurrent">关闭工单</van-button>
        </div>
      </div>
    </van-dialog>

    <!-- 分配工单弹窗 -->
    <van-dialog v-model="showAssign" title="分配工单" show-cancel-button @confirm="handleAssign">
      <van-field v-model="remark" label="备注" placeholder="输入备注" />
      <van-picker
        :columns="staffList.map(s => ({ text: s.nickname, value: s.id }))"
        @confirm="onStaffPick"
        visible-item-num="5"
      />
    </van-dialog>
  </div>
</template>

<script>
import { getAllOrders, assignOrder, updateOrderStatus, getServiceStaff, startProcessingOrder, completeOrder as completeOrderApi, rejectOrder } from '@/api/admin'

export default {
  name: 'AdminOrders',
  data() {
    return {
      orders: [],
      keyword: '',
      statusFilter: '',
      showDetailDialog: false,
      showAssign: false,
      currentOrder: null,
      staffList: [],
      selectedStaff: null,
      remark: '',
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
      },
      statusOptions: [
        { text: '全部状态', value: '' },
        { text: '待受理', value: 'pending_accept' },
        { text: '待派单', value: 'pending_dispatch' },
        { text: '已派单', value: 'dispatched' },
        { text: '已分配工程师', value: 'assigned_engineer' },
        { text: '处理中', value: 'processing' },
        { text: '待确认', value: 'pending_confirm' },
        { text: '已完成', value: 'completed' },
        { text: '已关闭', value: 'closed' },
        { text: '已撤销', value: 'cancelled' }
      ]
    }
  },
  created() {
    this.loadOrders()
    this.loadStaff()
  },
  methods: {
    async loadOrders() {
      try {
        const res = await getAllOrders({ status: this.statusFilter, keyword: this.keyword })
        this.orders = res.data.orders || []
      } catch (e) {
        console.error(e)
      }
    },
    async loadStaff() {
      try {
        const res = await getServiceStaff()
        this.staffList = res.data.users || []
      } catch (e) {
        console.error(e)
      }
    },
    tagType(status) {
      const map = {
        'pending_accept': 'warning',
        'pending_dispatch': 'orange',
        'dispatched': 'primary',
        'assigned_engineer': 'primary',
        'processing': 'primary',
        'pending_confirm': 'success',
        'completed': 'default',
        'closed': 'danger',
        'cancelled': 'danger'
      }
      return map[status] || 'default'
    },
    showDetail(order) {
      this.currentOrder = order
      this.showDetailDialog = true
    },
    showAssignDialog() {
      this.showAssign = true
    },
    onStaffPick(val) {
      this.selectedStaff = val.value
    },
    async handleAssign() {
      if (!this.selectedStaff) {
        this.$toast('请选择处理人')
        return
      }
      try {
        await assignOrder(this.currentOrder.id, this.selectedStaff)
        this.$toast.success('分配成功')
        this.showAssign = false
        this.showDetailDialog = false
        this.loadOrders()
      } catch (e) {
        this.$toast('操作失败')
      }
    },
    async startProcessing() {
      try {
        await startProcessingOrder(this.currentOrder.id, this.remark)
        this.$toast.success('已开始处理')
        this.showDetailDialog = false
        this.loadOrders()
      } catch (e) {
        this.$toast(e?.response?.data?.error || '操作失败')
      }
    },
    async completeOrder() {
      try {
        await completeOrderApi(this.currentOrder.id, this.remark)
        this.$toast.success('已处理完成，等待客户确认')
        this.showDetailDialog = false
        this.loadOrders()
      } catch (e) {
        this.$toast(e?.response?.data?.error || '操作失败')
      }
    },
    async confirmCompleted() {
      try {
        await updateOrderStatus(this.currentOrder.id, 'completed', this.remark)
        this.$toast.success('已确认完成')
        this.showDetailDialog = false
        this.loadOrders()
      } catch (e) {
        this.$toast(e?.response?.data?.error || '操作失败')
      }
    },
    async rejectCurrent() {
      const reason = window.prompt('请输入关闭原因', this.remark || '')
      if (!reason) return
      try {
        await rejectOrder(this.currentOrder.id, reason)
        this.$toast.success('已关闭')
        this.showDetailDialog = false
        this.loadOrders()
      } catch (e) {
        this.$toast(e?.response?.data?.error || '操作失败')
      }
    }
  }
}
</script>

<style scoped>
.admin-orders h3 {
  margin: 0 0 16px 0;
  color: #333;
}
.filter-bar {
  background: white;
  border-radius: 8px;
  padding: 8px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.order-list {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.order-detail {
  padding: 16px;
}
.action-section {
  padding: 16px;
  border-top: 1px solid #eee;
}
.action-section h4 {
  margin: 0 0 12px 0;
  color: #333;
}
.action-section .van-button {
  margin-right: 8px;
}
</style>
