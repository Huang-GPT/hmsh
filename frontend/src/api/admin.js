import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
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

export function getAllUsers(params) {
  return api.get('/admin/users', { params })
}

export function createUser(data) {
  return api.post('/admin/users', data)
}

export function updateUserRole(userId, role) {
  return api.put(`/admin/users/${userId}/role`, { role })
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

export function getAllFaults(params) {
  return api.get('/admin/faults', { params })
}

export function createFault(data) {
  return api.post('/faults', data)
}

export function updateFault(faultId, data) {
  return api.put(`/admin/faults/${faultId}`, data)
}

export function deleteFault(faultId) {
  return api.delete(`/admin/faults/${faultId}`)
}

export function getServiceStaff() {
  return api.get('/admin/service-staff')
}

export function getOrderDetail(orderId) {
  return api.get(`/work-orders/${orderId}`)
}
