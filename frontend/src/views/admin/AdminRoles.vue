<template>
  <div class="admin-roles">
    <h3>角色管理</h3>
    <p class="page-sub">管理角色与权限分配（基于 RBAC 行业标准设计）</p>

    <div class="toolbar">
      <div class="toolbar-row toolbar-top">
        <van-search
          v-model="keyword"
          placeholder="搜索角色编码/名称"
          @search="loadRoles(1)"
          shape="round"
          class="search-box"
        />
      </div>
      <div class="toolbar-row toolbar-bottom">
        <van-button size="small" plain icon="replay" @click="loadRoles()">刷新</van-button>
        <van-button size="small" type="primary" icon="plus" @click="openCreate">新增角色</van-button>
        <van-button size="small" plain icon="cluster-o" @click="showPermissions = true">查看权限库（{{ permissions.length }}）</van-button>
      </div>
    </div>

    <div class="table-wrap">
      <table class="role-table">
        <thead>
          <tr>
            <th>编码</th>
            <th>名称</th>
            <th>描述</th>
            <th>类型</th>
            <th>权限数</th>
            <th>用户数</th>
            <th>状态</th>
            <th>更新时间</th>
            <th class="col-actions">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading && roles.length === 0">
            <td colspan="9" class="state-cell">加载中…</td>
          </tr>
          <tr v-else-if="filteredRoles.length === 0">
            <td colspan="9" class="state-cell">
              <div class="empty-cell">
                <div class="empty-icon">🎭</div>
                <div class="empty-text">暂无角色</div>
              </div>
            </td>
          </tr>
          <tr v-for="r in filteredRoles" :key="r.id" :class="{ 'row-disabled': r.status === 'disabled' }">
            <td><code class="code-tag">{{ r.code }}</code></td>
            <td><span class="role-name">{{ r.name }}</span></td>
            <td><span class="desc">{{ r.description || '—' }}</span></td>
            <td>
              <van-tag v-if="r.builtin" type="warning" size="mini">内置</van-tag>
              <van-tag v-else type="primary" size="mini">自定义</van-tag>
            </td>
            <td>
              <a class="link" @click="showRolePerms(r)">{{ r.permission_count }}</a>
            </td>
            <td>{{ r.user_count }}</td>
            <td>
              <van-tag :type="r.status === 'active' ? 'success' : 'default'" size="mini">
                {{ r.status === 'active' ? '启用' : '停用' }}
              </van-tag>
            </td>
            <td class="col-time">{{ formatDateTime(r.updated_at) }}</td>
            <td class="col-actions" @click.stop>
              <a class="op-link primary" @click="openEdit(r)">编辑</a>
              <a class="op-link" @click="showRolePerms(r)">权限</a>
              <a v-if="!r.builtin" class="op-link danger" @click="doDelete(r)">删除</a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ============ 新增/编辑角色 ============ -->
    <van-dialog v-model:show="showForm" :title="formMode === 'create' ? '新增角色' : '编辑角色 ' + form.name" show-cancel-button @confirm="submitForm" width="92%">
      <div class="dialog-body dialog-body-large">
        <van-cell-group inset>
          <van-field v-model="form.code" label="编码" placeholder="英文唯一编码，如 operator" :disabled="formMode === 'edit'" required maxlength="32" />
          <van-field v-model="form.name" label="名称" placeholder="如：运营人员" required maxlength="32" />
          <van-field v-model="form.description" label="描述" placeholder="角色用途说明" maxlength="255" />
          <van-field v-if="formMode === 'edit' && !form.builtin" name="status" label="状态">
            <template #input>
              <select v-model="form.status" class="form-select">
                <option value="active">启用</option>
                <option value="disabled">停用</option>
              </select>
            </template>
          </van-field>
        </van-cell-group>

        <div class="perm-section">
          <div class="perm-section-title">
            <van-icon name="cluster-o" /> 权限分配
            <span class="perm-counter">已选 {{ selectedPermIds.length }} / {{ permissions.length }} 个权限</span>
          </div>
          <div class="perm-actions">
            <a @click="selectAllPerms">全选</a>
            <a @click="selectNonePerms">全清</a>
            <a @click="selectByModule('order')">仅订单</a>
            <a @click="selectByModule('dealer_order')">仅售后</a>
            <a @click="selectByModule('user')">仅用户/角色</a>
          </div>
          <div class="perm-modules">
            <div v-for="(items, module) in permissionsGrouped" :key="module" class="perm-module">
              <div class="perm-module-head">
                <span class="perm-module-name">{{ moduleLabel(module) }}</span>
                <label class="perm-module-toggle">
                  <input type="checkbox" :checked="isModuleAllSelected(items)" @change="toggleModule(items, $event.target.checked)" />
                  全选该模块
                </label>
              </div>
              <div class="perm-items">
                <label v-for="p in items" :key="p.id" class="perm-item" :class="{ checked: selectedPermIds.indexOf(p.id) >= 0 }">
                  <input type="checkbox" :value="p.id" v-model="selectedPermIds" />
                  <span class="pi-name">{{ p.name }}</span>
                  <code class="pi-code">{{ p.code }}</code>
                  <span class="pi-action">{{ p.action }}</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </van-dialog>

    <!-- ============ 查看权限库（只读） ============ -->
    <van-dialog v-model:show="showPermissions" title="权限库总览" :show-confirm-button="false" close-on-click-overlay width="85%">
      <div class="dialog-body">
        <div class="perm-modules">
          <div v-for="(items, module) in permissionsGrouped" :key="module" class="perm-module">
            <div class="perm-module-head">
              <span class="perm-module-name">{{ moduleLabel(module) }}</span>
              <span class="perm-module-count">{{ items.length }} 项</span>
            </div>
            <div class="perm-items">
              <div v-for="p in items" :key="p.id" class="perm-item perm-item-readonly">
                <span class="pi-name">{{ p.name }}</span>
                <code class="pi-code">{{ p.code }}</code>
              </div>
            </div>
          </div>
        </div>
      </div>
    </van-dialog>

    <!-- ============ 角色权限详情 ============ -->
    <van-dialog v-model:show="showRolePermsDialog" :title="currentRole ? (currentRole.name + ' — 已分配权限') : '角色权限'" :show-confirm-button="false" close-on-click-overlay width="85%">
      <div class="dialog-body">
        <div v-if="currentRolePerms.length === 0" class="empty-block">
          <van-icon name="warning-o" /> 该角色尚未分配任何权限
        </div>
        <div v-else class="perm-items">
          <div v-for="p in currentRolePerms" :key="p.id" class="perm-item perm-item-readonly">
            <span class="pi-name">{{ p.name }}</span>
            <code class="pi-code">{{ p.code }}</code>
            <span class="pi-action">{{ moduleLabel(p.module) }}</span>
          </div>
        </div>
      </div>
    </van-dialog>
  </div>
