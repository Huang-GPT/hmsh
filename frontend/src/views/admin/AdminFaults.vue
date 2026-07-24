<template>
  <div class="admin-faults">
    <h3>故障库管理</h3>

    <!-- Tabs -->
    <van-tabs v-model:active="tab" sticky offset-top="0" @click-tab="onTabChange">
      <van-tab title="故障分类" name="categories">
        <div class="toolbar">
          <van-search
            v-model="catKeyword"
            placeholder="搜索分类名"
            @search="loadCategories"
            shape="round"
          />
          <van-button type="primary" size="small" icon="plus" @click="openCatCreate">新建分类</van-button>
        </div>

        <div v-if="categories.length === 0" class="empty-tip">
          <van-empty description="暂无故障分类" />
        </div>
        <van-cell-group v-else class="cat-list">
          <van-cell
            v-for="cat in categories"
            :key="cat.id"
            :title="cat.name"
            :label="`${cat.fault_count || 0} 个常见故障 · 排序 ${cat.sort_order || 0}`"
          >
            <template #icon>
              <span class="cat-icon">{{ cat.icon || '🔧' }}</span>
            </template>
            <template #right-icon>
              <van-tag v-if="cat.status === 'disabled'" type="danger" size="mini" class="mr-1">已停用</van-tag>
              <van-button size="mini" plain class="mr-1" @click="openCatEdit(cat)">编辑</van-button>
              <van-button size="mini" type="danger" plain @click="confirmCatDelete(cat)">停用</van-button>
            </template>
          </van-cell>
        </van-cell-group>
      </van-tab>

      <van-tab title="故障条目" name="faults">
        <div class="toolbar">
          <van-search
            v-model="faultKeyword"
            placeholder="搜索标题/内容"
            @search="loadFaults"
            shape="round"
          />
          <van-button type="primary" size="small" icon="plus" @click="openFaultCreate">新建故障</van-button>
        </div>

        <van-cell-group class="fault-list">
          <van-cell
            v-for="f in faults"
            :key="f.id"
            :title="f.title"
            :label="`${f.category_name || '未分类'} · 适用型号 ${f.product_model || '通用'} · 排序 ${f.sort_order || 0}`"
            is-link
            @click="openFaultEdit(f)"
          >
            <template #right-icon>
              <van-tag v-if="f.status === 'disabled'" type="danger" size="mini" class="mr-1">已停用</van-tag>
              <van-button size="mini" type="danger" plain @click.stop="confirmFaultDelete(f)">停用</van-button>
            </template>
          </van-cell>
        </van-cell-group>
        <van-empty v-if="faults.length === 0" description="暂无故障条目" />
      </van-tab>
    </van-tabs>

    <!-- ============ 分类编辑弹窗 ============ -->
    <van-dialog
      v-model:show="showCatDialog"
      :title="editingCat ? '编辑故障分类' : '新建故障分类'"
      show-cancel-button
      @confirm="saveCat"
    >
      <div class="dialog-body">
        <van-field v-model="catForm.name" label="分类名称" placeholder="如: 电源故障" required maxlength="30" />
        <van-field v-model="catForm.icon" label="图标(Emoji)" placeholder="如: 🔌" maxlength="4" />
        <van-cell title="排序">
          <template #value>
            <input type="number" v-model.number="catForm.sort_order" class="num-input" min="0" />
          </template>
        </van-cell>
        <van-cell title="状态">
          <template #value>
            <van-switch v-model="catActive" />
            <span class="ml-1">{{ catActive ? '启用' : '停用' }}</span>
          </template>
        </van-cell>
      </div>
    </van-dialog>

    <!-- ============ 故障条目编辑弹窗 ============ -->
    <van-dialog
      v-model:show="showFaultDialog"
      :title="editingFault ? '编辑故障条目' : '新建故障条目'"
      show-cancel-button
      @confirm="saveFault"
    >
      <div class="dialog-body">
        <van-cell title="所属分类" :is-link="false">
          <template #value>
            <select v-model="faultForm.category_id" class="select-input">
              <option :value="null">请选择</option>
              <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </template>
        </van-cell>
        <van-field v-model="faultForm.title" label="标题" placeholder="如: 无法开机" required maxlength="60" />
        <van-field v-model="faultForm.product_model" label="适用型号" placeholder="如: HM-001（留空表示通用）" maxlength="40" />
        <van-field v-model="faultForm.content" label="详细内容" type="textarea" placeholder="故障描述、原因、解决方案…" rows="4" maxlength="1000" />
        <van-cell title="排序">
          <template #value>
            <input type="number" v-model.number="faultForm.sort_order" class="num-input" min="0" />
          </template>
        </van-cell>
        <van-cell title="状态">
          <template #value>
            <van-switch v-model="faultActive" />
            <span class="ml-1">{{ faultActive ? '启用' : '停用' }}</span>
          </template>
        </van-cell>
      </div>
    </van-dialog>
  </div>
</template>

<script>
import {
  getAllFaultCategories, createFaultCategory, updateFaultCategory, deleteFaultCategory,
  getAllFaults, createFault, updateFault, deleteFault,
} from '@/api/admin'

const emptyCatForm = () => ({
  name: '',
  icon: '',
  sort_order: 0,
  status: 'active',
})

