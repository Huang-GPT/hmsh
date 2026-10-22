/**
 * 401（登录态失效）统一处理
 *
 * 背景：此前只有 products.js / repair.js 有 401 拦截器，admin.js、workOrders.js、
 *       faults.js 都没有。后果是：
 *         - 后台 token 过期（JWT 2 小时）后，路由守卫读 localStorage 里的旧 token
 *           判断「已登录」→ 放行进入页面 → 但所有 API 都返回 401
 *         - 页面表现为「点进去了但是空白的 / 一片报错」，没有任何「请重新登录」提示
 *           —— 用户感知就是「点了没反应」
 *         - 移动端「我的工单」同理
 *
 * 统一在这里处理：清登录态 + 跳登录页 + 带 redirect，登录后自动跳回。
 */

const ADMIN_TOKEN_KEY = 'admin_token'
const ADMIN_USER_KEY = 'admin_user'
const TERMINAL_TOKEN_KEY = 'hongmen_terminal_token'
const TERMINAL_USER_KEY = 'hongmen_terminal_user'

// 防止多个并发 401 触发多次跳转
let _adminRedirecting = false
let _terminalRedirecting = false

function currentPath() {
  if (typeof window === 'undefined') return '/'
  return window.location.pathname + window.location.search
}

function redirectTo(url) {
  if (typeof window === 'undefined') return
  window.location.replace(url)
}

/**
 * 后台 401：清 admin 登录态 → 跳 /admin/login
 * @param {string} [redirectPath] 登录后要跳回的路径
 */
export function handleAdmin401(redirectPath) {
  if (_adminRedirecting) return
  _adminRedirecting = true
  try {
    localStorage.removeItem(ADMIN_TOKEN_KEY)
    localStorage.removeItem(ADMIN_USER_KEY)
  } catch (e) { /* localStorage 不可用时忽略 */ }
  const target = redirectPath || currentPath()
  // 已经在登录页就别再跳
  if (typeof window !== 'undefined' && window.location.pathname !== '/admin/login') {
    redirectTo('/admin/login?redirect=' + encodeURIComponent(target))
  }
  setTimeout(() => { _adminRedirecting = false }, 1000)
}

/**
 * 终端（移动端）401：清终端登录态 → 跳 /login
 */
export function handleTerminal401(redirectPath) {
  if (_terminalRedirecting) return
  _terminalRedirecting = true
  try {
    localStorage.removeItem(TERMINAL_TOKEN_KEY)
    localStorage.removeItem(TERMINAL_USER_KEY)
  } catch (e) { /* ignore */ }
  const target = redirectPath || currentPath()
  if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
    redirectTo('/login?redirect=' + encodeURIComponent(target))
  }
  setTimeout(() => { _terminalRedirecting = false }, 1000)
}

/**
 * 生成 axios response 错误拦截器
 * @param {Function} on401  401 时调用的处理器
 */
export function makeErrorInterceptor(on401) {
  return (err) => {
    const status = err && err.response && err.response.status
    if (status === 401) {
      try { on401() } catch (e) { /* ignore */ }
    }
    return Promise.reject(err)
  }
}
