<template>
  <div class="admin-faults">
    <div class="page-header">
      <h3>故障文件库</h3>
      <p class="page-sub">上传与管理常见故障的 PDF 文档、图片与 Office 文档（移动端自动展示）</p>
    </div>

    <!-- 工具栏：搜索 + 类型筛选 + 操作 -->
    <div class="toolbar">
      <div class="toolbar-row">
        <van-search
          v-model="keyword"
          placeholder="搜索文件名 / 描述"
          @search="loadFiles(1)"
          shape="round"
          class="search-box"
          background="transparent"
        />
        <van-button size="small" plain icon="replay" @click="loadFiles()">刷新</van-button>
      </div>
      <div class="toolbar-row toolbar-filters">
        <span
          v-for="f in typeFilters"
          :key="f.value"
          :class="['filter-chip', { active: typeFilter === f.value }]"
          @click="setTypeFilter(f.value)"
        >
          {{ f.label }} <span class="chip-count">({{ typeCounts[f.value] || 0 }})</span>
        </span>
      </div>
    </div>

    <!-- 表格 -->
    <div class="table-wrap">
      <table class="file-table">
        <thead>
          <tr>
            <th class="col-thumb">预览</th>
            <th>文件名</th>
            <th>类型</th>
            <th>大小</th>
            <th>描述</th>
            <th>上传时间</th>
            <th>上传人</th>
            <th class="col-actions">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading && files.length === 0">
            <td colspan="8" class="state-cell">加载中…</td>
          </tr>
          <tr v-else-if="files.length === 0">
            <td colspan="8" class="state-cell">
              <div class="empty-cell">
                <div class="empty-icon">📁</div>
                <div class="empty-text">暂无文件</div>
                <div class="empty-hint">点击下方"上传文件"按钮开始</div>
              </div>
            </td>
          </tr>
          <tr v-for="f in files" :key="f.id">
            <td class="col-thumb">
              <div class="thumb" :class="`thumb-${f.kind}`" @click="previewFile(f)">
                <van-icon v-if="f.kind !== 'image'" :name="kindIcon(f)" size="22" :color="kindColor(f)" />
                <img v-else :src="normalizeUrl(f.url)" :alt="f.filename" />
              </div>
            </td>
            <td class="col-name" :title="f.filename">{{ f.filename }}</td>
            <td>
              <span class="kind-badge" :class="`kind-badge-${f.kind}`">{{ kindLabel(f.kind) }}</span>
            </td>
            <td class="col-size">{{ formatSize(f.size) }}</td>
            <td class="col-desc" :title="f.description || ''">
              {{ f.description || '—' }}
            </td>
            <td class="col-time">{{ formatDate(f.created_at) }}</td>
            <td>{{ f.uploader_name || '—' }}</td>
            <td class="col-actions" @click.stop>
              <a v-if="f.kind === 'image' || f.kind === 'pdf'" class="op-link primary" @click="previewFile(f)">预览</a>
              <a class="op-link" @click="downloadFile(f)">下载</a>
              <a class="op-link" @click="openEditDesc(f)">编辑</a>
              <a class="op-link danger" @click="confirmDelete(f)">删除</a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 隐藏的批量上传 input -->
    <input
      ref="fileInputRef"
      type="file"
      multiple
      accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.gif,.webp,.bmp"
      style="display: none"
      @change="onFilesSelected"
    />

    <!-- 底部悬浮操作条 -->
    <div class="bottom-bar">
      <span class="stat-tip">共 {{ total }} 个文件</span>
      <van-button
        type="primary"
        size="small"
        icon="plus"
        :loading="uploading"
        @click="openUploadPicker"
      >
        上传文件
      </van-button>
    </div>

    <!-- 描述编辑弹窗 -->
    <van-dialog
      v-model:show="showEditDialog"
      title="编辑描述"
      show-cancel-button
      @confirm="saveDescription"
    >
      <div class="dialog-body">
        <div class="edit-filename" :title="editingFile && editingFile.filename">
          {{ editingFile && editingFile.filename }}
        </div>
        <van-field
          v-model="editingDescription"
          type="textarea"
          rows="3"
          maxlength="500"
          show-word-limit
          placeholder="为该文件添加一段描述（可选）"
        />
      </div>
    </van-dialog>

    <!-- 图片预览 -->
    <van-image-preview
      v-model:show="showImagePreview"
      :images="previewImages"
      :start-position="previewStart"
      closeable
    />
  </div>
</template>

<script>
import {
  getFaultFiles,
  uploadFaultFile,
  deleteFaultFile,
  updateFaultFile,
} from '@/api/admin'

const TYPE_FILTERS = [
  { value: '', label: '全部' },
  { value: 'pdf', label: 'PDF' },
  { value: 'image', label: '图片' },
  { value: 'doc', label: '文档' },
]

