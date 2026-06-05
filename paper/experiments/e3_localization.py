"""
E3 -- Per-pixel tamper-localization layer on REAL images (Kodak). Validates C9.

Protocol (active-watermark localization):
  1. Embed a keyed +/-delta per-pixel pattern into a genuine image.
  2. An adversary splices a foreign region (copied from another real image) into
     it, overwriting the pattern there. Masks: random rectangles + ellipses of
     varied size/position (with pixel-level ground truth).
  3. Verifier computes the per-block matched-filter statistic and flags blocks.

Metrics follow the forgery-localization literature (CASIA/Columbia/IMD2020):
pixel-level F1, permutation p-F1, IoU, and ROC-AUC. Reported on pristine media and
after JPEG Q90 (graceful degradation). Granularity = block size (32 px).

Outputs: results/e3_localization.txt, results/e3_roc.csv
"""
import glob, os, csv
import numpy as np
import pixelroot as pr

DATA = sorted(glob.glob(os.path.join(os.path.dirname(__file__), "data/kodak/*.png")))
OUT = os.path.join(os.path.dirname(__file__), "results"); os.makedirs(OUT, exist_ok=True)
DELTA = 4.0
BS = 32
KEY = "PIXELROOT-LOCALIZE-KEY"

def make_mask(H, W, kind, rng):
    m = np.zeros((H, W), dtype=bool)
    if kind == "rect":
        rh, rw = rng.randint(H // 8, H // 3), rng.randint(W // 8, W // 3)
        y0, x0 = rng.randint(0, H - rh), rng.randint(0, W - rw)
        m[y0:y0 + rh, x0:x0 + rw] = True
    else:  # ellipse
        ry, rx = rng.randint(H // 10, H // 4), rng.randint(W // 10, W // 4)
        cy, cx = rng.randint(ry, H - ry), rng.randint(rx, W - rx)
        yy, xx = np.ogrid[:H, :W]
        m[((yy - cy) / ry) ** 2 + ((xx - cx) / rx) ** 2 <= 1.0] = True
    return m

def block_labels(mask, bs):
    H, W = mask.shape
    nbh, nbw = H // bs, W // bs
    mb = mask[: nbh * bs, : nbw * bs].reshape(nbh, bs, nbw, bs).transpose(0, 2, 1, 3)
    return mb.mean(axis=(2, 3)) > 0.5  # block is tampered if majority pixels tampered

def roc_auc(scores, labels):
    order = np.argsort(-scores)
    s, l = scores[order], labels[order].astype(int)
    P, N = l.sum(), (1 - l).sum()
    if P == 0 or N == 0:
        return float("nan"), [], []
    tpr, fpr = [], []
    tp = fp = 0
    for li in l:
        if li: tp += 1
        else: fp += 1
        tpr.append(tp / P); fpr.append(fp / N)
    auc = np.trapz(tpr, fpr)
    return float(auc), fpr, tpr

def f1_iou(pred, gt):
    tp = np.sum(pred & gt); fp = np.sum(pred & ~gt); fn = np.sum(~pred & gt)
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    iou = tp / (tp + fp + fn) if (tp + fp + fn) else 0.0
    return f1, iou

def evaluate(jpeg_q=None):
    all_scores, all_labels = [], []
    pix_pred, pix_gt = [], []
    rng = np.random.RandomState(123)
    for idx, path in enumerate(DATA):
        rgb = pr.load_rgb(path)
        H, W, _ = rgb.shape
        marked, pat = pr.embed_fragile_rgb(rgb, KEY, DELTA)
        foreign = pr.load_rgb(DATA[(idx + 7) % len(DATA)])
        fh, fw = min(H, foreign.shape[0]), min(W, foreign.shape[1])
        for kind in ["rect", "ellipse"]:
            mask = make_mask(fh, fw, kind, rng)
            tampered = marked[:fh, :fw].copy()
            tampered[mask] = np.clip(np.round(foreign[:fh, :fw][mask]), 0, 255).astype(np.uint8)
            if jpeg_q is not None:
                tampered = pr.att_jpeg(tampered, jpeg_q)[:fh, :fw]
            y = pr.rgb_to_y(tampered.astype(np.float64))
            stat = pr.fragile_block_stat(y, pat[:fh, :fw], BS)
            labels = block_labels(mask, BS)
            score = DELTA - stat            # higher score => more likely tampered
            all_scores.append(score.ravel()); all_labels.append(labels.ravel())
            # pixel-level prediction at operating threshold (stat < delta/2 => tampered)
            pred_blk = stat < (DELTA * 0.5)
            pred_pix = np.kron(pred_blk, np.ones((BS, BS), dtype=bool))
            gt_pix = mask[: pred_pix.shape[0], : pred_pix.shape[1]]
            ph, pw = min(pred_pix.shape[0], gt_pix.shape[0]), min(pred_pix.shape[1], gt_pix.shape[1])
            pix_pred.append(pred_pix[:ph, :pw].ravel()); pix_gt.append(gt_pix[:ph, :pw].ravel())
    scores = np.concatenate(all_scores); labels = np.concatenate(all_labels)
    auc, fpr, tpr = roc_auc(scores, labels)
    pp = np.concatenate(pix_pred); pg = np.concatenate(pix_gt)
    f1, iou = f1_iou(pp, pg)
    f1_inv, _ = f1_iou(~pp, pg)
    pf1 = max(f1, f1_inv)
    # block-level TPR/FPR at operating threshold
    blk_pred = scores > (DELTA * 0.5)
    tp = np.sum(blk_pred & (labels == 1)); fn = np.sum(~blk_pred & (labels == 1))
    fp = np.sum(blk_pred & (labels == 0)); tn = np.sum(~blk_pred & (labels == 0))
    btpr = tp / (tp + fn); bfpr = fp / (fp + tn)
    return dict(auc=auc, f1=f1, pf1=pf1, iou=iou, btpr=btpr, bfpr=bfpr, fpr=fpr, tpr=tpr)

def main():
    pristine = evaluate(jpeg_q=None)
    jpeg = evaluate(jpeg_q=90)
    L = []
    L.append("=== E3: per-pixel tamper localization on REAL images (Kodak) ===")
    L.append(f"delta={DELTA}, block={BS}px, trials={len(DATA)*2} (rect+ellipse splices)")
    L.append(f"metrics follow forgery-localization literature (pixel-F1, p-F1, IoU, AUC)")
    L.append("")
    for tag, r in [("Pristine", pristine), ("After JPEG Q90", jpeg)]:
        L.append(f"[{tag}]")
        L.append(f"   ROC-AUC (block)        = {r['auc']:.4f}")
        L.append(f"   Pixel-F1               = {r['f1']:.4f}")
        L.append(f"   p-F1 (permutation)     = {r['pf1']:.4f}")
        L.append(f"   Pixel-IoU              = {r['iou']:.4f}")
        L.append(f"   Block TPR / FPR @thr   = {r['btpr']:.3f} / {r['bfpr']:.3f}")
        L.append("")
    txt = "\n".join(L)
    print(txt)
    with open(os.path.join(OUT, "e3_localization.txt"), "w") as f:
        f.write(txt + "\n")
    with open(os.path.join(OUT, "e3_roc.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["fpr", "tpr"])
        for a, b in zip(pristine["fpr"], pristine["tpr"]):
            w.writerow([f"{a:.5f}", f"{b:.5f}"])

if __name__ == "__main__":
    main()
