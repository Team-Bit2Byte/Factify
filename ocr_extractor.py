"""
ocr_extractor.py
────────────────
High-accuracy OCR & structured text extraction from images.
Outputs data ready for a fake-news detection pipeline.

Dependencies (install once):
    pip install pillow pytesseract opencv-python easyocr torch torchvision

System requirement:
    sudo apt-get install tesseract-ocr        # Linux
    brew install tesseract                    # macOS
"""

import re
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional

import cv2
import numpy as np
from PIL import Image

# ── Optional engines ──────────────────────────────────────────────────────────
try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════════════
# Data model
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class OCRResult:
    headline: str = "None"
    body: str = "None"
    dates: List[str] = field(default_factory=list)
    people: List[str] = field(default_factory=list)
    organizations: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    source: str = "None"
    suspicious_elements: List[str] = field(default_factory=list)

    def to_text(self) -> str:
        """Render result in the required structured format."""
        def fmt_list(lst): return ", ".join(lst) if lst else "None"

        susp = "\n".join(f"  - {s}" for s in self.suspicious_elements) \
               if self.suspicious_elements else "  None"

        return (
            f"HEADLINE:\n{self.headline}\n\n"
            f"BODY:\n{self.body}\n\n"
            f"METADATA:\n"
            f"Dates: {fmt_list(self.dates)}\n"
            f"People: {fmt_list(self.people)}\n"
            f"Organizations: {fmt_list(self.organizations)}\n"
            f"Locations: {fmt_list(self.locations)}\n"
            f"Source: {self.source}\n\n"
            f"SUSPICIOUS_ELEMENTS:\n{susp}"
        )

    def to_dict(self) -> dict:
        return asdict(self)


# ══════════════════════════════════════════════════════════════════════════════
# Image pre-processing
# ══════════════════════════════════════════════════════════════════════════════