</template>

<script>
import {
  listPermissions, listRoles, getRole, createRole, updateRole, deleteRole,
} from '@/api/admin'

export default {
  name: 'AdminRoles',
  data() {
    return {
      roles: [],
      permissions: [],
      permissionsGrouped: {},
      keyword: '',
      loading: false,

      showForm: false,
      formMode: 'create',
      form: { code: '', name: '', description: '', status: 'active' },
      selectedPermIds: [],

      showPermissions: false,
      showRolePermsDialog: false,
      currentRole: null,
      currentRolePerms: [],
    }
  },
  computed: {
    filteredRoles() {
      if (!this.keyword) return this.roles
      const kw = this.keyword.toLowerCase()
      return this.roles.filter(r =>
        (r.code && r.code.toLowerCase().includes(kw)) ||
        (r.name && r.name.toLowerCase().includes(kw)) ||
        (r.description && r.description.toLowerCase().includes(kw))
      )
    },
  },
  async created() {
    await Promise.all([this.loadRoles(), this.loadPermissions()])
  },
  methods: {
    async loadRoles() {
      this.loading = true
      try {
        const res = await listRoles()
        this.roles = (res.data && res.data.items) || []
      } catch (e) { this.roles = [] }
      finally { this.loading = false }
    },
    async loadPermissions() {
      try {
        const res = await listPermissions()
        this.permissions = (res.data && res.data.items) || []
        this.permissionsGrouped = (res.data && res.data.grouped) || {}
      } catch (e) {
        this.permissions = []
        this.permissionsGrouped = {}
      }
    },
    moduleLabel(code) {
      const m = {
        dashboard: '工作台', order: '工单管理', dealer_order: '工单售后',
        user: '用户管理', role: '角色权限', product: '产品管理',
        binding: '绑定记录', fault: '故障库', service_point: '服务点',
        statistics: '数据统计', system: '系统设置',
      }
      return m[code] || code
    },
    openCreate() {
      this.formMode = 'create'
      this.form = { code: '', name: '', description: '', status: 'active' }
      this.selectedPermIds = []
      this.showForm = true
    },
    async openEdit(r) {
      this.formMode = 'edit'
      this.form = { ...r }
      try {
        const res = await getRole(r.id)
        this.selectedPermIds = (res.data && res.data.permission_ids) || []
      } catch (e) {
        this.selectedPermIds = r.permission_ids || []
      }
      this.showForm = true
    },
    async submitForm() {
      if (!this.form.code || !this.form.name) { this.$toast('编码和名称必填'); return }
      const payload = { ...this.form, permission_ids: this.selectedPermIds }
      try {
        if (this.formMode === 'create') {
          await createRole(payload)
          this.$toast.success('角色创建成功')
        } else {
          await updateRole(this.form.id, payload)
          this.$toast.success('角色更新成功')
        }
        this.showForm = false
        this.loadRoles()
      } catch (e) {
        const err = (e && e.response && e.response.data && e.response.data.error) || '操作失败'
        this.$toast(err)
      }
    },
    async doDelete(r) {
      if (!confirm(`确定删除角色「${r.name}」？此操作不可恢复。`)) return
      try {
        await deleteRole(r.id)
        this.$toast.success('角色已删除')
        this.loadRoles()
      } catch (e) {
        const err = (e && e.response && e.response.data && e.response.data.error) || '操作失败'
        this.$toast(err)
      }
    },
    async showRolePerms(r) {
      this.currentRole = r
      try {
        const res = await getRole(r.id)
        this.currentRolePerms = (res.data && res.data.permissions) || []
      } catch (e) {
        this.currentRolePerms = []
      }
      this.showRolePermsDialog = true
    },
    selectAllPerms() {
      this.selectedPermIds = this.permissions.map(p => p.id)
    },
    selectNonePerms() {
      this.selectedPermIds = []
    },
    selectByModule(module) {
      const ids = this.permissionsGrouped[module] ? this.permissionsGrouped[module].map(p => p.id) : []
      this.selectedPermIds = [...new Set([...this.selectedPermIds, ...ids])]
    },
    isModuleAllSelected(items) {
      return items.every(p => this.selectedPermIds.indexOf(p.id) >= 0)
    },
    toggleModule(items, checked) {
      const ids = items.map(p => p.id)
      if (checked) {
        this.selectedPermIds = [...new Set([...this.selectedPermIds, ...ids])]
      } else {
        this.selectedPermIds = this.selectedPermIds.filter(id => ids.indexOf(id) < 0)
      }
    },
    formatDateTime(d) {
      if (!d) return '—'
      const s = String(d)
      return s.length >= 16 ? s.substring(0, 16).replace('T', ' ') : s
    },
  },
}
</script>

