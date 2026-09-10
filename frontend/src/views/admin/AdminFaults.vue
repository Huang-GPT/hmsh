<template>
  <div class="admin-faults">
    <h3>故障库管理</h3>

    <!-- Tabs -->
    <van-tabs v-model:active="tab" sticky offset-top="0" @click-tab="onTabChange">
      <van-tab title="故障分类" name="categories">
        <div class="toolbar">
          <van-search
            v-model="catKeyword"
            placeholder="搜索分类名"
            @search="loadCategories"
            shape="round"
          />
          <van-button v-if="$hasPermission('fault:create')" type="primary" size="small" icon="plus" @click="openCatCreate">新建分类</van-button>
        </div>

        <div v-if="categories.length === 0" class="empty-tip">
          <van-empty description="暂无故障分类" />
        </div>
        <van-cell-group v-else class="cat-list">
          <van-cell
            v-for="cat in categories"
            :key="cat.id"
            :title="cat.name"
            :label="`${cat.fault_count || 0} 个常见故障 · 排序 ${cat.sort_order || 0}`"
          >
            <template #icon>
              <span class="cat-icon">{{ cat.icon || '🔧' }}</span>
            </template>
            <template #right-icon>
              <van-tag v-if="cat.status === 'disabled'" type="danger" size="mini" class="mr-1">已停用</van-tag>
              <van-button v-if="$hasPermission('fault:edit')" size="mini" plain class="mr-1" @click="openCatEdit(cat)">编辑</van-button>
              <van-button v-if="$hasPermission('fault:delete')" size="mini" type="danger" plain @click="confirmCatDelete(cat)">停用</van-button>
            </template>
          </van-cell>
        </van-cell-group>
      </van-tab>

      <van-tab title="故障条目" name="faults">
        <div class="toolbar">
          <van-search
            v-model="faultKeyword"
            placeholder="搜索标题/内容"
            @search="loadFaults"
            shape="round"
          />
          <van-button v-if="$hasPermission('fault:create')" type="primary" size="small" icon="plus" @click="openFaultCreate">新建故障</van-button>
        </div>

        <van-cell-group class="fault-list">
          <van-cell
            v-for="f in faults"
            :key="f.id"
            :title="f.title"
            :label="`${f.category_name || '未分类'} · 适用型号 ${f.product_model || '通用'} · 排序 ${f.sort_order || 0}`"
            is-link
            @click="openFaultEdit(f)"
          >
            <template #right-icon>
              <van-tag v-if="f.status === 'disabled'" type="danger" size="mini" class="mr-1">已停用</van-tag>
              <van-button v-if="$hasPermission('fault:delete')" size="mini" type="danger" plain @click.stop="confirmFaultDelete(f)">停用</van-button>
            </template>
          </van-cell>
        </van-cell-group>
        <van-empty v-if="faults.length === 0" description="暂无故障条目" />
      </van-tab>
    </van-tabs>

    <!-- ============ 分类编辑弹窗 ============ -->
    <van-dialog
      v-model:show="showCatDialog"
      :title="editingCat ? '编辑故障分类' : '新建故障分类'"
      show-cancel-button
      @confirm="saveCat"
    >
      <div class="dialog-body">
        <van-field v-model="catForm.name" label="分类名称" placeholder="如: 电源故障" required maxlength="30" />
        <van-field v-model="catForm.icon" label="图标(Emoji)" placeholder="如: 🔌" maxlength="4" />
        <van-cell title="排序">
          <template #value>
            <input type="number" v-model.number="catForm.sort_order" class="num-input" min="0" />
          </template>
        </van-cell>
        <van-cell title="状态">
          <template #value>
            <van-switch v-model="catActive" />
            <span class="ml-1">{{ catActive ? '启用' : '停用' }}</span>
          </template>
        </van-cell>
      </div>
    </van-dialog>

    <!-- ============ 故障条目编辑弹窗 ============ -->
    <van-dialog
      v-model:show="showFaultDialog"
      :title="editingFault ? '编辑故障条目' : '新建故障条目'"
      show-cancel-button
      @confirm="saveFault"
    >
      <div class="dialog-body">
        <van-cell title="所属分类" :is-link="false">
          <template #value>
            <select v-model="faultForm.category_id" class="select-input">
              <option :value="null">请选择</option>
              <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </template>
        </van-cell>
        <van-field v-model="faultForm.title" label="标题" placeholder="如: 无法开机" required maxlength="60" />
        <van-field v-model="faultForm.product_model" label="适用型号" placeholder="如: HM-001（留空表示通用）" maxlength="40" />
        <van-field v-model="faultForm.content" label="详细内容" type="textarea" placeholder="故障描述、原因、解决方案…" rows="4" maxlength="1000" />

        <!-- ============ 常见故障文件管理（新增 2026-09 重构） ============ -->
        <div class="fault-files">
          <div class="files-title">
            <span>常见故障文件</span>
            <span class="files-hint">PDF / DOC / DOCX / 图片（单文件 ≤20MB）</span>
          </div>
          <div v-if="faultForm.files.length === 0" class="files-empty">暂无文件，请点击下方上传</div>
          <div v-for="(file, idx) in faultForm.files" :key="file.url" class="file-row">
            <van-icon :name="fileIcon(file)" :color="fileColor(file)" size="20" />
            <div class="file-meta">
              <div class="file-name" :title="file.filename">{{ file.filename }}</div>
              <div class="file-info">
                <span class="file-size">{{ formatSize(file.size) }}</span>
                <span class="file-kind">{{ fileKindLabel(file) }}</span>
              </div>
            </div>
            <van-button size="mini" plain type="danger" @click="removeFaultFile(idx)">删除</van-button>
          </div>
          <van-uploader
            v-if="faultForm.files.length < 20"
            class="files-uploader"
            :after-read="handleFaultFileUpload"
            :max-size="20 * 1024 * 1024"
            accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
            :preview-image="false"
            :multiple="true"
          >
            <van-button size="small" icon="plus" type="primary" plain>上传文件</van-button>
          </van-uploader>
        </div>

        <van-cell title="排序">
          <template #value>
            <input type="number" v-model.number="faultForm.sort_order" class="num-input" min="0" />
          </template>
        </van-cell>
        <van-cell title="状态">
          <template #value>
            <van-switch v-model="faultActive" />
            <span class="ml-1">{{ faultActive ? '启用' : '停用' }}</span>
          </template>
        </van-cell>
      </div>
    </van-dialog>
  </div>
