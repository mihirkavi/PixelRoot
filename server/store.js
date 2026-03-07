const fs = require('fs/promises');
const path = require('path');
const { Pool } = require('pg');

function sortByDateDesc(items, field) {
  return [...items].sort((left, right) => {
    const leftValue = new Date(left[field]).getTime();
    const rightValue = new Date(right[field]).getTime();
    return rightValue - leftValue;
  });
}

function normalizeImageRecord(record) {
  return {
    id: Number(record.id),
    image_hash: record.image_hash,
    algorithm_version: record.algorithm_version || 'v1',
    mac_address: record.mac_address,
    timestamp: Number(record.timestamp),
    latitude: Number(record.latitude),
    longitude: Number(record.longitude),
    location_source: record.location_source || 'neutral-origin',
    blockchain_tx: record.blockchain_tx,
    blockchain_provider: record.blockchain_provider || 'simulated-ledger',
    pixel_signature: record.pixel_signature || null,
    original_filename: record.original_filename,
    file_path: record.file_path,
    verified: Boolean(record.verified),
    created_at: record.created_at,
  };
}

function normalizeVerificationRecord(record) {
  return {
    id: Number(record.id),
    image_hash: record.image_hash,
    verified: Boolean(record.verified),
    verification_time: record.verification_time,
    verifier_ip: record.verifier_ip || null,
  };
}

class FileStore {
  constructor(config) {
    this.config = config;
    this.mode = 'file';
    this.data = {
      nextImageId: 1,
      nextVerificationId: 1,
      images: [],
      verifications: [],
    };
    this.writeChain = Promise.resolve();
  }

  async init() {
    await fs.mkdir(this.config.dataDir, { recursive: true });
    await fs.mkdir(this.config.uploadsDir, { recursive: true });

    try {
      const raw = await fs.readFile(this.config.dataFile, 'utf8');
      const parsed = JSON.parse(raw);
      this.data = {
        nextImageId: parsed.nextImageId || 1,
        nextVerificationId: parsed.nextVerificationId || 1,
        images: Array.isArray(parsed.images) ? parsed.images.map(normalizeImageRecord) : [],
        verifications: Array.isArray(parsed.verifications)
          ? parsed.verifications.map(normalizeVerificationRecord)
          : [],
      };
    } catch (error) {
      if (error.code !== 'ENOENT') {
        throw error;
      }
      await this.persist();
    }
  }

  async persist() {
    const tempFile = `${this.config.dataFile}.tmp`;
    const payload = JSON.stringify(this.data, null, 2);
    await fs.writeFile(tempFile, payload, 'utf8');
    await fs.rename(tempFile, this.config.dataFile);
  }

  async queueMutation(mutator) {
    const operation = this.writeChain.then(async () => {
      const result = await mutator();
      await this.persist();
      return result;
    });

    this.writeChain = operation.catch(() => {});
    return operation;
  }

  async getHealth() {
    return {
      mode: this.mode,
      ready: true,
      dataFile: path.relative(this.config.rootDir, this.config.dataFile),
    };
  }

  async createImage(payload) {
    return this.queueMutation(async () => {
      const now = new Date().toISOString();
      const record = normalizeImageRecord({
        ...payload,
        id: this.data.nextImageId++,
        created_at: payload.created_at || now,
      });
      this.data.images.unshift(record);
      return record;
    });
  }

  async listImages(limit = 50) {
    return sortByDateDesc(this.data.images, 'created_at').slice(0, limit);
  }

  async getAllImages() {
    return sortByDateDesc(this.data.images, 'created_at');
  }

  async findImageByHash(imageHash) {
    return this.data.images.find((image) => image.image_hash === imageHash) || null;
  }

  async createVerification(payload) {
    return this.queueMutation(async () => {
      const record = normalizeVerificationRecord({
        ...payload,
        id: this.data.nextVerificationId++,
        verification_time: payload.verification_time || new Date().toISOString(),
      });
      this.data.verifications.unshift(record);
      return record;
    });
  }

  async getStats() {
    return {
      totalImages: this.data.images.length,
      totalVerifications: this.data.verifications.filter((entry) => entry.verified).length,
      storageMode: this.mode,
    };
  }
}

class PostgresStore {
  constructor(config) {
    this.config = config;
    this.mode = 'postgres';
    this.pool = new Pool({
      connectionString: config.databaseUrl,
      ssl: /localhost|127\.0\.0\.1/.test(config.databaseUrl)
        ? false
        : { rejectUnauthorized: false },
    });
  }

