"""Generates the soft gradient artwork used by the UI (frontend/img/hero.jpg, banner.jpg).
To use REAL photos instead, just overwrite those two files with your own images (same names)."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

OUT = Path(__file__).resolve().parents[1] / "frontend" / "img"
OUT.mkdir(parents=True, exist_ok=True)

def mesh(w, h, colors, seed, blobs=7):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w]
    img = np.zeros((h, w, 3), float) + np.array(colors[0], float)
    for _ in range(blobs):
        cx, cy, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(.25, .6) * max(w, h)
        c = np.array(colors[rng.integers(1, len(colors))], float)
        a = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * (r / 2) ** 2)))[..., None]
        img = img * (1 - a * .85) + c * a * .85
    img += rng.normal(0, 3, img.shape)
    return Image.fromarray(np.clip(img, 0, 255).astype("uint8")).filter(ImageFilter.GaussianBlur(2))

palette = [(8, 28, 40), (14, 124, 123), (43, 108, 176), (95, 208, 201), (20, 60, 90), (235, 245, 244)]
mesh(1600, 1100, palette[:5], 11).save(OUT / "hero.jpg", quality=90)
mesh(1500, 360, palette[:5], 5, 6).save(OUT / "banner.jpg", quality=90)
print("images saved to", OUT)