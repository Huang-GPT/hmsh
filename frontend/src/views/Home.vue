<template>
  <div class="user-center">
    <div class="header">
      <van-icon name="user-o" size="60" color="white" />
      <h2>我的</h2>
    </div>
    
    <div class="content">
      <van-cell-group>
        <van-cell title="个人信息" is-link />
        <van-cell title="我的工单" is-link to="/progress" />
        <van-cell title="绑定产品" is-link to="/product/bind" />
        <van-cell title="系统设置" is-link />
      </van-cell-group>
    </div>
  </div>
</template>

<script>
export default {
  name: 'UserCenter'
}
</script>

<style scoped>
.user-center {
  min-height: 100vh;
  background: #f5f5f5;
}
.header {
  background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
  color: white;
  padding: 40px 20px;
  text-align: center;
}
.header h2 {
  margin: 16px 0 0 0;
  font-size: 20px;
}
.content {
  padding: 16px;
}
</style>