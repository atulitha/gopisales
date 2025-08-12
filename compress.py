import os
from pathlib import Path
from PIL import Image, ImageOps

# -------- Config --------
SRC_DIR        = Path("images")
OUT_DIR        = Path("images_optimized")        # hi-res optimized
THUMB_DIR      = OUT_DIR / "thumbs"              # low-res thumbs for blur-up
MAX_WIDTH_HI   = 1600                            # downscale if wider (keeps aspect)
THUMB_WIDTH    = 400                             # small, fast thumbnails
JPEG_QUALITY   = 85                              # visually lossless range 80–88
WEBP_QUALITY   = 80                              # optional WebP copies
MAKE_WEBP      = True                            # set False to skip WebP
STRIP_EXIF     = True

SUPPORTED = (".jpg", ".jpeg", ".png")

def ensure_dirs():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    THUMB_DIR.mkdir(parents=True, exist_ok=True)

def strip_exif(img: Image.Image) -> Image.Image:
    # Convert to no-metadata RGB
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    data = list(img.getdata())
    out = Image.new(img.mode, img.size)
    out.putdata(data)
    return out

def save_jpeg(img: Image.Image, path: Path, quality=JPEG_QUALITY):
    params = dict(
        format="JPEG",
        quality=quality,
        optimize=True,
        progressive=True,
        subsampling="4:2:0",
    )
    img.save(path, **params)

def save_webp(img: Image.Image, path: Path, quality=WEBP_QUALITY):
    img.save(path, format="WEBP", quality=quality, method=6)

def resize_by_width(img: Image.Image, target_w: int) -> Image.Image:
    w, h = img.size
    if w <= target_w:
        return img
    ratio = target_w / float(w)
    return img.resize((target_w, int(h * ratio)), Image.LANCZOS)

def process_one(src: Path):
    try:
        if src.suffix.lower() not in SUPPORTED:
            return

        # Skip 0-byte or corrupt files
        if src.stat().st_size == 0:
            print(f"⚠️  Skipping empty file: {src}")
            return

        rel = src.relative_to(SRC_DIR)
        out_hi   = OUT_DIR / rel.with_suffix(".jpg")
        out_webp = OUT_DIR / rel.with_suffix(".webp")
        out_thumb= THUMB_DIR / rel.with_suffix(".jpg")

        out_hi.parent.mkdir(parents=True, exist_ok=True)
        out_thumb.parent.mkdir(parents=True, exist_ok=True)

        img = Image.open(src)
        img.load()

        # Normalize & optionally strip EXIF
        if STRIP_EXIF:
            img = strip_exif(img)
        else:
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")

        # Hi-res (resize if wider than MAX_WIDTH_HI)
        hi = resize_by_width(img, MAX_WIDTH_HI)
        save_jpeg(hi, out_hi)

        # Thumbnail
        thumb = resize_by_width(img, THUMB_WIDTH)
        save_jpeg(thumb, out_thumb, quality=70)  # smaller/faster for blur-up

        # Optional WebP (often even smaller)
        if MAKE_WEBP:
            save_webp(hi, out_webp)

        print(f"✅ {src} → {out_hi} (+ thumb, {'+ webp' if MAKE_WEBP else ''})")

    except Exception as e:
        print(f"❌ Error processing {src}: {e}")

def main():
    ensure_dirs()
    for root, _, files in os.walk(SRC_DIR):
        for f in files:
            p = Path(root) / f
            process_one(p)

if __name__ == "__main__":
    main()