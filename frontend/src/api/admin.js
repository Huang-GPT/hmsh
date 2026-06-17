import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

export function adminLogin(openid) {
  return api.post('/auth/admin/login', { openid })
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
  return api.put(`/admin/orders/${orderId}/status`, { status, remark, operator_id: 1 })
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
