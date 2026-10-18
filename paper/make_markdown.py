"""Regenerate pixelroot.md (readable Markdown copy) from pixelroot.tex with pandoc."""
import re
import subprocess
import tempfile

src = open("pixelroot.tex").read()
pre = src.replace("\\pr{}", "PixelRoot").replace("\\IEEEPARstart{D}{igital}", "Digital")


def pandoc(args, text=None):
    return subprocess.run(["pandoc", "--from", "latex", "--to", "gfm", "--wrap=none"] + args,
                          input=text, capture_output=True, text=True, check=True).stdout


with tempfile.NamedTemporaryFile("w", suffix=".tex", dir=".", delete=True) as f:
    f.write(pre)
    f.flush()
    body = pandoc([f.name, "--citeproc", "--bibliography=references.bib"])
body = body[body.index("# Introduction"):]
abstract = pandoc([], pre[pre.index("\\begin{abstract}") + 16:pre.index("\\end{abstract}")]).strip()
kw = " ".join(pre[pre.index("\\begin{IEEEkeywords}") + 20:pre.index("\\end{IEEEkeywords}")].split())
head = f"""# PixelRoot: Hardware-Anchored, Sensor-Level Media Provenance with Real-Time Blockchain Notarization for Trustworthy Imaging

**Mihir Kavishwar** — PixelRoot Project — hello@mihirkavishwar.com

> Markdown rendering of the manuscript, generated from `pixelroot.tex` by
> `make_markdown.py` (pandoc); figures, algorithms and the contract listing are
> omitted or simplified. The authoritative version is `pixelroot.tex` / `pixelroot.pdf`.

## Abstract

{abstract}

**Index terms:** {kw}

---

"""
md = head + body
for _ in range(2):
    md = re.sub(r'<span class="(?:upright|smallcaps)">(.*?)</span>', r"\1", md)
open("pixelroot.md", "w").write(md)
print(f"wrote pixelroot.md ({len(md.splitlines())} lines)")
