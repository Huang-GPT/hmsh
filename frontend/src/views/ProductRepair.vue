<template>
  <div class="product-repair">
    <van-nav-bar title="产品报修" left-arrow @click-left="onBack" fixed :border="false" />
    <div class="repair-spacer" />

    <!-- 顶部步骤条 -->
    <div class="step-bar">
      <van-steps :active="step - 1" active-color="#1989fa" inactive-color="#dcdfe6">
        <van-step>选择产品</van-step>
        <van-step>故障分类</van-step>
        <van-step>详细信息</van-step>
        <van-step>确认提交</van-step>
      </van-steps>
    </div>

    <!-- 已选产品卡片（始终显示顶部，方便回看） -->
    <div v-if="selectedProduct" class="summary-card">
      <div class="summary-product">
        <span class="p-label">报修产品</span>
        <span class="p-name">{{ selectedProduct.product_name || selectedProduct.model }}</span>
        <van-tag v-if="selectedProduct.qr_code" type="primary" size="mini" class="p-qr">
          {{ selectedProduct.qr_code }}
        </van-tag>
      </div>
      <div v-if="selectedCategory || form.fault_type" class="summary-fault">
        <span class="p-label">故障</span>
        <span v-if="selectedCategory" class="f-cat">{{ selectedCategory.name }}</span>
        <span v-if="form.fault_type" class="f-type"> / {{ form.fault_type }}</span>
      </div>
    </div>

    <!-- ============ Step 1：选择产品 ============ -->
    <div v-if="step === 1" class="step-content">
      <div v-if="loadingProducts" class="loading-tip">加载产品列表…</div>
      <div v-else-if="productList.length === 0" class="empty-tip">
        <van-empty description="您还没有绑定任何产品">
          <van-button round type="primary" size="small" @click="$router.push('/product/bind')">
            立即绑定
          </van-button>
        </van-empty>
      </div>
      <div v-else class="product-cards">
        <div
          v-for="p in productList"
          :key="p.id"
          :class="['product-card', { selected: selectedProduct && selectedProduct.id === p.id }]"
          @click="pickProduct(p)"
        >
          <div class="pc-icon">📦</div>
          <div class="pc-info">
            <div class="pc-name">{{ p.product_name || p.model || '产品' }}</div>
            <div class="pc-meta">
              <span v-if="p.qr_code">码: {{ p.qr_code }}</span>
              <span v-if="p.sales_no" class="pc-meta-item">单号: {{ p.sales_no }}</span>
            </div>
            <div v-if="p.production_date" class="pc-meta-item pc-date">
              生产日期: {{ formatDate(p.production_date) }}
            </div>
          </div>
          <van-icon v-if="selectedProduct && selectedProduct.id === p.id" name="success" class="pc-check" />
        </div>
      </div>
    </div>

    <!-- ============ Step 2：故障分类 ============ -->
    <div v-if="step === 2" class="step-content">
      <div v-if="loadingCats" class="loading-tip">加载故障分类…</div>
      <div v-else-if="categories.length === 0" class="empty-tip">
        <van-empty description="暂无故障分类，请联系管理员" />
      </div>
      <div v-else>
        <div class="cat-section">
          <div class="section-title">选择故障分类</div>
          <div class="cat-grid">
            <div
              v-for="cat in categories"
              :key="cat.id"
              :class="['cat-item', { active: selectedCategory && selectedCategory.id === cat.id }]"
              @click="pickCategory(cat)"
            >
              <div class="cat-icon">{{ cat.icon || '🔧' }}</div>
              <div class="cat-name">{{ cat.name }}</div>
            </div>
          </div>
        </div>

        <!-- 选了分类后：展示子分类或常见故障 -->
        <div v-if="selectedCategory" class="cat-section">
          <div class="section-title">参考常见故障（可一键选用）</div>
          <div v-if="loadingFaults" class="loading-tip">加载中…</div>
          <div v-else-if="commonFaults.length === 0" class="hint-tip">该分类暂无常见故障案例，请直接在下方输入</div>
          <div v-else class="fault-list">
            <div
              v-for="f in commonFaults"
              :key="f.id"
              :class="['fault-item', { active: form.fault_type === f.title }]"
              @click="form.fault_type = f.title"
            >
              <div class="f-title">{{ f.title }}</div>
              <div v-if="f.content" class="f-desc">{{ f.content }}</div>
            </div>
          </div>
        </div>

        <van-cell-group inset class="fault-type-input">
          <van-field
            v-model="form.fault_type"
            label="故障概述"
            placeholder="简要描述故障（必填）"
            :rules="[{ required: true, message: '请输入故障概述' }]"
            maxlength="40"
            show-word-limit
          />
        </van-cell-group>
      </div>
    </div>

    <!-- ============ Step 3：详细信息 ============ -->
    <div v-if="step === 3" class="step-content">
      <van-cell-group inset>
        <van-field
          v-model="form.fault_desc"
          label="详细描述"
          type="textarea"
          placeholder="请详细描述故障现象、出现频率、错误提示等"
          rows="3"
          autosize
          maxlength="500"
          show-word-limit
          required
        />
      </van-cell-group>

      <van-cell-group inset class="block-group">
        <van-cell title="上传图片（最多 9 张）" />
        <div class="uploader-wrap">
          <van-uploader
            v-model="imageFiles"
            :max-count="9"
            :after-read="uploadImage"
            :before-delete="deleteImage"
            accept="image/*"
          >
            <template #default>
              <div class="upload-btn">
                <van-icon name="photograph" size="22" />
                <div>上传图片</div>
              </div>
            </template>
          </van-uploader>
        </div>
      </van-cell-group>

      <van-cell-group inset class="block-group">
        <van-field
          v-model="form.fault_address"
          label="故障地址"
          placeholder="如: 上海市浦东新区xxx路xx号"
          maxlength="120"
        />
      </van-cell-group>

      <van-cell-group inset class="block-group">
        <van-cell title="期望服务时间" :is-link="false">
          <template #value>
            <van-radio-group v-model="appointmentMode" direction="horizontal">
              <van-radio name="asap">尽快</van-radio>
              <van-radio name="specific">指定时间</van-radio>
            </van-radio-group>
          </template>
        </van-cell>
        <template v-if="appointmentMode === 'specific'">
          <van-cell title="日期" is-link @click="showDatePicker = true">
            <template #value>
              <span :class="{ placeholder: !form.appointment_date }">
                {{ form.appointment_date || '点击选择日期' }}
              </span>
            </template>
          </van-cell>
          <van-cell title="时段" is-link @click="showPeriodPicker = true">
            <template #value>
              <span :class="{ placeholder: !form.appointment_period }">
                {{ form.appointment_period === 'AM' ? '上午 (08:00-12:00)' :
                   form.appointment_period === 'PM' ? '下午 (12:00-18:00)' : '点击选择时段' }}
              </span>
            </template>
          </van-cell>
        </template>
      </van-cell-group>

      <van-cell-group inset class="block-group">
        <van-field
          v-model="form.contact_name"
          label="联系人"
          placeholder="请输入联系人姓名"
          required
          maxlength="20"
        />
        <van-field
          v-model="form.contact_phone"
          label="联系电话"
          type="tel"
          placeholder="请输入联系电话"
          required
          maxlength="11"
        />
      </van-cell-group>
    </div>

    <!-- ============ Step 4：确认提交 ============ -->
    <div v-if="step === 4" class="step-content">
      <div class="confirm-card">
        <div class="confirm-header">
          <van-icon name="success" class="check-icon" />
          <span>请确认报修信息</span>
        </div>
        <van-cell-group inset>
          <van-cell title="报修产品">
            <template #value>
              <span class="val-main">{{ selectedProduct.product_name || selectedProduct.model }}</span>
            </template>
          </van-cell>
          <van-cell v-if="selectedProduct.qr_code" title="产品二维码" :value="selectedProduct.qr_code" />
          <van-cell v-if="selectedProduct.sales_no" title="销售单号" :value="selectedProduct.sales_no" />
          <van-cell title="故障分类">
            <template #value>{{ selectedCategory ? selectedCategory.name : '—' }}</template>
          </van-cell>
          <van-cell title="故障概述" :value="form.fault_type" />
          <van-cell title="详细描述">
            <template #value>
              <div class="multi-line">{{ form.fault_desc || '—' }}</div>
            </template>
          </van-cell>
          <van-cell v-if="form.fault_address" title="故障地址" :value="form.fault_address" />
          <van-cell v-if="form.appointment_date" title="期望时间">
            <template #value>
              {{ form.appointment_date }} {{ form.appointment_period === 'AM' ? '上午' : form.appointment_period === 'PM' ? '下午' : '' }}
            </template>
          </van-cell>
          <van-cell v-if="appointmentMode === 'asap'" title="期望时间" value="尽快上门" />
          <van-cell title="联系人" :value="form.contact_name" />
          <van-cell title="联系电话" :value="form.contact_phone" />
          <van-cell v-if="form.images && form.images.length" title="图片">
            <template #value>{{ form.images.length }} 张</template>
          </van-cell>
        </van-cell-group>

        <div class="confirm-warning">
          <van-icon name="info-o" />
          <span>提交后将由客服主动联系您安排服务，预计 1 个工作日内反馈</span>
        </div>
      </div>
    </div>

    <!-- ============ 底部按钮 ============ -->
    <div class="bottom-bar">
      <van-button v-if="step > 1" plain @click="step--" class="bottom-btn">上一步</van-button>
      <van-button
        v-if="step < 4"
        type="primary"
        :loading="submitting"
        :disabled="!canNext"
        @click="next"
        class="bottom-btn"
      >下一步</van-button>
      <van-button
        v-if="step === 4"
        type="success"
        :loading="submitting"
        @click="submitOrder"
        class="bottom-btn"
      >确认提交</van-button>
    </div>

    <!-- 日期选择器（van-calendar 点选日历格） -->
    <van-calendar
      v-model:show="showDatePicker"
      :min-date="minDate"
      :max-date="maxDate"
      :default-date="selectedDateObj"
      type="single"
      color="#1989fa"
      :show-confirm="true"
      confirm-text="确定"
      @confirm="onDateConfirm"
    />

    <!-- 时段选择器 -->
    <van-popup v-model="showPeriodPicker" position="bottom">
      <van-picker
        :columns="periodColumns"
        @confirm="onPeriodConfirm"
        @cancel="showPeriodPicker = false"
        title="选择时段"
      />
    </van-popup>
  </div>
