<template>
  <div class="admin-layout">
    <div class="sidebar">
      <div class="logo">
        <h3>红门售后管理</h3>
      </div>
      <div class="menu-list">
        <div
          v-for="(item, index) in menuItems"
          :key="item.path"
          class="menu-item"
          :class="{ active: activeMenu === item.path }"
          @click="onMenuClick(item)"
        >
          <van-icon :name="item.icon" size="18" />
          <span>{{ item.title }}</span>
        </div>
        <div v-if="!menuItems.length" class="menu-empty">
          暂无可用菜单
        </div>
      </div>
      <div class="sidebar-footer">
        <van-button size="small" plain type="danger" @click="handleLogout">退出登录</van-button>
      </div>
    </div>
    <div class="main-content">
      <div class="topbar">
        <span class="admin-name">{{ adminName }}</span>
        <span v-if="adminRole" class="admin-role">[{{ adminRole }}]</span>
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
      activeMenu: '/admin/dashboard',
      adminName: '',
      adminRole: '',
      // 每个菜单项对应一个 permission code；不匹配的菜单不渲染
      allMenuItems: [
        { title: '工作台',   icon: 'wap-home-o',   path: '/admin/dashboard',      permission: 'dashboard:view' },
        { title: '工单管理', icon: 'orders-o',     path: '/admin/orders',         permission: 'order:view' },
        { title: '工单售后', icon: 'after-sale-o', path: '/admin/dealer-orders',  permission: 'dealer_order:view' },
        { title: '用户管理', icon: 'friends-o',    path: '/admin/users',          permission: 'user:view' },
        { title: '角色管理', icon: 'manager-o',    path: '/admin/roles',          permission: 'role:view' },
        { title: '服务点维护', icon: 'location-o', path: '/admin/service-points', permission: 'service_point:view' },
        { title: '产品管理', icon: 'goods-o',      path: '/admin/products',       permission: 'product:view' },
        { title: '绑定记录', icon: 'cluster-o',    path: '/admin/bindings',       permission: 'binding:view' },
        { title: '故障库',   icon: 'warning-o',    path: '/admin/faults',         permission: 'fault:view' }
      ]
    }
  },
  computed: {
    /** 根据当前用户的 permissions 过滤菜单；
     *  没权限的菜单完全不渲染（DOM 里都没有） */
    menuItems() {
      const perms = this.userPermissions
      if (!perms || !perms.length) {
        // 没拿到 permissions 时只显示工作台（避免完全空白）
        return this.allMenuItems.filter(i => i.permission === 'dashboard:view')
      }
      // admin 角色显示全部（防御性，正常不会有 admin 没全权限）
      if (this.adminRole === 'admin') {
        return this.allMenuItems
      }
      return this.allMenuItems.filter(i => perms.includes(i.permission))
    },
    userPermissions() {
      const raw = localStorage.getItem('admin_user')
      if (!raw) return []
      try {
        const u = JSON.parse(raw)
        return Array.isArray(u.permissions) ? u.permissions : []
      } catch (e) {
        return []
      }
    }
  },
  created() {
    const user = this.readUser()
    if (!user || !this.readToken()) {
      this.$router.push('/admin/login')
      return
    }
    this.adminName = user.nickname || '管理员'
    this.adminRole = user.role || ''
    this.updateActiveMenu()
  },
  watch: {
    $route() {
      this.updateActiveMenu()
    }
  },
  methods: {
    readUser() {
      const raw = localStorage.getItem('admin_user')
      if (!raw) return null
      try { return JSON.parse(raw) } catch (e) { return null }
    },
    readToken() {
      return localStorage.getItem('admin_token') || ''
    },
    updateActiveMenu() {
      const path = this.$route.path
      // 当前路径不在可见菜单里（被过滤掉了），高亮保留给工作台
      if (!this.menuItems.some(i => i.path === path)) {
        this.activeMenu = '/admin/dashboard'
      } else {
        this.activeMenu = path
      }
    },
    onMenuClick(item) {
      this.activeMenu = item.path
      this.$router.push(item.path)
    },
    handleLogout() {
      localStorage.removeItem('admin_user')
      localStorage.removeItem('admin_token')
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
  flex-direction: flex-start;
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
.menu-empty {
  padding: 16px 20px;
  color: rgba(255,255,255,0.4);
  font-size: 13px;
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
  gap: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.admin-name {
  font-size: 14px;
  color: #666;
}
.admin-role {
  font-size: 12px;
  color: #1976d2;
  background: rgba(25,118,210,0.08);
  padding: 2px 8px;
  border-radius: 4px;
}
.page-container {
  padding: 20px;
  flex: 1;
}
</style>
