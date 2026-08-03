const { createCanvas, loadImage } = require("canvas");
const path = require("path");
const fs = require("fs");

async function test() {
  const pngPath = path.join(__dirname, "temp_test_qr.png");
  const img = await loadImage(pngPath);
  const c = createCanvas(img.width, img.height);
  const ctx = c.getContext("2d");
  ctx.drawImage(img, 0, 0);
  const imageData = ctx.getImageData(0, 0, img.width, img.height);

  // Use CJS @zxing/library
  const { default: BufferedImageLuminanceSource } = require("@zxing/library/cjs/core/BufferedImageLuminanceSource");
  const { default: HybridBinarizer } = require("@zxing/library/cjs/core/common/HybridBinarizer");
  const { default: BinaryBitmap } = require("@zxing/library/cjs/core/BinaryBitmap");
  const { default: MultiFormatReader } = require("@zxing/library/cjs/core/MultiFormatReader");

  const source = new BufferedImageLuminanceSource(imageData);
  const bin = new HybridBinarizer(source);
  const bm = new BinaryBitmap(bin);
  const r = new MultiFormatReader();
  const result = r.decodeWithState(bm);
  console.log("DECODED:", result.getText());
}
test().catch(e => { console.error("FAIL:", e.message); process.exit(1); });
