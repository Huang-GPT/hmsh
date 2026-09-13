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

        <!-- ============ P1 标签字典管理 ============ -->
        <div class="tags-section">
          <div class="section-title">故障标签字典</div>
          <div class="tag-create-row">
            <van-field v-model="newTag.name" placeholder="标签名（如 紧急）" />
            <van-field v-model="newTag.slug" placeholder="slug（如 urgent）" />
            <van-button size="small" type="primary" @click="addTag">添加</van-button>
          </div>
          <van-cell-group v-if="availableTags.length" class="tags-list">
            <van-cell
              v-for="t in availableTags"
              :key="t.id"
              :title="t.name"
              :label="`slug: ${t.slug}`"
            >
              <template #right-icon>
                <van-tag :color="t.color" size="mini" class="mr-1">{{ t.slug }}</van-tag>
                <van-button size="mini" type="danger" plain @click="confirmDeleteTag(t)">删除</van-button>
              </template>
            </van-cell>
          </van-cell-group>
          <div v-else class="empty-tip" style="padding: 12px 0;">暂无标签</div>
        </div>
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

        <!-- ============ 常见故障文件管理（P0+P1 重构 2026-09） ============ -->
        <div class="fault-files">
          <div class="files-title">
            <span>常见故障文件</span>
            <span class="files-hint">PDF / DOC / DOCX / 图片（单文件 ≤20MB）</span>
          </div>
          <!-- P0：新建模式下禁用上传（必须先保存条目） -->
          <div v-if="!editingFault" class="files-empty files-empty-locked">
            ⚠️ 请先填写标题/分类并点击「确定」保存条目，再上传附件
          </div>
          <template v-else>
            <div v-if="faultForm.attachments.length === 0" class="files-empty">暂无文件，请点击下方上传</div>
            <div v-for="att in faultForm.attachments" :key="att.id" class="file-row">
              <van-icon :name="fileIcon(att)" :color="fileColor(att)" size="20" />
              <div class="file-meta">
                <div class="file-name" :title="att.filename">{{ att.filename }}</div>
                <div class="file-info">
                  <span class="file-size">{{ formatSize(att.size) }}</span>
                  <span class="file-kind">{{ fileKindLabel(att) }}</span>
                  <span v-if="att.uploaded_at" class="file-time">
                    · {{ formatUploadedTime(att.uploaded_at) }}
                  </span>
                </div>
              </div>
              <!-- P0 显式四态：上传中的临时条目 -->
              <span v-if="att.status === 'uploading'" class="status-tag status-uploading">上传中</span>
              <span v-else-if="att.status === 'failed'" class="status-tag status-failed">失败</span>
              <span v-else-if="att.status === 'done'" class="status-tag status-done">已上传</span>
              <van-button size="mini" plain type="danger" @click="removeFaultFile(att)">删除</van-button>
            </div>
            <van-uploader
              v-if="faultForm.attachments.length < 20"
              class="files-uploader"
              :after-read="handleFaultFileUpload"
              :max-size="20 * 1024 * 1024"
              accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
              :preview-image="false"
              :multiple="true"
            >
              <van-button size="small" icon="plus" type="primary" plain>上传文件</van-button>
            </van-uploader>
          </template>
        </div>

        <!-- ============ 故障标签（P1 多选） ============ -->
        <div v-if="availableTags.length > 0" class="fault-tags">
          <div class="files-title">
            <span>故障标签</span>
            <span class="files-hint">多选</span>
          </div>
          <div class="tag-list">
            <van-tag
              v-for="t in availableTags"
              :key="t.id"
              :type="faultForm.tag_ids.includes(t.id) ? 'primary' : 'default'"
              :color="faultForm.tag_ids.includes(t.id) ? t.color : undefined"
              plain
              class="tag-chip"
              @click="toggleTag(t.id)"
            >{{ t.name }}</van-tag>
          </div>
        </div>

        <!-- P1: 版本历史查看按钮（仅编辑模式可见） -->
        <div v-if="editingFault && editingFault.id" class="history-bar">
          <van-button size="small" plain icon="clock-o" @click="openRevisionDialog">查看版本历史</van-button>
          <span class="history-hint">每次更新自动保存快照</span>
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

    <!-- ============ P1 版本历史对话框 ============ -->
    <van-dialog
      v-model:show="showRevisionsDialog"
      title="版本历史"
      :show-confirm-button="false"
      close-on-click-overlay
    >
      <div class="dialog-body revision-dialog">
        <div v-if="revisions.length === 0" class="empty-tip">暂无历史版本（首次保存后才有）</div>
        <div v-for="r in revisions" :key="r.id" class="revision-row">
          <div class="rev-header">
            <span class="rev-version">v{{ r.version }}</span>
            <span class="rev-time">{{ formatUploadedTime(r.created_at) }}</span>
          </div>
          <div class="rev-note">{{ r.change_note || '(无说明)' }}</div>
        </div>
      </div>
    </van-dialog>
  </div>