def preprocess_image(image_path: str) -> np.ndarray:
    """
    Apply a best-practice preprocessing pipeline to maximise OCR accuracy:
      1. Greyscale conversion
      2. Upscaling to ≥ 300 DPI equivalent
      3. Adaptive thresholding (handles uneven lighting)
      4. Mild denoising
      5. Deskew
    Returns a processed numpy array (BGR).
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot open image: {image_path}")

    # 1. Greyscale
    grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. Upscale if small
    h, w = grey.shape
    if max(h, w) < 1000:
        scale = 1000 / max(h, w)
        grey = cv2.resize(grey, None, fx=scale, fy=scale,
                          interpolation=cv2.INTER_CUBIC)

    # 3. Adaptive threshold
    thresh = cv2.adaptiveThreshold(
        grey, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 11
    )

    # 4. Denoise
    denoised = cv2.fastNlMeansDenoising(thresh, h=10)

    # 5. Deskew
    deskewed = _deskew(denoised)

    return deskewed


def _deskew(image: np.ndarray) -> np.ndarray:
    """Correct slight rotation using moments."""
    coords = np.column_stack(np.where(image < 128))
    if len(coords) < 5:
        return image
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = 90 + angle
    if abs(angle) < 0.5:
        return image
    (h, w) = image.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, M, (w, h),
                          flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)


# ══════════════════════════════════════════════════════════════════════════════
# OCR engines
# ══════════════════════════════════════════════════════════════════════════════

def extract_with_tesseract(processed: np.ndarray) -> str:
    """Run Tesseract on a preprocessed image array."""
    if not TESSERACT_AVAILABLE:
        raise RuntimeError("pytesseract not installed.")
    pil_img = Image.fromarray(processed)
    config = "--oem 3 --psm 6"   # LSTM engine, uniform block of text
    return pytesseract.image_to_string(pil_img, config=config)


_easyocr_reader = None   # lazy singleton

def extract_with_easyocr(image_path: str) -> str:
    """Run EasyOCR on the original image path (handles colour natively)."""
    if not EASYOCR_AVAILABLE:
        raise RuntimeError("easyocr not installed.")
    global _easyocr_reader
    if _easyocr_reader is None:
        _easyocr_reader = easyocr.Reader(["en"], gpu=False)
    results = _easyocr_reader.readtext(image_path, detail=0, paragraph=True)
    return "\n".join(results)


def extract_text(image_path: str, engine: str = "tesseract") -> str:
    """
    Unified entry point.
    engine: "tesseract" | "easyocr" | "auto"
      "auto"  → tries tesseract first, falls back to easyocr
    """
    processed = preprocess_image(image_path)

    if engine == "tesseract":
        return extract_with_tesseract(processed)

    if engine == "easyocr":
        return extract_with_easyocr(image_path)

    # auto
    if TESSERACT_AVAILABLE:
        text = extract_with_tesseract(processed)
        if len(text.strip()) > 20:
            return text
    if EASYOCR_AVAILABLE:
        return extract_with_easyocr(image_path)

    raise RuntimeError(
        "No OCR engine available. Install pytesseract or easyocr."
    )


# ══════════════════════════════════════════════════════════════════════════════
# Text parsing & metadata extraction
# ══════════════════════════════════════════════════════════════════════════════

# ── Regex patterns ────────────────────────────────────────────────────────────

_DATE_RE = re.compile(
    r"""
    (?:
        (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|
           Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|
           Dec(?:ember)?)
        \s+\d{1,2},?\s+\d{4}
    )
    |
    (?:\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})
    |
    (?:\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})
    """,
    re.VERBOSE | re.IGNORECASE,
)

_SOURCE_RE = re.compile(
    r"(?:Source|Published by|By|Via|—|–)\s*:?\s*([A-Z][^\n]{2,60})",
    re.IGNORECASE,
)

# Common wire / outlet keywords for source heuristic
_SOURCE_KEYWORDS = re.compile(
    r"\b(Reuters|AP|AFP|BBC|CNN|Fox News|MSNBC|The Guardian|"
    r"New York Times|NYT|Washington Post|NPR|Al Jazeera|"
    r"Breitbart|Infowars|Daily Mail|BuzzFeed|Vice)\b",
    re.IGNORECASE,
)

_CAPS_RE = re.compile(r"\b[A-Z]{4,}\b")   # 4+ consecutive caps word

_SENSATIONAL = re.compile(
    r"\b(BREAKING|SHOCKING|BOMBSHELL|EXPLOSIVE|OUTRAGE|"
    r"SECRET|EXPOSED|SCANDAL|HOAX|CONSPIRACY|URGENT|"
    r"MUST.?READ|YOU WON.?T BELIEVE)\b",
    re.IGNORECASE,
)


def _extract_dates(text: str) -> List[str]:
    return list(dict.fromkeys(_DATE_RE.findall(text)))   # deduplicated


def _extract_source(text: str) -> str:
    m = _SOURCE_RE.search(text)
    if m:
        return m.group(1).strip()
    m2 = _SOURCE_KEYWORDS.search(text)
    if m2:
        return m2.group(0).strip()
    return "None"


def _extract_headline(lines: List[str]) -> str:
    """
    Heuristic: the headline is the first non-empty line that is
    ≤ 25 words and does not look like a URL or byline.
    """
    for line in lines:
        line = line.strip()
        if not line or line.startswith("http"):
            continue
        if len(line.split()) <= 25:
            return line
    return lines[0].strip() if lines else "None"


def _detect_suspicious(text: str, source: str) -> List[str]:
    flags = []
    caps_hits = _CAPS_RE.findall(text)
    if len(caps_hits) > 3:
        flags.append(f"ALL CAPS usage ({', '.join(set(caps_hits[:5]))})")
    if _SENSATIONAL.search(text):
        matches = set(_SENSATIONAL.findall(text))
        flags.append(f"Sensational/emotional language ({', '.join(matches)})")
    if source == "None":
        flags.append("Missing or unclear source")
    return flags


# ── Simple gazetteer-based NER (no extra ML dependency) ──────────────────────

_COMMON_ORG_WORDS = {
    "Reuters", "AP", "AFP", "BBC", "CNN", "Fox", "MSNBC", "NPR",
    "FBI", "CIA", "Pentagon", "Congress", "Senate", "Parliament",
    "WHO", "UN", "NATO", "EU", "IMF", "WTO", "NASA",
    "Google", "Apple", "Microsoft", "Facebook", "Twitter",
    "White House", "Department", "Ministry", "Committee",
}

_COMMON_LOC_WORDS = {
    "Washington", "New York", "London", "Moscow", "Beijing",
    "Paris", "Berlin", "Tokyo", "Delhi", "Islamabad", "Kabul",
    "Tehran", "Baghdad", "Jerusalem", "Brussels", "Geneva",
    "California", "Texas", "Florida", "Ukraine", "Russia",
    "China", "India", "Pakistan", "Israel", "Iran", "Iraq",
}

def _simple_ner(text: str):
    """
    Lightweight NER using capitalised n-gram matching against gazetteers.
    Returns (people, orgs, locations).
    """
    # Find all Capitalised runs (potential named entities)
    cap_chunks = re.findall(r"(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", text)
    cap_set = set(cap_chunks)

    orgs = [t for t in cap_set if any(w in t for w in _COMMON_ORG_WORDS)]
    locs = [t for t in cap_set if any(w in t for w in _COMMON_LOC_WORDS)]
    # People: 2-word chunks not in org/loc lists
    org_loc = set(orgs) | set(locs)
    people = [
        t for t in cap_set
        if t not in org_loc
        and len(t.split()) in (2, 3)
        and not re.search(r"\b(The|A|An|This|That|These|Those)\b", t)
    ]

    return sorted(people)[:15], sorted(orgs)[:10], sorted(locs)[:10]


# ══════════════════════════════════════════════════════════════════════════════
# Main pipeline
# ══════════════════════════════════════════════════════════════════════════════

def process_image(image_path: str, engine: str = "auto") -> OCRResult:
    """
    Full pipeline:
      raw image → preprocessing → OCR → parsing → OCRResult
    """
    raw_text = extract_text(image_path, engine)

    lines = [l for l in raw_text.splitlines() if l.strip()]
    if not lines:
        return OCRResult(headline="[unclear]", body="[unclear]")

    headline = _extract_headline(lines)
    # Body = everything after the headline
    body_lines = lines[1:] if len(lines) > 1 else lines
    body = " ".join(body_lines).strip() or "None"

    dates = _extract_dates(raw_text)
    source = _extract_source(raw_text)
    people, orgs, locs = _simple_ner(raw_text)
    suspicious = _detect_suspicious(raw_text, source)

    return OCRResult(
        headline=headline,
        body=body,
        dates=dates,
        people=people,
        organizations=orgs,
        locations=locs,
        source=source,
        suspicious_elements=suspicious,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Batch processing
# ══════════════════════════════════════════════════════════════════════════════

SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}


def process_folder(
    folder: str,
    engine: str = "auto",
    output_dir: Optional[str] = None,
    fmt: str = "txt",
) -> List[OCRResult]:
    """
    Process every supported image in `folder`.
    Saves individual output files to `output_dir` (defaults to folder).
    fmt: "txt" | "json"
    """
    folder_path = Path(folder)
    out_path = Path(output_dir) if output_dir else folder_path
    out_path.mkdir(parents=True, exist_ok=True)

    images = [p for p in folder_path.iterdir() if p.suffix.lower() in SUPPORTED_EXT]
    if not images:
        print(f"No supported images found in {folder}")
        return []

    results = []
    for img_path in sorted(images):
        print(f"Processing: {img_path.name}")
        try:
            result = process_image(str(img_path), engine)
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue

        stem = img_path.stem
        if fmt == "json":
            out_file = out_path / f"{stem}_ocr.json"
            out_file.write_text(json.dumps(result.to_dict(), indent=2))
        else:
            out_file = out_path / f"{stem}_ocr.txt"
            out_file.write_text(result.to_text())

        print(f"  ✓ Saved → {out_file.name}")
        results.append(result)

    return results


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="OCR text extractor for fake-news detection pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single image, print to stdout
  python ocr_extractor.py --image article.png

  # Single image, save as JSON
  python ocr_extractor.py --image article.png --format json --output ./out

  # Batch: entire folder, use EasyOCR engine
  python ocr_extractor.py --folder ./news_images --engine easyocr --output ./results

  # Force Tesseract
  python ocr_extractor.py --image scan.jpg --engine tesseract
        """,
    )
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--image",  help="Path to a single image file")
    group.add_argument("--folder", help="Path to a folder of images (batch mode)")

    p.add_argument(
        "--engine",
        choices=["auto", "tesseract", "easyocr"],
        default="auto",
        help="OCR engine to use (default: auto)",
    )
    p.add_argument(
        "--format", dest="fmt",
        choices=["txt", "json"],
        default="txt",
        help="Output format (default: txt)",
    )
    p.add_argument(
        "--output",
        help="Directory to save output files (batch mode or single image with --save)",
    )
    p.add_argument(
        "--save", action="store_true",
        help="Save output to file even in single-image mode",
    )
    return p


def main():
    args = _build_parser().parse_args()

    if args.image:
        result = process_image(args.image, args.engine)
        formatted = result.to_text() if args.fmt == "txt" \
                    else json.dumps(result.to_dict(), indent=2)
        print(formatted)

        if args.save and args.output:
            out_dir = Path(args.output)
            out_dir.mkdir(parents=True, exist_ok=True)
            ext = "txt" if args.fmt == "txt" else "json"
            out_file = out_dir / f"{Path(args.image).stem}_ocr.{ext}"
            out_file.write_text(formatted)
            print(f"\nSaved → {out_file}")

    else:  # folder / batch
        process_folder(
            folder=args.folder,
            engine=args.engine,
            output_dir=args.output,
            fmt=args.fmt,
        )


if __name__ == "__main__":
    main()
