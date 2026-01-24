const crypto = require('crypto');

class PixelRoot {
  constructor() {
    this.EMBED_BITS = 150;
    this.IMAGE_WIDTH = 1920;
    this.IMAGE_HEIGHT = 1080;
  }

  generateMACAddress() {
    const hexDigits = '0123456789ABCDEF';
    let mac = '';
    for (let i = 0; i < 6; i++) {
      if (i > 0) mac += ':';
      mac += hexDigits[Math.floor(Math.random() * 16)];
      mac += hexDigits[Math.floor(Math.random() * 16)];
    }
    return mac;
  }

  macToBytes(mac) {
    return Buffer.from(mac.replace(/:/g, ''), 'hex');
  }

  timestampToBytes(timestamp) {
    const buf = Buffer.alloc(4);
    buf.writeUInt32BE(Math.floor(timestamp / 1000), 0);
    return buf;
  }

  locationToBytes(lat, lng) {
    const buf = Buffer.alloc(5);
    const latInt = Math.floor((lat + 90) * 10000);
    const lngInt = Math.floor((lng + 180) * 10000);
    buf.writeUInt16BE(latInt & 0xFFFF, 0);
    buf.writeUInt16BE(lngInt & 0xFFFF, 2);
    buf.writeUInt8((latInt >> 16) & 0x0F | ((lngInt >> 16) & 0x0F) << 4, 4);
    return buf;
  }

  generateSeed(mac, timestamp, lat, lng) {
    const macBytes = this.macToBytes(mac);
    const timestampBytes = this.timestampToBytes(timestamp);
    const locationBytes = this.locationToBytes(lat, lng);
    
    const input = Buffer.concat([macBytes, timestampBytes, locationBytes]);
    const hash = crypto.createHash('sha256').update(input).digest();
    
    return hash.readUInt32BE(0);
  }

  seededRandom(seed) {
    let state = seed;
    return () => {
      state = (state * 1103515245 + 12345) & 0x7FFFFFFF;
      return state;
    };
  }

  generatePixelPositions(seed) {
    const prng = this.seededRandom(seed);
    const positions = [];
    const used = new Set();
    
    while (positions.length < this.EMBED_BITS) {
      const row = prng() % this.IMAGE_HEIGHT;
      const col = prng() % this.IMAGE_WIDTH;
      const key = `${row},${col}`;
      
      if (!used.has(key)) {
        used.add(key);
        positions.push({ row, col });
      }
    }
    
    return positions;
  }

  encodeMetadata(mac, timestamp, lat, lng) {
    const bits = [];
    
    const macBytes = this.macToBytes(mac);
    for (let i = 0; i < 6; i++) {
      for (let j = 7; j >= 0; j--) {
        bits.push((macBytes[i] >> j) & 1);
      }
    }
    
    const timestampBytes = this.timestampToBytes(timestamp);
    for (let i = 0; i < 4; i++) {
      for (let j = 7; j >= 0; j--) {
        bits.push((timestampBytes[i] >> j) & 1);
      }
    }
    
    const locationBytes = this.locationToBytes(lat, lng);
    for (let i = 0; i < 5; i++) {
      for (let j = 7; j >= 0; j--) {
        bits.push((locationBytes[i] >> j) & 1);
      }
    }
    
    return bits.slice(0, this.EMBED_BITS);
  }

  generatePixelSignature(mac, timestamp, lat, lng) {
    const seed = this.generateSeed(mac, timestamp, lat, lng);
    const positions = this.generatePixelPositions(seed);
    const bits = this.encodeMetadata(mac, timestamp, lat, lng);
    
    return {
      seed,
      positions,
      bits,
      gainValues: bits.map(b => b ? 1.02 : 1.0)
    };
  }

  generateImageHash(imageData, mac, timestamp, lat, lng) {
    const metadata = Buffer.concat([
      this.macToBytes(mac),
      this.timestampToBytes(timestamp),
      this.locationToBytes(lat, lng)
    ]);
    
    const combined = Buffer.concat([
      Buffer.from(imageData),
      metadata
    ]);
    
    return crypto.createHash('sha256').update(combined).digest('hex');
  }

  generateBlockchainTx() {
    return '0x' + crypto.randomBytes(32).toString('hex');
  }

  verifyImage(storedHash, imageData, mac, timestamp, lat, lng) {
    const computedHash = this.generateImageHash(imageData, mac, timestamp, lat, lng);
    return storedHash === computedHash;
  }
}

module.exports = new PixelRoot();
