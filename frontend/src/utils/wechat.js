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
  return new Promise((resolve, reject) => {
    wx.scanQRCode({
      needResult: 1,
      scanType: ['qrCode', 'barCode'],
      success: (res) => {
        resolve(res.resultStr)
      },
      error: (err) => {
        reject(err)
      }
    })
  })
}

export function getWxConfig(url) {
  return fetch(`/api/wechat/config?url=${encodeURIComponent(url)}`)
    .then(res => res.json())
}