# PixelRoot

<p><img src="assets/brand/logo.png" alt="PixelRoot logo" width="96" height="96"></p>

PixelRoot is an image provenance project with two parts: a working web console for registering images and verifying them against a provenance registry, and a research manuscript proposing hardware-anchored, sensor-level provenance with blockchain notarization.

## Overview

The console (React front end, Express API) lets an operator register an image, which creates a provenance record with a SHA-256-based signature, and later verify an uploaded image against stored records. The `paper/` directory contains the PixelRoot manuscript (IEEE-format LaTeX, plus a Markdown rendering) and the Python experiments that produce its measured results.

## Features

- Image registration and verification against a provenance registry, with a browsable list of recent entries and registry totals
- Storage that falls back to persistent local file storage when `DATABASE_URL` is not set
- A health API that reports storage mode, upload limits, and the active signature algorithm
- Provenance algorithm `v2` by default, with explicit support for verifying legacy `v1` records
- In-memory upload processing, async file writes, and cleanup on failed persistence
- An operations-style UI with system status, mobile layout, and explicit labeling that blockchain receipts are simulated

## Stack

- Frontend: React 19 + Vite
- Backend: Express 5
- Storage: PostgreSQL when `DATABASE_URL` is set, otherwise a local JSON-backed store
- Media persistence: local `uploads/`

## Project structure

```text
client/              React 19 + Vite front end
server/              Express API, provenance algorithm, storage, tests
paper/               Manuscript (pixelroot.tex, pixelroot.md, pixelroot.pdf), references, figures
paper/experiments/   Python experiments, figure generation, and recorded results
paper/submission/    Submission bundle materials
assets/brand/        Logo and project artwork
```

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

## Configuration

Environment variables (all optional): `DATABASE_URL`, `HOST` (default `127.0.0.1`), `PORT` (default `5000`).

## Research experiments

The experiments in `paper/experiments/` use the public Kodak image set. See [EXPERIMENT_PLAN.md](paper/experiments/EXPERIMENT_PLAN.md) for the claims they test.

```bash
cd paper/experiments
pip install -r requirements.txt
./fetch_data.sh          # download the Kodak images
python3 e1_robustness.py # likewise e2_security.py ... e5_crypto.py
python3 make_figures.py
```

## Notes

- Ledger receipts are currently simulated. The UI labels them accordingly.
- If geolocation is unavailable during registration, the app uses a neutral origin for the demo signature and reports that clearly in the interface.

## License

[Mozilla Public License 2.0](LICENSE).

<!-- project-artwork:start -->
## Project artwork

![Conceptual artwork for PixelRoot](assets/brand/cover.png)

Conceptual project artwork. [Asset files, design notes, and generation prompts](assets/brand/README.md).
<!-- project-artwork:end -->
