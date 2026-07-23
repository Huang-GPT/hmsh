/**
 * 任意浏览器都能扫码：靠 <input type=file accept=image/* capture=environment>
 *
 * - 移动端：capture=environment 让浏览器直接调起后置摄像头拍照
 * - 桌面端：capture 忽略，弹出文件选择器，让用户选一张二维码截图
 * - 选完图片后，两条解码路径：
 *     1. 优先用浏览器原生 BarcodeDetector（Chrome/Edge 83+、Safari 17+）
 *     2. 退回 jsQR（任何支持 canvas getImageData 的环境，含 Firefox）
 *
 * 不依赖 HTTPS（getUserMedia 在 HTTP 上拿不到相机，但 <input type=file>
 * + capture 不需要 HTTPS 也不需要 getUserMedia 权限弹窗）。
 */

import jsQR from 'jsqr'

async function loadImage(url) {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = () => reject(new Error('图片加载失败'))
    img.src = url
  })
}

// 把任意大图压到最大边长 1200px，白底填充，输出 imageData
// 解决了"手机照片 4000x3000 太大 jsQR 处理失败"和"照片边缘杂色 decoder 假设白底"两个常见问题
function preprocessToImageData(img) {
  const w = img.naturalWidth || img.width
  const h = img.naturalHeight || img.height
  if (!w || !h) throw new Error('图片尺寸为 0')

  const MAX = 1200
  const scale = Math.min(1, MAX / Math.max(w, h))
  const tw = Math.max(1, Math.round(w * scale))
  const th = Math.max(1, Math.round(h * scale))

  const canvas = document.createElement('canvas')
  canvas.width = tw
  canvas.height = th
  const ctx = canvas.getContext('2d')
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, tw, th)
  ctx.drawImage(img, 0, 0, tw, th)
  return { ctx, tw, th, data: ctx.getImageData(0, 0, tw, th) }
}

async function decodeFromImage(img) {
  // 路径 1：BarcodeDetector + 已经预处理过的 canvas（部分浏览器对 canvas 比 image 更稳）
  if (typeof BarcodeDetector !== 'undefined') {
    const { ctx, tw, th } = preprocessToImageData(img)
    try {
      const detector = new BarcodeDetector({ formats: ['qr_code'] })
      const results = await detector.detect(ctx.canvas)
      if (results && results.length > 0 && results[0].rawValue) {
        return results[0].rawValue
      }
    } catch (e) {
      // 继续 jsQR
    }
  }

  // 路径 2：jsQR 兜底，喂预处理过的 imageData
  const { data, tw, th } = preprocessToImageData(img)
  const code = jsQR(data.data, tw, th)
  if (code && code.data) return code.data

  throw new Error('未能从图片中识别到二维码，请拍照时让二维码占画面 1/3 以上、对准取景框、光线充足；或直接在下方手动输入二维码内容')
}

/**
 * 主入口：触发扫码流程
 * - 移动端：直接拉起后置摄像头
 * - 桌面端：弹出文件选择器
 * 成功 resolve 出识别到的 QR 字符串
 */
export function scanQRWithBrowser() {
  return new Promise((resolve, reject) => {
    let settled = false
    const cleanup = () => {
      if (input.parentNode) input.parentNode.removeChild(input)
      if (preview.parentNode) preview.parentNode.removeChild(preview)
    }
    const safeResolve = (v) => { if (!settled) { settled = true; cleanup(); resolve(v) } }
    const safeReject = (e) => { if (!settled) { settled = true; cleanup(); reject(e) } }

    // 用隐藏的 input click()，浏览器会照 capture 行为弹相机/选文件
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'image/*'
    // capture=environment：移动端直接打开后置相机；桌面端忽略
    input.setAttribute('capture', 'environment')
    input.style.position = 'fixed'
    input.style.left = '-9999px'
    document.body.appendChild(input)

    // 临时预览用的 img，把 File → Blob URL → Image
    const preview = new Image()
    preview.style.display = 'none'
    document.body.appendChild(preview)

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

    // 用户取消选文件
    input.addEventListener('cancel', () => {
      safeReject(new Error('已取消扫码'))
    })

    try {
      input.click()
    } catch (e) {
      safeReject(e)
    }
  })
}
