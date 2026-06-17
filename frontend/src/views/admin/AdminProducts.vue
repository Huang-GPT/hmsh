<template>
  <div class="admin-products">
    <h3>产品管理</h3>

    <div class="filter-bar">
      <van-search v-model="keyword" placeholder="搜索序列号/型号" @search="loadProducts" shape="round" />
    </div>

    <van-cell-group class="product-list">
      <van-cell
        v-for="product in products"
        :key="product.id"
        :title="product.model"
        :label="'序列号: ' + product.serial_number"
        :value="product.status === 'active' ? '有效' : '无效'"
      >
        <template #right-icon>
          <van-tag :type="product.status === 'active' ? 'success' : 'danger'" size="medium">
            {{ product.status === 'active' ? '有效' : '无效' }}
          </van-tag>
        </template>
      </van-cell>
    </van-cell-group>

    <van-empty v-if="products.length === 0" description="暂无产品" />
  </div>
</template>

<script>
import { getAllProducts } from '@/api/admin'

export default {
  name: 'AdminProducts',
  data() {
    return {
      products: [],
      keyword: ''
    }
  },
  created() {
    this.loadProducts()
  },
  methods: {
    async loadProducts() {
      try {
        const res = await getAllProducts({ keyword: this.keyword })
        this.products = res.data.products || []
      } catch (e) {
        console.error(e)
      }
    }
  }
}
</script>

<style scoped>
.admin-products h3 {
  margin: 0 0 16px 0;
  color: #333;
}
.filter-bar {
  background: white;
  border-radius: 8px;
  padding: 8px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.product-list {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
</style>
