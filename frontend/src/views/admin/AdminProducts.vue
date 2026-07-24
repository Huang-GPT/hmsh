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
        <van-button size="small" plain icon="down" @click="downloadTemplate">下载模板</van-button>
        <van-button size="small" plain icon="description" @click="triggerImport">导入CSV</van-button>
        <van-button size="small" plain icon="up" @click="exportCSV">导出CSV</van-button>
        <van-button size="small" plain icon="replay" @click="loadProducts()">刷新</van-button>
        <input ref="fileInput" type="file" accept=".csv" style="display:none" @change="onImportFile" />
        <a class="format-help" @click="showFormat = true">📋 导入格式说明</a>
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
            <th>销售单号</th>
            <th>行项目</th>
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
            <th>激活日期</th>
            <th>截至日期</th>
            <th>状态</th>
            <th class="col-bound">已绑定</th>
            <th class="col-actions sticky-right">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading && products.length === 0">
            <td colspan="19" class="state-cell">加载中…</td>
          </tr>
          <tr v-else-if="products.length === 0">
            <td colspan="19" class="state-cell">
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
            <td>{{ p.sales_no || '—' }}</td>
            <td class="col-int">{{ p.sap_line_item !== undefined && p.sap_line_item !== null ? p.sap_line_item : '—' }}</td>
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
            <td class="col-date">{{ formatDate(p.activation_date) }}</td>
            <td class="col-date">{{ formatDate(p.expiry_date) }}</td>
            <td>
              <van-tag :type="p.status === 'active' ? 'success' : 'danger'" size="mini">
                {{ p.status === 'active' ? '有效' : '无效' }}
              </van-tag>
            </td>
            <td class="col-bound">
              <van-tag
                v-if="(p.bound_count || 0) > 0"
                type="warning"
                size="mini"
                class="bound-badge"
                @click="openBindings(p)"
              >{{ p.bound_count }} 人</van-tag>
              <span v-else class="bound-zero">未绑定</span>
            </td>
            <td class="col-actions sticky-right">
              <a class="op-link" @click="previewProduct(p)">查看</a>
              <a class="op-link primary" @click="editProduct(p)">编辑</a>
              <a
                v-if="(p.bound_count || 0) > 0"
                class="op-link warn"
                @click="openBindings(p)"
              >绑定({{ p.bound_count }})</a>
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

    <!-- 导入格式说明弹窗 -->
    <van-dialog
      v-model="showFormat"
      title="CSV 导入格式说明"
      :show-confirm-button="false"
      cancel-button-text="关闭"
      close-on-click-overlay
    >
      <div class="format-guide">
        <h4>📋 字段说明（必须 UTF-8 编码，逗号分隔）</h4>
        <table class="format-table">
          <thead>
            <tr><th>列名（中文）</th><th>是否必填</th><th>格式 / 示例</th></tr>
          </thead>
          <tbody>
            <tr><td>二维码</td><td class="req">必填</td><td>每个二维码唯一，如 <code>QR123456</code></td></tr>
            <tr><td>销售单号</td><td></td><td>如 <code>0050384274</code></td></tr>
            <tr><td>行项目</td><td></td><td>整数，如 <code>10</code></td></tr>
            <tr><td>客户名称</td><td></td><td>客户公司名</td></tr>
            <tr><td>经销商名称</td><td></td><td>经销商名称</td></tr>
            <tr><td>经销商联系人</td><td></td><td>联系人</td></tr>
            <tr><td>经销商电话</td><td></td><td>电话</td></tr>
            <tr><td>产品编号</td><td></td><td>型号代码，如 <code>P001</code></td></tr>
            <tr><td>产品名称</td><td></td><td>产品名称</td></tr>
            <tr><td>发货地址</td><td></td><td>发货地址</td></tr>
            <tr><td>收货人</td><td></td><td>收货人姓名</td></tr>
            <tr><td>联系电话</td><td></td><td>收货人电话</td></tr>
            <tr><td>下单日期</td><td></td><td><code>2026-07-21</code> 或 <code>2026/7/21</code></td></tr>
            <tr><td>交货日期</td><td></td><td>同上</td></tr>
            <tr><td>生产日期</td><td></td><td>同上</td></tr>
            <tr><td>激活日期</td><td></td><td>同上</td></tr>
            <tr><td>截至日期</td><td></td><td>同上</td></tr>
            <tr><td>状态</td><td></td><td><code>active</code> 或 <code>inactive</code>，默认 active</td></tr>
          </tbody>
        </table>
        <div class="format-tips">
          <p>📌 <strong>建议先用"下载模板"拿到标准格式</strong>，模板表头为中文。</p>
          <p>📌 重复的 <strong>二维码</strong> 会被自动跳过（不报错）。</p>
          <p>📌 单文件建议 ≤ 5000 行；超量请分批导入。</p>
          <p>📌 表头中文英文任一均可识别（同时上传混合表头也兼容）。</p>
        </div>
      </div>
    </van-dialog>

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
        <van-cell title="激活日期">
          <input type="date" v-model="form.activation_date" class="date-input" placeholder="点击选择日期" />
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
        <div class="preview-row"><span class="label">激活日期</span><span class="value">{{ formatDate(previewingProduct.activation_date) }}</span></div>
        <div class="preview-row"><span class="label">截至日期</span><span class="value">{{ formatDate(previewingProduct.expiry_date) }}</span></div>
        <div class="preview-row"><span class="label">行项目</span><span class="value">{{ previewingProduct.sap_line_item !== undefined && previewingProduct.sap_line_item !== null ? previewingProduct.sap_line_item : '—' }}</span></div>
        <div class="preview-row"><span class="label">状态</span><span class="value">
          <van-tag :type="previewingProduct.status === 'active' ? 'success' : 'danger'" size="mini">
            {{ previewingProduct.status === 'active' ? '有效' : '无效' }}
          </van-tag>
        </span></div>
      </div>
    </van-dialog>

    <!-- 绑定用户列表弹窗 -->
    <van-dialog
      v-model="showBindings"
      :title="bindingsTitle"
      :show-confirm-button="false"
      cancel-button-text="关闭"
      close-on-click-overlay
    >
      <div class="bindings-view" v-if="bindingsProduct">
        <div class="bindings-summary">
          <div class="sum-row"><span class="label">二维码</span><code>{{ bindingsProduct.qr_code }}</code></div>
          <div class="sum-row"><span class="label">产品</span><span>{{ bindingsProduct.product_name || bindingsProduct.model }}</span></div>
          <div class="sum-row"><span class="label">已绑定</span>
            <van-tag :type="bindings.length > 0 ? 'warning' : 'default'" size="mini">
              共 {{ bindings.length }} 人
            </van-tag>
          </div>
        </div>
        <div v-if="bindingsLoading" class="bindings-loading">加载中…</div>
        <div v-else-if="bindings.length === 0" class="bindings-empty">暂无绑定记录</div>
        <div v-else class="bindings-list">
          <div v-for="b in bindings" :key="b.binding_id" class="binding-card">
            <div class="binding-head">
              <div class="binding-user">
                <span class="user-nick">{{ b.nickname || '用户' }}</span>
                <span class="user-phone">{{ b.phone || '—' }}</span>
              </div>
              <van-tag :type="b.bind_method === 'qrcode_sap' ? 'success' : 'primary'" size="mini">
                {{ methodLabel(b.bind_method) }}
              </van-tag>
            </div>
            <div class="binding-foot">
              <span class="bind-time">绑定于 {{ formatDateTime(b.bind_time) }}</span>
              <van-button
                size="mini"
                type="danger"
                plain
                @click="confirmUnbind(b)"
              >强制解绑</van-button>
            </div>
          </div>
        </div>
      </div>
    </van-dialog>
  </div>
