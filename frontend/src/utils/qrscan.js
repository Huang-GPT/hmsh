import { BrowserMultiFormatReader } from '@zxing/browser'

import * as zxing from '@zxing/library'
const { BarcodeFormat, DecodeHintType } = zxing

let _zxingReader = null
function getZxing() {
  if (!_zxingReader) {
    try {
      const hints = new Map()
      hints.set(DecodeHintType.POSSIBLE_FORMATS, [BarcodeFormat.QR_CODE])
      hints.set(DecodeHintType.TRY_HARDER, true)
      _zxingReader = new BrowserMultiFormatReader(hints, 100)
    } catch (e) {
      _zxingReader = null
    }
  }
  return _zxingReader
}

async function loadImage(url) {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = () => reject(new Error('图片加载失败'))
    img.src = url
  })
}

function imageToCanvas(img, maxSide) {
  const w = img.naturalWidth || img.width
  const h = img.naturalHeight || img.height
  if (!w || !h) throw new Error('图片尺寸为 0')
  if (!maxSide) {
    const canvas = document.createElement('canvas')
    canvas.width = w
    canvas.height = h
    const ctx = canvas.getContext('2d')
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, w, h)
    ctx.drawImage(img, 0, 0, w, h)
    return canvas
  }
  const scale = Math.min(1, maxSide / Math.max(w, h))
  const tw = Math.max(1, Math.round(w * scale))
  const th = Math.max(1, Math.round(h * scale))
  const canvas = document.createElement('canvas')
  canvas.width = tw
  canvas.height = th
  const ctx = canvas.getContext('2d')
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, tw, th)
  ctx.drawImage(img, 0, 0, tw, th)
  return canvas
}

function cloneCanvas(canvas) {
  const out = document.createElement('canvas')
  out.width = canvas.width
  out.height = canvas.height
  const ctx = out.getContext('2d')
  ctx.drawImage(canvas, 0, 0)
  return out
}

function grayscale(canvas) {
  const ctx = canvas.getContext('2d')
  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
  const d = imageData.data
  for (let i = 0; i < d.length; i += 4) {
    const y = (d[i] * 299 + d[i + 1] * 587 + d[i + 2] * 114) / 1000
    d[i] = d[i + 1] = d[i + 2] = y
  }
  ctx.putImageData(imageData, 0, 0)
  return canvas
}

function rotate(canvas, angle) {
  if (angle === 0) return canvas
  const w = canvas.width
  const h = canvas.height
  const out = document.createElement('canvas')
  const swap = angle === 90 || angle === 270
  out.width = swap ? h : w
  out.height = swap ? w : h
  const ctx = out.getContext('2d')
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, out.width, out.height)
  ctx.translate(out.width / 2, out.height / 2)
  ctx.rotate((angle * Math.PI) / 180)
  ctx.drawImage(canvas, -w / 2, -h / 2)
  return out
}

async function tryBarcodeDetector(canvas) {
  if (typeof BarcodeDetector === 'undefined') return null
  try {
    const detector = new BarcodeDetector({ formats: ['qr_code'] })
    const results = await detector.detect(canvas)
    if (results && results.length > 0 && results[0].rawValue) {
      return results[0].rawValue
    }
  } catch (e) { /* continue */ }
  return null
}

async function tryZxing(canvas) {
  const reader = getZxing()
  if (!reader) return null
  try {
    const result = await reader.decodeFromCanvas(canvas)
    if (result && result.getText) return result.getText()
  } catch (e) { /* no QR found */ }
  return null
}

