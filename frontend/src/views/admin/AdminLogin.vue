<template>
  <div class="admin-login">
    <div class="login-bg login-bg-1"></div>
    <div class="login-bg login-bg-2"></div>

    <div class="login-card">
      <div class="logo-area">
        <div class="logo-icon">
          <van-icon name="manager-o" size="32" color="#fff" />
        </div>
        <h2>红门售后管理系统</h2>
        <p class="logo-sub">管理员登录</p>
      </div>

      <div class="form-area">
        <van-cell-group inset>
          <van-field
            v-model="account"
            label="管理员账号"
            placeholder="请输入管理员账号"
            left-icon="manager-o"
            autocomplete="username"
          />
          <van-field
            v-model="password"
            type="password"
            label="密码"
            placeholder="请输入密码"
            left-icon="lock"
            autocomplete="current-password"
          />
        </van-cell-group>

        <div class="login-btn">
          <van-button type="info" block :loading="loading" @click="handleLogin" native-type="submit">
            登 录
          </van-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { adminLogin } from '@/api/admin'

export default {
  name: 'AdminLogin',
  data() {
    return {
      account: '',
      password: '',
      loading: false
    }
  },
  methods: {
    async handleLogin() {
      if (!this.account) {
        this.$toast('请输入管理员账号')
        return
      }
      if (!this.password) {
        this.$toast('请输入密码')
        return
      }
      this.loading = true
      try {
        const res = await adminLogin(this.account, this.password)
        const user = res.data.user || {}
        // token 已经在 api.js 的 response 拦截器里写进 localStorage.admin_token
        // permissions 字段由后端 generate_token 时填入 user.to_dict()（user.permissions）
        localStorage.setItem('admin_user', JSON.stringify(user))
        // 跳转依据：实际权限（user.permissions），不是业务字段（user.role）
        // —— 防止 role 声明 X 但实际 RBAC 角色权限不足时被守卫反复踢回形成"登了等于没登"
        const perms = Array.isArray(user.permissions) ? user.permissions : []
        const wantsDealer = user.role === 'service_point' || user.role === 'service_point_admin'
        if (wantsDealer && perms.includes('dealer_order:view')) {
          this.$router.push('/dealer/orders')
        } else {
          this.$router.push('/admin/dashboard')
        }
      } catch (e) {
        const msg = (e && e.response && e.response.data && e.response.data.error) || '登录失败'
        this.$toast(msg)
      }
      this.loading = false
    }
  }
}
</script>

<style scoped>
.admin-login {
  position: relative;
  min-height: 100vh;
  background: linear-gradient(135deg, var(--brand-500), #0d47a1);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

/* ===== 背景装饰圆 ===== */
.login-bg {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
}
.login-bg-1 {
  width: 360px;
  height: 360px;
  top: -120px;
  right: -80px;
}
.login-bg-2 {
  width: 240px;
  height: 240px;
  bottom: -100px;
  left: -60px;
  background: rgba(255, 255, 255, 0.05);
}

/* ===== 登录卡片 ===== */
.login-card {
  position: relative;
  background: #ffffff;
  border-radius: var(--radius-lg);
  padding: 32px 24px 24px;
  width: 380px;
  max-width: 92vw;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.18);
  z-index: 1;
}

/* ===== Logo 区 ===== */
.logo-area {
  text-align: center;
  margin-bottom: var(--space-6);
}
.logo-icon {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--brand-400), var(--brand-600));
  margin: 0 auto var(--space-3);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 16px rgba(25, 137, 250, 0.3);
}
.login-card h2 {
  text-align: center;
  color: var(--color-text);
  margin: 0 0 var(--space-1);
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
}
.logo-sub {
  text-align: center;
  color: var(--color-text-tertiary);
  font-size: var(--text-sm);
  margin: 0;
}

/* ===== 表单区 ===== */
.form-area {
  margin-top: var(--space-2);
}
.login-btn {
  margin-top: var(--space-5);
  padding: 0 var(--space-4);
}
.login-btn .van-button {
  height: 44px !important;
  font-size: var(--text-md) !important;
  font-weight: var(--font-medium);
  background: linear-gradient(135deg, var(--brand-400), var(--brand-600)) !important;
  border: none !important;
  box-shadow: 0 4px 12px rgba(25, 137, 250, 0.25);
}
</style>