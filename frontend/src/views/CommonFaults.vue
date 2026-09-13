<template>
  <div class="common-faults">
    <!-- 顶部导航条：列表态 vs 文件态 -->
    <van-nav-bar
      :title="view === 'categories' ? '常见故障' : (currentCategory ? currentCategory.name : '故障文件')"
      :left-arrow="view !== 'categories'"
      @click-left="backToCategories"
      fixed
      placeholder
    />

    <!-- ============ 视图1：分类列表 ============ -->
    <div v-if="view === 'categories'" class="cat-view">
      <van-search
        v-model="catKeyword"
        placeholder="搜索分类"
        @search="loadCategories"
      />
      <van-cell-group v-if="filteredCategories.length">
        <van-cell
          v-for="cat in filteredCategories"
          :key="cat.id"
          :title="cat.name"
          :label="`${fileCountOf(cat)} 个文件`"
          is-link
          @click="openCategory(cat)"
        >
          <template #icon>
            <span class="cat-icon">{{ cat.icon || '🔧' }}</span>
          </template>
        </van-cell>
      </van-cell-group>
      <van-empty v-else description="暂无故障分类" />
    </div>

    <!-- ============ 视图2：分类下的文件列表 ============ -->
    <div v-else class="files-view">
      <div class="cat-banner">
        <van-icon :name="currentCategory ? currentCategory.icon || '🔧' : '🔧'" size="20" />
        <span class="banner-text">{{ currentCategory ? currentCategory.name : '' }}</span>
      </div>

      <div v-if="loadingFiles" class="loading-tip">加载中…</div>

      <div v-else-if="flatFiles.length === 0" class="empty-tip">
        <van-empty description="该分类下暂无文件" />
      </div>

      <div v-else>
        <div
          v-for="grp in groupedFiles"
          :key="grp.faultId"
          class="fault-group"
        >
          <div v-if="grp.faultTitle" class="fault-title">{{ grp.faultTitle }}</div>
          <van-cell-group>
            <van-cell
              v-for="att in grp.attachments"
              :key="att.id || att.url"
              :title="att.filename"
              :label="`${fileKindLabel(att)} · ${formatSize(att.size)}`"
              is-link
              @click="openFile(att)"
            >
              <template #icon>
                <van-icon :name="fileIcon(att)" :color="fileColor(att)" size="22" class="file-cell-icon" />
              </template>
            </van-cell>
          </van-cell-group>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getFaultCategories, getFaultsByCategory } from '@/api/faults'

export default {
  name: 'CommonFaults',
  data() {
    return {
      view: 'categories',     // 'categories' | 'files'
      catKeyword: '',
      categories: [],
      currentCategory: null,
      faults: [],
      loadingFiles: false,
    }
  },
  computed: {
    filteredCategories() {
      const kw = (this.catKeyword || '').trim().toLowerCase()
      if (!kw) return this.categories
      return this.categories.filter(c => (c.name || '').toLowerCase().includes(kw))
    },
    /** 把 CommonFault 条目展平成单层文件数组（P0+P1 重构：来源 attachments 表） */
    flatFiles() {
      const out = []
      for (const f of this.faults) {
        if (Array.isArray(f.attachments) && f.attachments.length) {
          for (const att of f.attachments) {
            out.push({ ...att, _faultTitle: f.title, _faultId: f.id })
          }
        }
      }
      return out
    },
    /** 按 fault 分组的文件列表（每个故障一个 cell-group，P0+P1 数据源 attachments） */
    groupedFiles() {
      const out = []
      for (const f of this.faults) {
        if (Array.isArray(f.attachments) && f.attachments.length) {
          out.push({
            faultId: f.id,
            faultTitle: f.title,
            attachments: f.attachments,
          })
        }
      }
      return out
    },
  },
  created() {
    this.loadCategories()
  },
  methods: {
    async loadCategories() {
      try {
        const res = await getFaultCategories()
        this.categories = (res.data && res.data.categories) || []
      } catch (e) {
        console.error('加载分类失败', e)
        this.$toast('加载分类失败')
      }
    },
    async openCategory(cat) {
      this.currentCategory = cat
      this.view = 'files'
      this.loadingFiles = true
      try {
        const res = await getFaultsByCategory(cat.id)
        this.faults = (res.data && res.data.faults) || []
      } catch (e) {
        console.error('加载故障文件失败', e)
        this.$toast('加载失败')
        this.faults = []
      } finally {
        this.loadingFiles = false
      }
    },
    backToCategories() {
      this.view = 'categories'
      this.currentCategory = null
      this.faults = []
    },
    fileCountOf(cat) {
      // 分类列表不返回附件数 — 用 '—' 占位（不依赖后端聚合）
      return '—'
    },
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
    openFile(file) {
      const ext = this.fileExt(file)
      // PDF / 图片 → 浏览器打开（新标签）
      if (ext === 'pdf' || ['jpg', 'jpeg', 'png'].includes(ext)) {
        window.open(file.url, '_blank')
        return
      }
      // DOC / DOCX / 其他 → 触发下载（避免浏览器试图内嵌打开失败）
      const a = document.createElement('a')
      a.href = file.url
      a.download = file.filename || 'download'
      a.style.display = 'none'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    },
  },
}
</script>

<style scoped>
.common-faults {
  background: #f7f8fa;
  min-height: 100vh;
}
.cat-view,
.files-view {
  padding: 0 0 16px;
}
.cat-icon {
  font-size: 22px;
  margin-right: 10px;
  margin-left: 4px;
  flex-shrink: 0;
}
.cat-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: white;
  border-bottom: 1px solid #ebedf0;
}
.banner-text {
  font-size: 15px;
  color: #1f2937;
  font-weight: 500;
}
.fault-group {
  margin-bottom: 12px;
}
.fault-title {
  padding: 8px 16px 4px;
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
}
.file-cell-icon {
  margin-right: 10px;
  margin-left: 4px;
}
.loading-tip,
.empty-tip {
  padding: 40px 0;
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
}
</style>