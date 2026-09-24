<template>
  <div class="login-page">
    <van-nav-bar title="终端登录" :border="false" />

    <div class="login-hero">
      <div class="hero-bg-circle hero-bg-1"></div>
      <div class="hero-bg-circle hero-bg-2"></div>
      <div class="hero-icon">📱</div>
      <div class="hero-title">欢迎使用售后绑定</div>
      <div class="hero-sub">输入您的手机号即可登录</div>
    </div>

    <div class="login-form">
      <van-cell-group inset class="form-card">
        <van-field
          v-model="phone"
          type="tel"
          label="手机号"
          placeholder="11 位手机号"
          maxlength="11"
          clearable
          :disabled="loading"
          @keyup.enter="onLogin"
        />
      </van-cell-group>
      <div class="submit-row">
        <van-button
          round block type="info"
          :loading="loading"
          :disabled="!canLogin"
          @click="onLogin"
          class="login-btn"
        >登录</van-button>
      </div>
      <p class="hint">首次登录将自动注册账号</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { setTerminalAuth, getTerminalUser, clearTerminalAuth } from '@/api/products'

export default {
  name: 'TerminalLogin',
  data() {
    return {
      phone: '',
      loading: false,
    }
  },
  computed: {
    canLogin() {
      return /^\d{11}$/.test(this.phone.trim()) && !this.loading
    },
    redirectPath() {
      const r = this.$route.query.redirect
      return (typeof r === 'string' && r.startsWith('/')) ? r : '/product/bind'
    },
  },
  created() {
    // 已登录直接跳转
    if (getToken()) {
      this.$router.replace(this.redirectPath)
    }
  },
  methods: {
    async onLogin() {
      if (!this.canLogin) return
      this.loading = true
      try {
        const res = await axios.post('/api/auth/customer/login-by-phone', {
          phone: this.phone.trim(),
        })
        const token = res.data && res.data.token
        const user = res.data && res.data.user
        if (!token || !user) {
          this.$toast('登录失败：服务端未返回 token')
          return
        }
        setTerminalAuth(token, user)
        this.$toast.success(`欢迎回来，${user.nickname || user.phone}`)
        this.$router.replace(this.redirectPath)
      } catch (e) {
        const data = e && e.response && e.response.data
        const err = (data && data.error) || e.message || '登录失败'
        this.$toast(err)
      } finally {
        this.loading = false
      }
    },
  },
}

// 简化：避免未导入 getToken 报错
function getToken() {
  try { return localStorage.getItem('hongmen_terminal_token') } catch { return null }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: var(--color-bg-page);
  padding-top: var(--nav-bar-height);
}

/* ===== 顶部 Hero（带装饰圆）===== */
.login-hero {
  position: relative;
  text-align: center;
  padding: 56px 20px 32px;
  background: linear-gradient(135deg, var(--brand-400), var(--brand-600));
  color: #fff;
  overflow: hidden;
}
.hero-bg-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
}
.hero-bg-1 {
  width: 180px; height: 180px;
  top: -60px; right: -40px;
}
.hero-bg-2 {
  width: 120px; height: 120px;
  bottom: -40px; left: -20px;
  background: rgba(255, 255, 255, 0.06);
}
.hero-icon {
  position: relative;
  font-size: 56px;
  margin-bottom: var(--space-3);
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.1));
}
.hero-title {
  position: relative;
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  margin-bottom: var(--space-1);
  letter-spacing: 0.5px;
}
.hero-sub {
  position: relative;
  font-size: var(--text-sm);
  opacity: 0.92;
}

/* ===== 表单区 ===== */
.login-form {
  padding: 0 var(--space-4);
  margin-top: -16px;
  position: relative;
  z-index: 1;
}
.form-card {
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-md);
}
.submit-row {
  padding: var(--space-4) 0 var(--space-2);
}
.login-btn {
  height: 44px !important;
  font-size: var(--text-md) !important;
  font-weight: var(--font-medium);
  background: linear-gradient(135deg, var(--brand-400), var(--brand-600)) !important;
  border: none !important;
  box-shadow: 0 4px 12px rgba(25, 137, 250, 0.25);
}
.hint {
  text-align: center;
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  margin-top: var(--space-2);
}
</style>