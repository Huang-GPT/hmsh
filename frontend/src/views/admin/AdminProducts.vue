<template>
  <div class="admin-products">
    <h3>产品库管理</h3>

    <!-- 顶部 toolbar：搜索 + 状态过滤 + 操作 -->
    <div class="toolbar">
      <div class="toolbar-row toolbar-top">
        <van-search
          v-model="keyword"
          placeholder="搜索销售单号 / 二维码 / 客户 / 产品编号 / 产品名称"
          @search="loadProducts(1)"
          shape="round"
          class="search-box"
        />
        <div class="status-filter">
          <span
            v-for="f in statusFilters"
            :key="f.value"
            :class="['filter-chip', { active: statusFilter === f.value }]"
            @click="setStatusFilter(f.value)"
          >{{ f.label }} ({{ f.count }})</span>
        </div>
      </div>

      <div class="toolbar-row toolbar-bottom">
        <van-button size="small" type="primary" icon="plus" @click="openCreate">新建产品</van-button>
        <van-button size="small" plain icon="description" @click="triggerImport">导入CSV</van-button>
        <van-button size="small" plain icon="down" @click="exportCSV">导出CSV</van-button>
        <van-button size="small" plain icon="replay" @click="loadProducts()">刷新</van-button>
        <input ref="fileInput" type="file" accept=".csv" style="display:none" @change="onImportFile" />
      </div>

      <!-- 批量操作条 -->
      <transition name="fade">
        <div v-if="selectedIds.length > 0" class="bulk-bar">
          <span class="bulk-info">已选 <strong>{{ selectedIds.length }}</strong> 项</span>
          <van-button size="mini" type="danger" plain @click="bulkDelete">批量删除</van-button>
          <van-button size="mini" plain @click="clearSelection">取消选择</van-button>
        </div>
      </transition>
    </div>

    <!-- 表格 -->
    <div class="table-wrap">
      <table class="product-table">
        <thead>
          <tr>
            <th class="col-check">
              <input
                type="checkbox"
                :checked="allSelected"
                :indeterminate.prop="someSelected && !allSelected"
                @change="toggleAll"
              />
            </th>
            <th class="col-id">ID</th>
            <th>行项目</th>
            <th>销售单号</th>
            <th>二维码</th>
            <th>客户名称</th>
            <th>经销商</th>
            <th>产品编号</th>
            <th>产品名称</th>
            <th>收货人</th>
            <th>收货电话</th>
            <th>下单日期</th>
            <th>交货日期</th>
            <th>生产日期</th>
            <th>保修日期</th>
            <th>截至日期</th>
            <th>状态</th>
            <th class="col-actions sticky-right">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading && products.length === 0">
            <td colspan="18" class="state-cell">加载中…</td>
          </tr>
          <tr v-else-if="products.length === 0">
            <td colspan="18" class="state-cell">
              <div class="empty-cell">
                <div class="empty-icon">📦</div>
                <div class="empty-text">暂无产品数据</div>
                <div class="empty-hint">点击右上角"导入CSV"或"新建产品"</div>
              </div>
            </td>
          </tr>
          <tr
            v-for="p in products"
            :key="p.id"
            :class="{ selected: isSelected(p.id) }"
          >
            <td class="col-check">
              <input
                type="checkbox"
                :checked="isSelected(p.id)"
                @change="toggleSelect(p.id)"
              />
            </td>
            <td class="col-id">#{{ p.id }}</td>
            <td class="col-int">{{ p.sap_line_item !== undefined && p.sap_line_item !== null ? p.sap_line_item : '—' }}</td>
            <td>{{ p.sales_no || '—' }}</td>
            <td class="col-qr"><code>{{ p.qr_code || '—' }}</code></td>
            <td>{{ p.customer_name || '—' }}</td>
            <td>{{ p.dealer_name || '—' }}</td>
            <td>{{ p.product_no || '—' }}</td>
            <td class="col-name">{{ p.product_name || p.model || '—' }}</td>
            <td>{{ p.receiver || '—' }}</td>
            <td>{{ p.receiver_phone || '—' }}</td>
            <td class="col-date">{{ formatDate(p.order_date) }}</td>
            <td class="col-date">{{ formatDate(p.delivery_date) }}</td>
            <td class="col-date">{{ formatDate(p.production_date) }}</td>
            <td class="col-date">{{ formatDate(p.warranty_date) }}</td>
            <td class="col-date">{{ formatDate(p.expiry_date) }}</td>
            <td>
              <van-tag :type="p.status === 'active' ? 'success' : 'danger'" size="mini">
                {{ p.status === 'active' ? '有效' : '无效' }}
              </van-tag>
            </td>
            <td class="col-actions sticky-right">
              <a class="op-link" @click="previewProduct(p)">查看</a>
              <a class="op-link primary" @click="editProduct(p)">编辑</a>
              <a class="op-link danger" @click="removeProduct(p)">删除</a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分页 -->
    <div class="pagination">
      <span class="pagination-info">
        共 <strong>{{ total }}</strong> 条 ·
        第 {{ page }} / {{ totalPages }} 页 ·
        每页 {{ pageSize }} 条
      </span>
      <div class="pagination-buttons">
        <van-button size="mini" :disabled="page <= 1" @click="changePage(-1)">上一页</van-button>
        <van-button size="mini" :disabled="page >= totalPages" @click="changePage(1)">下一页</van-button>
      </div>
    </div>

    <!-- 导入结果弹窗 -->
    <van-dialog
      v-model="showImportResult"
      title="导入完成"
      :show-confirm-button="true"
      confirm-button-text="知道了"
    >
      <div class="import-result">
        <p>导入文件：{{ lastImport.filename }}</p>
        <p>总行数：{{ lastImport.total }}</p>
        <p style="color:#07c160">✓ 成功新增：{{ lastImport.inserted }}</p>
        <p v-if="lastImport.skipped_count > 0" style="color:#ff976a">⚠ 已跳过（重复二维码）：{{ lastImport.skipped_count }}</p>
        <p v-if="lastImport.error_count > 0" style="color:#ee0a24">✗ 失败行数：{{ lastImport.error_count }}</p>
        <div v-if="lastImport.errors.length" class="error-detail">
          <p style="font-weight:600">错误详情：</p>
          <p v-for="(e, i) in lastImport.errors.slice(0,10)" :key="i">
            第 {{ e.row }} 行: {{ e.reason }}
          </p>
          <p v-if="lastImport.errors.length > 10" style="color:#999">…还有 {{ lastImport.errors.length - 10 }} 条</p>
        </div>
      </div>
    </van-dialog>

    <!-- 新建/编辑产品弹窗 -->
    <van-dialog
      v-model="showCreate"
      :title="editingProduct ? '编辑产品记录' : '新建产品记录'"
      show-cancel-button
      @confirm="submitCreate"
      @cancel="onCancelCreate"
    >
      <div class="create-form">
        <van-field v-model="form.sales_no" label="销售单号" placeholder="如 0050384274" />
        <van-field v-model="form.customer_name" label="客户名称" placeholder="客户公司名" />
        <van-field v-model="form.dealer_name" label="经销商名称" />
        <van-field v-model="form.dealer_contact" label="经销商联系人" />
        <van-field v-model="form.dealer_phone" label="经销商电话" />
        <van-field v-model="form.product_no" label="产品编号" placeholder="型号代码" />
        <van-field v-model="form.product_name" label="产品名称" />
        <van-field v-model="form.shipping_address" label="发货地址" type="textarea" rows="2" autosize />
        <van-field v-model="form.qr_code" label="二维码" placeholder="必填" required />
        <van-field v-model="form.receiver" label="收货人" />
        <van-field v-model="form.receiver_phone" label="联系电话" />
        <van-cell title="下单日期">
          <input type="date" v-model="form.order_date" class="date-input" placeholder="点击选择日期" />
        </van-cell>
        <van-cell title="交货日期">
          <input type="date" v-model="form.delivery_date" class="date-input" placeholder="点击选择日期" />
        </van-cell>
        <van-cell title="生产日期">
          <input type="date" v-model="form.production_date" class="date-input" placeholder="点击选择日期" />
        </van-cell>
        <van-cell title="保修日期">
          <input type="date" v-model="form.warranty_date" class="date-input" placeholder="点击选择日期" />
        </van-cell>
        <van-cell title="截至日期">
          <input type="date" v-model="form.expiry_date" class="date-input" placeholder="点击选择日期" />
        </van-cell>
        <van-cell title="行项目">
          <input
            type="number"
            v-model.number="form.sap_line_item"
            class="date-input"
            placeholder="整数，如 10"
            min="0"
            step="1"
          />
        </van-cell>
      </div>
    </van-dialog>

    <!-- 查看产品详情弹窗 -->
    <van-dialog
      v-model="showPreview"
      title="产品详情"
      :show-confirm-button="false"
      cancel-button-text="关闭"
      close-on-click-overlay
    >
      <div class="preview-form" v-if="previewingProduct">
        <div class="preview-row"><span class="label">产品 ID</span><span class="value">#{{ previewingProduct.id }}</span></div>
        <div class="preview-row"><span class="label">销售单号</span><span class="value">{{ previewingProduct.sales_no || '—' }}</span></div>
        <div class="preview-row"><span class="label">客户名称</span><span class="value">{{ previewingProduct.customer_name || '—' }}</span></div>
        <div class="preview-row"><span class="label">经销商</span><span class="value">{{ previewingProduct.dealer_name || '—' }}</span></div>
        <div class="preview-row"><span class="label">经销商联系人</span><span class="value">{{ previewingProduct.dealer_contact || '—' }}</span></div>
        <div class="preview-row"><span class="label">经销商电话</span><span class="value">{{ previewingProduct.dealer_phone || '—' }}</span></div>
        <div class="preview-row"><span class="label">产品编号</span><span class="value">{{ previewingProduct.product_no || '—' }}</span></div>
        <div class="preview-row"><span class="label">产品名称</span><span class="value">{{ previewingProduct.product_name || previewingProduct.model || '—' }}</span></div>
        <div class="preview-row"><span class="label">发货地址</span><span class="value">{{ previewingProduct.shipping_address || '—' }}</span></div>
        <div class="preview-row"><span class="label">二维码</span><span class="value qr-code">{{ previewingProduct.qr_code || '—' }}</span></div>
        <div class="preview-row"><span class="label">收货人</span><span class="value">{{ previewingProduct.receiver || '—' }}</span></div>
        <div class="preview-row"><span class="label">收货电话</span><span class="value">{{ previewingProduct.receiver_phone || '—' }}</span></div>
        <div class="preview-row"><span class="label">下单日期</span><span class="value">{{ formatDate(previewingProduct.order_date) }}</span></div>
        <div class="preview-row"><span class="label">交货日期</span><span class="value">{{ formatDate(previewingProduct.delivery_date) }}</span></div>
        <div class="preview-row"><span class="label">生产日期</span><span class="value">{{ formatDate(previewingProduct.production_date) }}</span></div>
        <div class="preview-row"><span class="label">保修日期</span><span class="value">{{ formatDate(previewingProduct.warranty_date) }}</span></div>
        <div class="preview-row"><span class="label">截至日期</span><span class="value">{{ formatDate(previewingProduct.expiry_date) }}</span></div>
        <div class="preview-row"><span class="label">行项目</span><span class="value">{{ previewingProduct.sap_line_item !== undefined && previewingProduct.sap_line_item !== null ? previewingProduct.sap_line_item : '—' }}</span></div>
        <div class="preview-row"><span class="label">状态</span><span class="value">
          <van-tag :type="previewingProduct.status === 'active' ? 'success' : 'danger'" size="mini">
            {{ previewingProduct.status === 'active' ? '有效' : '无效' }}
          </van-tag>
        </span></div>
      </div>
    </van-dialog>
  </div>
