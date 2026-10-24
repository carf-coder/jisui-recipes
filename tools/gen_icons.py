"""アプリアイコン生成: 深緑地に白い椀と箸。"""
from PIL import Image, ImageDraw
from pathlib import Path
OUT = Path(__file__).resolve().parent / "docs" / "icons"
def make(size, path, radius_ratio=0.22):
    s = size * 4
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * radius_ratio), fill="#2F5E2B")
    cx, cy = s / 2, s * 0.56
    r = s * 0.30
    # 椀(下半円)
    d.pieslice([cx - r, cy - r, cx + r, cy + r], 0, 180, fill="#F4F5F0")
    # 椀の口(楕円の縁)
    d.ellipse([cx - r, cy - r * 0.16, cx + r, cy + r * 0.16], fill="#F4F5F0")
    d.ellipse([cx - r * 0.92, cy - r * 0.10, cx + r * 0.92, cy + r * 0.10], fill="#2F5E2B")
    # 高台
    d.rectangle([cx - r * 0.35, cy + r * 0.98, cx + r * 0.35, cy + r * 1.12], fill="#F4F5F0")
    # 箸(2本・斜め)
    w = s * 0.028
    for off in (-s * 0.035, s * 0.035):
        d.line([(cx - r * 1.1 + off, cy - r * 1.35), (cx + r * 0.75 + off, cy - r * 0.05)], fill="#E7B04A", width=int(w))
    im = im.resize((size, size), Image.LANCZOS)
    im.save(path)
for sz, name in [(180, "apple-touch-icon.png"), (192, "icon-192.png"), (512, "icon-512.png")]:
    make(sz, OUT / name)
    print("wrote", OUT / name)
