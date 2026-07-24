import wx from 'weixin-js-sdk'

export function initWxConfig(config) {
  wx.config({
    debug: false,
    appId: config.appId,
    timestamp: config.timestamp,
    nonceStr: config.nonceStr,
    signature: config.signature,
    jsApiList: ['scanQRCode', 'getLocation']
  })
}

// 探测是否在微信浏览器：true 表示可以扫，false 表示要降级
export function isWechatReady() {
  return typeof wx !== 'undefined' && typeof wx.scanQRCode === 'function'
}

export function scanQRCode() {
  // 微信环境未就绪时，wx.scanQRCode 永远不会回调 → 必须超时兜底
  return new Promise((resolve, reject) => {
    if (!isWechatReady()) {
      reject(new Error('当前浏览器不支持扫码（仅微信内置浏览器可用），请用下方手动输入'))
      return
    }
    const timeoutId = setTimeout(() => {
      reject(new Error('扫码超时，请在 8 秒内对准二维码'))
    }, 8000)
    const cleanup = () => clearTimeout(timeoutId)
    wx.scanQRCode({
      needResult: 1,
      scanType: ['qrCode', 'barCode'],
      success: (res) => { cleanup(); resolve(res.resultStr) },
      fail: (err) => { cleanup(); reject(new Error(err.errMsg || '扫码失败')) },
      cancel: () => { cleanup(); reject(new Error('已取消扫码')) }
    })
  })
}

export function getWxConfig(url) {
  return fetch(`/api/wechat/config?url=${encodeURIComponent(url)}`)
    .then(res => res.json())
}