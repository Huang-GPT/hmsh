<template>
  <div class="admin-bindings">
    <h3>绑定记录总览</h3>

    <div class="toolbar">
      <div class="toolbar-row">
        <van-search
          v-model="keyword"
          placeholder="搜索 二维码 / 销售单号 / 产品名 / 手机号 / 昵称"
          @search="loadList(1)"
          shape="round"
          class="search-box"
        />
      </div>
      <div class="toolbar-row toolbar-bottom">
        <span class="filter-label">绑定方式：</span>
        <span
          v-for="f in methodFilters"
          :key="f.value"
          :class="['filter-chip', { active: methodFilter === f.value }]"
          @click="setMethodFilter(f.value)"
        >{{ f.label }} ({{ f.count }})</span>
        <van-button size="small" plain icon="replay" @click="loadList()">刷新</van-button>
      </div>
    </div>

    <div class="table-wrap">
      <table class="binding-table">
        <thead>
          <tr>
            <th class="col-id">绑定ID</th>
            <th>绑定时间</th>
            <th>方式</th>
            <th>用户手机号</th>
            <th>昵称</th>
            <th>账号状态</th>
            <th>产品ID</th>
            <th>二维码</th>
            <th>销售单号</th>
            <th>产品名称</th>
            <th>生产日期</th>
            <th class="col-actions">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading && items.length === 0">
            <td colspan="12" class="state-cell">加载中…</td>
          </tr>
          <tr v-else-if="items.length === 0">
            <td colspan="12" class="state-cell">
              <div class="empty-cell">
                <div class="empty-icon">📋</div>
                <div class="empty-text">暂无绑定记录</div>
              </div>
            </td>
          </tr>
          <tr v-for="b in items" :key="b.binding_id">
            <td class="col-id">#{{ b.binding_id }}</td>
            <td class="col-time">{{ formatDateTime(b.bind_time) }}</td>
            <td>
              <van-tag :type="b.bind_method === 'qrcode_sap' ? 'success' : 'primary'" size="mini">
                {{ methodLabel(b.bind_method) }}
              </van-tag>
            </td>
            <td><code>{{ b.phone || '—' }}</code></td>
            <td>{{ b.nickname || '—' }}</td>
            <td>
              <van-tag :type="b.user_status === 'disabled' ? 'danger' : 'success'" size="mini">
                {{ b.user_status === 'disabled' ? '已停用' : '正常' }}
              </van-tag>
            </td>
            <td class="col-id">#{{ b.product_id }}</td>
            <td class="col-qr"><code>{{ b.qr_code || '—' }}</code></td>
            <td>{{ b.sales_no || '—' }}</td>
            <td>{{ b.product_name || '—' }}</td>
            <td class="col-date">{{ formatDate(b.production_date) }}</td>
            <td class="col-actions">
              <a class="op-link danger" @click="confirmUnbind(b)">解绑</a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

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
  </div>
</template>

<script>
import { getAllBindings, adminUnbind } from '@/api/admin'

export default {
  name: 'AdminBindings',
  data() {
    return {
      keyword: '',
      methodFilter: 'all',
      page: 1,
      pageSize: 50,
      total: 0,
      loading: false,
      items: [],
    }
  },
  computed: {
    totalPages() {
      return Math.max(1, Math.ceil(this.total / this.pageSize))
    },
    methodFilters() {
      return [
        { value: 'all', label: '全部' },
        { value: 'qrcode_sap', label: '扫码' },
        { value: 'qrcode_product', label: '序列号' },
        { value: 'manual', label: '手动' },
      ]
    },
  },
  watch: {
    methodFilter() {
      this.loadList(1)
    },
  },
  created() {
    this.loadList()
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
    setMethodFilter(v) {
      this.methodFilter = v
    },
    async loadList(targetPage) {
      if (targetPage) this.page = targetPage
      this.loading = true
      try {
        const params = {
          keyword: this.keyword,
          page: this.page,
          page_size: this.pageSize,
        }
        if (this.methodFilter && this.methodFilter !== 'all') {
          params.method = this.methodFilter
        }
        const res = await getAllBindings(params)
        const data = res.data || {}
        this.items = data.items || []
        this.total = data.total || this.items.length
      } catch (e) {
        this.$toast && this.$toast('加载绑定记录失败')
      } finally {
        this.loading = false
      }
    },
    changePage(delta) {
      const next = this.page + delta
      if (next < 1 || next > this.totalPages) return
      this.page = next
      this.loadList()
    },
    async confirmUnbind(b) {
      const ok = await this.$dialog.confirm({
        title: '强制解绑确认',
        message: `确定要解除 ${b.phone || b.nickname || ('用户#' + b.user_id)} 对产品 #${b.product_id} (${b.qr_code || '无码'}) 的绑定吗？`,
      }).catch(() => false)
      if (!ok) return
      try {
        await adminUnbind(b.binding_id)
        this.$toast.success('已解绑')
        this.items = this.items.filter(x => x.binding_id !== b.binding_id)
        this.total = Math.max(0, this.total - 1)
      } catch (e) {
        this.$toast && this.$toast((e && e.response && e.response.data && e.response.data.error) || '解绑失败')
      }
    },
  },
}
</script>

<style scoped>
.admin-bindings {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  min-height: calc(100vh - 88px);
}
h3 {
  margin: 0 0 16px;
  font-size: 18px;
  color: #1f2937;
}
.toolbar {
  margin-bottom: 12px;
}
.toolbar-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.toolbar-row.toolbar-bottom {
  margin-bottom: 0;
}
.search-box {
  flex: 1;
  min-width: 280px;
}
.filter-label {
  font-size: 13px;
  color: #6b7280;
}
.filter-chip {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 14px;
  background: #f3f4f6;
  font-size: 13px;
  color: #4b5563;
  cursor: pointer;
  transition: all 0.2s;
}
.filter-chip:hover {
  background: #e5e7eb;
}
.filter-chip.active {
  background: #1989fa;
  color: white;
}
.table-wrap {
  overflow-x: auto;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  margin-top: 16px;
}
.binding-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.binding-table th {
  background: #f9fafb;
  padding: 10px 8px;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
  white-space: nowrap;
}
.binding-table td {
  padding: 10px 8px;
  border-bottom: 1px solid #f3f4f6;
  color: #4b5563;
  vertical-align: middle;
}
.binding-table tr:hover td {
  background: #f9fafb;
}
.col-id {
  font-family: ui-monospace, monospace;
  color: #6b7280;
  white-space: nowrap;
}
.col-qr code {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
}
.col-time {
  font-family: ui-monospace, monospace;
  font-size: 12px;
  color: #6b7280;
  white-space: nowrap;
}
.col-date {
  white-space: nowrap;
}
.col-actions {
  white-space: nowrap;
}
.op-link {
  color: #1989fa;
  cursor: pointer;
  margin-right: 8px;
  font-size: 13px;
}
.op-link:hover {
  text-decoration: underline;
}
.op-link.danger {
  color: #ee0a24;
}
.op-link.danger:hover {
  color: #c8050a;
}
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
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 4px 0;
}
.pagination-info {
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
</style>