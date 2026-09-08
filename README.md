# PixelRoot

PixelRoot is an operator-facing image authenticity console for provenance registration and verification. This version focuses on making the product professionally usable: a resilient backend, honest system status reporting, and a clearer workflow for registering and validating media.

## What changed

- The backend no longer hard-fails without `DATABASE_URL`. It now falls back to persistent local file storage automatically.
- The health API exposes storage mode, upload limits, and the active signature algorithm.
- The provenance algorithm now defaults to `v2`, which fixes the old lossy coordinate packing bug while preserving explicit support for legacy `v1` verification.
- Upload handling is safer and cleaner: in-memory processing, async file writes, and cleanup on failed persistence.
- The UI was redesigned into a more professional operations console with system status, clearer registry browsing, better mobile behavior, and explicit messaging that blockchain receipts are simulated.

## Stack

- Frontend: React 19 + Vite
- Backend: Express 5
- Storage: PostgreSQL when `DATABASE_URL` is set, otherwise a local JSON-backed store
- Media persistence: local `uploads/`

## Run locally

1. Install dependencies:

```bash
npm install
npm --prefix client install
```

2. Start the app:

```bash
npm run dev
```

3. Open:

- Frontend: `http://localhost:5173`
- Backend/API: `http://localhost:5000`

## Scripts

```bash
npm run dev
npm run build
npm test
```

## Key endpoints

- `GET /api/health` - runtime health and storage details
- `POST /api/register` - create a provenance record for an image
- `POST /api/verify` - verify an uploaded image against stored records
- `GET /api/images` - recent registry entries
- `GET /api/stats` - registry totals

## Storage behavior

- With `DATABASE_URL`: images and verifications are stored in PostgreSQL.
- Without `DATABASE_URL`: records persist in `server/data/pixelroot-store.json`.

## Notes

- Ledger receipts are currently simulated. The UI labels them accordingly.
- If geolocation is unavailable during registration, the app uses a neutral origin for the demo signature and reports that clearly in the interface.

## License

[Mozilla Public License 2.0](LICENSE).
