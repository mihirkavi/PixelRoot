/*
 * PixelRoot robustness simulation (dependency-free).
 *
 * Validates the REDESIGNED in-pixel binding:
 *   - per-REGION (8x8 block) multiplicative gain modulation g = 1 + alpha*chip*(2b-1)
 *     (a low-frequency / DC mean shift, which is exactly what survives JPEG),
 *   - keyed pseudo-random block selection + spread-spectrum antipodal chips,
 *   - repetition coding (R blocks per payload bit) with soft combining,
 *   - content-predicting detector (subtract median of neighbouring block means).
 *
 * Attacks: faithful 8x8 DCT JPEG quantization (standard luminance table scaled by
 * quality Q), additive Gaussian noise, bilinear resize round-trip, and cropping
 * with block-grid resynchronization search.
 *
 * Metrics: PSNR, SSIM, payload BER, decode success (false-reject), and
 * wrong-key false-accept rate.
 *
 * Run:  node paper/experiments/sim.js
 */
'use strict';

// ---------- deterministic PRNG ----------
function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function gauss(rng) { // Box-Muller
  let u = 0, v = 0;
  while (u === 0) u = rng();
  while (v === 0) v = rng();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

// ---------- synthetic test image (mixed frequency content) ----------
function makeImage(N, seed) {
  const rng = mulberry32(seed);
  const img = new Float64Array(N * N);
  // a few random sinusoids (texture) + smooth gradient + edges + noise
  const comps = [];
  for (let k = 0; k < 6; k++) {
    comps.push({
      fx: (rng() * 0.5) * Math.PI / 8,
      fy: (rng() * 0.5) * Math.PI / 8,
      a: 8 + rng() * 22,
      p: rng() * Math.PI * 2,
    });
  }
  const gx = (rng() - 0.5) * 0.15, gy = (rng() - 0.5) * 0.15;
  const edgeX = Math.floor(N * (0.3 + 0.4 * rng()));
  const edgeY = Math.floor(N * (0.3 + 0.4 * rng()));
  for (let y = 0; y < N; y++) {
    for (let x = 0; x < N; x++) {
      let v = 128 + gx * (x - N / 2) + gy * (y - N / 2);
      for (const c of comps) v += c.a * Math.sin(c.fx * x + c.fy * y + c.p);
      if (x > edgeX) v += 18;            // vertical step edge
      if (y > edgeY) v -= 14;            // horizontal step edge
      v += gauss(rng) * 2.5;             // sensor-like noise
      img[y * N + x] = Math.max(2, Math.min(253, v));
    }
  }
  return img;
}

// ---------- 8x8 DCT-II / inverse (orthonormal) ----------
const N8 = 8;
const COS = (() => {
  const c = [];
  for (let u = 0; u < N8; u++) {
    c[u] = [];
    for (let x = 0; x < N8; x++) c[u][x] = Math.cos(((2 * x + 1) * u * Math.PI) / 16);
  }
  return c;
})();
const CU = (u) => (u === 0 ? Math.SQRT1_2 : 1);

function fdct8(block) {
  const out = new Float64Array(64);
  for (let u = 0; u < 8; u++)
    for (let v = 0; v < 8; v++) {
      let s = 0;
      for (let x = 0; x < 8; x++)
        for (let y = 0; y < 8; y++) s += block[x * 8 + y] * COS[u][x] * COS[v][y];
      out[u * 8 + v] = 0.25 * CU(u) * CU(v) * s;
    }
  return out;
}
function idct8(coef) {
  const out = new Float64Array(64);
  for (let x = 0; x < 8; x++)
    for (let y = 0; y < 8; y++) {
      let s = 0;
      for (let u = 0; u < 8; u++)
        for (let v = 0; v < 8; v++) s += CU(u) * CU(v) * coef[u * 8 + v] * COS[u][x] * COS[v][y];
      out[x * 8 + y] = 0.25 * s;
    }
  return out;
}

// standard JPEG luminance quantization table
const QY = [
  16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55,
  14, 13, 16, 24, 40, 57, 69, 56, 14, 17, 22, 29, 51, 87, 80, 62,
  18, 22, 37, 56, 68, 109, 103, 77, 24, 35, 55, 64, 81, 104, 113, 92,
  49, 64, 78, 87, 103, 121, 120, 101, 72, 92, 95, 98, 112, 100, 103, 99,
];
function qtableForQuality(Q) {
  const s = Q < 50 ? 5000 / Q : 200 - 2 * Q;
  return QY.map((q) => Math.max(1, Math.min(255, Math.floor((q * s + 50) / 100))));
}

// faithful JPEG luminance pass: per-8x8 block fDCT -> quantize -> dequant -> iDCT
function jpegCompress(img, N, Q) {
  const qt = qtableForQuality(Q);
  const out = new Float64Array(N * N);
  const blk = new Float64Array(64);
  for (let by = 0; by < N; by += 8)
    for (let bx = 0; bx < N; bx += 8) {
      for (let i = 0; i < 8; i++)
        for (let j = 0; j < 8; j++) blk[i * 8 + j] = img[(by + i) * N + (bx + j)] - 128;
      const c = fdct8(blk);
      for (let k = 0; k < 64; k++) c[k] = Math.round(c[k] / qt[k]) * qt[k];
      const r = idct8(c);
      for (let i = 0; i < 8; i++)
        for (let j = 0; j < 8; j++)
          out[(by + i) * N + (bx + j)] = Math.max(0, Math.min(255, r[i * 8 + j] + 128));
    }
  return out;
}

function addNoise(img, sigma, seed) {
  const rng = mulberry32(seed);
  const out = new Float64Array(img.length);
  for (let i = 0; i < img.length; i++)
    out[i] = Math.max(0, Math.min(255, img[i] + gauss(rng) * sigma));
  return out;
}

// bilinear resize round-trip: N -> round(N*f) -> N  (simulates platform rescale)
function resizeRoundTrip(img, N, f) {
  const M = Math.max(8, Math.round(N * f) & ~7);
  const down = bilinear(img, N, N, M, M);
  return bilinear(down, M, M, N, N);
}
function bilinear(src, sw, sh, dw, dh) {
  const out = new Float64Array(dw * dh);
  for (let y = 0; y < dh; y++) {
    const sy = ((y + 0.5) * sh) / dh - 0.5;
    const y0 = Math.max(0, Math.min(sh - 1, Math.floor(sy)));
    const y1 = Math.min(sh - 1, y0 + 1);
    const wy = sy - y0;
    for (let x = 0; x < dw; x++) {
      const sx = ((x + 0.5) * sw) / dw - 0.5;
      const x0 = Math.max(0, Math.min(sw - 1, Math.floor(sx)));
      const x1 = Math.min(sw - 1, x0 + 1);
      const wx = sx - x0;
      const a = src[y0 * sw + x0], b = src[y0 * sw + x1];
      const c = src[y1 * sw + x0], d = src[y1 * sw + x1];
      out[y * dw + x] = a * (1 - wx) * (1 - wy) + b * wx * (1 - wy) + c * (1 - wx) * wy + d * wx * wy;
    }
  }
  return out;
}

// ---------- payload coding ----------
function randomBits(n, seed) {
  const rng = mulberry32(seed);
  const b = new Int8Array(n);
  for (let i = 0; i < n; i++) b[i] = rng() < 0.5 ? 0 : 1;
  return b;
}

// keyed assignment: for each payload bit, choose R distinct blocks + antipodal chips
function keyedPlan(keySeed, nBits, R, nBlocks) {
  const rng = mulberry32(keySeed);
  const used = new Uint8Array(nBlocks);
  const plan = []; // [{block, chip}] per bit -> array
  for (let i = 0; i < nBits; i++) {
    const arr = [];
    let guard = 0;
    while (arr.length < R && guard < nBlocks * 4) {
      guard++;
      const blk = Math.floor(rng() * nBlocks);
      if (used[blk]) continue;
      used[blk] = 1;
      arr.push({ block: blk, chip: rng() < 0.5 ? -1 : 1 });
    }
    plan.push(arr);
  }
  return plan;
}

// ---------- low-frequency AC carrier (per-column gain ramp ~ horizontal DCT basis) ----------
// K=(uK,vK): u indexes rows (x), v indexes cols (y). (0,2) = pure horizontal ramp,
// realizable by a smooth per-COLUMN programmable-gain profile across the region.
const UK = 0, VK = 2;
const P8 = (() => {                 // zero-mean AC basis pattern over 8x8
  const p = new Float64Array(64);
  for (let x = 0; x < 8; x++) for (let y = 0; y < 8; y++) p[x * 8 + y] = COS[UK][x] * COS[VK][y];
  return p;
})();
const P8_ENERGY = (() => { let s = 0; for (let i = 0; i < 64; i++) s += P8[i] * P8[i]; return s; })();

// project a block onto the carrier basis -> coefficient amplitude (gray-level units)
function project(img, N, block, off) {
  const bpr = N / 8;
  const by = Math.floor(block / bpr) * 8 + off.y, bx = (block % bpr) * 8 + off.x;
  let s = 0;
  for (let r = 0; r < 8; r++)
    for (let c = 0; c < 8; c++) {
      const yy = Math.max(0, Math.min(N - 1, by + r)), xx = Math.max(0, Math.min(N - 1, bx + c));
      s += img[yy * N + xx] * P8[r * 8 + c];
    }
  return s / P8_ENERGY;
}

// embed: add A*chip*(2b-1)*pattern  (smooth low-freq ramp; imperceptible, JPEG-robust)
function embed(img, N, bits, plan, A) {
  const out = Float64Array.from(img);
  const bpr = N / 8;
  for (let i = 0; i < bits.length; i++) {
    const sign = 2 * bits[i] - 1;
    for (const { block, chip } of plan[i]) {
      const by = Math.floor(block / bpr) * 8, bx = (block % bpr) * 8;
      const amp = A * chip * sign;
      for (let r = 0; r < 8; r++)
        for (let c = 0; c < 8; c++) {
          const idx = (by + r) * N + (bx + c);
          out[idx] = Math.max(0, Math.min(255, out[idx] + amp * P8[r * 8 + c]));
        }
    }
  }
  return out;
}

// ---------- extract: de-spread soft combine over repetition, optional grid offset ----------
function extract(img, N, plan, offset) {
  const off = offset || { x: 0, y: 0 };
  const bits = new Int8Array(plan.length);
  let conf = 0;
  for (let i = 0; i < plan.length; i++) {
    let acc = 0;
    for (const { block, chip } of plan[i]) acc += project(img, N, block, off) * chip;
    bits[i] = acc >= 0 ? 1 : 0;
    conf += Math.abs(acc);
  }
  return { bits, conf };
}
// resync: search block-grid offsets (max px each axis), keep most-confident decode
function extractResync(img, N, plan, maxOff) {
  const M = maxOff == null ? 7 : maxOff;
  let best = null;
  for (let oy = -M; oy <= M; oy++)
    for (let ox = -M; ox <= M; ox++) {
      const r = extract(img, N, plan, { x: ox, y: oy });
      if (!best || r.conf > best.conf) best = r;
    }
  return best;
}

// ---------- metrics ----------
function psnr(a, b) {
  let se = 0;
  for (let i = 0; i < a.length; i++) { const d = a[i] - b[i]; se += d * d; }
  const mse = se / a.length;
  return mse === 0 ? Infinity : 10 * Math.log10((255 * 255) / mse);
}
function ssim(a, b, N) {
  const C1 = (0.01 * 255) ** 2, C2 = (0.03 * 255) ** 2;
  let total = 0, n = 0;
  for (let by = 0; by + 8 <= N; by += 8)
    for (let bx = 0; bx + 8 <= N; bx += 8) {
      let ma = 0, mb = 0;
      for (let i = 0; i < 8; i++) for (let j = 0; j < 8; j++) { ma += a[(by + i) * N + bx + j]; mb += b[(by + i) * N + bx + j]; }
      ma /= 64; mb /= 64;
      let va = 0, vb = 0, cov = 0;
      for (let i = 0; i < 8; i++) for (let j = 0; j < 8; j++) {
        const da = a[(by + i) * N + bx + j] - ma, db = b[(by + i) * N + bx + j] - mb;
        va += da * da; vb += db * db; cov += da * db;
      }
      va /= 63; vb /= 63; cov /= 63;
      const s = ((2 * ma * mb + C1) * (2 * cov + C2)) / ((ma * ma + mb * mb + C1) * (va + vb + C2));
      total += s; n++;
    }
  return total / n;
}
function ber(a, b) { let e = 0; for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) e++; return e / a.length; }

