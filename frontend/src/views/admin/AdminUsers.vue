<template>
  <div class="admin-users">
    <h3>用户管理</h3>

    <div class="toolbar">
      <div class="toolbar-row toolbar-top">
        <van-search
          v-model="keyword"
          placeholder="搜索账号/姓名/手机/邮箱"
          @search="loadUsers(1)"
          shape="round"
          class="search-box"
        />
      </div>
      <div class="toolbar-row toolbar-bottom">
        <span
          v-for="f in roleFilters"
          :key="f.value"
          :class="['filter-chip', { active: roleFilter === f.value }]"
          @click="setRoleFilter(f.value)"
        >{{ f.label }}</span>
        <span
          v-for="f in statusFilters"
          :key="'s-' + f.value"
          :class="['filter-chip', { active: statusFilter === f.value }]"
          @click="setStatusFilter(f.value)"
        >{{ f.label }}</span>
        <van-button size="small" plain icon="replay" @click="loadUsers()">刷新</van-button>
        <van-button size="small" type="primary" icon="plus" @click="openCreate">新增用户</van-button>
      </div>
    </div>

    <div class="table-wrap">
      <table class="user-table">
        <thead>
          <tr>
            <th>账号</th>
            <th>姓名</th>
            <th>手机</th>
            <th>邮箱</th>
            <th>所属部门</th>
            <th>服务点</th>
            <th>角色</th>
            <th>状态</th>
            <th>创建时间</th>
            <th class="col-actions">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading && users.length === 0">
            <td colspan="10" class="state-cell">加载中…</td>
          </tr>
          <tr v-else-if="filteredUsers.length === 0">
            <td colspan="10" class="state-cell">
              <div class="empty-cell">
                <div class="empty-icon">👥</div>
                <div class="empty-text">暂无用户</div>
              </div>
            </td>
          </tr>
          <tr v-for="u in filteredUsers" :key="u.id" :class="{ 'row-disabled': u.status === 'disabled' }">
            <td class="col-account">
              <code>{{ u.account || u.openid }}</code>
            </td>
            <td>
              <div class="name-cell">
                <span class="real-name">{{ u.real_name || u.nickname || '—' }}</span>
                <span v-if="u.nickname && u.nickname !== u.real_name" class="nick">{{ '(' + u.nickname + ')' }}</span>
              </div>
            </td>
            <td class="col-mono">{{ u.phone || '—' }}</td>
            <td>{{ u.email || '—' }}</td>
            <td>{{ u.department || '—' }}</td>
            <td>{{ u.service_point_name || '—' }}</td>
            <td>
              <div class="roles-cell">
                <span v-for="r in (u.roles || [])" :key="r.id" class="role-tag" :class="'role-tag-' + r.code">
                  {{ r.name }}
                </span>
                <span v-if="!u.roles || u.roles.length === 0" class="role-empty">未分配</span>
              </div>
            </td>
            <td>
              <van-tag :type="u.status === 'active' ? 'success' : 'default'" size="mini">
                {{ u.status === 'active' ? '启用' : '停用' }}
              </van-tag>
            </td>
            <td class="col-time">
              <div>{{ formatDate(u.created_at) }}</div>
              <div class="row-meta">{{ formatTime(u.created_at) }}</div>
            </td>
            <td class="col-actions" @click.stop>
              <a class="op-link primary" @click="openEdit(u)">编辑</a>
              <a class="op-link" @click="openAssignRoles(u)">分配角色</a>
              <a class="op-link warning" @click="doResetPwd(u)">重置密码</a>
              <a class="op-link" :class="u.status === 'active' ? 'danger' : 'success'" @click="doToggle(u)">
                {{ u.status === 'active' ? '停用' : '启用' }}
              </a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="pagination">
      <span class="pagination-info">
        共 <strong>{{ filteredUsers.length }}</strong> 条 · 第 {{ page }} / {{ totalPages }} 页
      </span>
      <div class="pagination-buttons">
        <van-button size="mini" :disabled="page <= 1" @click="changePage(-1)">上一页</van-button>
        <van-button size="mini" :disabled="page >= totalPages" @click="changePage(1)">下一页</van-button>
      </div>
    </div>

    <!-- ============ 新增/编辑用户 ============ -->
    <van-dialog v-model:show="showForm" :title="formMode === 'create' ? '新增用户' : '编辑用户'" show-cancel-button @confirm="submitForm" width="90%">
      <div class="dialog-body">
        <van-cell-group inset>
          <van-field v-model="form.account" label="账号" placeholder="登录账号（不可重复）" :disabled="formMode === 'edit'" required maxlength="32" />
          <van-field v-model="form.real_name" label="姓名" placeholder="真实姓名" maxlength="32" />
          <van-field v-model="form.nickname" label="昵称" placeholder="显示名（默认与姓名相同）" maxlength="32" />
          <van-field v-model="form.phone" label="手机号" placeholder="11 位手机号" type="tel" maxlength="11" />
          <van-field v-model="form.email" label="邮箱" placeholder="选填" />
          <van-field v-model="form.department" label="所属部门" placeholder="如：客服部、维修部" maxlength="32" />
          <van-field v-if="formMode === 'create'" v-model="form.password" label="初始密码" placeholder="留空则默认 123456" type="password" maxlength="32" />
          <van-field name="role" label="主角色">
            <template #input>
              <select v-model="form.role" class="form-select">
                <option v-for="r in rbacRoles" :key="r.code" :value="r.code">{{ r.name }}</option>
              </select>
            </template>
          </van-field>
          <van-field name="sp" label="所属服务点">
            <template #input>
              <select v-model="form.service_point_id" class="form-select">
                <option :value="null">— 无 —</option>
                <option v-for="sp in servicePoints" :key="sp.id" :value="sp.id">{{ sp.name }}</option>
              </select>
            </template>
          </van-field>
          <van-field v-model="form.remark" label="备注" placeholder="选填" maxlength="255" type="textarea" autosize />
        </van-cell-group>
      </div>
    </van-dialog>

    <!-- ============ 分配角色弹窗 ============ -->
    <van-dialog v-model:show="showAssign" title="分配角色" show-cancel-button @confirm="submitAssign" width="85%">
      <div class="dialog-body">
        <div class="dialog-tip">为「{{ currentUser && (currentUser.real_name || currentUser.nickname || currentUser.account) }}」分配角色（可多选）</div>
        <div class="role-checkboxes">
          <label v-for="r in rbacRoles" :key="r.id" class="role-checkbox">
            <input type="checkbox" :value="r.id" v-model="assignRoleIds" />
            <span class="rc-name">{{ r.name }}</span>
            <span class="rc-desc">{{ r.description }}</span>
            <span v-if="r.builtin" class="rc-builtin">内置</span>
          </label>
        </div>
      </div>
    </van-dialog>

    <!-- ============ 重置密码弹窗 ============ -->
    <van-dialog v-model:show="showResetPwd" title="重置密码" show-cancel-button @confirm="submitResetPwd">
      <div class="dialog-body">
        <div class="dialog-tip">为「{{ currentUser && (currentUser.real_name || currentUser.nickname || currentUser.account) }}」重置密码</div>
        <van-cell-group inset>
          <van-field v-model="resetPwdForm.new_password" label="新密码" placeholder="留空则重置为 123456" type="password" maxlength="32" />
        </van-cell-group>
      </div>
    </van-dialog>
  </div>
