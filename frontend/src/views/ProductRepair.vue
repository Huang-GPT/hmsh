<template>
  <div class="product-repair">
    <h1>产品维修</h1>
    
    <van-form @submit="onSubmit">
      <van-field
        v-model="form.product_id"
        is-link
        readonly
        label="选择产品"
        placeholder="请选择需要维修的产品"
        @click="showProductPicker = true"
        :rules="[{ required: true, message: '请选择产品' }]"
      />
      
      <van-field
        v-model="form.fault_type"
        is-link
        readonly
        label="故障类型"
        placeholder="请选择故障类型"
        @click="showFaultTypePicker = true"
        :rules="[{ required: true, message: '请选择故障类型' }]"
      />
      
      <van-field
        v-model="form.fault_desc"
        type="textarea"
        label="故障描述"
        placeholder="请详细描述故障现象"
        rows="4"
        autosize
        :rules="[{ required: true, message: '请输入故障描述' }]"
      />
      
      <van-field label="上传图片">
        <template #input>
          <van-uploader v-model="form.images" :max-count="9" />
        </template>
      </van-field>
      
      <van-field
        v-model="form.contact_name"
        label="联系人"
        placeholder="请输入联系人姓名"
        :rules="[{ required: true, message: '请输入联系人' }]"
      />
      
      <van-field
        v-model="form.contact_phone"
        label="联系电话"
        type="tel"
        placeholder="请输入联系电话"
        :rules="[{ required: true, message: '请输入联系电话' }]"
      />
      
      <van-field
        v-model="form.expected_time"
        is-link
        readonly
        label="期望服务时间"
        placeholder="请选择期望服务时间"
        @click="showDatePicker = true"
      />
      
      <div style="margin: 16px;">
        <van-button round block type="info" native-type="submit">
          提交工单
        </van-button>
      </div>
    </van-form>
    
    <van-popup v-model="showProductPicker" position="bottom">
      <van-picker
        :columns="productList"
        @confirm="onProductConfirm"
        @cancel="showProductPicker = false"
      />
    </van-popup>
    
    <van-popup v-model="showFaultTypePicker" position="bottom">
      <van-picker
        :columns="faultTypes"
        @confirm="onFaultTypeConfirm"
        @cancel="showFaultTypePicker = false"
      />
    </van-popup>
    
    <van-popup v-model="showDatePicker" position="bottom">
      <van-datetime-picker
        v-model="currentDate"
        type="datetime"
        @confirm="onDateConfirm"
        @cancel="showDatePicker = false"
      />
    </van-popup>
  </div>
</template>

<script>
import { createWorkOrder } from '@/api/workOrders'
import { getUserProducts } from '@/api/products'

export default {
  name: 'ProductRepair',
  data() {
    return {
      form: {
        product_id: '',
        fault_type: '',
        fault_desc: '',
        images: [],
        contact_name: '',
        contact_phone: '',
        expected_time: ''
      },
      productList: [],
      faultTypes: ['无法启动', '运行异常', '部件损坏', '功能故障', '其他'],
      showProductPicker: false,
      showFaultTypePicker: false,
      showDatePicker: false,
      currentDate: new Date()
    }
  },
  created() {
    this.loadProducts()
  },
  methods: {
    async loadProducts() {
      try {
        const res = await getUserProducts(this.$store.state.user.id)
        this.productList = res.data.products.map(p => ({
          text: `${p.model} (${p.serial_number})`,
          value: p.id
        }))
      } catch (error) {
        console.error('加载产品列表失败', error)
      }
    },
    onProductConfirm(picker) {
      this.form.product_id = picker.value
      this.showProductPicker = false
    },
    onFaultTypeConfirm(picker) {
      this.form.fault_type = picker.value
      this.showFaultTypePicker = false
    },
    onDateConfirm(value) {
      this.form.expected_time = value.toISOString()
      this.showDatePicker = false
    },
    async onSubmit() {
      try {
        await createWorkOrder({
          user_id: this.$store.state.user.id,
          ...this.form
        })
        this.$toast.success('工单提交成功')
        this.$router.push('/progress')
      } catch (error) {
        this.$toast.fail(error.message || '提交失败')
      }
    }
  }
}
</script>

<style scoped>
.product-repair {
  padding: 16px;
}
</style>