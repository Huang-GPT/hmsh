/**
 * 权限工具
 *
 * 当前用户拥有的 permission code 列表来自登录时由后端 generate_token() 聚合的 permissions，
 * 通过 User.to_dict() 返回前端，写入 localStorage.admin_user.permissions。
 *
 * 路由守卫（router/index.js）和菜单过滤（AdminLayout.vue）都依赖同一份缓存；
 * 角色变更后旧 token 里的 permissions 仍然生效到 JWT 失效，请用户在变更后重新登录以刷新。
 */

// 缓存当前用户，避免每次重复解析 localStorage
let _cachedUser = null
let _cachedRaw = null

function _loadUser() {
  try {
    const raw = localStorage.getItem('admin_user')
    if (raw === _cachedRaw) return _cachedUser
    _cachedRaw = raw
    _cachedUser = raw ? JSON.parse(raw) : null
    return _cachedUser
  } catch (e) {
    _cachedUser = null
    return null
  }
}

// 让 storage 事件 / 主动登录登出后能强制刷新缓存
export function refreshPermissionCache() {
  _cachedRaw = null
  _cachedUser = null
}

/** 是否有某个 permission code */
export function hasPermission(code) {
  const user = _loadUser()
  if (!user) return false
  // admin 角色直接全通（防御：万一 admin 没绑全权限）
  if (user.role === 'admin') return true
  if (!Array.isArray(user.permissions)) return false
  return user.permissions.includes(code)
}

/** 是否至少拥有 codes 中的一个（OR 语义） */
export function hasAnyPermission(codes) {
  if (!Array.isArray(codes) || codes.length === 0) return false
  return codes.some(hasPermission)
}

/** 是否拥有 codes 中的全部（AND 语义） */
export function hasAllPermissions(codes) {
  if (!Array.isArray(codes) || codes.length === 0) return false
  return codes.every(hasPermission)
}