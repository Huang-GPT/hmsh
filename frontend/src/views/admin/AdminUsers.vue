<template>
  <div class="admin-users">
    <h3>用户管理</h3>

    <div class="filter-bar">
      <van-search v-model="keyword" placeholder="搜索用户" shape="round" />
      <van-dropdown-menu>
        <van-dropdown-item v-model="roleFilter" :options="roleOptions" @change="loadUsers" />
      </van-dropdown-menu>
    </div>

    <van-cell-group class="user-list">
      <van-cell
        v-for="user in filteredUsers"
        :key="user.id"
        :title="user.nickname"
        :label="'ID: ' + user.id + ' | ' + user.openid"
        :value="roleMap[user.role]"
        is-link
        @click="showEdit(user)"
      >
        <template #right-icon>
          <van-tag :type="user.role === 'admin' ? 'danger' : user.role === 'service' ? 'primary' : 'success'" size="medium">
            {{ roleMap[user.role] }}
          </van-tag>
        </template>
      </van-cell>
    </van-cell-group>

    <van-empty v-if="filteredUsers.length === 0" description="暂无用户" />

    <van-dialog v-model="showEditDialog" title="编辑用户" show-cancel-button @confirm="handleUpdate">
      <van-field v-model="editForm.nickname" label="昵称" />
      <van-field v-model="editForm.phone" label="手机号" />
      <van-picker
        :columns="rolePickerOptions"
        @confirm="onRolePick"
        :default-index="currentRoleIndex"
        visible-item-num="3"
      />
    </van-dialog>
  </div>
</template>

<script>
import { getAllUsers, updateUserRole } from '@/api/admin'

export default {
  name: 'AdminUsers',
  data() {
    return {
      users: [],
      keyword: '',
      roleFilter: '',
      showEditDialog: false,
      editForm: {},
      currentRoleIndex: 0,
      roleMap: {
        'customer': '客户',
        'service': '客服',
        'admin': '管理员'
      },
      roleOptions: [
        { text: '全部角色', value: '' },
        { text: '客户', value: 'customer' },
        { text: '客服', value: 'service' },
        { text: '管理员', value: 'admin' }
      ],
      rolePickerOptions: [
        { text: '客户', value: 'customer' },
        { text: '客服', value: 'service' },
        { text: '管理员', value: 'admin' }
      ]
    }
  },
  computed: {
    filteredUsers() {
      let list = this.users
      if (this.roleFilter) {
        list = list.filter(u => u.role === this.roleFilter)
      }
      if (this.keyword) {
        const kw = this.keyword.toLowerCase()
        list = list.filter(u =>
          (u.nickname && u.nickname.toLowerCase().includes(kw)) ||
          (u.openid && u.openid.toLowerCase().includes(kw))
        )
      }
      return list
    }
  },
  created() {
    this.loadUsers()
  },
  methods: {
    async loadUsers() {
      try {
        const res = await getAllUsers()
        this.users = res.data.users || []
      } catch (e) {
        console.error(e)
      }
    },
    showEdit(user) {
      this.editForm = { ...user }
      const roleIndex = this.rolePickerOptions.findIndex(r => r.value === user.role)
      this.currentRoleIndex = roleIndex >= 0 ? roleIndex : 0
      this.showEditDialog = true
    },
    onRolePick(val) {
      this.editForm.role = val.value
    },
    async handleUpdate() {
      try {
        await updateUserRole(this.editForm.id, this.editForm.role)
        this.$toast.success('更新成功')
        this.showEditDialog = false
        this.loadUsers()
      } catch (e) {
        this.$toast('操作失败')
      }
    }
  }
}
</script>

<style scoped>
.admin-users h3 {
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
.user-list {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
</style>
