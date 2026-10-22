import axios from 'axios'
import { handleTerminal401 } from '@/utils/auth-interceptor'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

/**
 * 需要登录态的 C 端接口统一包一层 401 处理。
 *
 * 之前这个文件完全没有 401 拦截：终端用户 token 过期后，
 * 「我的工单」页面所有请求都 401，页面一片空白 + 「加载失败」，
 * 不会出现「请重新登录」—— 用户感知就是「点了没反应」。
 *
 * 只对明确需要登录的接口生效；下面的 /work-orders 兼容路径保持原样。
 */
function withAuthGuard(promise) {
  return promise.catch((err) => {
    if (err && err.response && err.response.status === 401) {
      handleTerminal401()
    }
    return Promise.reject(err)
  })
}

// ====== 客户/C端：我报修的工单 ======
export function getMyOrders(status, headers) {
  const params = {}
  if (status) params.status = status
  return withAuthGuard(api.get('/customer/orders', { params, headers: headers || {} }))
}

export function getMyOrderDetail(orderId, headers) {
  return withAuthGuard(api.get('/customer/orders/' + orderId, { headers: headers || {} }))
}

export function cancelMyOrder(orderId, headers) {
  return withAuthGuard(api.post('/customer/orders/' + orderId + '/cancel', {}, { headers: headers || {} }))
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
