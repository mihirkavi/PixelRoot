const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const fs = require('fs/promises');
const { v4: uuidv4 } = require('uuid');
const config = require('./config');
const { createStore } = require('./store');
const pixelroot = require('./pixelroot');

const app = express();
let store;

app.use(cors());
app.use(express.json());
app.use(express.static(config.clientDistDir));
app.use('/uploads', express.static(config.uploadsDir));

app.use((req, res, next) => {
  res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
  next();
});

const upload = multer({ 
  storage: multer.memoryStorage(),
  limits: { fileSize: config.maxUploadSizeBytes },
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

function clampCoordinate(value, min, max) {
  if (!Number.isFinite(value)) {
    return null;
  }
  return Math.max(min, Math.min(max, value));
}

function resolveLocation(body) {
  const latitude = clampCoordinate(Number.parseFloat(body.latitude), -90, 90);
  const longitude = clampCoordinate(Number.parseFloat(body.longitude), -180, 180);

  if (latitude === null || longitude === null) {
    return config.defaultLocation;
  }

  return {
    lat: latitude,
    lng: longitude,
    source: 'device',
  };
}

function getClientIp(req) {
  const forwarded = req.headers['x-forwarded-for'];
  if (typeof forwarded === 'string' && forwarded.length > 0) {
    return forwarded.split(',')[0].trim();
  }
  return req.ip;
}

function toPublicImage(record) {
  let pixelSignaturePreview = [];

  if (record.pixel_signature) {
    try {
      pixelSignaturePreview = JSON.parse(record.pixel_signature);
    } catch (error) {
      console.warn('Failed to parse pixel signature preview:', error);
    }
  }

  return {
    id: record.id,
    imageHash: record.image_hash,
    algorithmVersion: record.algorithm_version,
    macAddress: record.mac_address,
    timestamp: Number(record.timestamp),
    location: {
      lat: Number(record.latitude),
      lng: Number(record.longitude),
      source: record.location_source,
    },
    blockchainTx: record.blockchain_tx,
    blockchainProvider: record.blockchain_provider,
    pixelSignaturePreview,
    originalFilename: record.original_filename,
    filePath: record.file_path,
    fileUrl: `/uploads/${record.file_path}`,
    verified: Boolean(record.verified),
    createdAt: record.created_at,
  };
}

async function saveUploadedImage(file) {
  const filename = `${uuidv4()}${path.extname(file.originalname).toLowerCase()}`;
  const destination = path.join(config.uploadsDir, filename);
  await fs.mkdir(config.uploadsDir, { recursive: true });
  await fs.writeFile(destination, file.buffer);
  return filename;
}

function handleUploadError(error, req, res, next) {
  if (error instanceof multer.MulterError) {
    if (error.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({ error: 'Image exceeds the 10 MB upload limit.' });
    }
    return res.status(400).json({ error: error.message });
  }

  if (error) {
    return res.status(400).json({ error: error.message });
  }

  return next();
}

app.get('/api/health', async (req, res) => {
  try {
    const storage = await store.getHealth();
    res.json({
      status: 'ok',
      appName: config.appName,
      version: config.version,
      storage,
      uploadLimitBytes: config.maxUploadSizeBytes,
      algorithm: pixelroot.describeVersion(),
    });
  } catch (error) {
    console.error('Health check failed:', error);
    res.status(500).json({
      status: 'error',
      error: 'Storage backend is unavailable.',
    });
  }
});

app.post('/api/register', upload.single('image'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No image provided' });
    }

    const timestamp = Date.now();
    const mac = pixelroot.generateMACAddress();
    const location = resolveLocation(req.body);
    const algorithmVersion = pixelroot.DEFAULT_VERSION;
    const imageHash = pixelroot.generateImageHash(
      req.file.buffer,
      mac,
      timestamp,
      location.lat,
      location.lng,
      algorithmVersion
    );
    const pixelSignature = pixelroot.generatePixelSignature(
      mac,
      timestamp,
      location.lat,
      location.lng,
      algorithmVersion
    );
    const blockchainTx = pixelroot.generateBlockchainTx();
    const filePath = await saveUploadedImage(req.file);
    let record;

    try {
      record = await store.createImage({
        image_hash: imageHash,
        algorithm_version: algorithmVersion,
        mac_address: mac,
        timestamp,
        latitude: location.lat,
        longitude: location.lng,
        location_source: location.source,
        blockchain_tx: blockchainTx,
        blockchain_provider: config.blockchainProvider,
        pixel_signature: JSON.stringify(pixelSignature.positions.slice(0, 16)),
        original_filename: req.file.originalname,
        file_path: filePath,
        verified: true,
      });
    } catch (error) {
      await fs.unlink(path.join(config.uploadsDir, filePath)).catch(() => {});
      throw error;
    }

    res.json({
      success: true,
      data: toPublicImage(record),
    });
  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({ error: 'Failed to register image' });
  }
}, handleUploadError);

app.post('/api/verify', upload.single('image'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No image provided' });
    }

    const allImages = await store.getAllImages();

    let matchedRecord = null;
    
    for (const record of allImages) {
      const computedHash = pixelroot.generateImageHash(
        req.file.buffer,
        record.mac_address,
        Number(record.timestamp),
        Number(record.latitude),
        Number(record.longitude),
        record.algorithm_version || 'v1'
      );
      
      if (computedHash === record.image_hash) {
        matchedRecord = record;
        break;
      }
    }

    if (matchedRecord) {
      await store.createVerification({
        image_hash: matchedRecord.image_hash,
        verified: true,
        verifier_ip: getClientIp(req),
      });

      return res.json({
        verified: true,
        data: toPublicImage(matchedRecord),
      });
    }

    res.json({ verified: false, message: 'Image not found in registry or has been modified' });
  } catch (error) {
    console.error('Verification error:', error);
    res.status(500).json({ error: 'Failed to verify image' });
  }
}, handleUploadError);

app.get('/api/images', async (req, res) => {
  try {
    const images = await store.listImages(50);
    res.json(images.map(toPublicImage));
  } catch (error) {
    console.error('Error fetching images:', error);
    res.status(500).json({ error: 'Failed to fetch images' });
  }
});

app.get('/api/stats', async (req, res) => {
  try {
    const stats = await store.getStats();
    res.json(stats);
  } catch (error) {
    console.error('Error fetching stats:', error);
    res.status(500).json({ error: 'Failed to fetch stats' });
  }
});

app.get('/api/image/:hash', async (req, res) => {
  try {
    const image = await store.findImageByHash(req.params.hash);

    if (!image) {
      return res.status(404).json({ error: 'Image not found' });
    }
    
    res.json(toPublicImage(image));
  } catch (error) {
    console.error('Error fetching image:', error);
    res.status(500).json({ error: 'Failed to fetch image' });
  }
});

app.get('/{*splat}', (req, res) => {
  res.sendFile(path.join(config.clientDistDir, 'index.html'));
});

createStore(config).then((createdStore) => {
  store = createdStore;
  const server = app.listen(config.port, config.host, () => {
    console.log(`PixelRoot server running on http://${config.host}:${config.port}`);
  });

  server.on('error', (error) => {
    console.error('PixelRoot server failed to start:', error);
    process.exit(1);
  });
}).catch(err => {
  console.error('Failed to initialize storage:', err);
  process.exit(1);
});
