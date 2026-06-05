# Manufacturing per-pixel gain control for PixelRoot — an engineering deep-dive

This note expands §"Manufacturing per-pixel gain" of the paper with device-level
detail, sourced from current CMOS-image-sensor (CIS) literature. It is paired with
the engineering schematics in `figures/`:

- `fig_gain_spectrum` — granularity vs. manufacturing technique (the design space)
- `fig_m1_dcg` — M1: dual-conversion-gain pixel
- `fig_m2_coded` — M2: coded-exposure pixel with in-pixel SRAM
- `fig_m3_stack` — M3: 3-layer stacked BSI + Cu–Cu hybrid bonding
- `fig_datapath` — where provenance-write sits in the capture pipeline

## 0. What "per-pixel gain" must do for PixelRoot

PixelRoot embeds a keyed, payload-derived chip into the captured signal *at the
sensor*. The robust channel (evaluated in `e1_robustness.py`) only needs
**per-region** gain — programmable gain applied to tiles of the array, already
within reach of column-parallel analog front-ends. **Per-pixel** gain is an
*upgrade* that additionally enables a high-resolution tamper-localization layer
(`e3_localization.py`). The manufacturing question is therefore: *how can an OEM
make each pixel's effective gain individually programmable by a 1-bit (or few-bit)
control derived from the keyed PRNG, without wrecking fill factor, noise, or
yield?* Three production-proven mechanisms answer this.

---

## M1 — Per-pixel conversion-gain selection (floating-diffusion capacitance)

**Principle.** A pixel's *conversion gain* (µV per electron) is set by the
floating-diffusion (FD) capacitance: `CG = q / C_FD`. Smaller `C_FD` → higher gain.
Modern pixels already ship a **dual-conversion-gain (DCG)** (and increasingly
**triple-CG**) transistor that switches an extra capacitor in/out of the FD node to
trade low-light sensitivity against full-well/dynamic range. See `fig_m1_dcg`.

**Provenance use.** The DCG select line is normally a global mode bit. PixelRoot
needs it to be **per-pixel addressable** so the keyed PRNG can set a different
HIGH/LOW conversion gain per carrier pixel, imprinting a faint intensity chip.

**What the OEM changes.**
1. Route the CG-select gate per pixel (or per small group) instead of globally —
   one extra in-pixel switch transistor and a select line, analogous to the
   existing transfer/row-select routing.
2. Drive the select lines from a small **in-pixel or in-column latch** loaded with
   the PRNG pattern each frame.
3. Calibrate the two CG states (factory per-device LUT) so the induced gain step is
   a known, small, recoverable Δ (a few gray levels — matching the A≈3–4 amplitude
   that `e1` shows is the imperceptible-yet-robust operating point).

**Cost/risk.** One–two extra transistors per pixel; modest pixel-pitch pressure;
the CG step must be tightly trimmed (FD capacitance varies with process). DCG/TCG
are in **volume production**, so the device physics and trimming flows already
exist; the new work is *addressing granularity*, not a new device.

---

## M2 — Per-pixel exposure/charge modulation (coded-exposure pixels)

**Principle.** Effective gain ≈ (incident flux) × (integration time) × (conversion
gain). Holding flux and CG fixed, modulating **integration time per pixel** scales
the recorded value — exactly a per-pixel multiplicative gain. "Coded-exposure" /
"per-pixel shutter" sensors add an in-pixel switch plus a **1-bit memory** that
gates whether the photodiode integrates during each sub-window. See `fig_m2_coded`.

**Provenance use.** Load each carrier pixel's keyed chip bit into its 1-bit cell;
the pixel integrates for a keyed sub-window, writing a per-pixel effective-gain chip
that is independent of its neighbours — ideal for the localization layer.

**What the OEM changes.**
1. Add the in-pixel gating switch + 1-bit SRAM/DRAM cell (global-shutter and
   coded-exposure pixels already carry in-pixel storage).
2. Provide a per-frame load path for the PRNG pattern (a shift-in or stacked
   memory plane — see M3).
3. Keep the modulation depth small and keyed so the effect is imperceptible and
   only recoverable with the OEM key.

**Cost/risk.** In-pixel memory costs area and can add dark current / FPN; mitigated
by stacking the memory under the pixel (M3). The capability is demonstrated in
research and AR/VR DPS parts (e.g., a 3-layer-stacked **400×400, 3.24 µm DPS with a
10-bit in-pixel SRAM**, ITE 2025).

---

## M3 — Stacked per-pixel processing (3D integration + Cu–Cu hybrid bonding)

**Principle.** Back-side-illuminated (BSI) sensors put photodiodes on a top wafer
and bond a second (and now third) wafer underneath carrying pixel transistors, ADCs,
SRAM, and logic. **Cu–Cu hybrid bonding** forms dense per-pixel vertical
interconnects, so arbitrary per-pixel circuitry can live *under* each pixel with **no
fill-factor penalty** — light only reaches Layer 1. See `fig_m3_stack`.

**Current numbers (grounding the feasibility claim).**
- Cu–Cu hybrid-bond **pitch ≈ 0.4 µm** (Sony 2024; imec reported 400 nm at
  IEDM 2023), enabling ~10⁶ interconnects/mm² — i.e. *per-pixel* vias at modern
  pixel pitches.
- **3-layer stacking in production/research**: 64 Mp CIS at 0.5 µm pixels with
  top = PD + transfer gate, mid = pixel transistors, bottom = analog + logic
  (IEDM 2023); 3-layer DPS with in-pixel ADC + SRAM + a logic layer hosting frame
  memory and an ISP (ITE 2025).

**Provenance use.** This is the apex realization: a **Digital Pixel Sensor** with a
per-pixel ADC and memory, plus a logic layer that can host the **keyed PRNG, the
provenance-write controller, and a hashing pre-processor** directly on-die (see
`fig_datapath`). Per-pixel gain, exposure coding, *and* the in-pixel mark all become
local digital operations.

**Cost/risk.** Highest cost (extra wafer, bonding yield, thermal/area budget), but
every constituent technology is in **high-volume manufacturing today**. PixelRoot
adds a *function* to the logic layer, not a new process node.

---

## Putting it together: the provenance-write datapath

`fig_datapath` shows the capture-time flow: the keyed PRNG (`seed = H(k‖m)`) selects
carrier pixels/regions; M1/M2/M3 apply the ±chip as a gain/exposure modulation;
the ISP reads out; SHA-256 commits `H(I‖m)`; a Merkle batch + smart contract
notarize on a public ledger. The in-pixel mark is the **soft** binding (survives
transcoding, measured in `e1`); the on-chain hash is the **hard** binding. The two
are independent security barriers (paper Props. 1–3).

**Bottom line.** Per-pixel gain control is **manufacturable with technologies
already in volume production** (DCG/TCG, in-pixel memory, 3-D stacking with 0.4 µm
hybrid bonding). The engineering gap PixelRoot asks OEMs to close is *addressing and
control* — making existing gain/exposure knobs **per-pixel programmable from a keyed
pattern** — not inventing new device physics.