</template>

<script>
import {
  getAllProducts, createProduct, updateProduct, deleteProduct, importProducts,
  getProductBindings, adminUnbind
} from '@/api/admin'

const emptyForm = () => ({
  sales_no: '', customer_name: '', dealer_name: '',
  dealer_contact: '', dealer_phone: '',
  product_no: '', product_name: '', shipping_address: '',
  qr_code: '', receiver: '', receiver_phone: '',
  order_date: '', delivery_date: '', production_date: '',
  activation_date: '', expiry_date: '',
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

      showFormat: false,

      showBindings: false,
      bindingsProduct: null,
      bindings: [],
      bindingsLoading: false,
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
    bindingsTitle() {
      if (!this.bindingsProduct) return '已绑定用户'
      return `已绑定用户 · ${this.bindingsProduct.qr_code || ('#' + this.bindingsProduct.id)}`
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
    formatDateTime(d) {
      if (!d) return '—'
      const s = String(d)
      return s.length >= 16 ? s.substring(0, 16).replace('T', ' ') : s
    },
    methodLabel(m) {
      return { qrcode_sap: '扫码', qrcode_product: '序列号', manual: '手动' }[m] || m
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

    downloadTemplate() {
      // 中文表头 — 与后端 _coerce_csv_row 的 pick('中文', '英文') 一致
      const headers = [
        '二维码', '销售单号', '行项目', '客户名称', '经销商名称',
        '经销商联系人', '经销商电话', '产品编号', '产品名称',
        '发货地址', '收货人', '联系电话',
        '下单日期', '交货日期', '生产日期', '激活日期', '截至日期', '状态',
      ]
      const examples = [
        [
          'QR1001', 'SO202607001', '10', '示例客户公司', '示例经销商有限公司',
          '张三', '13800138000', 'P-001', '示例产品-A',
          '北京市朝阳区建国路 88 号', '李四', '13900139000',
          '2026-07-21', '2026-07-25', '2026-07-15',
          '2026-07-30', '2027-07-30', 'active',
        ],
        [
          'QR1002', 'SO202607001', '20', '另一客户', '另一经销商',
          '王五', '13800138001', 'P-002', '示例产品-B',
          '上海市浦东新区世纪大道 100 号', '赵六', '13900139001',
          '2026-07-22', '2026-07-26', '2026-07-16',
          '2026-07-31', '2027-07-31', 'active',
        ],
        [
          'QR1003', 'SO202607002', '10', '', '',
          '', '', 'P-003', '仅二维码示例',
          '', '', '',
          '2026-07-23', '', '',
          '', '', '',
        ],
      ]
      const escape = (v) => {
        if (v === null || v === undefined) return ''
        const s = String(v)
        if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`
        return s
      }
      const rows = examples.map(row => row.map(escape).join(','))
      // UTF-8 BOM 确保 Excel 打开不乱码
      const csv = '\uFEFF' + [headers.join(','), ...rows].join('\r\n')
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = '产品库导入模板.csv'
      a.click()
      URL.revokeObjectURL(url)
      this.$toast.success('模板已下载')
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
        '下单日期', '交货日期', '生产日期', '激活日期', '截至日期', '状态',
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
        this.formatDate(p.activation_date),
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
        activation_date: toFormDate(p.activation_date),
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

    // === 绑定管理 ===
    async openBindings(p) {
      this.bindingsProduct = p
      this.bindings = []
      this.showBindings = true
      this.bindingsLoading = true
      try {
        const res = await getProductBindings(p.id)
        this.bindings = (res.data && res.data.bindings) || []
        // 同步更新列表里的计数（如果返回的 bound_count 不同）
        if (p.bound_count !== this.bindings.length) {
          p.bound_count = this.bindings.length
        }
      } catch (e) {
        this.$toast && this.$toast('加载绑定列表失败')
      } finally {
        this.bindingsLoading = false
      }
    },
    async confirmUnbind(b) {
      const ok = await this.$dialog.confirm({
        title: '强制解绑确认',
        message: `确定要解除 ${b.phone || b.nickname || ('用户#' + b.user_id)} 的绑定吗？\n该用户的报修记录不会受影响。`,
      }).catch(() => false)
      if (!ok) return
      try {
        await adminUnbind(b.binding_id)
        this.$toast.success('已解绑')
        // 从本地列表移除
        this.bindings = this.bindings.filter(x => x.binding_id !== b.binding_id)
        if (this.bindingsProduct) {
          this.bindingsProduct.bound_count = this.bindings.length
        }
      } catch (e) {
        this.$toast && this.$toast((e && e.response && e.response.data && e.response.data.error) || '解绑失败')
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
.format-help {
  margin-left: auto;
  font-size: 12px;
  color: #1989fa;
  cursor: pointer;
  text-decoration: none;
}
.format-help:hover {
  text-decoration: underline;
}

/* ===== Format guide dialog ===== */
.format-guide {
  padding: 12px 16px;
  max-height: 60vh;
  overflow-y: auto;
  font-size: 13px;
}
.format-guide h4 {
  margin: 0 0 10px 0;
  font-size: 13px;
  color: #1f2937;
}
.format-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 12px;
}
.format-table th,
.format-table td {
  padding: 6px 8px;
  border-bottom: 1px solid #f0f0f0;
  text-align: left;
  font-size: 12px;
  vertical-align: top;
}
.format-table th {
  background: #fafbfc;
  color: #374151;
  font-weight: 600;
}
.format-table code {
  background: #f3f4f6;
  padding: 1px 6px;
  border-radius: 3px;
  font-family: monospace;
  font-size: 11px;
  color: #1989fa;
}
.format-table .req {
  color: #ee0a24;
  font-weight: 600;
}
.format-tips {
  background: #f7f8fa;
  border-radius: 4px;
  padding: 10px 12px;
  font-size: 12px;
  color: #4b5563;
}
.format-tips p {
  margin: 4px 0;
}
.format-tips strong {
  color: #1f2937;
}
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
.op-link.warn { color: #ff976a; }
.op-link.warn:hover { color: #e07643; }

/* ===== 绑定列 ===== */
.col-bound {
  text-align: center;
  min-width: 90px;
}
.bound-badge {
  cursor: pointer;
  font-weight: 600;
}
.bound-badge:hover {
  opacity: 0.85;
}
.bound-zero {
  color: #9ca3af;
  font-size: 12px;
}

/* ===== 绑定列表弹窗 ===== */
.bindings-view {
  padding: 16px 20px 8px;
  min-width: 320px;
}
.bindings-summary {
  background: #f5f6f8;
  border-radius: 6px;
  padding: 12px 14px;
  margin-bottom: 12px;
}
.bindings-summary .sum-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  line-height: 1.8;
}
.bindings-summary .sum-row .label {
  color: #6b7280;
  min-width: 60px;
}
.bindings-loading,
.bindings-empty {
  text-align: center;
  padding: 30px 0;
  color: #9ca3af;
  font-size: 13px;
}
.bindings-list {
  max-height: 50vh;
  overflow-y: auto;
}
.binding-card {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 12px 14px;
  margin-bottom: 10px;
  background: #fff;
}
.binding-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.binding-user {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.user-nick {
  font-weight: 600;
  font-size: 14px;
  color: #1f2937;
}
.user-phone {
  font-size: 12px;
  color: #6b7280;
}
.binding-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px dashed #f0f0f0;
  padding-top: 8px;
}
.bind-time {
  font-size: 12px;
  color: #9ca3af;
}

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