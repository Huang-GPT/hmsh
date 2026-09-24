<template>
  <div class="service">
    <!-- 顶部品牌头部 -->
    <div class="header">
      <div class="header-bg header-bg-1"></div>
      <div class="header-bg header-bg-2"></div>
      <img src="@/assets/logo.svg" alt="红门" class="logo" />
      <h1>红门售后服务</h1>
      <p class="header-sub">专业 · 高效 · 贴心</p>
    </div>

    <!-- 主菜单网格 -->
    <div class="menu-grid">
      <div class="menu-item menu-item-scan" @click="$router.push('/product/bind')">
        <div class="menu-icon-wrap">
          <van-icon name="scan" size="36" color="#fff" />
        </div>
        <span class="menu-title">产品绑定</span>
        <span class="menu-desc">绑定您的产品</span>
      </div>
      <div class="menu-item menu-item-repair" @click="$router.push('/product/repair')">
        <div class="menu-icon-wrap">
          <van-icon name="orders-o" size="36" color="#fff" />
        </div>
        <span class="menu-title">产品维修</span>
        <span class="menu-desc">一键申请报修</span>
      </div>
      <div class="menu-item menu-item-progress" @click="$router.push('/progress')">
        <div class="menu-icon-wrap">
          <van-icon name="clock-o" size="36" color="#fff" />
        </div>
        <span class="menu-title">进度查询</span>
        <span class="menu-desc">实时查看处理</span>
      </div>
      <div class="menu-item menu-item-faults" @click="$router.push('/faults')">
        <div class="menu-icon-wrap">
          <van-icon name="warning-o" size="36" color="#fff" />
        </div>
        <span class="menu-title">常见故障</span>
        <span class="menu-desc">自助排查问题</span>
      </div>
    </div>

    <!-- 底部 Tab -->
    <div class="bottom-menu">
      <van-tabbar v-model="activeMenu" active-color="#1989fa">
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
  background: var(--color-bg-page);
  padding-bottom: var(--tab-bar-height);
}

/* ===== 顶部品牌头部 ===== */
.header {
  position: relative;
  background: linear-gradient(135deg, var(--brand-400), var(--brand-600));
  color: white;
  padding: 56px 20px 48px;
  text-align: center;
  overflow: hidden;
}
.header-bg {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
}
.header-bg-1 {
  width: 220px; height: 220px;
  top: -80px; right: -60px;
}
.header-bg-2 {
  width: 140px; height: 140px;
  bottom: -60px; left: -40px;
  background: rgba(255, 255, 255, 0.06);
}
.logo {
  position: relative;
  width: 72px;
  height: 72px;
  margin-bottom: var(--space-3);
  background: rgba(255, 255, 255, 0.15);
  border-radius: var(--radius-lg);
  padding: 8px;
  backdrop-filter: blur(10px);
}
.header h1 {
  position: relative;
  font-size: var(--text-2xl);
  font-weight: var(--font-semibold);
  margin: 0;
  letter-spacing: 1px;
}
.header-sub {
  position: relative;
  margin: var(--space-2) 0 0;
  font-size: var(--text-sm);
  opacity: 0.92;
  letter-spacing: 2px;
}

/* ===== 主菜单网格 ===== */
.menu-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-3);
  padding: var(--space-5) var(--space-4);
}
.menu-item {
  position: relative;
  background: var(--color-bg-card);
  border-radius: var(--radius-md);
  padding: var(--space-5) var(--space-3);
  text-align: center;
  box-shadow: var(--shadow-card);
  cursor: pointer;
  transition: all var(--transition-base);
  overflow: hidden;
}
.menu-item::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: var(--menu-color, var(--color-primary));
}
.menu-item-scan    { --menu-color: #1989fa; }
.menu-item-repair  { --menu-color: #ff976a; }
.menu-item-progress{ --menu-color: #07c160; }
.menu-item-faults  { --menu-color: #ee0a24; }

.menu-item:active {
  transform: scale(0.97);
  box-shadow: var(--shadow-md);
}
.menu-icon-wrap {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-md);
  background: var(--menu-color, var(--color-primary));
  margin: 0 auto var(--space-3);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.10);
}
.menu-title {
  display: block;
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  margin-bottom: var(--space-1);
}
.menu-desc {
  display: block;
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

/* ===== 底部 Tab ===== */
.bottom-menu {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
}
</style>