<template>
  <div class="admin-service-points">
    <h3>服务点维护</h3>

    <div class="toolbar">
      <div class="toolbar-row toolbar-top">
        <van-search
          v-model="keyword"
          placeholder="搜索名称/联系人/电话/地区"
          @search="loadData(true)"
          shape="round"
          class="search-box"
        />
      </div>
      <div class="toolbar-row toolbar-bottom">
        <span
          v-for="f in statusFilters"
          :key="'s-' + f.value"
          :class="['filter-chip', { active: statusFilter === f.value }]"
          @click="setStatusFilter(f.value)"
        >{{ f.label }}</span>
        <van-button size="small" plain icon="replay" @click="loadData(true)">刷新</van-button>
        <van-button size="small" type="primary" icon="plus" @click="openCreate">新增服务点</van-button>
        <van-button size="small" plain icon="down" @click="onExport">导出CSV</van-button>
        <van-button size="small" plain icon="upgrade" @click="showImportDialog = true">导入CSV</van-button>
      </div>
    </div>

    <div class="table-wrap">
      <table class="sp-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>名称</th>
            <th>联系人</th>
            <th>联系电话</th>
            <th>地区</th>
            <th>地址</th>
            <th>状态</th>
            <th>创建时间</th>
            <th class="col-actions">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading && rows.length === 0">
            <td colspan="9" class="state-cell">加载中…</td>
          </tr>
          <tr v-else-if="filteredRows.length === 0">
            <td colspan="9" class="state-cell">
              <div class="empty-cell">
                <div class="empty-icon">🏢</div>
                <div class="empty-text">暂无服务点</div>
              </div>
            </td>
          </tr>
          <tr v-for="row in filteredRows" :key="row.id" :class="{ 'row-disabled': row.status === 'disabled' }">
            <td class="col-mono">{{ row.id }}</td>
            <td><strong>{{ row.name }}</strong></td>
            <td>{{ row.contact_person || '—' }}</td>
            <td class="col-mono">{{ row.contact_phone || '—' }}</td>
            <td>{{ row.region || '—' }}</td>
            <td class="col-address">{{ row.address || '—' }}</td>
            <td>
              <van-tag :type="row.status === 'active' ? 'success' : 'default'" size="mini">
                {{ row.status === 'active' ? '启用' : '停用' }}
              </van-tag>
            </td>
            <td class="col-time">{{ formatDate(row.created_at) }}</td>
            <td class="col-actions" @click.stop>
              <a class="op-link primary" @click="openEdit(row)">编辑</a>
              <a v-if="row.status === 'active'" class="op-link warning" @click="onDisable(row)">停用</a>
              <a v-else class="op-link success" @click="onRestore(row)">启用</a>
              <a class="op-link danger" @click="onHardDelete(row)">删除</a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="stat-bar">
      共 <strong>{{ rows.length }}</strong> 条 · 当前展示 <strong>{{ filteredRows.length }}</strong> 条
    </div>

    <!-- ============ 新增/编辑弹窗 ============ -->
    <van-dialog v-model:show="showForm" :title="formMode === 'create' ? '新增服务点' : '编辑服务点'" show-cancel-button @confirm="submitForm" width="90%">
      <div class="dialog-body">
        <van-cell-group inset>
          <van-field v-model="form.name" label="名称" placeholder="服务点名称（不可重复）" required maxlength="100" />
          <van-field v-model="form.contact_person" label="联系人" placeholder="选填" maxlength="50" />
          <van-field v-model="form.contact_phone" label="联系电话" placeholder="选填" type="tel" maxlength="20" />
          <van-field v-model="form.region" label="地区" placeholder="如：北京" maxlength="100" />
          <van-field v-model="form.address" label="地址" placeholder="详细地址" maxlength="255" />
        </van-cell-group>
      </div>
    </van-dialog>

    <!-- ============ 导入CSV弹窗 ============ -->
    <van-dialog v-model:show="showImportDialog" title="导入服务点" show-cancel-button @confirm="submitImport" width="85%">
      <div class="dialog-body">
        <div class="dialog-tip">
          CSV 列顺序：<strong>名称,联系人,联系电话,地区,地址</strong>（第一行可作为表头自动跳过）<br>
          同名服务点会被覆盖更新。如需模板，请点"导出CSV"后修改。
        </div>
        <van-cell-group inset>
          <van-field name="file" label="选择文件">
            <template #input>
              <input type="file" accept=".csv" @change="onFileChange" class="file-input" />
            </template>
          </van-field>
        </van-cell-group>
        <div v-if="importFile" class="file-info">
          已选：<strong>{{ importFile.name }}</strong>（{{ (importFile.size / 1024).toFixed(1) }} KB）
        </div>
      </div>
    </van-dialog>

    <!-- ============ 确认删除弹窗 ============ -->
    <van-dialog v-model:show="showHardDeleteConfirm" title="删除服务点" show-cancel-button @confirm="submitHardDelete">
      <div class="dialog-body">
        <div class="dialog-tip">确定彻底删除服务点 <strong>{{ currentRow && currentRow.name }}</strong>？</div>
        <div class="dialog-warn">⚠️ 此操作不可恢复，且仅在服务点下无用户/工程师/工单关联时才能成功。</div>
      </div>
    </van-dialog>
  </div>
