"""Generate the 'Adventure Pop' 3D LUT: punchy action-cam look with deep cyan-blue
skies, olive tropical greens, warm skin and lifted, detailed shadows."""
import numpy as np

N = 33

def rgb_to_hsv(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn
    h = np.zeros_like(mx)
    m = d > 1e-6
    rm = m & (mx == r); gm = m & (mx == g) & ~rm; bm = m & ~rm & ~gm
    h[rm] = ((g - b)[rm] / d[rm]) % 6
    h[gm] = (b - r)[gm] / d[gm] + 2
    h[bm] = (r - g)[bm] / d[bm] + 4
    h = h * 60.0
    s = np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0)
    return np.stack([h, s, mx], -1)

def hsv_to_rgb(hsv):
    h, s, v = hsv[..., 0] % 360, hsv[..., 1], hsv[..., 2]
    c = v * s
    x = c * (1 - np.abs((h / 60) % 2 - 1))
    z = np.zeros_like(h)
    i = (h // 60).astype(int)
    conds = [(c, x, z), (x, c, z), (z, c, x), (z, x, c), (x, z, c), (c, z, x)]
    out = np.zeros(h.shape + (3,))
    for k, (a, b2, c2) in enumerate(conds):
        sel = i == k
        out[sel] = np.stack([a, b2, c2], -1)[sel]
    return out + (v - c)[..., None]

def band(h, center, width):
    """Smooth 0..1 weight for hues near center (degrees)."""
    d = np.abs((h - center + 180) % 360 - 180)
    return np.clip(1 - d / width, 0, 1) ** 2

def tone(x):
    # brighter mids, deep blacks, strong S-curve contrast
    x = 0.008 + np.clip(x, 0, 1) ** 0.9 * 0.985   # brighten mids, keep blacks deep
    s = x + 0.30 * (x - 0.5) * (1 - np.abs(2 * x - 1)) * 2     # strong mid-contrast S-curve
    return np.clip(s, 0, 1)

def grade(rgb):
    rgb = rgb.copy()
    # slight warm white balance
    rgb[..., 0] *= 1.045; rgb[..., 1] *= 1.01; rgb[..., 2] *= 0.95
    rgb = np.clip(rgb, 0, 1)
    rgb = tone(rgb)

    hsv = rgb_to_hsv(rgb)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]

    # greens -> olive/yellow-green, a touch darker and calmer
    wg = band(h, 115, 50)
    h = h - 4 * wg
    s = s * (1 + 0.05 * wg)

    # skies -> deeper cyan-blue
    wb = band(h, 212, 40)
    h = h + (216 - h) * 0.5 * wb
    s = s * (1 + 0.50 * wb)
    v = v * (1 - 0.03 * wb)

    # skin / oranges -> warm and healthy
    wo = band(h, 28, 22)
    s = s * (1 + 0.08 * wo)

    # vibrance: boost muted colours more than already-saturated ones
    s = s + 0.45 * s * (1 - s)
    s = np.clip(s, 0, 1)

    rgb = hsv_to_rgb(np.stack([h, s, np.clip(v, 0, 1)], -1))

    # subtle split tone: neutral-warm shadows, golden highlights
    lum = (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2])[..., None]
    sh = np.clip(1 - lum * 2.2, 0, 1); hi = np.clip(lum * 2 - 1, 0, 1)
    rgb = rgb + sh * np.array([0.004, 0.002, -0.002]) + hi * np.array([0.015, 0.006, -0.012])
    return np.clip(rgb, 0, 1)

if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "adventure_pop.cube"
    g = np.linspace(0, 1, N)
    # .cube order: red varies fastest
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")
    grid = np.stack([r, gg, b], -1).reshape(-1, 3)
    res = grade(grid)
    with open(out, "w") as f:
        f.write('TITLE "Adventure Pop"\nLUT_3D_SIZE %d\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n' % N)
        for p in res:
            f.write("%.6f %.6f %.6f\n" % tuple(p))
    print("wrote", out)
