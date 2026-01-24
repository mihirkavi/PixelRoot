# PixelRoot

## Overview
PixelRoot is a hardware-anchored media authenticity framework that embeds cryptographic provenance directly into image pixels at the moment of capture. By coupling CMOS sensor-level pixel modulation with real-time blockchain logging, PixelRoot enables tamper-evident verification of images and videos without relying on mutable metadata.

## How It Works
1. **Capture**: Image captured with embedded pixel signature (MAC + timestamp + GPS)
2. **Hash Generation**: SHA-256 hash computed from image data + metadata
3. **Blockchain Submit**: Hash logged to blockchain within seconds of capture
4. **Verification**: Anyone can verify authenticity via blockchain lookup

## Project Structure
```
/
├── server/
│   ├── index.js        # Express API server
│   ├── db.js           # PostgreSQL database connection
│   └── pixelroot.js    # Core PixelRoot algorithm (pixel embedding, hashing)
├── client/
│   ├── src/
│   │   ├── App.jsx     # Main React application
│   │   ├── main.jsx    # React entry point
│   │   └── styles.css  # Application styles
│   ├── vite.config.js  # Vite configuration
│   └── index.html      # HTML template
├── uploads/            # Uploaded images storage
├── package.json        # Root package configuration
└── README.md           # Project description
```

## Technology Stack
- **Backend**: Node.js 20, Express 5
- **Frontend**: React 19, Vite 7
- **Database**: PostgreSQL (Neon)
- **Styling**: Custom CSS with CSS variables

## API Endpoints
- `POST /api/register` - Register a new image with PixelRoot
- `POST /api/verify` - Verify an image's authenticity
- `GET /api/images` - List all registered images
- `GET /api/stats` - Get registration/verification statistics
- `GET /api/image/:hash` - Get details for a specific image hash

## Running the Project
```bash
npm start          # Start production server
npm run dev        # Start development (server + client)
npm run build      # Build client for production
```

## Core Algorithm (pixelroot.js)
- **Pixel Signature**: 150 bits encoded across image pixels
- **Data Encoded**: MAC address (48 bits) + timestamp (32 bits) + GPS location (40 bits)
- **Hash Function**: SHA-256 for seed generation and image hashing
- **PRNG**: Linear congruential generator seeded with metadata hash

## Future Enhancements
- Real blockchain integration (Ethereum/Solana)
- Hardware device SDK for CMOS integration
- Video support with frame-level verification
- Privacy-preserving metadata encryption