const emptyFaultForm = () => ({
  category_id: null,
  title: '',
  content: '',
  product_model: '',
  sort_order: 0,
  status: 'active',
})

export default {
  name: 'AdminFaults',
  data() {
    return {
      tab: 'categories',

      // 分类
      catKeyword: '',
      categories: [],
      showCatDialog: false,
      editingCat: null,
      catForm: emptyCatForm(),
      catActive: true,

      // 故障条目
      faultKeyword: '',
      faults: [],
      showFaultDialog: false,
      editingFault: null,
      faultForm: emptyFaultForm(),
      faultActive: true,
    }
  },
  created() {
    this.loadCategories()
    this.loadFaults()
  },
  methods: {
    onTabChange() {
      if (this.tab === 'categories') this.loadCategories()
      else this.loadFaults()
    },

    // ===== 分类 =====
    async loadCategories() {
      try {
        const res = await getAllFaultCategories({ keyword: this.catKeyword })
        this.categories = (res.data && res.data.categories) || []
      } catch (e) {
        console.error(e)
      }
    },
    openCatCreate() {
      this.editingCat = null
      this.catForm = emptyCatForm()
      this.catActive = true
      this.showCatDialog = true
    },
    openCatEdit(cat) {
      this.editingCat = cat
      this.catForm = { ...cat }
      this.catActive = cat.status !== 'disabled'
      this.showCatDialog = true
    },
    async saveCat() {
      if (!this.catForm.name || !this.catForm.name.trim()) {
        this.$toast('请填写分类名称')
        return false
      }
      this.catForm.status = this.catActive ? 'active' : 'disabled'
      try {
        if (this.editingCat) {
          await updateFaultCategory(this.editingCat.id, this.catForm)
          this.$toast.success('更新成功')
        } else {
          await createFaultCategory(this.catForm)
          this.$toast.success('创建成功')
        }
        this.showCatDialog = false
        this.loadCategories()
      } catch (e) {
        const msg = (e && e.response && e.response.data && e.response.data.error) || '操作失败'
        this.$toast(msg)
        return false
      }
      return true
    },
    confirmCatDelete(cat) {
      this.$dialog.confirm({
        title: '停用确认',
        message: `确定停用分类「${cat.name}」吗？该分类下的故障条目不会被删除。`,
      }).then(async () => {
        try {
          await deleteFaultCategory(cat.id)
          this.$toast.success('已停用')
          this.loadCategories()
        } catch (e) {
          this.$toast('操作失败')
        }
      }).catch(() => {})
    },

    // ===== 故障条目 =====
    async loadFaults() {
      try {
        const res = await getAllFaults({ keyword: this.faultKeyword })
        this.faults = (res.data && res.data.faults) || []
      } catch (e) {
        console.error(e)
      }
    },
    openFaultCreate() {
      this.editingFault = null
      this.faultForm = emptyFaultForm()
      this.faultActive = true
      this.showFaultDialog = true
    },
    openFaultEdit(f) {
      this.editingFault = f
      this.faultForm = {
        category_id: f.category_id,
        title: f.title,
        content: f.content,
        product_model: f.product_model,
        sort_order: f.sort_order || 0,
        status: f.status,
      }
      this.faultActive = f.status !== 'disabled'
      this.showFaultDialog = true
    },
    async saveFault() {
      if (!this.faultForm.title || !this.faultForm.title.trim()) {
        this.$toast('请填写标题')
        return false
      }
      if (!this.faultForm.category_id) {
        this.$toast('请选择分类')
        return false
      }
      this.faultForm.status = this.faultActive ? 'active' : 'disabled'
      try {
        if (this.editingFault) {
          await updateFault(this.editingFault.id, this.faultForm)
          this.$toast.success('更新成功')
        } else {
          await createFault(this.faultForm)
          this.$toast.success('创建成功')
        }
        this.showFaultDialog = false
        this.loadFaults()
      } catch (e) {
        const msg = (e && e.response && e.response.data && e.response.data.error) || '操作失败'
        this.$toast(msg)
        return false
      }
      return true
    },
    confirmFaultDelete(f) {
      this.$dialog.confirm({
        title: '停用确认',
        message: `确定停用故障「${f.title}」吗？手机端将不再展示。`,
      }).then(async () => {
        try {
          await deleteFault(f.id)
          this.$toast.success('已停用')
          this.loadFaults()
        } catch (e) {
          this.$toast('操作失败')
        }
      }).catch(() => {})
    },
  },
}
</script>

<style scoped>
.admin-faults {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  min-height: calc(100vh - 88px);
}
h3 {
  margin: 0 0 16px;
  font-size: 18px;
  color: #1f2937;
}
.toolbar {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 8px 0;
}
.toolbar .van-search {
  flex: 1;
}
.empty-tip {
  padding: 40px 0;
}
.cat-list,
.fault-list {
  margin-top: 8px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.cat-icon {
  font-size: 22px;
  margin-right: 8px;
  flex-shrink: 0;
}
.mr-1 {
  margin-right: 6px;
}
.ml-1 {
  margin-left: 6px;
}
.dialog-body {
  padding: 8px 0;
  max-height: 60vh;
  overflow-y: auto;
}
.num-input,
.select-input {
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 13px;
  background: #fff;
  min-width: 80px;
}
.select-input {
  min-width: 140px;
}
</style>