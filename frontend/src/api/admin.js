import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  // 默认 10s 太短：上传 30MB 文件需要更多时间。
  // 大文件上传走专门的 uploadClient（timeout=180s）。
  timeout: 30000
})

// 大文件上传专用 client（30MB PDF/文档需要充足时间）
const uploadApi = axios.create({
  baseURL: '/api',
  timeout: 180000  // 3 分钟
})

// 复用 admin 的 token 拦截器（保证上传接口也带 token）
uploadApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token')
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ---- 拦截器：自动带 token + 把后端返回的 Authorization header 落 localStorage ----
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token')
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use((response) => {
  // 后端在登录响应里会把 Authorization: Bearer xxx 放在 header，前端抓出来
  const auth = response.headers && (response.headers.authorization || response.headers.Authorization)
  if (auth && /^Bearer\s+/.test(auth)) {
    const token = auth.replace(/^Bearer\s+/, '').trim()
    if (token) {
      localStorage.setItem('admin_token', token)
    }
  }
  return response
})

export function adminLogin(account, password) {
  return api.post('/auth/admin/login', { account, password })
}

export function getStatistics() {
  return api.get('/admin/statistics')
}

export function getStatisticsByStatus() {
  return api.get('/admin/statistics/by-status')
}

export function getAllOrders(params) {
  return api.get('/admin/orders', { params })
}

export function assignOrder(orderId, handlerId) {
  return api.post(`/admin/orders/${orderId}/assign`, { handler_id: handlerId })
}

// === 工单备注意见 ===
export function addOrderNote(orderId, remark) {
  return api.post(`/admin/orders/${orderId}/note`, { remark })
}

export function updateOrderStatus(orderId, status, remark) {
  return api.put(`/admin/orders/${orderId}/status`, { status, remark })
}

export function startProcessingOrder(orderId, remark) {
  return api.post(`/admin/orders/${orderId}/start-processing`, { remark })
}

export function completeOrder(orderId, remark) {
  return api.post(`/admin/orders/${orderId}/complete`, { remark })
}

export function rejectOrder(orderId, reason) {
  return api.post(`/admin/orders/${orderId}/reject`, { reason })
}

export function getReopenOptions(orderId) {
  return api.get(`/admin/orders/${orderId}/reopen-options`)
}

export function reopenClosedOrder(orderId, targetStatus, reason) {
  return api.post(`/admin/orders/${orderId}/reopen`, {
    target_status: targetStatus,
    reason,
  })
}

export function getAllUsers(params) {
  return api.get('/admin/users', { params })
}

export function createUser(data) {
  return api.post('/admin/users', data)
}

export function updateUserRole(userId, role) {
  return api.put(`/admin/users/${userId}/role`, { role })
}

// === 用户管理增强 ===
export function updateUser(userId, data) {
  return api.put(`/admin/users/${userId}`, data)
}


// === 用户删除 ===
export function deleteUser(userId) {
  return api.delete(`/admin/users/${userId}`)
}
// === 用户启停 ===
export function toggleUserStatus(userId) {
  return api.put(`/admin/users/${userId}/status`)
}


// === RBAC：权限 + 角色 ===
export function listPermissions() {
  return api.get('/admin/permissions')
}

export function listRoles() {
  return api.get('/admin/roles')
}

export function getRole(roleId) {
  return api.get(`/admin/roles/${roleId}`)
}

export function createRole(data) {
  return api.post('/admin/roles', data)
}

export function updateRole(roleId, data) {
  return api.put(`/admin/roles/${roleId}`, data)
}

export function deleteRole(roleId) {
  return api.delete(`/admin/roles/${roleId}`)
}

// === 用户-角色分配 ===
export function getUserRoles(userId) {
  return api.get(`/admin/users/${userId}/roles`)
}

export function setUserRoles(userId, roleIds) {
  return api.put(`/admin/users/${userId}/roles`, { role_ids: roleIds })
}


export function getAllProducts(params) {
  return api.get('/admin/products', { params })
}

export function createProduct(data) {
  return api.post('/admin/products', data)
}

export function deleteProduct(id) {
  return api.delete(`/admin/products/${id}`)
}

export function updateProduct(id, data) {
  return api.put(`/admin/products/${id}`, data)
}

export function getProductBindings(productId) {
  return api.get(`/admin/products/${productId}/bindings`)
}

export function adminUnbind(bindingId) {
  return api.delete(`/admin/bindings/${bindingId}`)
}

export function getAllBindings(params) {
  return api.get('/admin/bindings', { params })
}

// 导入 CSV multipart/form-data
export function importProducts(file, onProgress) {
  const form = new FormData()
  form.append('file', file)
  return api.post('/admin/products/import', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress,
  })
}

export function getAllFaultCategories(params) {
  return api.get('/admin/fault-categories', { params })
}

export function createFaultCategory(data) {
  return api.post('/admin/fault-categories', data)
}

export function updateFaultCategory(catId, data) {
  return api.put(`/admin/fault-categories/${catId}`, data)
}

export function deleteFaultCategory(catId) {
  return api.delete(`/admin/fault-categories/${catId}`)
}

export function getAllFaults(params) {
  return api.get('/admin/faults', { params })
}

