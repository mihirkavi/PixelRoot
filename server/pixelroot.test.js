const test = require('node:test');
const assert = require('node:assert/strict');

const pixelroot = require('./pixelroot');

test('v2 metadata uses full precision coordinate encoding', () => {
  const image = Buffer.from('pixelroot');
  const mac = '02:AA:BB:CC:DD:EE';
  const timestamp = 1731024000000;
  const lat = 37.7749;
  const lng = -122.4194;

  const v1Hash = pixelroot.generateImageHash(image, mac, timestamp, lat, lng, 'v1');
  const v2Hash = pixelroot.generateImageHash(image, mac, timestamp, lat, lng, 'v2');
  const signature = pixelroot.generatePixelSignature(mac, timestamp, lat, lng, 'v2');

  assert.notEqual(v1Hash, v2Hash);
  assert.equal(signature.version, 'v2');
  assert.equal(signature.bits.length, 128);
  assert.equal(signature.positions.length, 128);
});

test('verifyImage supports legacy and current versions explicitly', () => {
  const image = Buffer.from('integrity-check');
  const mac = '02:AA:BB:CC:DD:EE';
  const timestamp = 1731024000000;
  const lat = 12.3456;
  const lng = 78.9012;

  const legacyHash = pixelroot.generateImageHash(image, mac, timestamp, lat, lng, 'v1');
  const currentHash = pixelroot.generateImageHash(image, mac, timestamp, lat, lng, 'v2');

  assert.equal(pixelroot.verifyImage(legacyHash, image, mac, timestamp, lat, lng, 'v1'), true);
  assert.equal(pixelroot.verifyImage(currentHash, image, mac, timestamp, lat, lng, 'v2'), true);
  assert.equal(pixelroot.verifyImage(legacyHash, image, mac, timestamp, lat, lng, 'v2'), false);
});
