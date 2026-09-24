<template>
  <div class="common-faults">
    <van-nav-bar title="故障文件库" :border="false" />

    <div class="search-wrap">
      <van-search
        v-model="keyword"
        placeholder="搜索文件名 / 描述"
        @search="loadFiles"
        shape="round"
        background="transparent"
      />
      <div class="type-chips">
        <span
          v-for="f in typeFilters"
          :key="f.value"
          :class="['chip', { active: typeFilter === f.value }]"
          @click="setTypeFilter(f.value)"
        >
          {{ f.label }} <span class="chip-count">({{ typeCounts[f.value] || 0 }})</span>
        </span>
      </div>
    </div>

    <div v-if="loading" class="loading-tip">
      <van-loading size="20">加载中…</van-loading>
    </div>

    <div v-else-if="files.length === 0" class="empty-block">
      <van-empty description="暂无文件" />
    </div>

    <div v-else class="file-grid">
      <div
        v-for="f in files"
        :key="f.id"
        class="file-card"
        :class="`card-${f.kind}`"
        @click="onCardClick(f)"
      >
        <!-- 缩略图/图标区 -->
        <div class="card-thumb">
          <img v-if="f.kind === 'image'" :src="normalizeUrl(f.url)" :alt="f.filename" loading="lazy" />
          <div v-else class="card-icon" :class="`icon-${f.kind}`">
            <van-icon :name="kindIcon(f)" size="32" :color="kindColor(f)" />
          </div>
          <span class="kind-badge" :class="`badge-${f.kind}`">{{ kindLabel(f.kind) }}</span>
        </div>

        <!-- 信息区 -->
        <div class="card-body">
          <div class="file-name" :title="f.filename">{{ f.filename }}</div>
          <div v-if="f.description" class="file-desc">{{ f.description }}</div>
          <div class="file-meta">
            <span>{{ formatSize(f.size) }}</span>
            <span>{{ formatDate(f.created_at) }}</span>
          </div>
        </div>

        <!-- 操作区 -->
        <div class="card-actions" @click.stop>
          <van-button size="mini" plain icon="down" @click.stop="downloadFile(f)">下载</van-button>
          <van-button
            v-if="f.kind === 'image'"
            size="mini"
            plain
            type="primary"
            @click.stop="previewFile(f)"
          >预览</van-button>
        </div>
      </div>
    </div>

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
import { getPublicFaultFiles } from '@/api/faults'

const TYPE_FILTERS = [
  { value: '', label: '全部' },
  { value: 'pdf', label: 'PDF' },
  { value: 'image', label: '图片' },
  { value: 'doc', label: '文档' },
]

export default {
  name: 'CommonFaults',
  data() {
    return {
      files: [],
      loading: false,
      keyword: '',
      typeFilter: '',
      showImagePreview: false,
      previewImages: [],
      previewStart: 0,
    }
  },
  computed: {
    typeFilters() {
      return TYPE_FILTERS
    },
    // 当前已加载数据中各类型计数
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

    // ===== 文件工具方法 =====
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
      if (!s) return ''
      const str = String(s).replace('T', ' ')
      return str.length >= 10 ? str.substring(0, 10) : str
    },
    normalizeUrl(url) {
      if (!url) return ''
      if (/^https?:\/\//.test(url) || url.startsWith('data:')) return url
      return url.startsWith('/') ? url : '/' + url
    },

    // ===== 数据加载 =====
    async loadFiles() {
      this.loading = true
      try {
        const params = {}
        if (this.keyword) params.keyword = this.keyword
        if (this.typeFilter) params.kind = this.typeFilter
        const res = await getPublicFaultFiles(params)
        this.files = (res.data && res.data.files) || []
      } catch (e) {
        console.error('加载失败', e)
        this.$toast('加载失败')
        this.files = []
      } finally {
        this.loading = false
      }
    },

    // ===== 文件操作 =====
    onCardClick(f) {
      if (f.kind === 'image') {
        this.previewFile(f)
        return
      }
      if (f.kind === 'pdf') {
        // PDF 用浏览器原生查看
        window.open(this.normalizeUrl(f.url), '_blank')
        return
      }
      // DOC / DOCX：触发下载
      this.downloadFile(f)
    },
    previewFile(f) {
      this.previewImages = [{ url: this.normalizeUrl(f.url) }]
      this.previewStart = 0
      this.showImagePreview = true
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
  },
}
</script>

<style scoped>
.common-faults {
  background: var(--color-bg-page);
  min-height: 100vh;
  padding-bottom: var(--space-6);
}

/* ===== 搜索 + 筛选 ===== */
.search-wrap {
  padding: var(--space-3) var(--space-4) var(--space-2);
}
.type-chips {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
  padding: var(--space-2) 0 0;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 14px;
  border-radius: var(--radius-full);
  background: var(--color-bg-card);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-base);
  border: 1px solid var(--color-border);
}
.chip-count {
  font-size: var(--text-xs);
  opacity: 0.85;
}
.chip.active {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}

/* ===== 文件网格 ===== */
.file-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-3);
  padding: var(--space-2) var(--space-4);
}
@media (min-width: 640px) {
  .file-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

.file-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-card);
  cursor: pointer;
  transition: all var(--transition-base);
  display: flex;
  flex-direction: column;
}
.file-card:active {
  transform: scale(0.98);
  box-shadow: var(--shadow-hover);
}

/* ===== 缩略图区 ===== */
.card-thumb {
  position: relative;
  width: 100%;
  aspect-ratio: 4 / 3;
  background: var(--color-bg-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.card-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.card-icon {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
}
.icon-pdf {
  background: #fef2f2;
}
.icon-doc {
  background: #eff6ff;
}
.icon-image {
  background: var(--color-bg-card);
}

.kind-badge {
  position: absolute;
  top: var(--space-2);
  right: var(--space-2);
  font-size: var(--text-xs);
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-weight: var(--font-semibold);
  letter-spacing: 0.5px;
}
.badge-pdf {
  background: #e74c3c;
  color: #fff;
}
.badge-image {
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
}
.badge-doc {
  background: #2c5aa0;
  color: #fff;
}

/* ===== 信息区 ===== */
.card-body {
  padding: var(--space-3);
  flex: 1;
}
.file-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text);
  line-height: 1.4;
  word-break: break-all;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 38px;
}
.file-desc {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  margin-top: var(--space-1);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.file-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-text-placeholder);
}

/* ===== 操作区 ===== */
.card-actions {
  padding: var(--space-2) var(--space-3) var(--space-3);
  display: flex;
  gap: var(--space-2);
  border-top: 1px solid var(--color-divider);
}
.card-actions .van-button {
  flex: 1;
  height: 28px !important;
  font-size: var(--text-xs) !important;
}

/* ===== Loading / Empty ===== */
.loading-tip {
  padding: 60px 0;
  text-align: center;
  color: var(--color-text-tertiary);
}
.empty-block {
  padding: 40px 0;
}
</style>