</template>

<script>
import { getUserProducts } from '@/api/products'
import { getFaultCategories, getFaultsByCategory, createOrder, uploadMedia } from '@/api/repair'

const emptyForm = () => ({
  fault_category_id: null,
  fault_type: '',
  fault_desc: '',
  images: [],
  fault_address: '',
  appointment_date: '',
  appointment_period: '',
  contact_name: '',
  contact_phone: '',
})

export default {
  name: 'ProductRepair',
  data() {
    return {
      step: 1,
      productList: [],
      loadingProducts: false,
      selectedProduct: null,

      categories: [],
      loadingCats: false,
      selectedCategory: null,
      commonFaults: [],
      loadingFaults: false,

      form: emptyForm(),
      imageFiles: [],
      appointmentMode: 'asap',

      showDatePicker: false,
      selectedDateObj: new Date(),
      showPeriodPicker: false,
      periodColumns: [
        { text: '上午 (08:00-12:00)', value: 'AM' },
        { text: '下午 (12:00-18:00)', value: 'PM' },
      ],

      submitting: false,
      minDate: new Date(),
      maxDate: (() => {
        const d = new Date()
        d.setDate(d.getDate() + 30)
        return d
      })(),
    }
  },
  computed: {
    canNext() {
      if (this.step === 1) return !!this.selectedProduct
      if (this.step === 2) return !!this.selectedCategory && !!this.form.fault_type.trim()
      if (this.step === 3) {
        return !!this.form.fault_desc.trim() &&
               !!this.form.contact_name.trim() &&
               /^1[3-9]\d{9}$/.test(this.form.contact_phone)
      }
      return true
    },
  },
  watch: {
    // 图片文件变化：同步 form.images
    imageFiles: {
      handler(newList) {
        const newUrls = newList
          .filter(f => f.status === 'done' && f._uploadedUrl)
          .map(f => f._uploadedUrl)
        this.form.images = newUrls
      },
      deep: true,
    },
  },
  created() {
    this.loadProducts()
    this.loadCategories()
  },
  methods: {
    onBack() {
      if (this.step > 1) {
        this.step -= 1
        return
      }
      this.$router.back()
    },
    formatDate(d) {
      if (!d) return ''
      const s = String(d)
      return s.length >= 10 ? s.substring(0, 10) : s
    },
    async loadProducts() {
      this.loadingProducts = true
      try {
        const res = await getUserProducts()
        this.productList = (res.data && res.data.products) || []
      } catch (e) {
        this.$toast && this.$toast('加载产品列表失败')
      } finally {
        this.loadingProducts = false
      }
    },
    pickProduct(p) {
      this.selectedProduct = p
      // 智能预填联系人（如果之前填过）
      if (!this.form.contact_name) this.form.contact_name = ''
      if (!this.form.contact_phone) this.form.contact_phone = ''
    },
    async loadCategories() {
      this.loadingCats = true
      try {
        const res = await getFaultCategories()
        this.categories = (res.data && res.data.categories) || []
      } catch (e) {
        // 静默失败，进入 Step 2 时再 toast
      } finally {
        this.loadingCats = false
      }
    },
    async pickCategory(cat) {
      this.selectedCategory = cat
      this.form.fault_category_id = cat.id
      // 加载该分类的常见故障
      this.loadingFaults = true
      try {
        const res = await getFaultsByCategory(cat.id)
        this.commonFaults = (res.data && res.data.faults) || []
      } catch (e) {
        this.commonFaults = []
      } finally {
        this.loadingFaults = false
      }
    },
    next() {
      if (!this.canNext) {
        if (this.step === 2) {
          this.$toast && this.$toast('请选择故障分类并输入故障概述')
        }
        return
      }
      this.step += 1
    },

    // ===== 图片 / 视频 上传 =====
    /**
     * van-uploader 在 Vue 2 中有反应式坑：
     *   - fileList 是 v-model 数组（反应式）
     *   - 但数组项 file 是普通对象，修改属性不会触发响应
     *   - 所以直接 file.status = 'done' 不会让 UI 更新
     * 修复：上传完成后用 splice + 替换对象，强制触发响应
     */
    _markFileDone(file, url) {
      const list = this.imageFiles
      const idx = list.indexOf(file)
      if (idx < 0) return
      const newItem = Object.assign({}, file, {
        status: 'done',
        message: '',
        _uploadedUrl: url,
        url: url,
      })
      list.splice(idx, 1, newItem)
    },
    _markFileFailed(file, message) {
      const idx = this.imageFiles.indexOf(file)
      if (idx < 0) return
      const newItem = Object.assign({}, file, {
        status: 'failed',
        message,
      })
      this.imageFiles.splice(idx, 1, newItem)
    },

    async uploadImage(file) {
      const f = file.file || file
      if (!f) return
      try {
        const fd = new FormData()
        fd.append('file', f)
        fd.append('kind', 'image')
        const res = await uploadMedia(fd)
        const url = (res.data && res.data.url) || ''
        this._markFileDone(file, url)
      } catch (e) {
        this._markFileFailed(file, '上传失败')
        this.$toast && this.$toast('图片上传失败')
        throw e
      }
    },
    deleteImage(file, detail) {
      // van-uploader 内部 splice（响应式），watch 会同步 form.images
      return true
    },

    // ===== 日期 / 时段 =====
    onDateConfirm(date) {
      // van-calendar confirm 回调：date 是 Date 对象
      const d = date instanceof Date ? date : (date && date[0]) || new Date()
      const yyyy = d.getFullYear()
      const mm = String(d.getMonth() + 1).padStart(2, '0')
      const dd = String(d.getDate()).padStart(2, '0')
      this.form.appointment_date = `${yyyy}-${mm}-${dd}`
      this.selectedDateObj = d
      this.showDatePicker = false
    },
    onPeriodConfirm({ selectedOptions }) {
      this.form.appointment_period = selectedOptions[0] && selectedOptions[0].value
      this.showPeriodPicker = false
    },

    // ===== 提交 =====
    async submitOrder() {
      this.submitting = true
      try {
        const payload = {
          product_id: this.selectedProduct.id,
          fault_category_id: this.form.fault_category_id,
          fault_type: this.form.fault_type,
          fault_desc: this.form.fault_desc,
          images: this.form.images,
          fault_address: this.form.fault_address,
          contact_name: this.form.contact_name,
          contact_phone: this.form.contact_phone,
        }
        if (this.appointmentMode === 'specific') {
          payload.appointment_date = this.form.appointment_date
          payload.appointment_period = this.form.appointment_period
        }
        const res = await createOrder(payload)
        const orderNo = (res.data && res.data.order_no) || ''
        this.$dialog.alert({
          title: '报修成功',
          message: `工单号：${orderNo}\n请保持电话畅通，客服将尽快联系您。`,
          confirmButtonText: '查看进度',
        }).then(() => {
          this.$router.replace({ path: '/progress' })
        }).catch(() => {
          this.$router.replace({ path: '/progress' })
        })
      } catch (e) {
        const msg = (e && e.response && e.response.data && e.response.data.error) || '提交失败'
        this.$toast && this.$toast(msg)
      } finally {
        this.submitting = false
      }
    },
  },
}
</script>

