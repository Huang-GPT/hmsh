<template>
  <div class="login-page">
    <van-nav-bar title="终端登录" :border="false" />

    <div class="login-hero">
      <div class="hero-icon">📱</div>
      <div class="hero-title">欢迎使用售后绑定</div>
      <div class="hero-sub">输入您的手机号即可登录</div>
    </div>

    <div class="login-form">
      <van-cell-group inset>
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
  background: #f5f6f8;
  padding-top: 46px;
}
.login-hero {
  text-align: center;
  padding: 40px 20px 24px;
}
.hero-icon {
  font-size: 56px;
  margin-bottom: 12px;
}
.hero-title {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 6px;
}
.hero-sub {
  font-size: 13px;
  color: #6b7280;
}
.login-form {
  padding: 0 16px;
}
.submit-row {
  padding: 16px 0 8px;
}
.hint {
  text-align: center;
  font-size: 12px;
  color: #9ca3af;
  margin-top: 8px;
}
</style>