export default {
  name: 'AdminFaults',
  data() {
    return {
      files: [],
      loading: false,
      total: 0,
      keyword: '',
      typeFilter: '',

      uploading: false,
      uploadQueue: [],   // 待上传队列 { file, status, error }

      showEditDialog: false,
      editingFile: null,
      editingDescription: '',

      showImagePreview: false,
      previewImages: [],
      previewStart: 0,
    }
  },
  computed: {
    typeFilters() {
      return TYPE_FILTERS
    },
    // 当前结果内每个类型的计数（仅基于当前已加载数据，不重查后端）
    typeCounts() {
      const counts = { '': this.files.length, pdf: 0, image: 0, doc: 0 }
      for (const f of this.files) {
        if (counts[f.kind] !== undefined) counts[f.kind]++
      }
      return counts
    },
  },
  created() {
    this.loadFiles()
  },
  methods: {
    setTypeFilter(v) {
      this.typeFilter = v
      this.loadFiles()
    },

    // ============ 文件工具方法 ============
    kindIcon(f) {
      if (f.kind === 'pdf') return 'description'
      if (f.kind === 'doc') return 'word'
      return 'file-o'
    },
    kindColor(f) {
      if (f.kind === 'pdf') return '#e74c3c'
      if (f.kind === 'doc') return '#2c5aa0'
      return '#909399'
    },
    kindLabel(kind) {
      const map = { pdf: 'PDF', image: '图片', doc: 'DOC' }
      return map[kind] || kind.toUpperCase()
    },
    formatSize(bytes) {
      if (!bytes && bytes !== 0) return '—'
      if (bytes < 1024) return bytes + ' B'
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
      return (bytes / 1024 / 1024).toFixed(1) + ' MB'
    },
    formatDate(s) {
      if (!s) return '—'
      const str = String(s).replace('T', ' ')
      return str.length >= 16 ? str.substring(0, 16) : str
    },
    normalizeUrl(url) {
      if (!url) return ''
      if (/^https?:\/\//.test(url) || url.startsWith('data:')) return url
      return url.startsWith('/') ? url : '/' + url
    },

    // ============ 列表 ============
    async loadFiles() {
      this.loading = true
      try {
        const params = {}
        if (this.keyword) params.keyword = this.keyword
        if (this.typeFilter) params.kind = this.typeFilter
        const res = await getFaultFiles(params)
        this.files = (res.data && res.data.files) || []
        this.total = (res.data && res.data.total) || this.files.length
      } catch (e) {
        console.error(e)
        this.$toast('加载失败')
      } finally {
        this.loading = false
      }
    },

    // ============ 上传 ============
    openUploadPicker() {
      if (this.$refs.fileInputRef) this.$refs.fileInputRef.click()
    },
    onFilesSelected(event) {
      const fileList = Array.from(event.target.files || [])
      // 允许重复选择同一文件
      event.target.value = ''
      if (fileList.length === 0) return
      this.uploadQueue = fileList.map(f => ({ file: f, status: 'pending', error: '' }))
      this.uploadAll()
    },
    async uploadAll() {
      this.uploading = true
      let ok = 0, fail = 0
      const failNames = []
      for (const item of this.uploadQueue) {
        if (item.status !== 'pending') continue
        item.status = 'uploading'
        item.error = ''
        try {
          await uploadFaultFile(item.file, '')
          item.status = 'done'
          ok++
        } catch (e) {
          item.status = 'failed'
          item.error = (e && e.response && e.response.data && e.response.data.error) || '上传失败'
          fail++
          failNames.push(`${item.file.name} (${item.error})`)
        }
      }
      this.uploading = false
      // 清理已结束的项
      this.uploadQueue = this.uploadQueue.filter(it => it.status === 'uploading' || it.status === 'pending')
      if (ok > 0) this.$toast.success(`上传成功 ${ok} 个`)
      if (fail > 0) {
        this.$dialog.alert({
          title: `上传失败 ${fail} 个`,
          message: failNames.join('\n'),
          confirmButtonText: '知道了',
        }).catch(() => {})
      }
      if (ok > 0) this.loadFiles()
    },

    // ============ 预览 / 下载 ============
    previewFile(f) {
      if (f.kind === 'image') {
        this.previewImages = [{ url: this.normalizeUrl(f.url) }]
        this.previewStart = 0
        this.showImagePreview = true
        return
      }
      if (f.kind === 'pdf') {
        // PDF 用浏览器原生查看（新标签）
        window.open(this.normalizeUrl(f.url), '_blank')
        return
      }
      // doc / 其他：直接下载
      this.downloadFile(f)
    },
    downloadFile(f) {
      const a = document.createElement('a')
      a.href = this.normalizeUrl(f.url)
      a.download = f.filename || 'download'
      a.style.display = 'none'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    },

    // ============ 描述编辑 ============
    openEditDesc(f) {
      this.editingFile = f
      this.editingDescription = f.description || ''
      this.showEditDialog = true
    },
    async saveDescription() {
      if (!this.editingFile) return
      try {
        await updateFaultFile(this.editingFile.id, {
          description: this.editingDescription,
        })
        this.$toast.success('已保存')
        this.showEditDialog = false
        this.loadFiles()
      } catch (e) {
        this.$toast((e && e.response && e.response.data && e.response.data.error) || '保存失败')
      }
    },

    // ============ 删除 ============
    confirmDelete(f) {
      this.$dialog.confirm({
        title: '删除确认',
        message: `确定删除文件「${f.filename}」吗？`,
      }).then(async () => {
        try {
          await deleteFaultFile(f.id)
          this.$toast.success('已删除')
          this.loadFiles()
        } catch (e) {
          this.$toast((e && e.response && e.response.data && e.response.data.error) || '删除失败')
        }
      }).catch(() => {})
    },
  },
}
</script>

<style scoped>
.admin-faults { max-width: 1400px; padding-bottom: 80px; }
.page-header { margin-bottom: var(--space-5); }
.admin-faults h3 {
  margin: 0 0 var(--space-1);
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--color-text);
}
.page-sub {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
}