  async init() {
    await fs.mkdir(this.config.uploadsDir, { recursive: true });
    await this.pool.query(`
      CREATE TABLE IF NOT EXISTS images (
        id SERIAL PRIMARY KEY,
        image_hash VARCHAR(64) NOT NULL UNIQUE,
        algorithm_version VARCHAR(16) NOT NULL DEFAULT 'v1',
        mac_address VARCHAR(17) NOT NULL,
        timestamp BIGINT NOT NULL,
        latitude DOUBLE PRECISION NOT NULL,
        longitude DOUBLE PRECISION NOT NULL,
        location_source VARCHAR(32) NOT NULL DEFAULT 'neutral-origin',
        blockchain_tx VARCHAR(66) NOT NULL,
        blockchain_provider VARCHAR(32) NOT NULL DEFAULT 'simulated-ledger',
        pixel_signature TEXT,
        original_filename VARCHAR(255) NOT NULL,
        file_path VARCHAR(255) NOT NULL,
        verified BOOLEAN DEFAULT false,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS verifications (
        id SERIAL PRIMARY KEY,
        image_hash VARCHAR(64) NOT NULL,
        verified BOOLEAN NOT NULL,
        verification_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        verifier_ip VARCHAR(45),
        FOREIGN KEY (image_hash) REFERENCES images(image_hash)
      );

      ALTER TABLE images ADD COLUMN IF NOT EXISTS algorithm_version VARCHAR(16) NOT NULL DEFAULT 'v1';
      ALTER TABLE images ADD COLUMN IF NOT EXISTS location_source VARCHAR(32) NOT NULL DEFAULT 'neutral-origin';
      ALTER TABLE images ADD COLUMN IF NOT EXISTS blockchain_provider VARCHAR(32) NOT NULL DEFAULT 'simulated-ledger';
      ALTER TABLE images ADD COLUMN IF NOT EXISTS pixel_signature TEXT;
      ALTER TABLE images ALTER COLUMN latitude TYPE DOUBLE PRECISION USING latitude::double precision;
      ALTER TABLE images ALTER COLUMN longitude TYPE DOUBLE PRECISION USING longitude::double precision;

      CREATE INDEX IF NOT EXISTS idx_images_hash ON images(image_hash);
      CREATE INDEX IF NOT EXISTS idx_images_timestamp ON images(timestamp);
      CREATE INDEX IF NOT EXISTS idx_verifications_hash ON verifications(image_hash);
    `);
  }

  async getHealth() {
    await this.pool.query('SELECT 1');
    return {
      mode: this.mode,
      ready: true,
    };
  }

  async createImage(payload) {
    const result = await this.pool.query(
      `INSERT INTO images (
        image_hash,
        algorithm_version,
        mac_address,
        timestamp,
        latitude,
        longitude,
        location_source,
        blockchain_tx,
        blockchain_provider,
        pixel_signature,
        original_filename,
        file_path,
        verified
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
      RETURNING *`,
      [
        payload.image_hash,
        payload.algorithm_version,
        payload.mac_address,
        payload.timestamp,
        payload.latitude,
        payload.longitude,
        payload.location_source,
        payload.blockchain_tx,
        payload.blockchain_provider,
        payload.pixel_signature,
        payload.original_filename,
        payload.file_path,
        payload.verified,
      ]
    );

    return normalizeImageRecord(result.rows[0]);
  }

  async listImages(limit = 50) {
    const result = await this.pool.query(
      `SELECT *
       FROM images
       ORDER BY created_at DESC
       LIMIT $1`,
      [limit]
    );
    return result.rows.map(normalizeImageRecord);
  }

  async getAllImages() {
    const result = await this.pool.query(
      `SELECT *
       FROM images
       ORDER BY created_at DESC`
    );
    return result.rows.map(normalizeImageRecord);
  }

  async findImageByHash(imageHash) {
    const result = await this.pool.query(
      `SELECT *
       FROM images
       WHERE image_hash = $1
       LIMIT 1`,
      [imageHash]
    );
    return result.rows[0] ? normalizeImageRecord(result.rows[0]) : null;
  }

  async createVerification(payload) {
    const result = await this.pool.query(
      `INSERT INTO verifications (image_hash, verified, verifier_ip)
       VALUES ($1, $2, $3)
       RETURNING *`,
      [payload.image_hash, payload.verified, payload.verifier_ip]
    );
    return normalizeVerificationRecord(result.rows[0]);
  }

  async getStats() {
    const [imagesResult, verificationsResult] = await Promise.all([
      this.pool.query('SELECT COUNT(*)::int AS count FROM images'),
      this.pool.query('SELECT COUNT(*)::int AS count FROM verifications WHERE verified = true'),
    ]);

    return {
      totalImages: imagesResult.rows[0].count,
      totalVerifications: verificationsResult.rows[0].count,
      storageMode: this.mode,
    };
  }
}

async function createStore(config) {
  const store = config.databaseUrl ? new PostgresStore(config) : new FileStore(config);
  await store.init();
  return store;
}

module.exports = {
  createStore,
};
