import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

export function bindProduct(data) {
  return api.post('/products/bind', data)
}

export function getUserProducts(userId) {
  return api.get('/products', {
    params: { user_id: userId }
  })
}

export function unbindProduct(userId, productId) {
  return api.post('/products/unbind', {
    user_id: userId,
    product_id: productId
  })
}