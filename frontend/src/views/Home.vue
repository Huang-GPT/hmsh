<template>
  <div class="home">
    <div class="header">
      <img src="@/assets/logo.png" alt="红门" class="logo" />
      <h1>红门售后服务</h1>
    </div>
    
    <div class="content">
      <div class="news-section">
        <h2>公司动态</h2>
        <van-cell-group>
          <van-cell title="红门最新产品发布" label="2024-01-15" is-link />
          <van-cell title="售后服务政策更新" label="2024-01-10" is-link />
          <van-cell title="全国服务网点信息" label="2024-01-05" is-link />
        </van-cell-group>
      </div>
      
      <div class="quick-access">
        <h2>快捷入口</h2>
        <van-grid :column-num="4">
          <van-grid-item icon="scan" text="扫码绑定" @click="$router.push('/product/bind')" />
          <van-grid-item icon="orders-o" text="提交工单" @click="$router.push('/product/repair')" />
          <van-grid-item icon="clock-o" text="进度查询" @click="$router.push('/progress')" />
          <van-grid-item icon="warning-o" text="常见故障" @click="$router.push('/faults')" />
        </van-grid>
      </div>
    </div>
    
    <div class="bottom-menu">
      <van-tabbar v-model="activeMenu">
        <van-tabbar-item icon="home-o" to="/">首页</van-tabbar-item>
        <van-tabbar-item icon="service-o" to="/service">品牌服务</van-tabbar-item>
        <van-tabbar-item icon="user-o" to="/user">我的</van-tabbar-item>
      </van-tabbar>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Home',
  data() {
    return {
      activeMenu: 0
    }
  }
}
</script>

<style scoped>
.home {
  min-height: 100vh;
  background: #f5f5f5;
}
.header {
  background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
  color: white;
  padding: 24px;
  text-align: center;
}
.logo {
  width: 60px;
  height: 60px;
  margin-bottom: 12px;
}
.content {
  padding: 16px;
}
.news-section, .quick-access {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}
.news-section h2, .quick-access h2 {
  margin-bottom: 12px;
  font-size: 16px;
}
.bottom-menu {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
}
</style>