<template>
  <div class="user-center">
    <!-- 顶部用户卡片 -->
    <div class="header">
      <div class="header-bg header-bg-1"></div>
      <div class="header-bg header-bg-2"></div>
      <div class="avatar-wrap">
        <van-icon name="user-o" size="48" color="#fff" />
      </div>
      <h2 class="header-title">我的</h2>
      <p class="header-sub">管理个人信息与产品</p>
    </div>

    <!-- 功能菜单 -->
    <div class="menu-card">
      <van-cell-group>
        <van-cell title="个人信息" is-link>
          <template #icon>
            <van-icon name="user-o" class="cell-icon" />
          </template>
        </van-cell>
        <van-cell title="我的工单" is-link to="/progress">
          <template #icon>
            <van-icon name="orders-o" class="cell-icon" />
          </template>
        </van-cell>
        <van-cell title="绑定产品" is-link to="/product/bind">
          <template #icon>
            <van-icon name="goods-o" class="cell-icon" />
          </template>
        </van-cell>
        <van-cell title="系统设置" is-link>
          <template #icon>
            <van-icon name="setting-o" class="cell-icon" />
          </template>
        </van-cell>
      </van-cell-group>
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
  name: 'UserCenter',
  data() {
    return {
      activeMenu: 1
    }
  }
}
</script>

<style scoped>
.user-center {
  min-height: 100vh;
  background: var(--color-bg-page);
  padding-bottom: var(--tab-bar-height);
}

/* ===== 顶部头部 ===== */
.header {
  position: relative;
  background: linear-gradient(135deg, var(--brand-400), var(--brand-600));
  color: white;
  padding: 56px 20px 40px;
  text-align: center;
  overflow: hidden;
}
.header-bg {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
}
.header-bg-1 {
  width: 200px; height: 200px;
  top: -80px; right: -50px;
}
.header-bg-2 {
  width: 120px; height: 120px;
  bottom: -40px; left: -30px;
  background: rgba(255, 255, 255, 0.06);
}
.avatar-wrap {
  position: relative;
  width: 80px;
  height: 80px;
  margin: 0 auto var(--space-3);
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid rgba(255, 255, 255, 0.3);
}
.header-title {
  position: relative;
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  margin: 0;
}
.header-sub {
  position: relative;
  margin: var(--space-1) 0 0;
  font-size: var(--text-sm);
  opacity: 0.92;
}

/* ===== 功能菜单卡片 ===== */
.menu-card {
  margin: -16px var(--space-4) 0;
  position: relative;
  z-index: 1;
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-card);
}
.cell-icon {
  color: var(--color-primary);
  font-size: var(--text-lg);
  margin-right: var(--space-2);
}

/* ===== 底部 Tab ===== */
.bottom-menu {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
}
</style>