/* ===== Toolbar ===== */
.toolbar {
  background: var(--color-bg-card);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  margin-bottom: var(--space-4);
  box-shadow: var(--shadow-card);
}
.toolbar-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}
.toolbar-row + .toolbar-row {
  margin-top: var(--space-3);
}
.toolbar-filters {
  border-top: 1px solid var(--color-divider);
  padding-top: var(--space-3);
}
.search-box {
  flex: 1;
  min-width: 280px;
}
.filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 14px;
  border-radius: var(--radius-full);
  background: var(--color-bg-muted);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-base);
  border: 1px solid transparent;
}
.filter-chip:hover {
  background: var(--color-border-light);
}
.filter-chip.active {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}
.chip-count {
  font-size: var(--text-xs);
  opacity: 0.85;
}

/* ===== Table ===== */
.table-wrap {
  background: var(--color-bg-card);
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
}
.file-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
}
.file-table th,
.file-table td {
  padding: 12px var(--space-2);
  text-align: left;
  vertical-align: middle;
}
.file-table thead {
  background: var(--color-bg-muted);
}
.file-table th {
  font-weight: var(--font-semibold);
  color: var(--color-text-secondary);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}
.file-table td {
  border-bottom: 1px solid var(--color-divider);
  color: var(--color-text-secondary);
}
.file-table tbody tr { transition: background var(--transition-fast); }
.file-table tbody tr:hover td { background: var(--brand-50); }

.col-thumb { width: 60px; }
.col-name { max-width: 240px; }
.col-size { width: 100px; font-family: ui-monospace, monospace; }
.col-desc { max-width: 220px; color: var(--color-text-tertiary); }
.col-time { width: 140px; font-family: ui-monospace, monospace; font-size: var(--text-xs); white-space: nowrap; }
.col-actions { width: 220px; white-space: nowrap; }

/* ===== Thumbnail ===== */
.thumb {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-sm);
  background: var(--color-bg-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  overflow: hidden;
  transition: transform var(--transition-fast);
}
.thumb:hover {
  transform: scale(1.05);
}
.thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.thumb-pdf {
  background: #fef2f2;
}
.thumb-doc {
  background: #eff6ff;
}
.thumb-image {
  background: var(--color-bg-muted);
}

/* ===== Kind badge ===== */
.kind-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  white-space: nowrap;
}
.kind-badge-pdf {
  background: #fef2f2;
  color: #b91c1c;
}
.kind-badge-image {
  background: #ecfdf5;
  color: #047857;
}
.kind-badge-doc {
  background: #eff6ff;
  color: #1d4ed8;
}

/* ===== State / Empty ===== */
.state-cell {
  text-align: center !important;
  padding: 60px !important;
  color: var(--color-text-tertiary);
  font-size: var(--text-sm);
}
.empty-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
}
.empty-icon { font-size: 48px; opacity: 0.5; }
.empty-text { font-size: var(--text-base); color: var(--color-text-tertiary); }
.empty-hint { font-size: var(--text-sm); color: var(--color-text-placeholder); }

/* ===== Action links ===== */
.op-link {
  display: inline-block;
  margin-right: var(--space-2);
  cursor: pointer;
  font-size: var(--text-sm);
  color: var(--color-primary);
  text-decoration: none;
}
.op-link:hover { text-decoration: underline; }
.op-link.primary { color: var(--color-primary); }
.op-link.danger { color: var(--color-danger); }

/* ===== Bottom bar ===== */
.bottom-bar {
  position: fixed;
  bottom: var(--space-4);
  right: var(--space-4);
  display: flex;
  gap: var(--space-3);
  align-items: center;
  background: var(--color-bg-card);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-full);
  box-shadow: var(--shadow-md);
  z-index: 10;
}
.stat-tip {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
}

/* ===== Dialog ===== */
.dialog-body {
  padding: var(--space-3) var(--space-4);
}
.edit-filename {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-3);
  word-break: break-all;
  line-height: 1.5;
  max-height: 60px;
  overflow-y: auto;
}
</style>