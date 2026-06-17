<template>
  <div class="admin-layout">
    <div class="sidebar">
      <div class="logo">
        <h3>红门售后管理</h3>
      </div>
      <div class="menu-list">
        <div
          v-for="(item, index) in menuItems"
          :key="index"
          class="menu-item"
          :class="{ active: activeMenu === index }"
          @click="onMenuClick(index)"
        >
          <van-icon :name="item.icon" size="18" />
          <span>{{ item.title }}</span>
        </div>
      </div>
      <div class="sidebar-footer">
        <van-button size="small" plain type="danger" @click="handleLogout">退出登录</van-button>
      </div>
    </div>
    <div class="main-content">
      <div class="topbar">
        <span class="admin-name">{{ adminName }}</span>
      </div>
      <div class="page-container">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AdminLayout',
  data() {
    return {
      activeMenu: 0,
      adminName: '',
      menuItems: [
        { title: '工作台', icon: 'wap-home-o', path: '/admin/dashboard' },
        { title: '工单管理', icon: 'orders-o', path: '/admin/orders' },
        { title: '用户管理', icon: 'friends-o', path: '/admin/users' },
        { title: '产品管理', icon: 'goods-o', path: '/admin/products' },
        { title: '故障库', icon: 'warning-o', path: '/admin/faults' }
      ]
    }
  },
  created() {
    const user = JSON.parse(localStorage.getItem('admin_user'))
    if (!user) {
      this.$router.push('/admin/login')
      return
    }
    this.adminName = user.nickname || '管理员'
    this.updateActiveMenu()
  },
  watch: {
    $route() {
      this.updateActiveMenu()
    }
  },
  methods: {
    updateActiveMenu() {
      const path = this.$route.path
      const index = this.menuItems.findIndex(item => item.path === path)
      this.activeMenu = index >= 0 ? index : 0
    },
    onMenuClick(index) {
      this.activeMenu = index
      this.$router.push(this.menuItems[index].path)
    },
    handleLogout() {
      localStorage.removeItem('admin_user')
      this.$router.push('/admin/login')
    }
  }
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
  background: #f0f2f5;
}
.sidebar {
  width: 200px;
  background: #001529;
  color: white;
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 100;
}
.logo {
  padding: 20px 16px;
  text-align: center;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.logo h3 {
  color: white;
  margin: 0;
  font-size: 16px;
}
.menu-list {
  flex: 1;
  padding: 8px 0;
}
.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  color: rgba(255,255,255,0.65);
  cursor: pointer;
  transition: all 0.3s;
}
.menu-item:hover {
  color: white;
  background: rgba(255,255,255,0.08);
}
.menu-item.active {
  color: white;
  background: #1976d2;
}
.sidebar-footer {
  padding: 16px;
  text-align: center;
  border-top: 1px solid rgba(255,255,255,0.1);
}
.main-content {
  flex: 1;
  margin-left: 200px;
  display: flex;
  flex-direction: column;
}
.topbar {
  height: 48px;
  background: white;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.admin-name {
  font-size: 14px;
  color: #666;
}
.page-container {
  padding: 20px;
  flex: 1;
}
</style>