</template>

<script>
import {
  listAllServicePoints, createServicePoint, updateServicePoint,
  softDeleteServicePoint, restoreServicePoint, hardDeleteServicePoint,
  importServicePoints, exportServicePointsUrl,
} from '@/api/admin'

export default {
  name: 'AdminServicePoints',
  data() {
    return {
      rows: [],
      loading: false,
      keyword: '',
      statusFilter: 'all',
      statusFilters: [
        { value: 'all', label: '全部状态' },
        { value: 'active', label: '启用' },
        { value: 'disabled', label: '停用' },
      ],

      showForm: false,
      formMode: 'create',
      form: this.emptyForm(),

      showHardDeleteConfirm: false,
      currentRow: null,

      showImportDialog: false,
      importFile: null,
    }
  },
  computed: {
    filteredRows() {
      let list = this.rows
      if (this.statusFilter !== 'all') {
        list = list.filter(r => r.status === this.statusFilter)
      }
      if (this.keyword) {
        const kw = this.keyword.toLowerCase()
        list = list.filter(r =>
          (r.name && r.name.toLowerCase().includes(kw)) ||
          (r.contact_person && r.contact_person.toLowerCase().includes(kw)) ||
          (r.contact_phone && r.contact_phone.includes(kw)) ||
          (r.region && r.region.toLowerCase().includes(kw)) ||
          (r.address && r.address.toLowerCase().includes(kw))
        )
      }
      return list
    },
  },
  async created() {
    await this.loadData(true)
  },
  methods: {
    emptyForm() {
      return { name: '', contact_person: '', contact_phone: '', region: '', address: '' }
    },
    setStatusFilter(v) { this.statusFilter = v },
    async loadData(showLoading) {
      if (showLoading) this.loading = true
      try {
        const res = await listAllServicePoints()
        this.rows = (res.data && res.data.items) || []
      } catch (e) {
        this.rows = []
      } finally {
        this.loading = false
      }
    },
    openCreate() {
      this.formMode = 'create'
      this.form = this.emptyForm()
      this.showForm = true
    },
    openEdit(row) {
      this.formMode = 'edit'
      this.form = {
        name: row.name,
        contact_person: row.contact_person || '',
        contact_phone: row.contact_phone || '',
        region: row.region || '',
        address: row.address || '',
      }
      this.currentRow = row
      this.showForm = true
    },
    async submitForm() {
      const f = this.form
      if (!f.name || !f.name.trim()) {
        this.$toast('请填写名称')
        return
      }
      try {
        const payload = {
          name: f.name.trim(),
          contact_person: (f.contact_person || '').trim() || null,
          contact_phone: (f.contact_phone || '').trim() || null,
          region: (f.region || '').trim() || null,
          address: (f.address || '').trim() || null,
        }
        if (this.formMode === 'create') {
          await createServicePoint(payload)
          this.$toast.success('创建成功')
        } else {
          await updateServicePoint(this.currentRow.id, payload)
          this.$toast.success('更新成功')
        }
        this.showForm = false
        this.loadData(false)
      } catch (e) {
        const err = (e && e.response && e.response.data && e.response.data.error) || '操作失败'
        this.$toast(err)
      }
    },
    async onDisable(row) {
      try {
        await softDeleteServicePoint(row.id)
        this.$toast.success('已停用')
        this.loadData(false)
      } catch (e) {
        this.$toast('操作失败')
      }
    },
    async onRestore(row) {
      try {
        await restoreServicePoint(row.id)
        this.$toast.success('已启用')
        this.loadData(false)
      } catch (e) {
        this.$toast('操作失败')
      }
    },
    onHardDelete(row) {
      this.currentRow = row
      this.showHardDeleteConfirm = true
    },
    async submitHardDelete() {
      try {
        await hardDeleteServicePoint(this.currentRow.id)
        this.$toast.success('已彻底删除')
        this.showHardDeleteConfirm = false
        this.currentRow = null
        this.loadData(false)
      } catch (e) {
        const err = (e && e.response && e.response.data && e.response.data.error) || '操作失败'
        this.$toast(err)
        // 不关闭弹窗，让用户看错误后手动取消
      }
    },
    onFileChange(ev) {
      const f = ev.target.files && ev.target.files[0]
      this.importFile = f || null
    },
    async submitImport() {
      if (!this.importFile) {
        this.$toast('请先选择文件')
        return
      }
      try {
        const res = await importServicePoints(this.importFile)
        const data = res.data || {}
        const msg = data.message || (`新增 ${data.created || 0} 条，更新 ${data.updated || 0} 条`)
        this.$toast.success(msg)
        this.showImportDialog = false
        this.importFile = null
        this.loadData(false)
      } catch (e) {
        const err = (e && e.response && e.response.data && e.response.data.error) || '导入失败'
        this.$toast(err)
      }
    },
    onExport() {
      // 直接打开下载链接，浏览器自动带 cookie
      window.open(exportServicePointsUrl(), '_blank')
    },
    formatDate(d) {
      if (!d) return '—'
      const s = String(d)
      return s.length >= 10 ? s.substring(0, 10) : s
    },
  },
}
</script>

