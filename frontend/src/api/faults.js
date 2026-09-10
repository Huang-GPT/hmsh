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