</template>

<script>
import {
  getAllProducts, createProduct, updateProduct, deleteProduct, importProducts
} from '@/api/admin'

const emptyForm = () => ({
  sales_no: '', customer_name: '', dealer_name: '',
  dealer_contact: '', dealer_phone: '',
  product_no: '', product_name: '', shipping_address: '',
  qr_code: '', receiver: '', receiver_phone: '',
  order_date: '', delivery_date: '', production_date: '',
  warranty_date: '', expiry_date: '',
  sap_line_item: null,
})

export default {
  name: 'AdminProducts',
  data() {
    return {
      products: [],
      keyword: '',
      statusFilter: 'all',
      page: 1,
      pageSize: 50,
      total: 0,
      loading: false,
      selectedIds: [],

      showCreate: false,
      form: emptyForm(),
      editingProduct: null,

      showPreview: false,
      previewingProduct: null,

      showImportResult: false,
      lastImport: { inserted: 0, skipped: [], errors: [], total: 0, filename: '' },
    }
  },
  computed: {
    totalPages() {
      return Math.max(1, Math.ceil(this.total / this.pageSize))
    },
    statusFilters() {
      return [
        { value: 'all', label: '全部', count: '' },
        { value: 'active', label: '有效', count: '' },
        { value: 'inactive', label: '无效', count: '' },
      ]
    },
    allSelected() {
      return this.products.length > 0 && this.selectedIds.length === this.products.length
    },
    someSelected() {
      return this.selectedIds.length > 0
    },
  },
  watch: {
    statusFilter() {
      this.selectedIds = []
      this.loadProducts(1)
    },
  },
  created() {
    this.loadProducts()
  },
  methods: {
    formatDate(d) {
      if (!d) return '—'
      return String(d).substring(0, 10)
    },

    async loadProducts(targetPage) {
      if (targetPage) this.page = targetPage
      this.loading = true
      try {
        const params = {
          keyword: this.keyword,
          page: this.page,
          page_size: this.pageSize,
        }
        if (this.statusFilter && this.statusFilter !== 'all') {
          params.status = this.statusFilter
        }
        const res = await getAllProducts(params)
        const data = res.data || {}
        this.products = data.items || data.products || []
        this.total = data.total || this.products.length
        // 清掉已选项目里不在当前页的
        const visibleIds = new Set(this.products.map(p => p.id))
        this.selectedIds = this.selectedIds.filter(id => visibleIds.has(id))
      } catch (e) {
        console.error(e)
      } finally {
        this.loading = false
      }
    },

    changePage(delta) {
      const next = this.page + delta
      if (next < 1 || next > this.totalPages) return
      this.page = next
      this.loadProducts()
    },

    setStatusFilter(v) {
      if (this.statusFilter === v) return
      this.statusFilter = v
    },

    isSelected(id) {
      return this.selectedIds.includes(id)
    },
    toggleSelect(id) {
      const idx = this.selectedIds.indexOf(id)
      if (idx >= 0) this.selectedIds.splice(idx, 1)
      else this.selectedIds.push(id)
    },
    toggleAll() {
      if (this.allSelected) {
        this.selectedIds = []
      } else {
        this.selectedIds = this.products.map(p => p.id)
      }
    },
    clearSelection() {
      this.selectedIds = []
    },
    async bulkDelete() {
      const ok = await this.$dialog.confirm({
        title: '批量删除确认',
        message: `将永久删除选中的 ${this.selectedIds.length} 条产品记录，继续？`,
      }).catch(() => false)
      if (!ok) return
      this.$toast.loading({ message: '删除中...', forbidClick: true })
      let success = 0, fail = 0
      for (const id of this.selectedIds) {
        try {
          await deleteProduct(id)
          success++
        } catch (e) {
          fail++
        }
      }
      this.$toast.clear()
      this.$toast(`删除完成：成功 ${success}，失败 ${fail}`)
      this.selectedIds = []
      this.loadProducts()
    },

    exportCSV() {
      if (this.products.length === 0) {
        this.$toast('当前页无数据可导出')
        return
      }
      const headers = [
        'ID', '行项目', '销售单号', '二维码', '客户名称', '经销商', '经销商联系人',
        '经销商电话', '产品编号', '产品名称', '发货地址', '收货人', '收货电话',
        '下单日期', '交货日期', '生产日期', '保修日期', '截至日期', '状态',
      ]
      const escape = (v) => {
        if (v === null || v === undefined) return ''
        const s = String(v)
        if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`
        return s
      }
      const rows = this.products.map(p => [
        p.id, p.sap_line_item, p.sales_no, p.qr_code, p.customer_name, p.dealer_name,
        p.dealer_contact, p.dealer_phone, p.product_no, p.product_name,
        p.shipping_address, p.receiver, p.receiver_phone,
        this.formatDate(p.order_date),
        this.formatDate(p.delivery_date),
        this.formatDate(p.production_date),
        this.formatDate(p.warranty_date),
        this.formatDate(p.expiry_date),
        p.status,
      ].map(escape).join(','))
      // 加 BOM 让 Excel 正确识别 UTF-8
      const csv = '\uFEFF' + [headers.join(','), ...rows].join('\r\n')
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const ts = new Date().toISOString().replace(/[:T]/g, '-').substring(0, 19)
      a.download = `products_${ts}.csv`
      a.click()
      URL.revokeObjectURL(url)
      this.$toast.success(`已导出 ${this.products.length} 条记录`)
    },

    openCreate() {
      this.editingProduct = null
      this.form = emptyForm()
      this.showCreate = true
    },
    editProduct(p) {
      const toFormDate = (s) => s ? String(s).substring(0, 10) : ''
      this.editingProduct = p
      this.form = {
        sales_no: p.sales_no || '',
        customer_name: p.customer_name || '',
        dealer_name: p.dealer_name || '',
        dealer_contact: p.dealer_contact || '',
        dealer_phone: p.dealer_phone || '',
        product_no: p.product_no || '',
        product_name: p.product_name || '',
        shipping_address: p.shipping_address || '',
        qr_code: p.qr_code || '',
        receiver: p.receiver || '',
        receiver_phone: p.receiver_phone || '',
        order_date: toFormDate(p.order_date),
        delivery_date: toFormDate(p.delivery_date),
        production_date: toFormDate(p.production_date),
        warranty_date: toFormDate(p.warranty_date),
        expiry_date: toFormDate(p.expiry_date),
        // 避免 ?? 运算符（Babel 不支持）；用显式 null 检查，保证 0 仍被识别
        sap_line_item: (p.sap_line_item !== undefined && p.sap_line_item !== null) ? p.sap_line_item : null,
      }
      this.showCreate = true
    },
    previewProduct(p) {
      this.previewingProduct = p
      this.showPreview = true
    },
    onCancelCreate() {
      this.showCreate = false
      this.editingProduct = null
    },
    async submitCreate() {
      if (!this.form.qr_code || !this.form.qr_code.trim()) {
        this.$toast('请填写二维码')
        return
      }
      const isEdit = !!this.editingProduct
      try {
        const payload = {}
        for (const k in this.form) {
          const v = this.form[k]
          // sap_line_item 是整数字段，原样传；其余空字符串当作 null
          if (k === 'sap_line_item') {
            payload[k] = (v === '' || v === null || v === undefined) ? null : Number(v)
          } else {
            payload[k] = (v && String(v).trim()) || null
          }
        }
        if (isEdit) {
          await updateProduct(this.editingProduct.id, payload)
          this.$toast.success('更新成功')
        } else {
          await createProduct(payload)
          this.$toast.success('创建成功')
        }
        this.showCreate = false
        this.editingProduct = null
        this.loadProducts()
      } catch (e) {
        const data = e && e.response && e.response.data
        const err = (data && data.error) || (isEdit ? '更新失败' : '创建失败')
        const detail = (data && data.detail) || ''
        this.$toast(detail ? err + '：' + detail : err)
        console.error(`[admin/products ${isEdit ? 'PUT' : 'POST'}]`, e.response && e.response.data)
      }
    },
    async removeProduct(p) {
      const ok = await this.$dialog.confirm({
        title: '删除确认',
        message: `确定删除产品 #${p.id} (${p.qr_code || '无码'})?`,
      }).catch(() => false)
      if (!ok) return
      try {
        await deleteProduct(p.id)
        this.$toast.success('删除成功')
        this.loadProducts()
      } catch (e) {
        this.$toast('删除失败')
      }
    },

    // CSV 导入
    triggerImport() {
      this.$refs.fileInput && this.$refs.fileInput.click()
    },
    async onImportFile(e) {
      const file = e.target.files && e.target.files[0]
      e.target.value = ''
      if (!file) return
      if (!file.name.toLowerCase().endsWith('.csv')) {
        this.$toast('请选择 .csv 文件')
        return
      }
      this.$toast.loading({ message: '导入中...', forbidClick: true })
      try {
        const res = await importProducts(file)
        const data = (res.data && res.data) || {}
        this.lastImport = {
          filename: file.name,
          inserted: data.inserted || 0,
          skipped: data.skipped || [],
          errors: data.errors || [],
          total: data.total || 0,
        }
        this.lastImport.skipped_count = this.lastImport.skipped.length
        this.lastImport.error_count = this.lastImport.errors.length
        this.showImportResult = true
        this.loadProducts()
      } catch (e) {
        const msg = (e && e.response && e.response.data && e.response.data.error) || '导入失败'
        this.$toast(msg)
      } finally {
        this.$toast.clear()
      }
    },
  },
}
</script>