export function createFault(data) {
  return api.post('/admin/faults', data)
}

export function updateFault(faultId, data) {
  return api.put(`/admin/faults/${faultId}`, data)
}

export function deleteFault(faultId) {
  return api.delete(`/admin/faults/${faultId}`)
}

// ========== 故障附件 CRUD（事务化上传 + 软删） ==========

export function getFaultAttachments(faultId, includeDeleted = false) {
  return api.get(`/admin/faults/${faultId}/attachments`, {
    params: { include_deleted: includeDeleted ? 'true' : 'false' },
  })
}

export function uploadFaultAttachment(faultId, file, onProgress) {
  const form = new FormData()
  form.append('file', file)
  return api.post(`/admin/faults/${faultId}/attachments`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress,
  })
}

export function deleteFaultAttachment(faultId, attachmentId) {
  return api.delete(`/admin/faults/${faultId}/attachments/${attachmentId}`)
}

// ========== 故障文件库 v2（2026-09 重构：平铺 PDF/图片/文档） ==========

/**
 * 列出故障文件
 * @param {Object} params { kind?: 'pdf'|'image'|'doc', keyword?: string, include_deleted?: boolean }
 */
export function getFaultFiles(params = {}) {
  const p = {}
  if (params.kind) p.kind = params.kind
  if (params.keyword) p.keyword = params.keyword
  if (params.include_deleted) p.include_deleted = '1'
  return api.get('/admin/fault-files', { params: p })
}

/**
 * 上传故障文件（multipart/form-data）
 * @param {File} file
 * @param {string} [description]
 * @param {function} [onProgress] 上传进度回调
 */
export function uploadFaultFile(file, description = '', onProgress = null) {
  const form = new FormData()
  form.append('file', file)
  if (description) form.append('description', description)
  // 用大文件专用 client（180s timeout）覆盖默认 api 的 30s
  return uploadApi.post('/admin/fault-files', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress,
  })
}

/**
 * 删除故障文件（软删）
 */
export function deleteFaultFile(id) {
  return api.delete(`/admin/fault-files/${id}`)
}

/**
 * 更新文件描述 / 排序 / 状态
 */
export function updateFaultFile(id, data) {
  return api.patch(`/admin/fault-files/${id}`, data)
}

export function getServiceStaff() {
  return api.get('/admin/service-staff')
}

export function getOrderDetail(orderId) {
  return api.get(`/admin/orders/${orderId}`)
}

export function getServicePoints(params) {
  return api.get('/admin/service-points', { params })
}

export function getEngineers(params) {
  return api.get('/admin/engineers', { params })
}

export function acceptOrderApi(orderId, contactPhone) {
  return api.post(`/admin/orders/${orderId}/accept`, { contact_phone: contactPhone || '' })
}

export function dispatchOrder(orderId, servicePointId, remark) {
  return api.post(`/admin/orders/${orderId}/dispatch`, {
    service_point_id: servicePointId,
    remark: remark || '',
  })
}

export function assignEngineer(orderId, engineerId, remark) {
  return api.post(`/admin/orders/${orderId}/assign-engineer`, {
    engineer_id: engineerId,
    remark: remark || '',
  })
}

export function confirmCompletedApi(orderId, remark) {
  return api.post(`/admin/orders/${orderId}/confirm`, { remark: remark || '' })
}


export function getServicePointOrders() {
  return api.get('/admin/orders/service-point')
}

export function assignEngineerByText(orderId, engineerName, engineerPhone) {
  return api.post('/admin/orders/assign-engineer-text', {
    engineer_name: engineerName,
    engineer_phone: engineerPhone
  })
}

export function updateRolePermissions(role, permissions) {
  return api.put('/admin/role-permissions/', { permissions })
}

export function updateUserPermissions(userId, permissions) {
  return api.put('/admin/users/permissions', { permissions })
}


export function acceptOrderByText(orderId, engineerName, engineerPhone) {
  // 经销商接单：一步完成（填工程师 + dispatched → processing）
  return api.post(`/dealer/orders/${orderId}/accept`, {
    engineer_name: engineerName,
    engineer_phone: engineerPhone,
  })
}


export function getAllDealerOrders(params) {
  // 总部视角：查看所有经销商的工单售后
  return api.get('/admin/dealer-orders', { params })
}


// === 服务点维护（admin） ===
export function listAllServicePoints() {
  return api.get('/admin/service-points/all')
}

export function createServicePoint(data) {
  return api.post('/admin/service-points', data)
}

export function updateServicePoint(spId, data) {
  return api.put(`/admin/service-points/${spId}`, data)
}

export function softDeleteServicePoint(spId) {
  return api.delete(`/admin/service-points/${spId}`)
}

export function restoreServicePoint(spId) {
  return api.post(`/admin/service-points/${spId}/restore`)
}

export function hardDeleteServicePoint(spId) {
  return api.delete(`/admin/service-points/${spId}/hard-delete`)
}

export function importServicePoints(file) {
  const fd = new FormData()
  fd.append('file', file)
  return api.post('/admin/service-points/import', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function exportServicePointsUrl() {
  return '/api/admin/service-points/export'
}
