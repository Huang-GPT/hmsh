<template>
  <div class="progress-query">
    <h1>进度查询</h1>
    
    <van-tabs v-model="activeStatus" @change="onStatusChange">
      <van-tab title="全部" name="" />
      <van-tab title="待受理" name="pending_accept" />
      <van-tab title="待派单" name="pending_dispatch" />
      <van-tab title="处理中" name="processing" />
      <van-tab title="待确认" name="pending_confirm" />
      <van-tab title="已完成" name="completed" />
    </van-tabs>
    
    <van-list>
      <van-cell-group>
        <van-cell
          v-for="order in orders"
          :key="order.id"
          :title="order.order_no"
          :label="order.fault_type"
          :value="statusText[order.status]"
          is-link
          @click="viewDetail(order.id)"
        />
      </van-cell-group>
    </van-list>
    
    <van-empty v-if="orders.length === 0" description="暂无工单" />
    
    <van-popup v-model="showDetail" position="bottom" :style="{ height: '80%' }">
      <div class="order-detail" v-if="orderDetail">
        <h2>工单详情</h2>
        <van-cell title="工单编号" :value="orderDetail.order.order_no" />
        <van-cell title="故障类型" :value="orderDetail.order.fault_type" />
        <van-cell title="故障描述" :value="orderDetail.order.fault_desc" />
        <van-cell title="当前状态" :value="statusText[orderDetail.order.status]" />
        <van-cell title="联系人" :value="orderDetail.order.contact_name" />
        <van-cell title="联系电话" :value="orderDetail.order.contact_phone" />
        
        <h3>处理记录</h3>
        <van-steps direction="vertical" :active="orderDetail.logs.length - 1">
          <van-step v-for="(log, index) in orderDetail.logs" :key="index">
            <h4>{{ statusText[log.to_status] }}</h4>
            <p>{{ log.remark }}</p>
            <p>{{ log.created_at }}</p>
          </van-step>
        </van-steps>
      </div>
    </van-popup>
  </div>
</template>

<script>
import { getUserOrders, getOrderDetail } from '@/api/workOrders'

export default {
  name: 'ProgressQuery',
  data() {
    return {
      activeStatus: '',
      orders: [],
      showDetail: false,
      orderDetail: null,
        statusText: {
        pending_accept: '待受理',
        pending_dispatch: '待派单',
        dispatched: '已派单',
        assigned_engineer: '已分配工程师',
        processing: '处理中',
        pending_confirm: '待确认',
        completed: '已完成',
        closed: '已关闭',
        cancelled: '已撤销'
      }
    }
  },
  created() {
    this.loadOrders()
  },
  methods: {
    onStatusChange(status) {
      this.activeStatus = status
      this.loadOrders()
    },
    async loadOrders() {
      try {
        const res = await getUserOrders(this.$store.state.user.id, this.activeStatus)
        this.orders = res.data.orders
      } catch (error) {
        console.error('加载工单列表失败', error)
      }
    },
    async viewDetail(orderId) {
      try {
        const res = await getOrderDetail(orderId)
        this.orderDetail = res.data
        this.showDetail = true
      } catch (error) {
        this.$toast.fail('加载详情失败')
      }
    }
  }
}
</script>

<style scoped>
.progress-query {
  padding: 16px;
}
.order-detail {
  padding: 16px;
}
.order-detail h2 {
  margin-bottom: 16px;
}
.order-detail h3 {
  margin-top: 16px;
  margin-bottom: 8px;
}
</style>