<style scoped>
.admin-products h3 {
  margin: 0 0 16px 0;
  color: #1f2937;
  font-size: 20px;
  font-weight: 600;
}

/* ===== Toolbar ===== */
.toolbar {
  background: white;
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.toolbar-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.toolbar-top {
  margin-bottom: 10px;
}
.toolbar-bottom {
  border-top: 1px solid #f0f0f0;
  padding-top: 10px;
}
.search-box {
  flex: 0 0 320px;
}
.status-filter {
  display: flex;
  gap: 6px;
}
.filter-chip {
  padding: 6px 14px;
  border-radius: 16px;
  background: #f4f4f5;
  color: #606266;
  font-size: 13px;
  cursor: pointer;
  user-select: none;
  transition: all 0.15s;
}
.filter-chip:hover {
  background: #e9e9eb;
}
.filter-chip.active {
  background: #1989fa;
  color: white;
}

/* ===== Bulk action bar ===== */
.bulk-bar {
  margin-top: 10px;
  padding: 8px 14px;
  background: #ecf5ff;
  border: 1px solid #d9ecff;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: #1989fa;
}
.bulk-bar strong {
  margin: 0 4px;
  font-size: 14px;
}
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}

/* ===== Table ===== */
.table-wrap {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  overflow-x: auto;
  margin-bottom: 12px;
}
.product-table {
  width: 100%;
  min-width: 1800px;
  border-collapse: collapse;
  font-size: 13px;
}
.product-table th,
.product-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
  white-space: nowrap;
  vertical-align: middle;
}
.product-table thead {
  background: #fafbfc;
}
.product-table th {
  font-weight: 600;
  color: #374151;
  font-size: 12px;
  letter-spacing: 0.3px;
  position: sticky;
  top: 0;
  background: #fafbfc;
  z-index: 1;
  border-bottom: 2px solid #e5e7eb;
}
.product-table tbody tr:hover {
  background: #f5f7fa;
}
.product-table tbody tr.selected {
  background: #ecf5ff;
}
.product-table tbody tr.selected:hover {
  background: #d9ecff;
}