</template>

<script>
import {
  getAllUsers, createUser, updateUser, toggleUserStatus, resetPassword,
  listRoles, getUserRoles, setUserRoles, getServicePoints,
} from '@/api/admin'

export default {
  name: 'AdminUsers',
  data() {
    return {
      users: [],
      rbacRoles: [],
      servicePoints: [],
      keyword: '',
      roleFilter: 'all',
      statusFilter: 'all',
      page: 1,
      pageSize: 20,
      loading: false,

      roleFilters: [
        { value: 'all', label: '全部角色' },
        { value: 'admin', label: '管理员' },
        { value: 'dispatcher', label: '派单员' },
        { value: 'service_point', label: '经销商' },
      ],
      statusFilters: [
        { value: 'all', label: '全部状态' },
        { value: 'active', label: '启用' },
        { value: 'disabled', label: '停用' },
      ],

      showForm: false,
      formMode: 'create',
      form: this.emptyForm(),

      showAssign: false,
      assignRoleIds: [],
      currentUser: null,

      showResetPwd: false,
      resetPwdForm: { new_password: '' },
    }
  },
  computed: {
    filteredUsers() {
      let list = this.users
      if (this.statusFilter !== 'all') {
        list = list.filter(u => u.status === this.statusFilter)
      }
      if (this.roleFilter !== 'all') {
        list = list.filter(u => u.role === this.roleFilter || (u.roles || []).some(r => r.code === this.roleFilter))
      }
      if (this.keyword) {
        const kw = this.keyword.toLowerCase()
        list = list.filter(u =>
          (u.account && u.account.toLowerCase().includes(kw)) ||
          (u.openid && u.openid.toLowerCase().includes(kw)) ||
          (u.nickname && u.nickname.toLowerCase().includes(kw)) ||
          (u.real_name && u.real_name.toLowerCase().includes(kw)) ||
          (u.phone && u.phone.includes(kw)) ||
          (u.email && u.email.toLowerCase().includes(kw))
        )
      }
      return list
    },
    totalPages() {
      return Math.max(1, Math.ceil(this.filteredUsers.length / this.pageSize))
    },
  },
  watch: {
    roleFilter() { this.page = 1 },
    statusFilter() { this.page = 1 },
  },
  async created() {
    await Promise.all([this.loadUsers(), this.loadRoles(), this.loadServicePoints()])
  },
  methods: {
    emptyForm() {
      return { account: '', real_name: '', nickname: '', phone: '', email: '', department: '', password: '', role: 'customer', service_point_id: null, remark: '' }
    },
    async loadUsers() {
      this.loading = true
      try {
        const res = await getAllUsers()
        this.users = (res.data && res.data.users) || []
      } catch (e) {
        this.users = []
      } finally {
        this.loading = false
      }
    },
    async loadRoles() {
      try {
        const res = await listRoles()
        this.rbacRoles = (res.data && res.data.items) || []
      } catch (e) { this.rbacRoles = [] }
    },
    async loadServicePoints() {
      try {
        const res = await getServicePoints()
        const data = res.data || {}
        this.servicePoints = data.items || data.service_points || []
      } catch (e) { this.servicePoints = [] }
    },
    setRoleFilter(v) { this.roleFilter = v },
    setStatusFilter(v) { this.statusFilter = v },
    changePage(d) {
      const np = this.page + d
      if (np >= 1 && np <= this.totalPages) this.page = np
    },
    openCreate() {
      this.formMode = 'create'
      this.form = this.emptyForm()
      this.showForm = true
    },
    openEdit(u) {
      this.formMode = 'edit'
      this.form = {
        account: u.account || u.openid,
        real_name: u.real_name || '',
        nickname: u.nickname || '',
        phone: u.phone || '',
        email: u.email || '',
        department: u.department || '',
        role: u.role,
        service_point_id: u.service_point_id,
        remark: u.remark || '',
      }
      this.currentUser = u
      this.showForm = true
    },
    async submitForm() {
      const f = this.form
      if (!f.account) { this.$toast('请填写账号'); return }
      if (this.formMode === 'create' && !f.real_name && !f.nickname) { this.$toast('请填写姓名或昵称'); return }
      try {
        const payload = { ...f }
        if (this.formMode === 'create') {
          if (!f.password) payload.password = '123456'
          await createUser(payload)
          this.$toast.success('创建成功，初始密码：' + payload.password)
        } else {
          await updateUser(this.currentUser.id, payload)
          this.$toast.success('更新成功')
        }
        this.showForm = false
        this.loadUsers()
      } catch (e) {
        const err = (e && e.response && e.response.data && e.response.data.error) || '操作失败'
        this.$toast(err)
      }
    },
    async openAssignRoles(u) {
      this.currentUser = u
      try {
        const res = await getUserRoles(u.id)
        this.assignRoleIds = (res.data && res.data.role_ids) || []
      } catch (e) { this.assignRoleIds = [] }
      this.showAssign = true
    },
    async submitAssign() {
      try {
        await setUserRoles(this.currentUser.id, this.assignRoleIds)
        this.$toast.success('角色分配成功')
        this.showAssign = false
        this.loadUsers()
      } catch (e) {
        const err = (e && e.response && e.response.data && e.response.data.error) || '操作失败'
        this.$toast(err)
      }
    },
    doResetPwd(u) {
      this.currentUser = u
      this.resetPwdForm = { new_password: '' }
      this.showResetPwd = true
    },
    async submitResetPwd() {
      const pwd = (this.resetPwdForm.new_password || '').trim() || '123456'
      try {
        await resetPassword(this.currentUser.id, pwd)
        this.$toast.success('密码已重置为：' + pwd)
        this.showResetPwd = false
      } catch (e) {
        this.$toast('操作失败')
      }
    },
    async doToggle(u) {
      try {
        await toggleUserStatus(u.id)
        this.$toast.success(u.status === 'active' ? '已停用' : '已启用')
        this.loadUsers()
      } catch (e) {
        this.$toast('操作失败')
      }
    },
    formatDate(d) {
      if (!d) return '—'
      const s = String(d)
      return s.length >= 10 ? s.substring(0, 10) : s
    },
    formatTime(d) {
      if (!d) return '—'
      const s = String(d)
      return s.length >= 16 ? s.substring(11, 16) : s
    },
  },
}
</script>

