import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

export function getWechatOAuthUrl(redirectUri) {
  return api.get('/auth/wechat/oauth', {
    params: { redirect_uri: redirectUri }
  })
}

export function wechatCallback(code) {
  return api.get('/auth/wechat/callback', {
    params: { code }
  })
}

export function login(openid) {
  return api.post('/auth/login', { openid })
}

export function updateUserInfo(userData) {
  return api.put('/auth/user', userData)
}