<style scoped>
.product-repair {
  min-height: 100vh;
  background: #f5f6f8;
  padding-bottom: 80px;
}
.repair-spacer {
  height: 46px;
}
.step-bar {
  background: #fff;
  padding: 16px 12px 8px;
  margin-bottom: 12px;
}
.summary-card {
  background: #fff;
  border-left: 3px solid #1989fa;
  padding: 10px 16px;
  margin: 0 16px 12px;
  border-radius: 4px;
  font-size: 13px;
  color: #4b5563;
}
.summary-product,
.summary-fault {
  display: flex;
  align-items: center;
  gap: 6px;
}
.p-label {
  color: #9ca3af;
  margin-right: 2px;
}
.p-name {
  color: #1f2937;
  font-weight: 600;
}
.p-qr {
  margin-left: 4px;
}
.f-cat {
  color: #1989fa;
}
.f-type {
  color: #6b7280;
}

.step-content {
  padding: 0 16px 16px;
}

.loading-tip,
.empty-tip,
.hint-tip {
  text-align: center;
  padding: 30px 0;
  color: #9ca3af;
  font-size: 13px;
}

/* === Step 1 产品卡片 === */
.product-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.product-card {
  background: #fff;
  border-radius: 8px;
  padding: 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
}
.product-card:active {
  background: #f3f4f6;
}
.product-card.selected {
  border-color: #1989fa;
  background: #ecf5ff;
}
.pc-icon {
  font-size: 32px;
  width: 48px;
  height: 48px;
  background: #f3f4f6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.pc-info {
  flex: 1;
  min-width: 0;
}
.pc-name {
  font-weight: 600;
  color: #1f2937;
  font-size: 15px;
  margin-bottom: 4px;
}
.pc-meta {
  font-size: 12px;
  color: #6b7280;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.pc-meta-item {
  font-size: 12px;
  color: #9ca3af;
}
.pc-date {
  margin-top: 2px;
}
.pc-check {
  color: #1989fa;
  font-size: 22px;
}

