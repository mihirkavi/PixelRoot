# README images

Images used by the root [README](../../README.md) of PixelRoot. They are presentation assets only; the app does not load them.

## Files

| File | What it is |
| --- | --- |
| `banner-light.png`, `banner-dark.png` | Title banner for light and dark GitHub themes, rendered from [`source/banner.html`](source/banner.html) with headless Chromium |
| `hero.jpg` | Framed desktop and phone screenshot used at the top of the README |
| `screenshots/verify-match.jpg`, `verify-edited.jpg`, `overview.jpg` | Console views: a successful verification, a rejected one-pixel edit, and the overview |
| `api-terminal.png` | A real terminal transcript of the health and verify endpoints, rendered as an image |

## Visual identity

PixelRoot's README reads like a **forensic figure** from its paper: a synthetic landscape with a selected patch, magnified through a loupe into a Bayer (RGGB) sensor mosaic in which a few cells carry identifier bits, captioned "illustrative" and "simulated in software only". The console's four steps (capture, sign, register, verify) run along the bottom.

- **Fonts:** Space Grotesk for headlines and IBM Plex Mono for labels, the same pair the console loads in `client/index.html`.
- **Colors:** from `client/src/styles.css`: paper `#f5f1e8`, ink `#162126`, deep teal `#0d3b3c`, teal `#0d7c86` and copper `#b3653b`, on the console's 42 px grid. The dark banner uses `#0b1d1e` with teal `#37aab4` and copper `#e59a68`.
- **Badges** use `0d3b3c`, `0d7c86`, `162126` and `b3653b`. Section headers use plain numbers instead of emoji, in keeping with a research project.
- **Re-render:** see [`source/README.md`](source/README.md).

## How they were made

Captured on 2026-10-26 from the console running locally from this repository (`npm run build`, then `PORT=5123 npm start`) with headless Chromium. The registry was seeded with three synthetic, computer-generated landscape images (gradients and shapes, no real photos); the edited copy differs by one pixel. The terminal transcript is the real output of the commands shown. Screenshots are framed in a browser window or phone outline by a small Playwright script, then saved as JPEG.

## Notes for agents

- Screenshots must show only public pages or demo data, never personal, financial or health information.
- Keep names lowercase with hyphens. When you replace an image, keep its file name so README links keep working, and update this table.
- Retake screenshots after visible interface changes so the README stays truthful.