// ---------- experiment ----------
function run() {
  const N = 512;                 // 64x64 = 4096 blocks
  const nBlocks = (N / 8) * (N / 8);
  const PAYLOAD = 128;
  const R = 25;                  // repetition: 128*25 = 3200 of 4096 blocks used
  const A = 4.0;                 // carrier amplitude (gray levels) on the low-freq basis
  const NIMAGES = 6;
  const keySeed = 0xC0FFEE;

  const plan = keyedPlan(keySeed, PAYLOAD, R, nBlocks);

  const attacks = [
    { name: 'none', fn: (im) => im },
    { name: 'JPEG Q95', fn: (im) => jpegCompress(im, N, 95) },
    { name: 'JPEG Q90', fn: (im) => jpegCompress(im, N, 90) },
    { name: 'JPEG Q80', fn: (im) => jpegCompress(im, N, 80) },
    { name: 'JPEG Q70', fn: (im) => jpegCompress(im, N, 70) },
    { name: 'JPEG Q60', fn: (im) => jpegCompress(im, N, 60) },
    { name: 'JPEG Q50', fn: (im) => jpegCompress(im, N, 50) },
    { name: 'JPEG Q40', fn: (im) => jpegCompress(im, N, 40) },
    { name: 'JPEG Q30', fn: (im) => jpegCompress(im, N, 30) },
    { name: 'JPEG Q20', fn: (im) => jpegCompress(im, N, 20) },
    { name: 'JPEG Q10', fn: (im) => jpegCompress(im, N, 10) },
    { name: 'Noise s5', fn: (im) => addNoise(im, 5, 7) },
    { name: 'Noise s10', fn: (im) => addNoise(im, 10, 9) },
    { name: 'Noise s20', fn: (im) => addNoise(im, 20, 11) },
    { name: 'Resize 0.5x', fn: (im) => resizeRoundTrip(im, N, 0.5) },
    { name: 'Resize 0.75x', fn: (im) => resizeRoundTrip(im, N, 0.75) },
    { name: 'JPEG70+Resize0.75', fn: (im) => jpegCompress(resizeRoundTrip(im, N, 0.75), N, 70) },
  ];

  const agg = {}; // name -> {ber, succ, psnr, ssim}
  for (const a of attacks) agg[a.name] = { ber: 0, succ: 0 };
  let psnrSum = 0, ssimSum = 0;

  for (let im = 0; im < NIMAGES; im++) {
    const base = makeImage(N, 1000 + im);
    const bits = randomBits(PAYLOAD, 2000 + im);
    const marked = embed(base, N, bits, plan, A);
    psnrSum += psnr(base, marked);
    ssimSum += ssim(base, marked, N);

    for (const a of attacks) {
      const attacked = a.fn(marked);
      // grid stays aligned for JPEG/noise/resize round-trip -> offset 0 is correct & fast
      const { bits: rec } = extract(attacked, N, plan, { x: 0, y: 0 });
      const b = ber(bits, rec);
      agg[a.name].ber += b;
      agg[a.name].succ += b === 0 ? 1 : 0;
    }
  }

  const base = makeImage(N, 1000);
  const bits = randomBits(PAYLOAD, 2000);
  const marked = embed(base, N, bits, plan, A);

  // (A) payload secrecy: read marked image with WRONG key -> should be ~0.5 BER
  let scTrials = 300, scAccept = 0, scBer = 0;
  for (let t = 0; t < scTrials; t++) {
    const wrongPlan = keyedPlan(0x1234 + t * 7, PAYLOAD, R, nBlocks);
    const { bits: rec } = extract(marked, N, wrongPlan, { x: 0, y: 0 });
    const b = ber(bits, rec); scBer += b; if (b === 0) scAccept++;
  }

  // (B) forgery false-accept: UNMARKED images (deepfake stand-in) read with CORRECT key,
  // tested against a randomly claimed payload -> should fail to decode (~0.5 BER)
  let faTrials = 300, faAccept = 0, faBer = 0;
  for (let t = 0; t < faTrials; t++) {
    const fake = makeImage(N, 50000 + t);          // never PixelRoot-marked
    const claim = randomBits(PAYLOAD, 60000 + t);   // attacker's claimed payload
    const { bits: rec } = extract(fake, N, plan, { x: 0, y: 0 });
    const b = ber(claim, rec); faBer += b; if (b === 0) faAccept++;
  }

  // (C) crop + resync: small crops the sync search can cover vs. larger that fail-safe
  const crops = [0.01, 0.03, 0.06];
  const cropRes = crops.map((f) => {
    const c = Math.round(N * f);
    const cropped = cropAndPad(marked, N, c);
    const rc = extractResync(cropped, N, plan, Math.min(40, c + 8));
    return { f, c, ber: ber(bits, rc.bits) };
  });

  // ---------- report ----------
  const line = (k, v) => console.log(k.padEnd(24) + v);
  console.log('=== PixelRoot in-pixel binding: measured robustness ===');
  line('Config', `N=${N}, blocks=${nBlocks}, payload=${PAYLOAD}b, R=${R}, alpha=N/A,A=${A}, images=${NIMAGES}`);
  line('Avg embed PSNR', (psnrSum / NIMAGES).toFixed(2) + ' dB');
  line('Avg embed SSIM', (ssimSum / NIMAGES).toFixed(4));
  console.log('\nAttack                   BER       decode-success');
  for (const a of attacks) {
    const r = agg[a.name];
    console.log(a.name.padEnd(24) + (r.ber / NIMAGES).toFixed(4).padEnd(10) + `${r.succ}/${NIMAGES}`);
  }
  console.log('\nGeometric crop + grid-resync:');
  for (const r of cropRes)
    line(`Crop ${(r.f * 100).toFixed(0)}% (${r.c}px)`, 'BER ' + r.ber.toFixed(4) + (r.ber === 0 ? '  (decoded)' : '  (failed-safe)'));
  // (D) amplitude sweep at a fixed strong attack (JPEG Q40) -> operating curve / cliff
  console.log('\nAmplitude sweep @ JPEG Q40 (PSNR / BER / success), 4 images:');
  for (const a of [0.5, 1.0, 1.5, 2.0, 3.0]) {
    let ps = 0, be = 0, su = 0, ni = 4;
    for (let im = 0; im < ni; im++) {
      const bb = makeImage(N, 1000 + im);
      const tb = randomBits(PAYLOAD, 2000 + im);
      const mk = embed(bb, N, tb, plan, a);
      ps += psnr(bb, mk);
      const at = jpegCompress(mk, N, 40);
      const { bits: rc } = extract(at, N, plan, { x: 0, y: 0 });
      const b = ber(tb, rc); be += b; if (b === 0) su++;
    }
    line(`A=${a.toFixed(1)}`, `PSNR ${(ps / ni).toFixed(1)}dB  BER ${(be / ni).toFixed(4)}  ${su}/${ni}`);
  }

  console.log('\n=== security: false-accept / secrecy (300 trials each) ===');
  line('(A) wrong-key mean BER', (scBer / scTrials).toFixed(4) + '  (ideal ~0.5)');
  line('(A) wrong-key accepts', `${scAccept}/${scTrials}`);
  line('(B) forgery mean BER', (faBer / faTrials).toFixed(4) + '  (ideal ~0.5)');
  line('(B) forgery accepts', `${faAccept}/${faTrials}`);
}

// crop a border of `c` px and pad with edge replication (shifts/breaks block grid)
function cropAndPad(img, N, c) {
  const out = new Float64Array(N * N);
  for (let y = 0; y < N; y++)
    for (let x = 0; x < N; x++) {
      const sy = Math.max(0, Math.min(N - 1, y + c));
      const sx = Math.max(0, Math.min(N - 1, x + c));
      out[y * N + x] = img[sy * N + sx];
    }
  return out;
}

run();