/* === Step 2 故障分类 === */
.cat-section {
  background: #fff;
  border-radius: 8px;
  padding: 14px 12px;
  margin-bottom: 12px;
}
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 12px;
}
.cat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}
.cat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 6px;
  border-radius: 8px;
  background: #f9fafb;
  cursor: pointer;
  transition: all 0.2s;
}
.cat-item:active {
  background: #f3f4f6;
}
.cat-item.active {
  background: #ecf5ff;
  border: 1px solid #1989fa;
}
.cat-icon {
  font-size: 28px;
  margin-bottom: 4px;
}
.cat-name {
  font-size: 12px;
  color: #4b5563;
  text-align: center;
  line-height: 1.3;
}

.fault-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.fault-item {
  background: #f9fafb;
  border-radius: 6px;
  padding: 10px 12px;
  cursor: pointer;
  border: 1px solid transparent;
}
.fault-item.active {
  background: #ecf5ff;
  border-color: #1989fa;
}
.f-title {
  font-weight: 600;
  font-size: 13px;
  color: #1f2937;
}
.f-desc {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
  line-height: 1.5;
}
.fault-type-input {
  margin-top: 12px;
}

/* === Step 3 信息表单 === */
.block-group {
  margin-bottom: 12px;
}
.uploader-wrap {
  padding: 12px;
}
.upload-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  background: #f9fafb;
  border-radius: 6px;
  color: #6b7280;
  font-size: 12px;
  gap: 4px;
}
.placeholder {
  color: #c0c4cc;
}

/* === Step 4 确认卡片 === */
.confirm-card {
  background: #fff;
  border-radius: 8px;
  margin-bottom: 12px;
  overflow: hidden;
}
.confirm-header {
  background: linear-gradient(135deg, #4a90e2, #1989fa);
  color: #fff;
  padding: 14px 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}
.check-icon {
  font-size: 20px;
  color: #fff;
}
.val-main {
  font-weight: 600;
  color: #1f2937;
}
.multi-line {
  white-space: pre-wrap;
  color: #4b5563;
  line-height: 1.6;
  max-width: 220px;
}
.confirm-warning {
  background: #fffbe6;
  color: #ad6800;
  padding: 12px 16px;
  font-size: 12px;
  display: flex;
  align-items: flex-start;
  gap: 6px;
  border-top: 1px solid #fde68a;
}
.confirm-warning .van-icon {
  flex-shrink: 0;
  margin-top: 1px;
}

/* === 底部按钮 === */
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #fff;
  padding: 12px 16px;
  display: flex;
  gap: 12px;
  box-shadow: 0 -2px 8px rgba(0,0,0,0.04);
  z-index: 100;
}
.bottom-btn {
  flex: 1;
}
</style>