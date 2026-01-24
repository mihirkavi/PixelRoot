const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

async function initDatabase() {
  const client = await pool.connect();
  try {
    await client.query(`
      CREATE TABLE IF NOT EXISTS images (
        id SERIAL PRIMARY KEY,
        image_hash VARCHAR(64) NOT NULL UNIQUE,
        mac_address VARCHAR(17) NOT NULL,
        timestamp BIGINT NOT NULL,
        latitude DECIMAL(10, 8),
        longitude DECIMAL(11, 8),
        blockchain_tx VARCHAR(66),
        pixel_signature VARCHAR(255),
        original_filename VARCHAR(255),
        file_path VARCHAR(255),
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

      CREATE INDEX IF NOT EXISTS idx_images_hash ON images(image_hash);
      CREATE INDEX IF NOT EXISTS idx_images_timestamp ON images(timestamp);
    `);
    console.log('Database initialized successfully');
  } finally {
    client.release();
  }
}

module.exports = { pool, initDatabase };
