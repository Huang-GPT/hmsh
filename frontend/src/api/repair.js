import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

const TOKEN_KEY = 'hongmen_terminal_token'

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 401 拦截：token 失效 → 跳登录
let _redirecting = false
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err && err.response && err.response.status
    if (status === 401 && !_redirecting) {
      _redirecting = true
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem('hongmen_terminal_user')
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        const redirect = encodeURIComponent(window.location.pathname + window.location.search)
        window.location.replace('/login?redirect=' + redirect)
      }
      setTimeout(() => { _redirecting = false }, 1000)
    }
    return Promise.reject(err)
  }
)

// ========== 故障分类（手机端） ==========
export function getFaultCategories() {
  return api.get('/customer/fault-categories')
}

export function getFaultsByCategory(categoryId, productModel) {
  return api.get('/customer/faults', {
    params: { category_id: categoryId, product_model: productModel },
  })
}

// ========== 提交报修 ==========
export function createOrder(data) {
  return api.post('/customer/orders', data)
}

// ========== 图片上传（视频已禁用） ==========
export function uploadMedia(formData) {
  return api.post('/upload/media', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 30000,
  })
}