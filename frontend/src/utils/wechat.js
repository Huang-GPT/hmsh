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

export function scanQRCode() {
  // 微信环境未就绪时，wx.scanQRCode 永远不会回调 → 必须超时兜底
  return new Promise((resolve, reject) => {
    const timeoutId = setTimeout(() => {
      reject(new Error('扫码超时或当前浏览器不支持微信JS-SDK，请直接用下方输入框手动绑定'))
    }, 8000)
    const cleanup = () => clearTimeout(timeoutId)
    if (typeof wx === 'undefined' || !wx.scanQRCode) {
      cleanup()
      reject(new Error('微信 JS-SDK 未加载，请用下方手动输入绑定'))
      return
    }
    wx.scanQRCode({
      needResult: 1,
      scanType: ['qrCode', 'barCode'],
      success: (res) => { cleanup(); resolve(res.resultStr) },
      error: (err) => { cleanup(); reject(err) },
      cancel: () => { cleanup(); reject(new Error('已取消扫码')) }
    })
  })
}

export function getWxConfig(url) {
  return fetch(`/api/wechat/config?url=${encodeURIComponent(url)}`)
    .then(res => res.json())
}