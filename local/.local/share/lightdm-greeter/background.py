#!/usr/bin/env python3
"""Genera el fondo del greeter: negro monocromo, rejilla tenue y viñeta.

Uso: python background.py [salida.png]
Requiere Pillow y numpy.
"""

import sys

import numpy as np
from PIL import Image

W, H = 1920, 1080
BASE = 10.0
GRID = 64
MAJOR = 320


def smoothstep(edge0, edge1, x):
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def main(out="background.png"):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)

    img = np.full((H, W), BASE, dtype=np.float32)

    # Rejilla fina y rejilla maestra, apenas visibles.
    img += np.where((x % GRID == 0), 5.0, 0.0)
    img += np.where((y % GRID == 0), 5.0, 0.0)
    img += np.where((x % MAJOR == 0), 4.0, 0.0)
    img += np.where((y % MAJOR == 0), 4.0, 0.0)

    # Viñeta radial: el centro respira, las esquinas caen a negro.
    cx, cy = W / 2.0, H / 2.0
    d = np.sqrt(((x - cx) / cx) ** 2 + ((y - cy) / cy) ** 2) / np.sqrt(2.0)
    img *= 1.0 - 0.55 * smoothstep(0.30, 1.0, d)

    # Levísimo halo central para dar profundidad a la tarjeta.
    r2 = (x - cx) ** 2 + (y - cy) ** 2
    img += 3.0 * np.exp(-r2 / (2.0 * 420.0 ** 2))

    # Dithering suave para evitar banding en el degradado.
    rng = np.random.default_rng(7)
    img += rng.uniform(-0.6, 0.6, size=(H, W))

    img = np.clip(img, 0, 255).astype(np.uint8)
    rgb = np.dstack([img, img, img])
    Image.fromarray(rgb, "RGB").save(out, optimize=True)
    print(f"escrito {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "background.png")
