<template>
  <div class="service">
    <h1>品牌服务</h1>
    
    <van-grid :column-num="2" :gutter="10">
      <van-grid-item icon="scan" text="产品绑定" to="/product/bind" />
      <van-grid-item icon="orders-o" text="产品维修" to="/product/repair" />
      <van-grid-item icon="clock-o" text="进度查询" to="/progress" />
      <van-grid-item icon="warning-o" text="常见故障" to="/faults" />
    </van-grid>
  </div>
</template>

<script>
export default {
  name: 'Service'
}
</script>

<style scoped>
.service {
  padding: 16px;
}
.service h1 {
  margin-bottom: 24px;
}
</style>