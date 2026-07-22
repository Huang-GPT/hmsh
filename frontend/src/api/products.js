import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000
})

const TOKEN_KEY = 'hongmen_terminal_token'
const USER_KEY = 'hongmen_terminal_user'

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export function setTerminalAuth(token, user) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user))
  else localStorage.removeItem(USER_KEY)
}

export function getTerminalUser() {
  const raw = localStorage.getItem(USER_KEY)
  return raw ? safeParse(raw) : null
}

export function clearTerminalAuth() {
  setTerminalAuth(null, null)
}

function safeParse(s) {
  try { return JSON.parse(s) } catch { return null }
}

// 销售单 + 行项目号 绑定（产品库必须存在）
export function bindBySapOrder(sapOrderNo, sapLineItem) {
  return api.post('/customer/products/scan-sap', {
    sap_order_no: sapOrderNo,
    sap_line_item: sapLineItem,
  })
}

// 序列号 绑定（产品库必须存在）
export function bindBySerialNumber(serialNumber) {
  return api.post('/customer/products/bind', {
    serial_number: serialNumber,
    bind_method: 'qrcode_product',
  })
}

export function getUserProducts() {
  return api.get('/customer/products')
}

export function unbindProduct(productId) {
  return api.post(`/customer/products/${productId}/unbind`)
}