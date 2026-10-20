"""Concatenate the per-experiment outputs into results/ALL_RESULTS.txt."""
import datetime
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
FILES = ["e1_robustness.txt", "e2_security.txt", "e3_localization.txt", "e4_prnu.txt",
         "e5_crypto.txt", "e6_device_identity.txt"]
parts = ["PixelRoot — consolidated experimental results",
         f"Generated: {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M UTC}", ""]
for name in FILES:
    with open(os.path.join(OUT, name)) as f:
        parts += ["#" * 72, f.read().rstrip(), ""]
with open(os.path.join(OUT, "ALL_RESULTS.txt"), "w") as f:
    f.write("\n".join(parts) + "\n")
print("wrote results/ALL_RESULTS.txt")