<style scoped>
.admin-users h3 {
  margin: 0 0 16px;
  color: #1f2937;
  font-size: 18px;
}
.toolbar { margin-bottom: 12px; }
.toolbar-row { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; flex-wrap: wrap; }
.search-box { flex: 1; min-width: 280px; }
.filter-chip {
  display: inline-block; padding: 4px 12px; border-radius: 14px;
  background: #f3f4f6; font-size: 13px; color: #4b5563; cursor: pointer;
}
.filter-chip:hover { background: #e5e7eb; }
.filter-chip.active { background: #1989fa; color: white; }

.table-wrap { overflow-x: auto; border: 1px solid #e5e7eb; border-radius: 6px; }
.user-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.user-table th { background: #f9fafb; padding: 10px 8px; text-align: left; font-weight: 600; color: #374151; border-bottom: 1px solid #e5e7eb; white-space: nowrap; }
.user-table td { padding: 10px 8px; border-bottom: 1px solid #f3f4f6; color: #4b5563; vertical-align: middle; }
.user-table tbody tr:hover td { background: #f9fafb; }
.user-table tbody tr.row-disabled td { opacity: 0.6; }
.col-account code { background: #f3f4f6; padding: 2px 6px; border-radius: 3px; font-family: ui-monospace, monospace; font-size: 12px; color: #1989fa; }
.col-mono { font-family: ui-monospace, monospace; font-size: 12px; }
.col-time { font-family: ui-monospace, monospace; font-size: 12px; }
.row-meta { font-size: 11px; color: #9ca3af; margin-top: 2px; }
.name-cell { display: flex; flex-direction: column; gap: 2px; }
.real-name { font-weight: 500; color: #1f2937; }
.nick { font-size: 11px; color: #9ca3af; }
.state-cell { text-align: center; padding: 40px; color: #9ca3af; }
.empty-cell { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 20px; }
.empty-icon { font-size: 36px; }
.empty-text { font-size: 13px; color: #9ca3af; }
.roles-cell { display: flex; flex-wrap: wrap; gap: 4px; }
.role-tag {
  display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px;
  background: #e0e7ff; color: #4338ca;
}
.role-tag-admin { background: #fee2e2; color: #b91c1c; }
.role-tag-dispatcher { background: #fef3c7; color: #b45309; }
.role-tag-service_point_admin { background: #d1fae5; color: #047857; }
.role-tag-engineer { background: #dbeafe; color: #1d4ed8; }
.role-tag-operator { background: #ede9fe; color: #6d28d9; }
.role-tag-customer { background: #f3f4f6; color: #6b7280; }
.role-empty { font-size: 11px; color: #c8c9cc; font-style: italic; }

.col-actions { white-space: nowrap; }
.op-link { display: inline-block; margin-right: 6px; padding: 2px 4px; cursor: pointer; font-size: 13px; text-decoration: none; color: #1989fa; }
.op-link:hover { text-decoration: underline; }
.op-link.primary { color: #1989fa; }
.op-link.success { color: #07c160; }
.op-link.warning { color: #ee0a24; }
.op-link.danger { color: #ee0a24; }

.pagination { display: flex; align-items: center; justify-content: space-between; margin-top: 16px; }
.pagination-info { font-size: 13px; color: #6b7280; }
.pagination-info strong { color: #1989fa; margin: 0 2px; }
.pagination-buttons { display: flex; gap: 8px; }

.dialog-body { padding: 12px 0; }
.dialog-tip { font-size: 13px; color: #6b7280; margin-bottom: 12px; padding: 0 16px; }
.form-select {
  width: 100%; padding: 6px 10px; border: 1px solid #e5e7eb; border-radius: 6px;
  font-size: 14px; background: #fff; color: #1f2937; cursor: pointer;
}

.role-checkboxes { padding: 8px 16px; display: flex; flex-direction: column; gap: 8px; max-height: 60vh; overflow-y: auto; }
.role-checkbox {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; border: 1px solid #e5e7eb; border-radius: 6px;
  cursor: pointer; background: #fff;
}
.role-checkbox:hover { background: #f9fafb; }
.role-checkbox input { width: 16px; height: 16px; }
.rc-name { font-weight: 500; color: #1f2937; }
.rc-desc { font-size: 12px; color: #6b7280; flex: 1; }
.rc-builtin { font-size: 11px; background: #fef3c7; color: #b45309; padding: 1px 6px; border-radius: 8px; }
</style>
