const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { v4: uuidv4 } = require('uuid');
const { pool, initDatabase } = require('./db');
const pixelroot = require('./pixelroot');

const app = express();
const PORT = 5000;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../client/dist')));
app.use('/uploads', express.static(path.join(__dirname, '../uploads')));

app.use((req, res, next) => {
  res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
  next();
});

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, path.join(__dirname, '../uploads'));
  },
  filename: (req, file, cb) => {
    const uniqueName = `${uuidv4()}${path.extname(file.originalname)}`;
    cb(null, uniqueName);
  }
});

const upload = multer({ 
  storage,
  limits: { fileSize: 10 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    const allowedTypes = /jpeg|jpg|png|gif|webp/;
    const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
    const mimetype = allowedTypes.test(file.mimetype);
    if (extname && mimetype) {
      cb(null, true);
    } else {
      cb(new Error('Only image files are allowed'));
    }
  }
});

app.post('/api/register', upload.single('image'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No image provided' });
    }

    const imageData = fs.readFileSync(req.file.path);
    const timestamp = Date.now();
    const mac = pixelroot.generateMACAddress();
    const lat = parseFloat(req.body.latitude) || (Math.random() * 180 - 90);
    const lng = parseFloat(req.body.longitude) || (Math.random() * 360 - 180);

    const imageHash = pixelroot.generateImageHash(imageData, mac, timestamp, lat, lng);
    const pixelSignature = pixelroot.generatePixelSignature(mac, timestamp, lat, lng);
    const blockchainTx = pixelroot.generateBlockchainTx();

    const result = await pool.query(
      `INSERT INTO images (image_hash, mac_address, timestamp, latitude, longitude, blockchain_tx, pixel_signature, original_filename, file_path, verified)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, true)
       RETURNING *`,
      [imageHash, mac, timestamp, lat, lng, blockchainTx, JSON.stringify(pixelSignature.positions.slice(0, 10)), req.file.originalname, req.file.filename]
    );

    res.json({
      success: true,
      data: {
        id: result.rows[0].id,
        imageHash,
        macAddress: mac,
        timestamp,
        location: { lat, lng },
        blockchainTx,
        pixelPositions: pixelSignature.positions.slice(0, 10),
        filename: req.file.filename
      }
    });
  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({ error: 'Failed to register image' });
  }
});

app.post('/api/verify', upload.single('image'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No image provided' });
    }

    const imageData = fs.readFileSync(req.file.path);
    const imageHash = req.body.hash;

    if (imageHash) {
      const result = await pool.query(
        'SELECT * FROM images WHERE image_hash = $1',
        [imageHash]
      );

      if (result.rows.length > 0) {
        const record = result.rows[0];
        await pool.query(
          'INSERT INTO verifications (image_hash, verified, verifier_ip) VALUES ($1, $2, $3)',
          [imageHash, true, req.ip]
        );

        fs.unlinkSync(req.file.path);

        return res.json({
          verified: true,
          data: {
            imageHash: record.image_hash,
            macAddress: record.mac_address,
            timestamp: parseInt(record.timestamp),
            location: { lat: parseFloat(record.latitude), lng: parseFloat(record.longitude) },
            blockchainTx: record.blockchain_tx,
            registeredAt: record.created_at
          }
        });
      }
    }

    fs.unlinkSync(req.file.path);
    res.json({ verified: false, message: 'Image not found in registry' });
  } catch (error) {
    console.error('Verification error:', error);
    res.status(500).json({ error: 'Failed to verify image' });
  }
});

app.get('/api/images', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT id, image_hash, mac_address, timestamp, latitude, longitude, blockchain_tx, original_filename, file_path, verified, created_at FROM images ORDER BY created_at DESC LIMIT 50'
    );
    res.json(result.rows);
  } catch (error) {
    console.error('Error fetching images:', error);
    res.status(500).json({ error: 'Failed to fetch images' });
  }
});

app.get('/api/stats', async (req, res) => {
  try {
    const imagesResult = await pool.query('SELECT COUNT(*) as count FROM images');
    const verificationsResult = await pool.query('SELECT COUNT(*) as count FROM verifications WHERE verified = true');
    
    res.json({
      totalImages: parseInt(imagesResult.rows[0].count),
      totalVerifications: parseInt(verificationsResult.rows[0].count)
    });
  } catch (error) {
    console.error('Error fetching stats:', error);
    res.status(500).json({ error: 'Failed to fetch stats' });
  }
});

app.get('/api/image/:hash', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM images WHERE image_hash = $1',
      [req.params.hash]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Image not found' });
    }
    
    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error fetching image:', error);
    res.status(500).json({ error: 'Failed to fetch image' });
  }
});

app.get('/{*splat}', (req, res) => {
  res.sendFile(path.join(__dirname, '../client/dist/index.html'));
});

initDatabase().then(() => {
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`PixelRoot server running on http://0.0.0.0:${PORT}`);
  });
}).catch(err => {
  console.error('Failed to initialize database:', err);
  process.exit(1);
});
