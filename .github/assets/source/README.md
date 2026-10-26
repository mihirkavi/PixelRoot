# Banner source

`banner.html` is the self-contained source of `../banner-light.png` and `../banner-dark.png`. It uses Google Fonts CSS shapes and a few lines of inline script, and switches palettes with `prefers-color-scheme`.

## Re-render

With Playwright's Chromium available, render at 1600 × 600 and 2× scale, once per color scheme (the README kit's `render-html.mjs` does this):

```bash
node "$KIT/render-html.mjs" .github/assets/source/banner.html .github/assets/banner-light.png --scheme light
node "$KIT/render-html.mjs" .github/assets/source/banner.html .github/assets/banner-dark.png --scheme dark
```

## Notes for agents

- Keep the "illustrative" and "simulated in software only" captions: no sensor hardware exists, and the console itself does not embed anything in pixels. The mosaic is drawn by a small inline script, so render with JavaScript enabled.
- Colors and fonts are documented in [`../README.md`](../README.md). Check both PNGs for overflow after any edit.
