<template>
  <div class="no-permission">
    <van-empty
      image="error"
      description=" "
    >
      <template #image>
        <van-icon name="warning-o" size="120" color="#f5a623" />
      </template>
    </van-empty>

    <div class="card">
      <h3 class="title">无权访问</h3>
      <p class="hint">
        您的账号缺少 <code class="perm-code">{{ required }}</code> 权限，
        请联系管理员为您开通相应权限后再试。
      </p>

      <div class="meta">
        <div class="meta-row">
          <span class="meta-label">当前账号</span>
          <span class="meta-value">{{ user.nickname || '-' }}</span>
        </div>
        <div class="meta-row">
          <span class="meta-label">账号</span>
          <span class="meta-value">{{ user.openid || user.account || '-' }}</span>
        </div>
        <div class="meta-row">
          <span class="meta-label">业务角色</span>
          <span class="meta-value">{{ user.role || '-' }}</span>
        </div>
        <div v-if="user.service_point_name" class="meta-row">
          <span class="meta-label">所属服务点</span>
          <span class="meta-value">{{ user.service_point_name }}</span>
        </div>
        <div class="meta-row">
          <span class="meta-label">已开通权限</span>
          <span class="meta-value perms">{{ permsText }}</span>
        </div>
      </div>

      <div class="actions">
        <van-button
          v-if="hasDashboard"
          type="info"
          plain
          block
          @click="$router.push('/admin/dashboard')"
        >返回工作台</van-button>
        <van-button type="danger" block @click="handleLogout">退出登录</van-button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AdminNoPermission',
  data() {
    return {
      required: '',
      user: {},
      perms: []
    }
  },
  computed: {
    permsText() {
      return this.perms.length ? this.perms.join(', ') : '（无）'
    },
    hasDashboard() {
      return this.perms.includes('dashboard:view')
    }
  },
  created() {
    this.required = this.$route.query.required || '（未知）'
    const fromPath = this.$route.query.from
    // 防御：若用户从 /admin/no-permission 自己手动访问（罕见），给个明确来源
    if (!fromPath) {
      this.$route.query.from = '(无来源)'
    }

    const raw = localStorage.getItem('admin_user')
    if (raw) {
      try {
        const u = JSON.parse(raw)
        this.user = u || {}
        this.perms = Array.isArray(u.permissions) ? u.permissions : []
      } catch (e) {
        this.user = {}
        this.perms = []
      }
    }
  },
  methods: {
    handleLogout() {
      localStorage.removeItem('admin_user')
      localStorage.removeItem('admin_token')
      this.$router.push('/admin/login')
    }
  }
}
</script>

<style scoped>
.no-permission {
  padding: 24px 0;
}
.card {
  max-width: 560px;
  margin: 0 auto;
  background: white;
  border-radius: 8px;
  padding: 24px 32px 32px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}
.title {
  text-align: center;
  font-size: 20px;
  color: #f5a623;
  margin: 0 0 16px;
}
.hint {
  text-align: center;
  color: #666;
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 24px;
}
.perm-code {
  display: inline-block;
  background: #fff4e5;
  color: #d97706;
  padding: 2px 8px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}
.meta {
  border-top: 1px solid #f0f0f0;
  padding-top: 16px;
  margin-bottom: 24px;
}
.meta-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 8px 0;
  font-size: 14px;
  gap: 12px;
}
.meta-label {
  color: #999;
  flex-shrink: 0;
}
.meta-value {
  color: #333;
  text-align: right;
  word-break: break-all;
}
.meta-value.perms {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #1976d2;
}
.actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>