<style scoped>
.admin-service-points h3 {
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
.sp-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.sp-table th { background: #f9fafb; padding: 10px 8px; text-align: left; font-weight: 600; color: #374151; border-bottom: 1px solid #e5e7eb; white-space: nowrap; }
.sp-table td { padding: 10px 8px; border-bottom: 1px solid #f3f4f6; color: #4b5563; vertical-align: middle; }
.sp-table tbody tr:hover td { background: #f9fafb; }
.sp-table tbody tr.row-disabled td { opacity: 0.6; }
.col-mono { font-family: ui-monospace, monospace; font-size: 12px; }
.col-time { font-family: ui-monospace, monospace; font-size: 12px; }
.col-address { max-width: 280px; }
.state-cell { text-align: center; padding: 40px; color: #9ca3af; }
.empty-cell { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 20px; }
.empty-icon { font-size: 36px; }
.empty-text { font-size: 13px; color: #9ca3af; }

.col-actions { white-space: nowrap; }
.op-link { display: inline-block; margin-right: 6px; padding: 2px 4px; cursor: pointer; font-size: 13px; text-decoration: none; color: #1989fa; }
.op-link:hover { text-decoration: underline; }
.op-link.primary { color: #1989fa; }
.op-link.success { color: #07c160; }
.op-link.warning { color: #ee0a24; }
.op-link.danger { color: #ee0a24; }

.stat-bar {
  margin-top: 12px;
  font-size: 13px;
  color: #6b7280;
}
.stat-bar strong { color: #1989fa; margin: 0 2px; }

.dialog-body { padding: 12px 0; }
.dialog-tip { font-size: 13px; color: #6b7280; margin-bottom: 12px; padding: 0 16px; line-height: 1.6; }
.dialog-warn {
  font-size: 13px;
  color: #ee0a24;
  background: #fff7e8;
  border: 1px solid #ffd591;
  border-radius: 4px;
  padding: 8px 12px;
  margin: 8px 16px 0;
}
.file-input {
  width: 100%;
  padding: 6px 0;
  font-size: 13px;
}
.file-info {
  padding: 8px 16px 0;
  font-size: 13px;
  color: #4b5563;
}
.file-info strong { color: #1989fa; }
</style>
