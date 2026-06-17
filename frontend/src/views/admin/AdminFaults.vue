<template>
  <div class="admin-faults">
    <h3>故障库管理</h3>

    <div class="filter-bar">
      <van-search v-model="keyword" placeholder="搜索故障类型/描述" @search="loadFaults" shape="round" />
      <van-button type="primary" size="small" @click="showAddDialog">添加故障</van-button>
    </div>

    <van-cell-group class="fault-list">
      <van-cell
        v-for="fault in faults"
        :key="fault.id"
        :title="fault.fault_type"
        :label="fault.product_model + ' | ' + fault.fault_desc.substring(0, 30) + '...'"
        is-link
        @click="showEdit(fault)"
      >
        <template #right-icon>
          <van-button size="mini" type="danger" plain @click.stop="handleDelete(fault)">删除</van-button>
        </template>
      </van-cell>
    </van-cell-group>

    <van-empty v-if="faults.length === 0" description="暂无故障数据" />

    <!-- 添加故障弹窗 -->
    <van-dialog v-model="showAdd" title="添加故障" show-cancel-button @confirm="handleAdd">
      <van-field v-model="addForm.product_model" label="产品型号" placeholder="如: HM-001" />
      <van-field v-model="addForm.fault_type" label="故障类型" placeholder="如: 无法启动" />
      <van-field v-model="addForm.fault_desc" label="故障描述" type="textarea" placeholder="详细描述故障现象" rows="2" />
      <van-field v-model="addForm.solution" label="解决方案" type="textarea" placeholder="解决方案" rows="3" />
    </van-dialog>

    <!-- 编辑故障弹窗 -->
    <van-dialog v-model="showEditDialog" title="编辑故障" show-cancel-button @confirm="handleUpdate">
      <van-field v-model="editForm.fault_type" label="故障类型" />
      <van-field v-model="editForm.fault_desc" label="故障描述" type="textarea" rows="2" />
      <van-field v-model="editForm.solution" label="解决方案" type="textarea" rows="3" />
    </van-dialog>
  </div>
</template>

<script>
import { getAllFaults, createFault, updateFault, deleteFault } from '@/api/admin'

export default {
  name: 'AdminFaults',
  data() {
    return {
      faults: [],
      keyword: '',
      showAdd: false,
      showEditDialog: false,
      addForm: {
        product_model: '',
        fault_type: '',
        fault_desc: '',
        solution: ''
      },
      editForm: {}
    }
  },
  created() {
    this.loadFaults()
  },
  methods: {
    async loadFaults() {
      try {
        const res = await getAllFaults({ keyword: this.keyword })
        this.faults = res.data.faults || []
      } catch (e) {
        console.error(e)
      }
    },
    showAddDialog() {
      this.addForm = { product_model: '', fault_type: '', fault_desc: '', solution: '' }
      this.showAdd = true
    },
    async handleAdd() {
      if (!this.addForm.product_model || !this.addForm.fault_type || !this.addForm.fault_desc || !this.addForm.solution) {
        this.$toast('请填写完整信息')
        return
      }
      try {
        await createFault(this.addForm)
        this.$toast.success('添加成功')
        this.showAdd = false
        this.loadFaults()
      } catch (e) {
        this.$toast('添加失败')
      }
    },
    showEdit(fault) {
      this.editForm = { ...fault }
      this.showEditDialog = true
    },
    async handleUpdate() {
      try {
        await updateFault(this.editForm.id, {
          fault_type: this.editForm.fault_type,
          fault_desc: this.editForm.fault_desc,
          solution: this.editForm.solution
        })
        this.$toast.success('更新成功')
        this.showEditDialog = false
        this.loadFaults()
      } catch (e) {
        this.$toast('更新失败')
      }
    },
    handleDelete(fault) {
      this.$dialog.confirm({
        title: '确认删除',
        message: `确定要删除故障「${fault.fault_type}」吗？`
      }).then(async () => {
        try {
          await deleteFault(fault.id)
          this.$toast.success('删除成功')
          this.loadFaults()
        } catch (e) {
          this.$toast('删除失败')
        }
      }).catch(() => {})
    }
  }
}
</script>

<style scoped>
.admin-faults h3 {
  margin: 0 0 16px 0;
  color: #333;
}
.filter-bar {
  background: white;
  border-radius: 8px;
  padding: 8px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  display: flex;
  gap: 8px;
  align-items: center;
}
.filter-bar .van-search {
  flex: 1;
}
.fault-list {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
</style>