</template>

<script>
import {
  getAllFaultCategories, createFaultCategory, updateFaultCategory, deleteFaultCategory,
  getAllFaults, createFault, updateFault, deleteFault,
  uploadFaultAttachment, deleteFaultAttachment, getFaultAttachments,
  listFaultTags, createFaultTag, deleteFaultTag, listFaultRevisions,
  searchFaultsFulltext,
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
  tag_ids: [],
  attachments: [],  // [{id, url, filename, size, kind, uploaded_at, uploaded_by_name, status}]
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
      availableTags: [],  // P1 标签字典
      newTag: { name: '', slug: '', color: '#909399' },  // P1 新建标签表单
      revisions: [],  // P1 版本历史
      showRevisionsDialog: false,
      showFaultDialog: false,
      editingFault: null,
      faultForm: emptyFaultForm(),
      faultActive: true,
    }
  },
  created() {
    this.loadCategories()
    this.loadFaults()
    this.loadTags()
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
      // P1：≥4 字符走 FULLTEXT (MATCH AGAINST)，短查询自动 fallback LIKE
      try {
        const kw = (this.faultKeyword || '').trim()
        const res = kw
          ? await searchFaultsFulltext(kw)
          : await getAllFaults({ keyword: kw })
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
    async openFaultEdit(f) {
      this.editingFault = f
      this.faultForm = {
        category_id: f.category_id,
        title: f.title,
        content: f.content,
        product_model: f.product_model,
        tag_ids: Array.isArray(f.tags) ? f.tags.map(t => t.id) : [],
        attachments: [],  // 异步加载
        sort_order: f.sort_order || 0,
        status: f.status,
      }
      this.faultActive = f.status !== 'disabled'
      this.showFaultDialog = true
      // 异步拉附件列表（list 接口不返回 attachments，detail 又未必有缓存）
      this.loadFaultAttachments(f.id)
    },
    async loadFaultAttachments(faultId) {
      try {
        const res = await getFaultAttachments(faultId)
        this.faultForm.attachments = (res.data && res.data.attachments) || []
      } catch (e) {
        console.error('加载附件失败', e)
        this.faultForm.attachments = []
      }
    },
    async loadTags() {
      try {
        const res = await listFaultTags()
        this.availableTags = (res.data && res.data.tags) || []
      } catch (e) {
        console.error('加载标签失败', e)
        this.availableTags = []
      }
    },
    toggleTag(tagId) {
      const idx = this.faultForm.tag_ids.indexOf(tagId)
      if (idx >= 0) this.faultForm.tag_ids.splice(idx, 1)
      else this.faultForm.tag_ids.push(tagId)
    },
    async addTag() {
      if (!this.newTag.name || !this.newTag.name.trim() || !this.newTag.slug || !this.newTag.slug.trim()) {
        this.$toast('请填写标签名和 slug')
        return
      }
      try {
        await createFaultTag({
          name: this.newTag.name.trim(),
          slug: this.newTag.slug.trim(),
          color: this.newTag.color || '#909399',
        })
        this.$toast.success('已添加')
        this.newTag = { name: '', slug: '', color: '#909399' }
        await this.loadTags()
      } catch (e) {
        this.$toast((e && e.response && e.response.data && e.response.data.error) || '添加失败')
      }
    },
    async confirmDeleteTag(t) {
      try {
        await this.$dialog.confirm({
          title: '删除标签',
          message: `确定删除标签「${t.name}」吗？使用此标签的故障条目会失去该标签。`,
        })
      } catch (_) { return }
      try {
        await deleteFaultTag(t.id)
        this.$toast.success('已删除')
        await this.loadTags()
      } catch (e) {
        this.$toast((e && e.response && e.response.data && e.response.data.error) || '删除失败')
      }
    },
    async openRevisionDialog() {
      if (!this.editingFault || !this.editingFault.id) {
        this.$toast('请先保存条目，再查看历史')
        return
      }
      this.showRevisionsDialog = true
      this.revisions = []
      try {
        const res = await listFaultRevisions(this.editingFault.id)
        this.revisions = (res.data && res.data.revisions) || []
      } catch (e) {
        this.$toast((e && e.response && e.response.data && e.response.data.error) || '加载历史失败')
      }
    },
    formatUploadedTime(iso) {
      if (!iso) return ''
      // iso 形如 '2026-09-13T06:29:14'，显示 '09-13 06:29'
      try {
        const d = new Date(iso)
        const mm = String(d.getMonth() + 1).padStart(2, '0')
        const dd = String(d.getDate()).padStart(2, '0')
        const hh = String(d.getHours()).padStart(2, '0')
        const mi = String(d.getMinutes()).padStart(2, '0')
        return `${mm}-${dd} ${hh}:${mi}`
      } catch (_) {
        return iso
      }
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
      // P0+P1 重构：不再发 files 字段（附件独立 endpoint 管理）
      // P1：发 tag_ids 数组
      const payload = { ...this.faultForm }
      delete payload.attachments  // 附件走独立 API
      try {
        if (this.editingFault) {
          await updateFault(this.editingFault.id, payload)
          this.$toast.success('更新成功')
        } else {
          const res = await createFault(payload)
          this.$toast.success('创建成功')
          // P0：新建后立即切到编辑模式，允许上传附件
          if (res && res.data && res.data.fault && res.data.fault.id) {
            this.editingFault = res.data.fault
            // 重新拉一次完整详情，确保 attachments 等字段就位
            await this.loadFaultAttachments(res.data.fault.id)
          }
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
      // 【P0+P1 重构】事务化上传：disk → DB 一体化；新建模式下禁用（必须先保存条目）
      if (!this.editingFault || !this.editingFault.id) {
        // 防御性：理论上模板已禁用按钮，这里再保一次
        this.$toast('请先保存条目，再上传附件')
        return
      }
      const faultId = this.editingFault.id
      const files = Array.isArray(fileObj) ? fileObj : [fileObj]
      for (const item of files) {
        if (!item || !item.file) continue
        item.status = 'uploading'
        item.message = '上传中…'
        try {
          const res = await uploadFaultAttachment(faultId, item.file)
          const d = (res && res.data && res.data.attachment) || {}
          // 显式四态：uploading → done
          item.status = 'done'
          item.message = '已上传'
          // 追加到本地 attachments 列表（带审计字段）
          if (d && d.id) {
            this.faultForm.attachments.push({
              id: d.id,
              url: d.url,
              filename: d.filename,
              size: d.size,
              kind: d.kind,
              mime: d.mime,
              uploaded_at: d.uploaded_at,
              uploaded_by: d.uploaded_by,
              status: 'done',
            })
          }
        } catch (e) {
          // 显式四态：uploading → failed，附带后端 error
          item.status = 'failed'
          item.message = (e && e.response && e.response.data && e.response.data.error) || '上传失败'
          this.$toast(item.message)
        }
      }
    },
    async removeFaultFile(attOrIdx) {
      // attOrIdx 既可能是 number（旧逻辑，faultForm.files 数组下标），
      // 也可能是 attachment 对象本身（新版，传 att 进来）
      let att, idx
      if (typeof attOrIdx === 'number') {
        idx = attOrIdx
        att = this.faultForm.attachments[idx]
      } else {
        att = attOrIdx
        idx = this.faultForm.attachments.findIndex(x => x.id === att.id)
      }
      if (!att || !att.id) return
      try {
        await this.$dialog.confirm({
          title: '删除确认',
          message: `确定删除文件「${att.filename}」吗？文件将从服务器彻底删除。`,
        })
      } catch (_) {
        return
      }
      try {
        await deleteFaultAttachment(this.editingFault.id, att.id)
        this.faultForm.attachments.splice(idx, 1)
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
.files-empty-locked {
  background: #fef3c7;
  color: #92400e;
  border-radius: 4px;
  padding: 10px 12px;
  font-size: 12px;
  margin: 8px 0;
}
.file-time {
  color: #9ca3af;
  font-size: 11px;
}
.status-tag {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
  margin-right: 4px;
  font-weight: 500;
}
.status-uploading { background: #fef3c7; color: #92400e; }
.status-failed    { background: #fee2e2; color: #b91c1c; }
.status-done      { background: #d1fae5; color: #065f46; }
.fault-tags {
  margin: 12px 16px;
}
.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}
.tag-chip {
  cursor: pointer;
}

/* ============ P1 标签字典管理 ============ */
.tags-section {
  margin-top: 20px;
  padding: 12px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}
.section-title {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 8px;
}
.tag-create-row {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-bottom: 8px;
}
.tag-create-row .van-field {
  flex: 1;
}
.tags-list {
  background: #fff;
}
.history-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #f9fafb;
}
.history-hint {
  font-size: 11px;
  color: #9ca3af;
}
.textarea-field {
  width: 100%;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 6px 8px;
  font-size: 13px;
  font-family: inherit;
  resize: vertical;
}
.revision-dialog {
  max-height: 60vh;
  overflow-y: auto;
}
.revision-row {
  padding: 10px 0;
  border-bottom: 1px solid #f3f4f6;
}
.revision-row:last-child {
  border-bottom: none;
}
.rev-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.rev-version {
  font-size: 13px;
  font-weight: 500;
  color: #1976d2;
}
.rev-time {
  font-size: 11px;
  color: #9ca3af;
}
.rev-note {
  font-size: 12px;
  color: #6b7280;
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