.col-check {
  width: 44px;
  text-align: center !important;
}
.col-check input[type="checkbox"] {
  cursor: pointer;
  width: 14px;
  height: 14px;
}
.col-id {
  width: 60px;
  color: #9ca3af;
  font-family: monospace;
}
.col-int {
  font-family: monospace;
  font-weight: 600;
  color: #1989fa;
  text-align: right;
  width: 80px;
}
.col-qr code {
  background: #f3f4f6;
  padding: 2px 8px;
  border-radius: 4px;
  color: #1989fa;
  font-size: 12px;
  font-family: monospace;
  letter-spacing: 0.3px;
}
.col-name {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.col-date {
  color: #6b7280;
  font-size: 12px;
  font-family: monospace;
}
.col-actions {
  width: 200px;
  text-align: right !important;
}
.sticky-right {
  position: sticky;
  right: 0;
  background: white;
  box-shadow: -2px 0 4px rgba(0,0,0,0.04);
}
.product-table tbody tr:hover .sticky-right {
  background: #f5f7fa;
}
.product-table tbody tr.selected .sticky-right,
.product-table tbody tr.selected:hover .sticky-right {
  background: #ecf5ff;
}
.op-link {
  display: inline-block;
  margin-left: 12px;
  cursor: pointer;
  color: #6b7280;
  font-size: 13px;
  transition: color 0.15s;
}
.op-link:first-child { margin-left: 0; }
.op-link:hover { color: #374151; }
.op-link.primary { color: #1989fa; }
.op-link.primary:hover { color: #0570d4; }
.op-link.danger { color: #ee0a24; }
.op-link.danger:hover { color: #c8050a; }

/* ===== Loading / empty cells ===== */
.state-cell {
  text-align: center !important;
  padding: 60px !important;
  color: #9ca3af;
  font-size: 13px;
}
.empty-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.empty-icon {
  font-size: 48px;
  opacity: 0.5;
}
.empty-text {
  font-size: 14px;
  color: #6b7280;
}
.empty-hint {
  font-size: 12px;
  color: #9ca3af;
}

/* ===== Pagination ===== */
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  font-size: 13px;
  color: #6b7280;
}
.pagination-info strong {
  color: #1989fa;
  margin: 0 2px;
}
.pagination-buttons {
  display: flex;
  gap: 8px;
}

/* ===== Dialog forms ===== */
.create-form {
  max-height: 60vh;
  overflow-y: auto;
}
.preview-form {
  padding: 8px 16px;
  max-height: 60vh;
  overflow-y: auto;
}
.preview-row {
  display: flex;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}
.preview-row:last-child {
  border-bottom: none;
}
.preview-row .label {
  flex: 0 0 90px;
  color: #9ca3af;
}
.preview-row .value {
  flex: 1;
  color: #1f2937;
  word-break: break-all;
}
.preview-row .value.qr-code {
  font-family: monospace;
  color: #1989fa;
}
.date-input {
  border: none;
  outline: none;
  background: transparent;
  text-align: right;
  font-size: 14px;
  color: #1f2937;
  width: 60%;
  font-family: inherit;
}
.date-input::-webkit-calendar-picker-indicator {
  cursor: pointer;
  opacity: 0.6;
}
.date-input::placeholder {
  color: #c8c9cc;
}

/* ===== Import result ===== */
.import-result {
  padding: 16px;
}
.import-result p {
  margin: 6px 0;
}
.error-detail {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #eee;
  font-size: 12px;
  color: #6b7280;
  max-height: 200px;
  overflow-y: auto;
}
</style>