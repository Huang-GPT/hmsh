const QRCode = require('qrcode');
const fs = require('fs');
const path = require('path');

async function test() {
  // Generate QR with test data
  const testData = 'SO202607001|10';
  const pngPath = path.join(__dirname, 'temp_test_qr.png');
  await QRCode.toFile(pngPath, testData, { width: 512, margin: 2 });
  console.log('QR generated:', pngPath, 'data:', testData);

  // Now decode with @zxing/library directly (no Browser wrappers)
  const { default: MultiFormatReader } = require('@zxing/library/esm/core/MultiFormatReader');
  const { default: BinaryBitmap } = require('@zxing/library/esm/core/BinaryBitmap');
  const { default: HybridBinarizer } = require('@zxing/library/esm/core/common/HybridBinarizer');
  const { default: BufferedImageLuminanceSource } = require('@zxing/library/esm/core/BufferedImageLuminanceSource');
  
  // Load PNG as raw pixels (simple approach: use the canvas package if available)
  try {
    const { createCanvas, loadImage } = require('canvas');
    const img = await loadImage(pngPath);
    const canvas = createCanvas(img.width, img.height);
    const ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0);
    const imageData = ctx.getImageData(0, 0, img.width, img.height);
    
    const source = new BufferedImageLuminanceSource(imageData);
    const binarizer = new HybridBinarizer(source);
    const bitmap = new BinaryBitmap(binarizer);
    
    const reader = new MultiFormatReader();
    const result = reader.decodeWithState(bitmap);
    
    console.log('DECODED! text:', result.getText());
    console.log('format:', result.getBarcodeFormat());
    
    if (result.getText() === testData) {
      console.log('✓ MATCH!');
      process.exit(0);
    } else {
      console.log('✗ MISMATCH:', result.getText(), 'vs expected', testData);
      process.exit(1);
    }
  } catch(e) {
    console.log('Failed to decode:', e.message);
    // Try alternative: use @zxing/library cjs
    console.log('Trying cjs path...');
    const MultiFormatReader2 = require('@zxing/library').default || require('@zxing/library');
    console.log('Available exports:', Object.keys(require('@zxing/library')));
    process.exit(1);
  }
}

test().catch(e => { console.error(e); process.exit(1); });
