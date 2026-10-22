import axios from 'axios'
import { handleTerminal401 } from '@/utils/auth-interceptor'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 401 → 清终端登录态并跳登录页（避免「点了我的工单/故障库，页面空白无提示」）
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err && err.response && err.response.status
    if (status === 401) {
      try { handleTerminal401() } catch (e) { /* ignore */ }
    }
    return Promise.reject(err)
  },
)

export function getFaults(productModel, keyword) {
  return api.get('/faults', {
    params: { product_model: productModel, keyword }
  })
}

export function getFaultDetail(faultId) {
  return api.get(`/faults/${faultId}`)
}

export function markHelpful(faultId) {
  return api.post(`/faults/${faultId}/helpful`)
}

export function getPopularFaults(limit = 10) {
  return api.get('/faults/popular', {
    params: { limit }
  })
}

export function createFault(data) {
  return api.post('/faults', data)
}

// ========== 重构 2026-09：分类→文件列表 ==========
export function getFaultCategories() {
  return api.get('/fault-categories')
}

export function getFaultsByCategory(categoryId) {
  return api.get('/faults', { params: { category_id: categoryId } })
}

// P0+P1 重构后，手机端 data source 从 fault.files 改为 fault.attachments
// 后端 CommonFault.to_dict() 默认已包含 attachments 列表，无需单独 endpoint
// 此函数保留供「按需刷新某故障的附件」场景使用
export function getFaultAttachments(faultId) {
  return api.get(`/admin/faults/${faultId}/attachments`)
}

// ========== 故障文件库 v2（2026-09 重构：移动端公开端点，无需登录） ==========

/**
 * 移动端获取公开的故障文件列表
 * @param {Object} params { kind?: 'pdf'|'image'|'doc' }
 */
export function getPublicFaultFiles(params = {}) {
  const p = {}
  if (params.kind) p.kind = params.kind
  return api.get('/fault-files', { params: p })
}