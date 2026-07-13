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
          <van-button size="mini" type="danger" plain @click="removeProduct(p)">删除</van-button>
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

    <!-- 新建产品弹窗 -->
    <van-dialog
      v-model="showCreate"
      title="新建产品记录"
      show-cancel-button
      :before-close="onCreateBeforeClose"
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
        <van-field v-model="form.order_date" label="下单日期" placeholder="YYYY-MM-DD HH:mm:ss" />
        <van-field v-model="form.delivery_date" label="交货日期" placeholder="YYYY-MM-DD HH:mm:ss" />
        <van-field v-model="form.production_date" label="生产日期" placeholder="YYYY-MM-DD" />
      </div>
    </van-dialog>
  </div>
</template>

<script>
import {
  getAllProducts, createProduct, deleteProduct, importProducts
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

      showImportResult: false,
      lastImport: { inserted: 0, skipped: [], errors: [], total: 0, filename: '' },
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
      this.form = emptyForm()
      this.showCreate = true
    },
    onCreateBeforeClose(action) {
      // 'confirm' = 点击确认；return false 阻止关闭
      if (action === 'confirm') {
        return this.submitCreate()
      }
      return true
    },
    async submitCreate() {
      if (!this.form.qr_code || !this.form.qr_code.trim()) {
        this.$toast('请填写二维码')
        return false
      }
      try {
        const payload = {}
        for (const k in this.form) {
          const v = this.form[k]
          payload[k] = (v && String(v).trim()) || null
        }
        await createProduct(payload)
        this.$toast.success('创建成功')
        this.showCreate = false
        this.loadProducts()
        return true
      } catch (e) {
        const msg = (e && e.response && e.response.data && e.response.data.error) || '创建失败'
        this.$toast(msg)
        return false
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
