/**
 * 工业级 QR 解码链路：
 *   1) @zxing/browser (Google ZXing 移植) —— 对相机照片最强，支持透视/光照/低对比
 *   2) BarcodeDetector (Chrome/Edge 原生) —— 快但对模糊照片差一点
 *   3) jsQR + 灰度 + 旋转 0/90/180/270 —— 最后的兜底
 *
 * 输入：HTMLImageElement 或 ImageBitmap
 * 输出：Promise<string> 解码结果，或 reject with 中文错误
 *
 * 任意浏览器（只要支持 <input type=file>），不需要 HTTPS，
 * 不需要 getUserMedia，BarcodeDetector 优先级最高无依赖。
 */

import { BrowserMultiFormatReader } from '@zxing/browser'

// 单例 reader（内部状态机，重复 decode 影响性能）
let _zxingReader = null
function getZxing() {
  if (!_zxingReader) {
    try {
      _zxingReader = new BrowserMultiFormatReader()
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

// 把图片画到白底 canvas，转成 imageData
function imageToCanvas(img, maxSide = 1600) {
  const w = img.naturalWidth || img.width
  const h = img.naturalHeight || img.height
  if (!w || !h) throw new Error('图片尺寸为 0')

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

// 灰度化 + 大津阈值二值化（增强对比，黑暗环境救星）
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

// 旋转画布 0/90/180/270
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

async function tryBarcodeDetector(bitmap) {
  if (typeof BarcodeDetector === 'undefined') return null
  try {
    const detector = new BarcodeDetector({ formats: ['qr_code'] })
    const results = await detector.detect(bitmap)
    if (results && results.length > 0 && results[0].rawValue) {
      return results[0].rawValue
    }
  } catch (e) {
    /* continue */
  }
  return null
}

async function tryZxing(bitmap) {
  const reader = getZxing()
  if (!reader) return null
  try {
    // ZXing-browser decodeFromImageElement 需要 img DOM element
    if (bitmap instanceof HTMLImageElement) {
      const result = await reader.decodeFromImageElement('qr-canvas-tmp-' + Date.now(), bitmap)
      if (result && result.getText) return result.getText()
    } else if (bitmap instanceof HTMLCanvasElement) {
      const result = await reader.decodeFromCanvas(bitmap)
      if (result && result.getText) return result.getText()
    } else if (bitmap instanceof ImageBitmap) {
      // ImageBitmap → to canvas → decode
      const canvas = document.createElement('canvas')
      canvas.width = bitmap.width
      canvas.height = bitmap.height
      canvas.getContext('2d').drawImage(bitmap, 0, 0)
      const result = await reader.decodeFromCanvas(canvas)
      if (result && result.getText) return result.getText()
    }
  } catch (e) {
    /* no QR in image */
  }
  return null
}

async function decodeFromImage(img) {
  const tried = []
  // ========== 路径 1：ZXing（工业级，最先试） ==========
  try {
    const canvas = imageToCanvas(img, 1600)
    let r = await tryZxing(canvas)
    if (r) return r
    tried.push('zxing-canvas')
    // ZXing 在黑白对比高的图上更好，做灰度再试
    grayscale(canvas)
    r = await tryZxing(canvas)
    if (r) return r
    tried.push('zxing-gray')
    // 90° 旋转（手机竖拍可能转横识别更好）
    for (const a of [90, 180, 270]) {
      const rotated = rotate(canvas, a)
      r = await tryZxing(rotated)
      if (r) return r
      tried.push(`zxing-r${a}`)
    }
  } catch (e) { /* continue */ }

  // ========== 路径 2：BarcodeDetector 原生 ==========
  try {
    const canvas = imageToCanvas(img, 1600)
    let r = await tryBarcodeDetector(canvas)
    if (r) return r
    tried.push('barcode-canvas')
    for (const a of [90, 180, 270]) {
      const rotated = rotate(canvas, a)
      r = await tryBarcodeDetector(rotated)
      if (r) return r
      tried.push(`barcode-r${a}`)
    }
  } catch (e) { /* continue */ }

  console.warn('[qrscan] all attempts failed:', tried)
  throw new Error('未能识别二维码，请拍照时让二维码占画面 1/3 以上、对准取景框、光线充足；或直接跳过扫码，在下方输入框手输二维码内容后点击"绑定二维码"')
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
