<template>
  <div class="admin-layout">
    <div class="sidebar">
      <div class="logo">
        <div class="logo-mark">
          <van-icon name="setting-o" size="22" color="#fff" />
        </div>
        <div class="logo-text">
          <h3>红门售后管理</h3>
          <span class="logo-sub">After-Sales System</span>
        </div>
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
        <div class="topbar-title">
          <van-icon :name="currentMenuIcon" class="topbar-icon" />
          <span>{{ currentMenuTitle }}</span>
        </div>
        <div class="topbar-user">
          <div class="user-avatar">
            {{ (adminName || 'U').charAt(0) }}
          </div>
          <div class="user-meta">
            <span class="admin-name">{{ adminName }}</span>
            <span v-if="adminRole" class="admin-role">{{ adminRole }}</span>
          </div>
        </div>
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
    },
    currentMenuTitle() {
      const m = this.menuItems.find(i => i.path === this.activeMenu)
      return m ? m.title : '红门售后管理'
    },
    currentMenuIcon() {
      const m = this.menuItems.find(i => i.path === this.activeMenu)
      return m ? m.icon : 'wap-home-o'
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
  background: var(--color-bg-page);
}

/* ===== 侧边栏 ===== */
.sidebar {
  width: var(--sidebar-width);
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
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 18px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.logo-mark {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--brand-400), var(--brand-600));
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(25, 137, 250, 0.4);
}
.logo-text h3 {
  color: white;
  margin: 0;
  font-size: 15px;
  font-weight: var(--font-semibold);
  line-height: 1.3;
}
.logo-sub {
  display: block;
  font-size: var(--text-xs);
  color: rgba(255,255,255,0.4);
  margin-top: 1px;
}

/* ===== 菜单 ===== */
.menu-list {
  flex: 1;
  padding: var(--space-2) 0;
  overflow-y: auto;
}
.menu-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 11px 20px;
  color: rgba(255,255,255,0.65);
  cursor: pointer;
  transition: all var(--transition-base);
  font-size: var(--text-base);
  position: relative;
}
.menu-item:hover {
  color: white;
  background: rgba(255,255,255,0.05);
}
.menu-item.active {
  color: white;
  background: var(--brand-500);
}
.menu-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: #fff;
}
.menu-empty {
  padding: var(--space-4) 20px;
  color: rgba(255,255,255,0.4);
  font-size: var(--text-sm);
}
.sidebar-footer {
  padding: var(--space-3);
  text-align: center;
  border-top: 1px solid rgba(255,255,255,0.1);
}

/* ===== 主内容区 ===== */
.main-content {
  flex: 1;
  margin-left: var(--sidebar-width);
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* ===== 顶部 bar ===== */
.topbar {
  height: var(--top-bar-height);
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-6);
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  position: sticky;
  top: 0;
  z-index: 50;
}
.topbar-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--color-text);
}
.topbar-icon {
  color: var(--color-primary);
  font-size: var(--text-lg);
}
.topbar-user {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--brand-400), var(--brand-600));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--font-semibold);
  font-size: var(--text-base);
  box-shadow: 0 2px 6px rgba(25, 137, 250, 0.25);
}
.user-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}
.admin-name {
  font-size: var(--text-base);
  font-weight: var(--font-medium);
  color: var(--color-text);
}
.admin-role {
  font-size: var(--text-xs);
  color: var(--color-primary);
  background: var(--brand-50);
  padding: 1px 6px;
  border-radius: var(--radius-xs);
  margin-top: 2px;
  align-self: flex-start;
}

/* ===== 内容容器 ===== */
.page-container {
  padding: var(--space-5);
  flex: 1;
}
</style>