<template>
  <div class="admin-products">
    <h3>产品库</h3>

    <!-- 顶部 toolbar -->
    <div class="toolbar">
      <van-search
        v-model="keyword"
        placeholder="搜索销售单号/二维码/客户/产品编号/产品名称"
        @search="loadProducts"
        shape="round"
      />
      <div class="toolbar-buttons">
        <van-button size="small" type="primary" icon="plus" @click="openCreate">新建产品</van-button>
        <van-button size="small" plain icon="description" @click="triggerImport">导入CSV</van-button>
        <input ref="fileInput" type="file" accept=".csv" style="display:none" @change="onImportFile" />
      </div>
    </div>

    <!-- 列表 -->
    <van-cell-group class="product-list">
      <van-cell
        v-for="p in products"
        :key="p.id"
        :title="(p.sales_no || '—') + ' · ' + (p.product_no || '')"
        :label="(p.product_name || p.model || '—') + ' · ' + (p.customer_name || '无客户')"
      >
        <template #value>
          <div class="cell-value">
            <div class="qr">二维码：{{ p.qr_code || '—' }}</div>
            <div class="receiver">{{ p.receiver || '' }} {{ p.receiver_phone || '' }}</div>
            <div class="dates">
              下单 {{ formatDate(p.order_date) }}
              · 交货 {{ formatDate(p.delivery_date) }}
            </div>
            <van-tag :type="p.status === 'active' ? 'success' : 'danger'" size="mini" style="margin-top:4px;">
              {{ p.status === 'active' ? '有效' : '无效' }}
            </van-tag>
          </div>
        </template>
        <template #right-icon>
          <div class="row-actions">
            <van-button size="mini" plain @click="previewProduct(p)">查看</van-button>
            <van-button size="mini" type="primary" plain @click="editProduct(p)">编辑</van-button>
            <van-button size="mini" type="danger" plain @click="removeProduct(p)">删除</van-button>
          </div>
        </template>
      </van-cell>
    </van-cell-group>

    <van-empty v-if="!loading && products.length === 0" description="暂无产品数据，点击右上角导入CSV或新建" />

    <div v-if="total > 0" class="pagination">
      共 {{ total }} 条 · 第 {{ page }} / {{ totalPages }} 页
      <van-button size="mini" :disabled="page <= 1" @click="changePage(-1)">上一页</van-button>
      <van-button size="mini" :disabled="page >= totalPages" @click="changePage(1)">下一页</van-button>
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
        <van-field
          v-model="form.qr_code"
          label="二维码"
          placeholder="必填"
          required
        />
        <van-field v-model="form.receiver" label="收货人" />
        <van-field v-model="form.receiver_phone" label="联系电话" />
        <van-cell title="下单日期" :value="form.order_date || '点击选择'" is-link @click="openDatePicker('order_date')" />
        <van-cell title="交货日期" :value="form.delivery_date || '点击选择'" is-link @click="openDatePicker('delivery_date')" />
        <van-cell title="生产日期" :value="form.production_date || '点击选择'" is-link @click="openDatePicker('production_date')" />
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
        <div class="preview-row"><span class="label">状态</span><span class="value">
          <van-tag :type="previewingProduct.status === 'active' ? 'success' : 'danger'" size="mini">
            {{ previewingProduct.status === 'active' ? '有效' : '无效' }}
          </van-tag>
        </span></div>
      </div>
    </van-dialog>

    <!-- 日期选择器（自渲染覆盖层，避免 van-popup 在 dialog 内被遮） -->
    <div v-if="showDatePicker" class="date-overlay" @click.self="showDatePicker = false">
      <div class="date-panel">
        <van-date-picker
          v-model="datePickerValue"
          title="选择日期"
          :min-date="minDate"
          :max-date="maxDate"
          @confirm="onDatePickerConfirm"
          @cancel="showDatePicker = false"
        />
      </div>
    </div>
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
})