async function decodeFromImage(img) {
  const tried = []

  // 有序尝试：最可能成功的在前，越往后越 aggressive
  const plan = [
    { scale: null, gray: false, angle: 0 },   // 原始分辨率彩图
    { scale: 1600, gray: false, angle: 0 },   // 1600 彩图
    { scale: 1200, gray: false, angle: 0 },   // 1200 彩图
    { scale: 800, gray: false, angle: 0 },    // 800 彩图
    { scale: 1600, gray: true, angle: 0 },    // 灰度
    { scale: 1600, gray: true, angle: 90 },   // 灰度+竖拍旋转
    { scale: 1600, gray: false, angle: 90 },  // 彩图+竖拍旋转
    { scale: null, gray: false, angle: 90 },  // 原分辨率+旋转
  ]

  for (const p of plan) {
    try {
      let c = imageToCanvas(img, p.scale)
      if (p.gray) grayscale(c)
      if (p.angle !== 0) c = rotate(c, p.angle)
      const z = await tryZxing(c)
      if (z) return z
      tried.push('zx-s' + (p.scale || 'f') + '-g' + (p.gray ? '1' : '0') + '-r' + p.angle)
    } catch (e) { /* skip */ }
  }

  for (const p of plan) {
    try {
      let c = imageToCanvas(img, p.scale)
      if (p.angle !== 0) c = rotate(c, p.angle)
      const b = await tryBarcodeDetector(c)
      if (b) return b
      tried.push('bd-s' + (p.scale || 'f') + '-g0-r' + p.angle)
    } catch (e) { /* skip */ }
  }

  // 最后兜底：灰度+全旋转，只在 1600 尺度
  for (const gray of [false, true]) {
    for (const angle of [180, 270]) {
      try {
        let c = imageToCanvas(img, 1600)
        if (gray) grayscale(c)
        const r = rotate(c, angle)
        const z = await tryZxing(r)
        if (z) return z
        tried.push(`zx-s1600-g${gray ? '1' : '0'}-r${angle}`)
        const b = await tryBarcodeDetector(r)
        if (b) return b
        tried.push(`bd-s1600-g${gray ? '1' : '0'}-r${angle}`)
      } catch (e) { /* skip */ }
    }
  }

  console.warn('[qrscan] all attempts failed:', tried)
  throw new Error(
    '未能识别到二维码。请确保二维码居中、光线充足、占画面 1/3 以上；' +
    '或直接跳过扫码，在下方输入框手输二维码内容后点击"绑定二维码"。'
  )
}

export function scanQRWithBrowser() {
  return new Promise((resolve, reject) => {
    let settled = false
    const cleanup = () => {
      if (input.parentNode) input.parentNode.removeChild(input)
    }
    const safeResolve = (v) => { if (!settled) { settled = true; cleanup(); resolve(v) } }
    const safeReject = (e) => { if (!settled) { settled = true; cleanup(); reject(e) } }

    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'image/*'
    input.setAttribute('capture', 'environment')
    input.style.position = 'fixed'
    input.style.left = '-9999px'
    document.body.appendChild(input)

    input.addEventListener('change', async () => {
      const file = input.files && input.files[0]
      if (!file) return safeReject(new Error('未选择文件'))
      const url = URL.createObjectURL(file)
      try {
        const img = await loadImage(url)
        const text = await decodeFromImage(img)
        URL.revokeObjectURL(url)
        safeResolve(text)
      } catch (err) {
        URL.revokeObjectURL(url)
        safeReject(err)
      }
    })

    input.addEventListener('cancel', () => safeReject(new Error('已取消扫码')))

    try { input.click() } catch (e) { safeReject(e) }
  })
}

// 从扫码文本中提取纯二维码内容
// 兼容：
//   http://suyuan1.hongmen.com?code=4728458525491308  -> 4728458525491308
//   https://suyuan1.hongmen.com/?code=4728458525491308 -> 4728458525491308
//   suyuan1.hongmen.com?code=4728458525491308         -> 4728458525491308
//   4728458525491308                                  -> 4728458525491308
//   4728458525491308#xxx                              -> 4728458525491308
export function extractQrCode(raw) {
  if (!raw) return ''
  let text = String(raw).trim()
  if (!text) return ''
  // 优先尝试 ?code= / &code=
  const m = text.match(/[?&]code=([^&#\s]+)/)
  if (m && m[1]) return m[1].trim()
  // 兜底：去掉所有非数字字符
  const digits = text.replace(/[^0-9]/g, '')
  return digits
}
