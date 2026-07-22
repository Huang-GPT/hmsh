import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000
})

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