export default {
  name: 'AdminProducts',
  data() {
    return {
      products: [],
      keyword: '',
      page: 1,
      pageSize: 50,
      total: 0,
      loading: false,

      showCreate: false,
      form: emptyForm(),
      editingProduct: null,

      showPreview: false,
      previewingProduct: null,

      showImportResult: false,
      lastImport: { inserted: 0, skipped: [], errors: [], total: 0, filename: '' },

      showDatePicker: false,
      datePickerTarget: null,
      datePickerValue: (() => {
        const t = new Date()
        return [t.getFullYear(), t.getMonth() + 1, t.getDate()]
      })(),
      minDate: new Date(2000, 0, 1),
      maxDate: new Date(2099, 11, 31),
    }
  },
  computed: {
    totalPages() {
      return Math.max(1, Math.ceil(this.total / this.pageSize))
    }
  },
  created() {
    this.loadProducts()
  },
  methods: {
    formatDate(d) {
      if (!d) return '—'
      // 接受 "2026-07-06T10:44:15" 或 "2026-07-06 10:44:15"
      return String(d).substring(0, 16).replace('T', ' ')
    },
    async loadProducts() {
      this.loading = true
      try {
        const res = await getAllProducts({
          keyword: this.keyword,
          page: this.page,
          page_size: this.pageSize,
        })
        const data = res.data || {}
        // 兼容旧接口 {products: [...]} 和新接口 {items: [...], total}
        this.products = data.items || data.products || []
        this.total = data.total || this.products.length
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
    openCreate() {
      this.editingProduct = null
      this.form = emptyForm()
      this.showCreate = true
    },
    editProduct(p) {
      // 把后端 ISO 时间格式转成 YYYY-MM-DD（去时间部分，因为 picker 只到日）
      const toFormDate = (s) => {
        if (!s) return ''
        return String(s).substring(0, 10)
      }
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
      }
      this.showCreate = true
    },
    previewProduct(p) {
      this.previewingProduct = p
      this.showPreview = true
    },
    openDatePicker(field) {
      this.datePickerTarget = field
      const cur = this.form[field]
      const m = cur && String(cur).match(/^(\d{4})-(\d{1,2})-(\d{1,2})/)
      if (m) {
        this.datePickerValue = [Number(m[1]), Number(m[2]), Number(m[3])]
      } else {
        const today = new Date()
        this.datePickerValue = [
          today.getFullYear(),
          today.getMonth() + 1,
          today.getDate(),
        ]
      }
      this.showDatePicker = true
    },
    onDatePickerConfirm({ selectedValues }) {
      if (this.datePickerTarget && selectedValues && selectedValues.length >= 3) {
        const [y, mo, d] = selectedValues
        const pad = (n) => String(n).padStart(2, '0')
        this.form[this.datePickerTarget] = `${y}-${pad(mo)}-${pad(d)}`
      }
      this.showDatePicker = false
      this.datePickerTarget = null
    },
    onCancelCreate() {
      // 点"取消"或点遮罩：直接关闭 dialog
      this.showCreate = false
      this.editingProduct = null
    },
    async submitCreate() {
      // 注意: 不再依赖 :before-close 钩子（vant 收到 async Promise 会卡死）
      // 改为 @confirm 调用，成功时手动关 dialog，失败时保持打开让用户重试
      if (!this.form.qr_code || !this.form.qr_code.trim()) {
        this.$toast('请填写二维码')
        return
      }
      const isEdit = !!this.editingProduct
      try {
        const payload = {}
        for (const k in this.form) {
          const v = this.form[k]
          payload[k] = (v && String(v).trim()) || null
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
        const hint = (data && data.hint) || ''
        this.$toast(detail ? err + '：' + detail : err)
        console.error(`[admin/products ${isEdit ? 'PUT' : 'POST'}]`, e.response && e.response.data, hint)
        // 失败时不关 dialog，让用户修改重试
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
      // 立即清空 value，允许重复选同一文件
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
  color: #333;
}
.toolbar {
  background: white;
  border-radius: 8px;
  padding: 8px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.toolbar-buttons {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  padding: 0 8px;
}
.product-list {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.cell-value {
  text-align: right;
  font-size: 12px;
  color: #666;
}
.cell-value .qr {
  font-family: monospace;
  color: #333;
  font-size: 13px;
}
.cell-value .receiver {
  margin-top: 2px;
}
.cell-value .dates {
  margin-top: 2px;
  color: #999;
}
.pagination {
  text-align: center;
  padding: 12px;
  color: #666;
  font-size: 13px;
}
.pagination .van-button {
  margin-left: 8px;
}
.create-form {
  max-height: 60vh;
  overflow-y: auto;
}
.row-actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-end;
}
.row-actions .van-button {
  margin: 0;
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
  color: #999;
}
.preview-row .value {
  flex: 1;
  color: #333;
  word-break: break-all;
}
.preview-row .value.qr-code {
  font-family: monospace;
  color: #1989fa;
}
.date-picker-wrap {
  /* 兼容老样式，无实际作用 */
  min-height: 280px;
}
.date-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 99999;
  display: flex;
  align-items: flex-end;
}
.date-panel {
  width: 100%;
  background: #fff;
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
  overflow: hidden;
}
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
  color: #666;
  max-height: 200px;
  overflow-y: auto;
}
</style>
