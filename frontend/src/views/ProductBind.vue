<template>
  <div class="product-bind">
    <h1>产品绑定</h1>
    
    <div class="bind-method-tabs">
      <van-tabs v-model="activeTab" @change="onTabChange">
        <van-tab title="手动添加">
          <van-form @submit="onManualSubmit">
            <van-field
              v-model="manualForm.serial_number"
              label="产品序列号"
              placeholder="请输入产品序列号"
              :rules="[{ required: true, message: '请输入产品序列号' }]"
            />
            <van-field
              v-model="manualForm.model"
              label="产品型号"
              placeholder="请输入产品型号"
              :rules="[{ required: true, message: '请输入产品型号' }]"
            />
            <div style="margin: 16px;">
              <van-button round block type="info" native-type="submit">
                绑定产品
              </van-button>
            </div>
          </van-form>
        </van-tab>
        
        <van-tab title="扫码添加">
          <div class="scan-section">
            <van-button type="primary" @click="scanProduct">
              扫描产品二维码
            </van-button>
          </div>
          
          <van-divider>或</van-divider>
          
          <van-form @submit="onOrderSubmit">
            <van-field
              v-model="orderForm.sap_order_no"
              label="SAP销售订单号"
              placeholder="请输入SAP销售订单号"
              :rules="[{ required: true, message: '请输入SAP销售订单号' }]"
            />
            <van-field
              v-model="orderForm.sap_line_item"
              label="行项目号"
              placeholder="请输入行项目号"
              :rules="[{ required: true, message: '请输入行项目号' }]"
            />
            <div style="margin: 16px;">
              <van-button round block type="info" native-type="submit">
                绑定产品
              </van-button>
            </div>
          </van-form>
        </van-tab>
      </van-tabs>
    </div>
    
    <div class="bound-products">
      <h2>已绑定产品</h2>
      <van-list>
        <van-cell
          v-for="product in boundProducts"
          :key="product.id"
          :title="product.model"
          :label="product.serial_number"
          :value="product.bind_method === 'manual' ? '手动绑定' : '订单绑定'"
        />
      </van-list>
    </div>
  </div>
</template>

<script>
import { bindProduct, getUserProducts } from '@/api/products'
import { scanQRCode } from '@/utils/wechat'

export default {
  name: 'ProductBind',
  data() {
    return {
      activeTab: 0,
      manualForm: {
        serial_number: '',
        model: ''
      },
      orderForm: {
        sap_order_no: '',
        sap_line_item: ''
      },
      boundProducts: []
    }
  },
  created() {
    this.loadBoundProducts()
  },
  methods: {
    onTabChange(name) {
      this.activeTab = name
    },
    async onManualSubmit() {
      try {
        await bindProduct({
          user_id: this.$store.state.user.id,
          bind_method: 'manual',
          ...this.manualForm
        })
        this.$toast.success('绑定成功')
        this.loadBoundProducts()
        this.manualForm = { serial_number: '', model: '' }
      } catch (error) {
        this.$toast.fail(error.message || '绑定失败')
      }
    },
    async onOrderSubmit() {
      try {
        await bindProduct({
          user_id: this.$store.state.user.id,
          bind_method: 'order',
          ...this.orderForm
        })
        this.$toast.success('绑定成功')
        this.loadBoundProducts()
        this.orderForm = { sap_order_no: '', sap_line_item: '' }
      } catch (error) {
        this.$toast.fail(error.message || '绑定失败')
      }
    },
    async scanProduct() {
      try {
        const result = await scanQRCode()
        const [sap_order_no, sap_line_item] = result.split('|')
        await bindProduct({
          user_id: this.$store.state.user.id,
          bind_method: 'order',
          sap_order_no,
          sap_line_item
        })
        this.$toast.success('绑定成功')
        this.loadBoundProducts()
      } catch (error) {
        this.$toast.fail('扫码失败')
      }
    },
    async loadBoundProducts() {
      try {
        const res = await getUserProducts(this.$store.state.user.id)
        this.boundProducts = res.data.products
      } catch (error) {
        console.error('加载产品列表失败', error)
      }
    }
  }
}
</script>

<style scoped>
.product-bind {
  padding: 16px;
}
.bind-method-tabs {
  margin-bottom: 24px;
}
.scan-section {
  text-align: center;
  padding: 24px;
}
.bound-products {
  margin-top: 24px;
}
</style>