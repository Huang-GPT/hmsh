<template>
  <div class="service">
    <div class="header">
      <img src="@/assets/logo.svg" alt="红门" class="logo" />
      <h1>红门售后服务</h1>
    </div>
    
    <div class="menu-grid">
      <div class="menu-item" @click="$router.push('/product/bind')">
        <van-icon name="scan" size="40" color="#1976d2" />
        <span>产品绑定</span>
      </div>
      <div class="menu-item" @click="$router.push('/product/repair')">
        <van-icon name="orders-o" size="40" color="#1976d2" />
        <span>产品维修</span>
      </div>
      <div class="menu-item" @click="$router.push('/progress')">
        <van-icon name="clock-o" size="40" color="#1976d2" />
        <span>进度查询</span>
      </div>
      <div class="menu-item" @click="$router.push('/faults')">
        <van-icon name="warning-o" size="40" color="#1976d2" />
        <span>常见故障</span>
      </div>
    </div>
    
    <div class="bottom-menu">
      <van-tabbar v-model="activeMenu">
        <van-tabbar-item icon="service-o" to="/">品牌服务</van-tabbar-item>
        <van-tabbar-item icon="user-o" to="/user">我的</van-tabbar-item>
      </van-tabbar>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Service',
  data() {
    return {
      activeMenu: 0
    }
  }
}
</script>

<style scoped>
.service {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 50px;
}
.header {
  background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
  color: white;
  padding: 40px 20px;
  text-align: center;
}
.logo {
  width: 80px;
  height: 80px;
  margin-bottom: 16px;
}
.header h1 {
  font-size: 24px;
  margin: 0;
}
.menu-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  padding: 24px;
}
.menu-item {
  background: white;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  cursor: pointer;
  transition: transform 0.2s;
}
.menu-item:active {
  transform: scale(0.95);
}
.menu-item span {
  display: block;
  margin-top: 12px;
  font-size: 16px;
  color: #333;
}
.bottom-menu {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
}
</style>