<template>
  <div class="common-faults">
    <h1>常见故障</h1>
    
    <van-search
      v-model="keyword"
      placeholder="搜索故障"
      @search="onSearch"
    />
    
    <van-tabs v-model="activeModel" @change="onModelChange">
      <van-tab title="HM-001" name="HM-001" />
      <van-tab title="HM-002" name="HM-002" />
      <van-tab title="HM-003" name="HM-003" />
    </van-tabs>
    
    <van-list>
      <van-cell-group>
        <van-cell
          v-for="fault in faults"
          :key="fault.id"
          :title="fault.fault_type"
          :label="fault.fault_desc"
          is-link
          @click="viewDetail(fault.id)"
        />
      </van-cell-group>
    </van-list>
    
    <van-empty v-if="faults.length === 0" description="暂无相关故障" />
    
    <van-popup v-model="showDetail" position="bottom" :style="{ height: '70%' }">
      <div class="fault-detail" v-if="currentFault">
        <h2>{{ currentFault.fault_type }}</h2>
        <h3>故障现象</h3>
        <p>{{ currentFault.fault_desc }}</p>
        <h3>解决方案</h3>
        <p>{{ currentFault.solution }}</p>
        
        <div class="feedback">
          <van-button type="primary" size="small" @click="markHelpful">
            有帮助 ({{ currentFault.helpful_count }})
          </van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script>
import { getFaults, getFaultDetail, markHelpful } from '@/api/faults'

export default {
  name: 'CommonFaults',
  data() {
    return {
      keyword: '',
      activeModel: 'HM-001',
      faults: [],
      showDetail: false,
      currentFault: null
    }
  },
  created() {
    this.loadFaults()
  },
  methods: {
    onSearch() {
      this.loadFaults()
    },
    onModelChange(model) {
      this.activeModel = model
      this.loadFaults()
    },
    async loadFaults() {
      try {
        const res = await getFaults(this.activeModel, this.keyword)
        this.faults = res.data.faults
      } catch (error) {
        console.error('加载故障列表失败', error)
      }
    },
    async viewDetail(faultId) {
      try {
        const res = await getFaultDetail(faultId)
        this.currentFault = res.data.fault
        this.showDetail = true
      } catch (error) {
        this.$toast.fail('加载详情失败')
      }
    },
    async markHelpful() {
      try {
        const res = await markHelpful(this.currentFault.id)
        this.currentFault = res.data.fault
        this.$toast.success('感谢反馈')
      } catch (error) {
        this.$toast.fail('操作失败')
      }
    }
  }
}
</script>

<style scoped>
.common-faults {
  padding: 16px;
}
.fault-detail {
  padding: 16px;
}
.fault-detail h2 {
  margin-bottom: 16px;
}
.fault-detail h3 {
  margin-top: 16px;
  margin-bottom: 8px;
  color: #666;
}
.feedback {
  margin-top: 24px;
  text-align: center;
}
</style>