<style scoped>
.admin-roles h3 { margin: 0 0 8px; color: #1f2937; font-size: 18px; }
.page-sub { font-size: 13px; color: #6b7280; margin: 0 0 16px; }
.toolbar { margin-bottom: 12px; }
.toolbar-row { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; flex-wrap: wrap; }
.search-box { flex: 1; min-width: 280px; }

.table-wrap { overflow-x: auto; border: 1px solid #e5e7eb; border-radius: 6px; }
.role-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.role-table th { background: #f9fafb; padding: 10px 8px; text-align: left; font-weight: 600; color: #374151; border-bottom: 1px solid #e5e7eb; }
.role-table td { padding: 10px 8px; border-bottom: 1px solid #f3f4f6; color: #4b5563; vertical-align: middle; }
.role-table tbody tr:hover td { background: #f9fafb; }
.role-table tbody tr.row-disabled td { opacity: 0.6; }
.code-tag { background: #f3f4f6; padding: 2px 6px; border-radius: 3px; font-family: ui-monospace, monospace; font-size: 12px; color: #1f2937; }
.role-name { font-weight: 500; color: #1f2937; }
.desc { color: #6b7280; font-size: 12px; }
.link { color: #1989fa; cursor: pointer; }
.link:hover { text-decoration: underline; }
.col-time { font-family: ui-monospace, monospace; font-size: 12px; }
.state-cell { text-align: center; padding: 40px; color: #9ca3af; }
.empty-cell { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 20px; }
.empty-icon { font-size: 36px; }
.empty-text { font-size: 13px; color: #9ca3af; }
.empty-block { text-align: center; padding: 40px; color: #9ca3af; font-size: 13px; }
.col-actions { white-space: nowrap; }
.op-link { display: inline-block; margin-right: 6px; padding: 2px 4px; cursor: pointer; font-size: 13px; color: #1989fa; text-decoration: none; }
.op-link:hover { text-decoration: underline; }
.op-link.primary { color: #1989fa; }
.op-link.danger { color: #ee0a24; }

.dialog-body { padding: 12px 0; }
.dialog-body-large { max-height: 70vh; overflow-y: auto; }
.form-select { width: 100%; padding: 6px 10px; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 14px; background: #fff; color: #1f2937; cursor: pointer; }

.perm-section { margin-top: 16px; padding: 0 16px; }
.perm-section-title { font-weight: 600; color: #1f2937; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
.perm-counter { font-weight: normal; font-size: 12px; color: #6b7280; margin-left: auto; }
.perm-actions { display: flex; gap: 12px; margin-bottom: 12px; }
.perm-actions a { color: #1989fa; font-size: 13px; cursor: pointer; }
.perm-actions a:hover { text-decoration: underline; }

.perm-modules { display: flex; flex-direction: column; gap: 12px; }
.perm-module { border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; }
.perm-module-head { background: #f9fafb; padding: 8px 12px; display: flex; align-items: center; justify-content: space-between; }
.perm-module-name { font-weight: 500; color: #374151; }
.perm-module-toggle { font-size: 12px; color: #6b7280; cursor: pointer; }
.perm-module-toggle input { margin-right: 4px; }
.perm-module-count { font-size: 12px; color: #9ca3af; }

.perm-items { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; padding: 8px; }
.perm-item { display: flex; align-items: center; gap: 6px; padding: 6px 8px; border-radius: 4px; cursor: pointer; border: 1px solid transparent; }
.perm-item:hover { background: #f9fafb; }
.perm-item.checked { background: #eff6ff; border-color: #bfdbfe; }
.perm-item input { width: 14px; height: 14px; }
.perm-item-readonly { cursor: default; }
.perm-item-readonly:hover { background: transparent; }
.pi-name { font-size: 13px; color: #1f2937; flex: 1; }
.pi-code { font-family: ui-monospace, monospace; font-size: 11px; color: #6b7280; background: #f3f4f6; padding: 1px 4px; border-radius: 3px; }
.pi-action { font-size: 11px; color: #1989fa; }
</style>
