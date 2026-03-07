const crypto = require('crypto');

class PixelRoot {
  constructor() {
    this.IMAGE_WIDTH = 1920;
    this.IMAGE_HEIGHT = 1080;
    this.DEFAULT_VERSION = 'v2';
    this.VERSION_BITS = {
      v1: 120,
      v2: 128,
    };
  }

  generateMACAddress() {
    const bytes = crypto.randomBytes(6);

    // Generate a locally administered unicast MAC for demo provenance records.
    bytes[0] = (bytes[0] | 0x02) & 0xfe;

    return [...bytes]
      .map((value) => value.toString(16).padStart(2, '0').toUpperCase())
      .join(':');
  }

  macToBytes(mac) {
    return Buffer.from(mac.replace(/:/g, ''), 'hex');
  }

  timestampToBytes(timestamp) {
    const buf = Buffer.alloc(4);
    buf.writeUInt32BE(Math.floor(timestamp / 1000), 0);
    return buf;
  }

  resolveVersion(version) {
    return this.VERSION_BITS[version] ? version : this.DEFAULT_VERSION;
  }

  getEmbedBits(version = this.DEFAULT_VERSION) {
    return this.VERSION_BITS[this.resolveVersion(version)];
  }

  normalizeCoordinates(lat, lng) {
    const safeLat = Number.isFinite(lat) ? Math.max(-90, Math.min(90, lat)) : 0;
    const safeLng = Number.isFinite(lng) ? Math.max(-180, Math.min(180, lng)) : 0;

    return {
      lat: Number(safeLat.toFixed(6)),
      lng: Number(safeLng.toFixed(6)),
    };
  }

  writeUInt24BE(value) {
    const buf = Buffer.alloc(3);
    buf[0] = (value >>> 16) & 0xff;
    buf[1] = (value >>> 8) & 0xff;
    buf[2] = value & 0xff;
    return buf;
  }

  locationToBytesV1(lat, lng) {
    const buf = Buffer.alloc(5);
    const latInt = Math.floor((lat + 90) * 10000);
    const lngInt = Math.floor((lng + 180) * 10000);
    buf.writeUInt16BE(latInt & 0xFFFF, 0);
    buf.writeUInt16BE(lngInt & 0xFFFF, 2);
    buf.writeUInt8((latInt >> 16) & 0x0F | ((lngInt >> 16) & 0x0F) << 4, 4);
    return buf;
  }

  locationToBytesV2(lat, lng) {
    const normalized = this.normalizeCoordinates(lat, lng);
    const latInt = Math.round((normalized.lat + 90) * 10000);
    const lngInt = Math.round((normalized.lng + 180) * 10000);

    return Buffer.concat([
      this.writeUInt24BE(latInt),
      this.writeUInt24BE(lngInt),
    ]);
  }

  locationToBytes(lat, lng, version = this.DEFAULT_VERSION) {
    return this.resolveVersion(version) === 'v1'
      ? this.locationToBytesV1(lat, lng)
      : this.locationToBytesV2(lat, lng);
  }

  buildMetadataBuffer(mac, timestamp, lat, lng, version = this.DEFAULT_VERSION) {
    return Buffer.concat([
      this.macToBytes(mac),
      this.timestampToBytes(timestamp),
      this.locationToBytes(lat, lng, version),
    ]);
  }

  generateSeed(mac, timestamp, lat, lng, version = this.DEFAULT_VERSION) {
    const macBytes = this.macToBytes(mac);
    const timestampBytes = this.timestampToBytes(timestamp);
    const locationBytes = this.locationToBytes(lat, lng, version);
    
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

  generatePixelPositions(seed, bitCount = this.getEmbedBits()) {
    const prng = this.seededRandom(seed);
    const positions = [];
    const used = new Set();
    
    while (positions.length < bitCount) {
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

  encodeMetadata(mac, timestamp, lat, lng, version = this.DEFAULT_VERSION) {
    const bits = [];

    const metadataBytes = this.buildMetadataBuffer(mac, timestamp, lat, lng, version);
    for (let i = 0; i < metadataBytes.length; i++) {
      for (let j = 7; j >= 0; j--) {
        bits.push((metadataBytes[i] >> j) & 1);
      }
    }
    
    return bits;
  }

  generatePixelSignature(mac, timestamp, lat, lng, version = this.DEFAULT_VERSION) {
    const resolvedVersion = this.resolveVersion(version);
    const seed = this.generateSeed(mac, timestamp, lat, lng, resolvedVersion);
    const bits = this.encodeMetadata(mac, timestamp, lat, lng, resolvedVersion);
    const positions = this.generatePixelPositions(seed, bits.length);
    
    return {
      version: resolvedVersion,
      seed,
      positions,
      bits,
      gainValues: bits.map(b => b ? 1.02 : 1.0)
    };
  }

  generateImageHash(imageData, mac, timestamp, lat, lng, version = this.DEFAULT_VERSION) {
    const metadata = this.buildMetadataBuffer(mac, timestamp, lat, lng, version);
    const combined = Buffer.concat([
      Buffer.from(imageData),
      metadata
    ]);
    
    return crypto.createHash('sha256').update(combined).digest('hex');
  }

  generateBlockchainTx() {
    return '0x' + crypto.randomBytes(32).toString('hex');
  }

  verifyImage(storedHash, imageData, mac, timestamp, lat, lng, version = this.DEFAULT_VERSION) {
    const computedHash = this.generateImageHash(imageData, mac, timestamp, lat, lng, version);
    return storedHash === computedHash;
  }

  describeVersion(version = this.DEFAULT_VERSION) {
    const resolvedVersion = this.resolveVersion(version);
    return {
      version: resolvedVersion,
      metadataBits: this.getEmbedBits(resolvedVersion),
      coordinateEncoding: resolvedVersion === 'v1' ? 'legacy-packed-5-byte' : '24-bit-per-coordinate',
    };
  }
}

module.exports = new PixelRoot();
