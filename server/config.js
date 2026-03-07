const path = require('path');
const packageJson = require('../package.json');

const ROOT_DIR = path.join(__dirname, '..');

function parsePositiveInteger(value, fallback) {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

module.exports = {
  appName: 'PixelRoot',
  version: packageJson.version,
  host: process.env.HOST || '127.0.0.1',
  port: parsePositiveInteger(process.env.PORT, 5000),
  databaseUrl: process.env.DATABASE_URL || '',
  rootDir: ROOT_DIR,
  clientDistDir: path.join(ROOT_DIR, 'client', 'dist'),
  uploadsDir: path.join(ROOT_DIR, 'uploads'),
  dataDir: path.join(ROOT_DIR, 'server', 'data'),
  dataFile: path.join(ROOT_DIR, 'server', 'data', 'pixelroot-store.json'),
  maxUploadSizeBytes: 10 * 1024 * 1024,
  defaultLocation: {
    lat: 0,
    lng: 0,
    source: 'neutral-origin',
  },
  blockchainProvider: 'simulated-ledger',
};
