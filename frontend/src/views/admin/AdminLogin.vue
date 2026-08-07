<template>
  <div class="admin-login">
    <div class="login-card">
      <h2>红门售后管理系统</h2>
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
      <div class="login-btn">
        <van-button type="info" block @click="handleLogin" :loading="loading">登 录</van-button>
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
        const user = res.data.user
        localStorage.setItem('admin_user', JSON.stringify(user))
        const user = res.data.user
        if user.role == 'service_point' { this.$router.push('/dealer/orders') } else { this.$router.push('/admin/dashboard') }
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
  min-height: 100vh;
  background: linear-gradient(135deg, #1976d2 0%, #0d47a1 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-card {
  background: white;
  border-radius: 12px;
  padding: 40px 24px;
  width: 360px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
}
.login-card h2 {
  text-align: center;
  color: #1976d2;
  margin-bottom: 32px;
  font-size: 20px;
}
.login-btn {
  margin-top: 24px;
  padding: 0 16px;
}
</style>