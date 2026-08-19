import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// ====== 客户/C端：我报修的工单 ======
export function getMyOrders(status, headers) {
  const params = {}
  if (status) params.status = status
  return api.get('/customer/orders', { params, headers: headers || {} })
}

export function getMyOrderDetail(orderId, headers) {
  return api.get('/customer/orders/' + orderId, { headers: headers || {} })
}

export function cancelMyOrder(orderId, headers) {
  return api.post('/customer/orders/' + orderId + '/cancel', {}, { headers: headers || {} })
}

// ====== 兼容旧路径（前端别处可能还在用） ======
export function createWorkOrder(data) {
  return api.post('/work-orders', data)
}

export function getUserOrders(userId, status) {
  return api.get('/work-orders', {
    params: { user_id: userId, status }
  })
}

export function getOrderDetail(orderId) {
  return api.get('/work-orders/' + orderId)
}

export function updateOrderStatus(orderId, status, operatorId, remark) {
  return api.put('/work-orders/' + orderId + '/status', {
    status,
    operator_id: operatorId,
    remark
  })
}

export function assignOrder(orderId, handlerId) {
  return api.post('/work-orders/' + orderId + '/assign', {
    handler_id: handlerId
  })
}
