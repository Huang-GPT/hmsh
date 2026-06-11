import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

export function createWorkOrder(data) {
  return api.post('/work-orders', data)
}

export function getUserOrders(userId, status) {
  return api.get('/work-orders', {
    params: { user_id: userId, status }
  })
}

export function getOrderDetail(orderId) {
  return api.get(`/work-orders/${orderId}`)
}

export function updateOrderStatus(orderId, status, operatorId, remark) {
  return api.put(`/work-orders/${orderId}/status`, {
    status,
    operator_id: operatorId,
    remark
  })
}

export function assignOrder(orderId, handlerId) {
  return api.post(`/work-orders/${orderId}/assign`, {
    handler_id: handlerId
  })
}