</template>

<script>
import {
  getAllFaultCategories, createFaultCategory, updateFaultCategory, deleteFaultCategory,
  getAllFaults, createFault, updateFault, deleteFault,
  uploadFaultFile, deleteFaultFile,
} from '@/api/admin'

const emptyCatForm = () => ({
  name: '',
  icon: '',
  sort_order: 0,
  status: 'active',
})

const emptyFaultForm = () => ({
  category_id: null,
  title: '',
  content: '',
  product_model: '',
  files: [],
  sort_order: 0,
  status: 'active',
})

export default {
  name: 'AdminFaults',
  data() {
    return {
      tab: 'categories',

      // 分类
      catKeyword: '',
      categories: [],
      showCatDialog: false,
      editingCat: null,
      catForm: emptyCatForm(),
      catActive: true,

      // 故障条目
      faultKeyword: '',
      faults: [],
      showFaultDialog: false,
      editingFault: null,
      faultForm: emptyFaultForm(),
      faultActive: true,
    }
  },
  created() {
    this.loadCategories()
    this.loadFaults()
  },
  methods: {
    onTabChange() {
      if (this.tab === 'categories') this.loadCategories()
      else this.loadFaults()
    },

    // ===== 分类 =====
    async loadCategories() {
      try {
        const res = await getAllFaultCategories({ keyword: this.catKeyword })
        this.categories = (res.data && res.data.categories) || []
      } catch (e) {
        console.error(e)
      }
    },
    openCatCreate() {
      this.editingCat = null
      this.catForm = emptyCatForm()
      this.catActive = true
      this.showCatDialog = true
    },
    openCatEdit(cat) {
      this.editingCat = cat
      this.catForm = { ...cat }
      this.catActive = cat.status !== 'disabled'
      this.showCatDialog = true
    },
    async saveCat() {
      if (!this.catForm.name || !this.catForm.name.trim()) {
        this.$toast('请填写分类名称')
        return false
      }
      this.catForm.status = this.catActive ? 'active' : 'disabled'
      try {
        if (this.editingCat) {
          await updateFaultCategory(this.editingCat.id, this.catForm)
          this.$toast.success('更新成功')
        } else {
          await createFaultCategory(this.catForm)
          this.$toast.success('创建成功')
        }
        this.showCatDialog = false
        this.loadCategories()
      } catch (e) {
        const msg = (e && e.response && e.response.data && e.response.data.error) || '操作失败'
        this.$toast(msg)
        return false
      }
      return true
    },
    confirmCatDelete(cat) {
      this.$dialog.confirm({
        title: '停用确认',
        message: `确定停用分类「${cat.name}」吗？该分类下的故障条目不会被删除。`,
      }).then(async () => {
        try {
          await deleteFaultCategory(cat.id)
          this.$toast.success('已停用')
          this.loadCategories()
        } catch (e) {
          this.$toast('操作失败')
        }
      }).catch(() => {})
    },

    // ===== 故障条目 =====
    async loadFaults() {
      try {
        const res = await getAllFaults({ keyword: this.faultKeyword })
        this.faults = (res.data && res.data.faults) || []
      } catch (e) {
        console.error(e)
      }
    },
    openFaultCreate() {
      this.editingFault = null
      this.faultForm = emptyFaultForm()
      this.faultActive = true
      this.showFaultDialog = true
    },
    openFaultEdit(f) {
      this.editingFault = f
      this.faultForm = {
        category_id: f.category_id,
        title: f.title,
        content: f.content,
        product_model: f.product_model,
        files: Array.isArray(f.files) ? [...f.files] : [],
        sort_order: f.sort_order || 0,
        status: f.status,
      }
      this.faultActive = f.status !== 'disabled'
      this.showFaultDialog = true
    },
    async saveFault() {
      if (!this.faultForm.title || !this.faultForm.title.trim()) {
        this.$toast('请填写标题')
        return false
      }
      if (!this.faultForm.category_id) {
        this.$toast('请选择分类')
        return false
      }
      this.faultForm.status = this.faultActive ? 'active' : 'disabled'
      try {
        if (this.editingFault) {
          await updateFault(this.editingFault.id, this.faultForm)
          this.$toast.success('更新成功')
        } else {
          await createFault(this.faultForm)
          this.$toast.success('创建成功')
        }
        this.showFaultDialog = false
        this.loadFaults()
      } catch (e) {
        const msg = (e && e.response && e.response.data && e.response.data.error) || '操作失败'
        this.$toast(msg)
        return false
      }
      return true
    },
    confirmFaultDelete(f) {
      this.$dialog.confirm({
        title: '停用确认',
        message: `确定停用故障「${f.title}」吗？手机端将不再展示。`,
      }).then(async () => {
        try {
          await deleteFault(f.id)
          this.$toast.success('已停用')
          this.loadFaults()
        } catch (e) {
          this.$toast('操作失败')
        }
      }).catch(() => {})
    },

    // ===== 故障文件管理 =====
    fileExt(file) {
      return (file.filename || '').toLowerCase().split('.').pop() || ''
    },
    fileIcon(file) {
      const ext = this.fileExt(file)
      if (ext === 'pdf') return 'description'
      if (ext === 'doc' || ext === 'docx') return 'word'
      if (['jpg', 'jpeg', 'png'].includes(ext)) return 'photo-o'
      return 'file-o'
    },
    fileColor(file) {
      const ext = this.fileExt(file)
      if (ext === 'pdf') return '#e74c3c'
      if (ext === 'doc' || ext === 'docx') return '#2c5aa0'
      if (['jpg', 'jpeg', 'png'].includes(ext)) return '#16a34a'
      return '#666'
    },
    fileKindLabel(file) {
      const ext = this.fileExt(file)
      const map = { pdf: 'PDF', doc: 'DOC', docx: 'DOCX', jpg: 'JPG', jpeg: 'JPG', png: 'PNG' }
      return map[ext] || ext.toUpperCase()
    },
    formatSize(bytes) {
      if (!bytes) return ''
      if (bytes < 1024) return bytes + ' B'
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
      return (bytes / 1024 / 1024).toFixed(1) + ' MB'
    },
    async handleFaultFileUpload(fileObj) {
      // van-uploader 多文件时 fileObj 是数组；单文件是单个对象
      const files = Array.isArray(fileObj) ? fileObj : [fileObj]
      for (const item of files) {
        if (!item || !item.file) continue
        item.status = 'uploading'
        item.message = '上传中…'
        try {
          const res = await uploadFaultFile(item.file)
          const d = (res && res.data) || {}
          // 立即保存到 DB（不依赖 dialog 的 save 按钮）
          if (this.editingFault && this.editingFault.id) {
            const next = [...this.faultForm.files, {
              url: d.url,
              filename: d.filename,
              size: d.size,
              content_type: d.content_type,
              kind: d.kind,
            }]
            await updateFault(this.editingFault.id, { files: next })
            this.faultForm.files = next
          }
          item.status = 'done'
        } catch (e) {
          item.status = 'failed'
          item.message = (e && e.response && e.response.data && e.response.data.error) || '上传失败'
        }
      }
      // 同步刷新列表中该条目的 files（不重载整列表）
      if (this.editingFault && this.editingFault.id) {
        const idx = this.faults.findIndex(x => x.id === this.editingFault.id)
        if (idx >= 0) this.faults[idx].files = [...this.faultForm.files]
      }
    },
    async removeFaultFile(idx) {
      const file = this.faultForm.files[idx]
      if (!file) return
      try {
        await this.$dialog.confirm({
          title: '删除确认',
          message: `确定删除文件「${file.filename}」吗？文件将从服务器彻底删除。`,
        })
      } catch (_) {
        return
      }
      try {
        // 后端 URL 形如 /uploads/faults/<date>/<uuid>.<ext>，去掉前缀
        const rel = (file.url || '').replace(/^\/uploads\//, '')
        await deleteFaultFile(rel)
        this.faultForm.files.splice(idx, 1)
        if (this.editingFault && this.editingFault.id) {
          await updateFault(this.editingFault.id, { files: this.faultForm.files })
          const i = this.faults.findIndex(x => x.id === this.editingFault.id)
          if (i >= 0) this.faults[i].files = [...this.faultForm.files]
        }
        this.$toast.success('已删除')
      } catch (e) {
        this.$toast((e && e.response && e.response.data && e.response.data.error) || '删除失败')
      }
    },
  },
}
</script>

<style scoped>
.admin-faults {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  min-height: calc(100vh - 88px);
}
h3 {
  margin: 0 0 16px;
  font-size: 18px;
  color: #1f2937;
}
.toolbar {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 8px 0;
}
.toolbar .van-search {
  flex: 1;
}
.empty-tip {
  padding: 40px 0;
}
.cat-list,
.fault-list {
  margin-top: 8px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.cat-icon {
  font-size: 22px;
  margin-right: 8px;
  flex-shrink: 0;
}
.mr-1 {
  margin-right: 6px;
}
.ml-1 {
  margin-left: 6px;
}
.dialog-body {
  padding: 8px 0;
  max-height: 60vh;
  overflow-y: auto;
}
.num-input,
.select-input {
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 13px;
  background: #fff;
  min-width: 80px;
}
.select-input {
  min-width: 140px;
}

/* ============ 常见故障文件管理样式 ============ */
.fault-files {
  margin: 12px 16px;
  padding: 12px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}
.files-title {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
}
.files-hint {
  font-size: 11px;
  color: #6b7280;
  font-weight: normal;
}
.files-empty {
  padding: 12px 0;
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
}
.file-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid #f3f4f6;
}
.file-row:last-of-type {
  border-bottom: none;
}
.file-meta {
  flex: 1;
  min-width: 0;
}
.file-name {
  font-size: 13px;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 280px;
}
.file-info {
  display: flex;
  gap: 8px;
  margin-top: 2px;
  font-size: 11px;
  color: #6b7280;
}
.file-kind {
  background: #e5e7eb;
  padding: 1px 6px;
  border-radius: 3px;
  font-weight: 500;
}
.files-uploader {
  margin-top: 8px;
}
</style>