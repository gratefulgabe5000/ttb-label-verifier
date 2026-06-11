"""
WBS 2.6 -- Degraded-quality label images for OpenCV preprocessing tests
(FR-039: deskew/perspective correction, contrast normalization, glare
suppression; DevLog Sec. 3.1 TS-02, WBS 6.1).

Each degraded image is a Pillow-only transformation of an EXISTING real label
image already cataloged in manifest.json (WBS 2.1) and used as a
label_images entry across the WBS 2.3-2.5 test_sets.json fixtures. Source
image: "Woodford Reserve burbon front.jpg" (the most heavily-used baseline).

Outputs (testdata/degraded/):
  woodford_front_angle.jpg     -- ~8 deg rotation (deskew/perspective-correction target)
  woodford_front_glare.jpg     -- soft white radial overlay (glare-suppression target)
  woodford_front_lowlight.jpg  -- reduced brightness/contrast (contrast-normalization target)
  woodford_front_combined.jpg  -- angle + glare, matching FR-039's literal test
                                   ("a label image photographed at an angle with glare")

See testdata/degraded_images.json for the per-image degradation parameters
and preprocessing expectations.

Usage:
    testdata/.venv/Scripts/python.exe testdata/build_degraded_images.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

SOURCE_DIR = Path(__file__).parent
OUT_DIR = SOURCE_DIR / "degraded"
SOURCE_IMAGE = "Woodford Reserve burbon front.jpg"

ROTATION_DEGREES = 8
LOWLIGHT_BRIGHTNESS = 0.35
LOWLIGHT_CONTRAST = 0.75


def apply_angle(img: Image.Image) -> Image.Image:
    """Rotate by ROTATION_DEGREES, expanding the canvas with a white fill --
    simulates a label photographed slightly crooked (the deskew/perspective-
    correction target)."""
    return img.rotate(
        ROTATION_DEGREES,
        expand=True,
        fillcolor=(255, 255, 255),
        resample=Image.BICUBIC,
    )


GLARE_PEAK_ALPHA = 175  # 0-255; translucent so underlying text remains a
# recoverable "ghost" -- a fully opaque (255) overlay would permanently
# destroy the pixel data and give glare-suppression nothing to recover.


def apply_glare(img: Image.Image) -> Image.Image:
    """Overlay a soft, translucent white radial blob in the upper-right
    quadrant -- simulates a camera-flash/light reflection (the
    glare-suppression target). Peak opacity is GLARE_PEAK_ALPHA (not fully
    opaque) so text under the glare is faded but still present in the pixel
    data for a contrast-normalization step to recover."""
    img = img.convert("RGB")
    w, h = img.size

    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    cx, cy = int(w * 0.7), int(h * 0.3)
    rx, ry = int(w * 0.28), int(h * 0.4)
    draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=GLARE_PEAK_ALPHA)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=min(w, h) * 0.08))

    white = Image.new("RGB", (w, h), (255, 255, 255))
    return Image.composite(white, img, mask)


def apply_lowlight(img: Image.Image) -> Image.Image:
    """Reduce brightness and contrast -- simulates an underexposed/dimly-lit
    photo (the contrast-normalization target)."""
    img = ImageEnhance.Brightness(img).enhance(LOWLIGHT_BRIGHTNESS)
    img = ImageEnhance.Contrast(img).enhance(LOWLIGHT_CONTRAST)
    return img


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source = Image.open(SOURCE_DIR / SOURCE_IMAGE)

    variants = {
        "woodford_front_angle.jpg": apply_angle(source),
        "woodford_front_glare.jpg": apply_glare(source),
        "woodford_front_lowlight.jpg": apply_lowlight(source),
        # Glare proportions are computed against the original (un-rotated)
        # frame, then the glared image is rotated -- avoids the glare blob
        # being sized against the larger expand=True canvas.
        "woodford_front_combined.jpg": apply_angle(apply_glare(source)),
    }

    for filename, image in variants.items():
        output_path = OUT_DIR / filename
        image.convert("RGB").save(output_path, quality=90)
        print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
