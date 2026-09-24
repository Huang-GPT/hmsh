import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

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