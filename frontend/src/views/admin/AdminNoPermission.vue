<template>
  <div class="no-permission">
    <van-empty
      image="error"
      description=" "
    >
      <template #image>
        <van-icon name="warning-o" size="120" color="var(--color-warning)" />
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
  padding: var(--space-6) 0;
}
.card {
  max-width: 560px;
  margin: 0 auto;
  background: var(--color-bg-card);
  border-radius: var(--radius-md);
  padding: var(--space-6) var(--space-8) var(--space-8);
  box-shadow: var(--shadow-md);
}
.title {
  text-align: center;
  font-size: var(--text-xl);
  color: var(--color-warning);
  margin: 0 0 var(--space-4);
  font-weight: var(--font-semibold);
}
.hint {
  text-align: center;
  color: var(--color-text-secondary);
  font-size: var(--text-base);
  line-height: 1.6;
  margin: 0 0 var(--space-6);
}
.perm-code {
  display: inline-block;
  background: #fff4e5;
  color: #d97706;
  padding: 2px var(--space-2);
  border-radius: var(--radius-xs);
  font-family: 'Courier New', monospace;
  font-size: var(--text-sm);
}
.meta {
  border-top: 1px solid var(--color-divider);
  padding-top: var(--space-4);
  margin-bottom: var(--space-6);
}
.meta-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--space-2) 0;
  font-size: var(--text-base);
  gap: var(--space-3);
}
.meta-label {
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}
.meta-value {
  color: var(--color-text);
  text-align: right;
  word-break: break-all;
}
.meta-value.perms {
  font-family: 'Courier New', monospace;
  font-size: var(--text-sm);
  color: var(--color-primary);
}
.actions {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
</style>