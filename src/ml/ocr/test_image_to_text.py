"""
image_to_text.py — Unified Image → Text Pipeline
for Fake News Detection System

Merged best-of-both from:
  • image_to_text.py   — preprocessing, BLIP captioning, auto-detect, row-bucket sort
  • ocr_extractor.py   — dual OCR engines (EasyOCR + Tesseract), structured NER output,
                         batch processing, suspicious element detection

Usage (single image):
  python image_to_text.py --image article.jpg
  python image_to_text.py --image article.jpg --mode both      # OCR + captioning
  python image_to_text.py --image article.jpg --engine easyocr
  python image_to_text.py --image article.jpg --format json --save

Usage (batch folder):
  python image_to_text.py --folder ./news_images --output ./results
  python image_to_text.py --folder ./news_images --format json
"""

import re
import sys
import json
import time
import argparse
import shutil
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional

import cv2
import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ml.models.fake_news_predictor import classify_text

# ── Tesseract (optional — works without it) ───────────────────────────────────
try:
    import pytesseract
    # Tesseract is auto-detected from system PATH on Linux/macOS
    # On Windows, uncomment and set the path if needed:
    # if sys.platform == "win32":
    #     pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    TESSERACT_OK = shutil.which("tesseract") is not None
except ImportError:
    TESSERACT_OK = False


# ══════════════════════════════════════════════════════════════════════════════
# 1. DATA MODEL
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ImageTextResult:
    """Structured output fed directly into the credibility model."""

    # ── Core text ─────────────────────────────────────────────────────────────
    combined_text: str = ""        # <- primary field for your model
    headline: str = "None"
    body: str = "None"

    # ── Metadata extracted from text ──────────────────────────────────────────
    dates: List[str]              = field(default_factory=list)
    people: List[str]             = field(default_factory=list)
    organizations: List[str]      = field(default_factory=list)
    locations: List[str]          = field(default_factory=list)
    source: str                   = "None"
    suspicious_elements: List[str] = field(default_factory=list)

    # ── Pipeline metadata ─────────────────────────────────────────────────────
    image_path: str           = ""
    image_type: str           = "unknown"   # document | scene
    engine_used: str          = ""
    ocr_region_count: int     = 0
    caption: str              = ""
    processing_time_sec: float = 0.0
    raw_ocr_text: str         = ""
    detection: dict           = field(default_factory=dict)

    def to_text(self) -> str:
        def fmt(lst): return ", ".join(lst) if lst else "None"
        susp = "\n".join(f"  - {s}" for s in self.suspicious_elements) \
               if self.suspicious_elements else "  None"
        return (
            f"HEADLINE:\n{self.headline}\n\n"
            f"BODY:\n{self.body}\n\n"
            f"METADATA:\n"
            f"  Dates         : {fmt(self.dates)}\n"
            f"  People        : {fmt(self.people)}\n"
            f"  Organizations : {fmt(self.organizations)}\n"
            f"  Locations     : {fmt(self.locations)}\n"
            f"  Source        : {self.source}\n\n"
            f"SUSPICIOUS ELEMENTS:\n{susp}\n\n"
            f"CAPTION (scene):\n{self.caption or 'N/A'}\n\n"
            f"COMBINED TEXT FOR MODEL:\n{self.combined_text}"
        )

    def to_dict(self) -> dict:
        return asdict(self)


# ══════════════════════════════════════════════════════════════════════════════
# 2. IMAGE PREPROCESSING
# ══════════════════════════════════════════════════════════════════════════════

def preprocess_for_ocr(image_path: str) -> np.ndarray:
    """
    Best-practice preprocessing pipeline:
      1. Upscale to >= 1500px longest side
      2. Grayscale
      3. Denoise BEFORE thresholding (avoids amplifying noise)
      4. Adaptive Gaussian threshold (handles uneven lighting / shadows)
      5. Deskew
      6. Morphological opening (remove speck noise)
    Returns a binary numpy array suitable for both EasyOCR and Tesseract.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot open image: {image_path}")

    # 1. Upscale
    h, w = img.shape[:2]
    if max(h, w) < 1500:
        scale = max(2.0, 1500 / max(h, w))
        img = cv2.resize(img, None, fx=scale, fy=scale,
                         interpolation=cv2.INTER_CUBIC)

    # 2. Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. Denoise (on gray, before binarizing)
    gray = cv2.fastNlMeansDenoising(gray, h=10,
                                     templateWindowSize=7,
                                     searchWindowSize=21)

    # 4. Adaptive threshold
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31, C=15
    )

    # 5. Deskew
    thresh = _deskew(thresh)

    # 6. Morphological cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    return thresh


def _deskew(image: np.ndarray) -> np.ndarray:
    """Correct document tilt using minAreaRect on dark pixel coords."""
    coords = np.column_stack(np.where(image < 128))
    if len(coords) < 100:
        return image
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = 90 + angle
    if abs(angle) < 0.5:
        return image
    h, w = image.shape
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(image, M, (w, h),
                          flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)


# ══════════════════════════════════════════════════════════════════════════════
# 3. IMAGE TYPE DETECTION
# ══════════════════════════════════════════════════════════════════════════════

def detect_image_type(image_path: str) -> str:
    """
    Returns 'document' if image is text-heavy (newspaper, screenshot, article)
    or 'scene' if it is a real-world photograph.
    Used to decide whether to run captioning.
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return "scene"

    _, binary = cv2.threshold(img, 0, 255,
                               cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)
    total_px = img.shape[0] * img.shape[1]
    text_like = 0
    for cnt in contours:
        x, y, cw, ch = cv2.boundingRect(cnt)
        aspect = cw / max(ch, 1)
        area   = cw * ch
        if 0.1 < aspect < 10 and 20 < area < total_px * 0.01:
            text_like += 1

    color_img = cv2.imread(image_path)
    color_std = np.std(color_img.reshape(-1, 3), axis=0).mean()

    if (text_like > 80 and color_std < 60) or text_like > 200:
        return "document"
    return "scene"


# ══════════════════════════════════════════════════════════════════════════════
# 4. OCR ENGINES
# ══════════════════════════════════════════════════════════════════════════════

_easy_reader = None   # singleton
_torch = None
_easyocr = None
_blip_processor_cls = None
_blip_model_cls = None


def _load_torch():
    global _torch
    if _torch is None:
        import torch
        _torch = torch
    return _torch


def _load_easyocr():
    global _easyocr
    if _easyocr is None:
        import easyocr
        _easyocr = easyocr
    return _easyocr


def _load_blip_modules():
    global _blip_processor_cls, _blip_model_cls
    if _blip_processor_cls is None or _blip_model_cls is None:
        from transformers import BlipProcessor, BlipForConditionalGeneration
        _blip_processor_cls = BlipProcessor
        _blip_model_cls = BlipForConditionalGeneration
    return _blip_processor_cls, _blip_model_cls


def _ocr_easyocr(image_path: str,
                  preprocessed_path: str,
                  confidence_threshold: float = 0.4):
    """
    Run EasyOCR with row-bucket sorting for correct left-to-right,
    top-to-bottom reading order — critical for justified / spaced text.
    Returns (filtered_text, region_count).
    """
    global _easy_reader
    if _easy_reader is None:
        easyocr = _load_easyocr()
        torch = _load_torch()
        _easy_reader = easyocr.Reader(
            ["en"],
            gpu=torch.cuda.is_available(),
            model_storage_directory=str(Path.home() / ".easyocr"),
        )

    # paragraph=False keeps per-word bboxes needed for row-bucket sort
    raw = _easy_reader.readtext(image_path, detail=1, paragraph=False)
    pre = _easy_reader.readtext(preprocessed_path, detail=1, paragraph=False, mag_ratio=1.5)

    # Pick whichever run accumulated more confident detections
    def _score(res):
        return sum(c for _, _, c in res if c >= confidence_threshold)

    results = pre if _score(pre) >= _score(raw) else raw

    # Filter noise
    filtered = [
        (bbox, text, conf) for bbox, text, conf in results
        if conf >= confidence_threshold and len(text.strip()) > 1
    ]

    if not filtered:
        return {"all_text": "", "headline": "", "body": ""}, 0

    # Calculate median height of bounding boxes
    heights = [abs(b[2][1] - b[0][1]) for b, t, c in filtered]
    median_h = sorted(heights)[len(heights)//2]

    # Group into headline vs body based on visual height
    headline_nodes = []
    body_nodes = []
    for item in filtered:
        h = abs(item[0][2][1] - item[0][0][1])
        if h >= 1.4 * median_h:
            headline_nodes.append(item)
        else:
            body_nodes.append(item)

    # ── Row-bucket sort ───────────────────────────────────────────────────────
    # Dynamic tolerance based on median height
    ROW_TOLERANCE = max(10, int(median_h * 0.5))

    def sort_nodes(nodes):
        nodes.sort(key=lambda x: (
            round(x[0][0][1] / ROW_TOLERANCE) * ROW_TOLERANCE,
            x[0][0][0],
        ))
        return " ".join(t for _, t, _ in nodes)

    all_nodes = headline_nodes + body_nodes

    text_out = {
        "all_text": sort_nodes(all_nodes),
        "headline": sort_nodes(headline_nodes),
        "body": sort_nodes(body_nodes)
    }
    return text_out, len(filtered)


def _ocr_tesseract(preprocessed: np.ndarray) -> str:
    """
    Run Tesseract with LSTM engine.
    PSM 3 = fully automatic page segmentation (best for mixed layouts).
    PSM 6 = uniform block of text (best for single articles).
    Tries PSM 3 first, falls back to PSM 6 if output is too short.
    """
    if not TESSERACT_OK:
        raise RuntimeError("Tesseract OCR is not installed or the 'tesseract' binary is not in PATH.")
    pil  = Image.fromarray(preprocessed)
    text = pytesseract.image_to_string(pil, config="--oem 3 --psm 3")
    if len(text.strip()) < 20:
        text = pytesseract.image_to_string(pil, config="--oem 3 --psm 6")
    return text


def run_ocr(image_path: str,
            engine: str = "auto",
            confidence_threshold: float = 0.4) -> dict:
    """
    Unified OCR entry point.

    engine:
      'easyocr'   - EasyOCR only (best for natural-scene / low-quality images)
      'tesseract' - Tesseract only (best for clean scanned documents)
      'auto'      - runs both, returns the longer result
      'both'      - same as auto
    """
    print("\n[OCR] Preprocessing image...")
    preprocessed = preprocess_for_ocr(image_path)
    tmp = "/tmp/_ocr_prep.png"
    cv2.imwrite(tmp, preprocessed)

    easy_text, easy_count, tess_text = "", 0, ""
    easy_result = {}

    use_easy = engine in ("easyocr", "auto", "both")
    use_tess = engine in ("tesseract", "auto", "both") and TESSERACT_OK

    if engine == "tesseract" and not TESSERACT_OK:
        if use_easy or _easyocr is not None:
            print("[OCR] Tesseract binary not found. Falling back to EasyOCR...")
            use_easy = True
        else:
            raise RuntimeError(
                "Tesseract OCR is not installed or the 'tesseract' binary is not in PATH. "
                "Install Tesseract or use --engine easyocr."
            )

    if engine in ("auto", "both") and not TESSERACT_OK:
        print("[OCR] Tesseract binary not found. Skipping Tesseract and continuing without it.")

    if use_easy:
        print("[OCR] Running EasyOCR...")
        easy_result, easy_count = _ocr_easyocr(
            image_path, tmp, confidence_threshold
        )
        easy_text = easy_result.get("all_text", "")
        print(f"[OCR] EasyOCR -> {easy_count} regions | "
              f"{len(easy_text.split())} words")

    if use_tess:
        print("[OCR] Running Tesseract...")
        tess_text = _ocr_tesseract(preprocessed).strip()
        print(f"[OCR] Tesseract -> {len(tess_text.split())} words")

    if not easy_text and not tess_text:
        raise RuntimeError(
            "No OCR engine produced output. Install the Tesseract binary or configure EasyOCR."
        )

    # ── Select best result ────────────────────────────────────────────────────
    if use_easy and use_tess:
        # Prefer whichever recovered more words; 15% buffer favours EasyOCR
        if len(tess_text.split()) > len(easy_text.split()) * 1.15:
            chosen, used = tess_text, "tesseract"
        else:
            chosen, used = easy_text, "easyocr"
    elif use_tess:
        chosen, used = tess_text, "tesseract"
    else:
        chosen, used = easy_text, "easyocr"

    print(f"[OCR] Selected: {used} | "
          f"Final word count: {len(chosen.split())}")

    return {
        "filtered_text":  chosen,
        "easyocr_result": easy_result,
        "tesseract_text": tess_text,
        "region_count":   easy_count,
        "engine_used":    used,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 5. IMAGE CAPTIONING  (BLIP-large)
# ══════════════════════════════════════════════════════════════════════════════

_blip_processor = None
_blip_model     = None


def run_captioning(image_path: str) -> str:
    """
    Generate a news-context-aware caption using BLIP-large.
    Returns the best caption string.
    """
    global _blip_processor, _blip_model

    print("\n[CAPTION] Loading BLIP-large "
          "(first run ~1 GB download, cached after)...")
    torch = _load_torch()
    BlipProcessor, BlipForConditionalGeneration = _load_blip_modules()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    if _blip_model is None:
        _blip_processor = BlipProcessor.from_pretrained(
            "Salesforce/blip-image-captioning-large"
        )
        _blip_model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-large"
        ).to(device)

    image = Image.open(image_path).convert("RGB")

    def _gen(prompt=None):
        if prompt:
            inputs = _blip_processor(image, prompt,
                                      return_tensors="pt").to(device)
        else:
            inputs = _blip_processor(image, return_tensors="pt").to(device)
        out = _blip_model.generate(
            **inputs, max_new_tokens=80, num_beams=5, early_stopping=True
        )
        return _blip_processor.decode(out[0], skip_special_tokens=True)

    general = _gen()
    news    = _gen("a news photograph of")

    print(f"[CAPTION] General  : {general}")
    print(f"[CAPTION] News-ctx : {news}")

    # Prefer the news-context caption if it's substantively longer
    caption = news if len(news) > len(general) * 0.8 else general
    return caption


# ══════════════════════════════════════════════════════════════════════════════
# 6. TEXT PARSING & NER
# ══════════════════════════════════════════════════════════════════════════════

_DATE_RE = re.compile(
    r"""
    (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|
       Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|
       Dec(?:ember)?)\s+\d{1,2},?\s+\d{4}
    |
    \d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}
    |
    \d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}
    """,
    re.VERBOSE | re.IGNORECASE,
)

_SOURCE_RE = re.compile(
    r"(?:Source|Published by|By|Via|--|-)\\s*:?\\s*([A-Z][^\\n]{2,60})",
    re.IGNORECASE,
)
_OUTLET_RE = re.compile(
    r"\b(Reuters|AP|AFP|BBC|CNN|Fox News|MSNBC|The Guardian|"
    r"New York Times|NYT|Washington Post|NPR|Al Jazeera|"
    r"Times of India|Hindustan Times|NDTV|India Today|"
    r"Breitbart|Infowars|Daily Mail|BuzzFeed|Vice)\b",
    re.IGNORECASE,
)
_SENSATIONAL_RE = re.compile(
    r"\b(BREAKING|SHOCKING|BOMBSHELL|EXPLOSIVE|OUTRAGE|SECRET|EXPOSED|"
    r"SCANDAL|HOAX|CONSPIRACY|URGENT|MUST.?READ|YOU WON.?T BELIEVE|"
    r"CLICK HERE|SHARE NOW|GOING VIRAL)\b",
    re.IGNORECASE,
)
_CAPS_RE = re.compile(r"\b[A-Z]{4,}\b")

_ORG_WORDS = {
    "Reuters","AP","AFP","BBC","CNN","Fox","MSNBC","NPR",
    "FBI","CIA","Pentagon","Congress","Senate","Parliament",
    "WHO","UN","NATO","EU","IMF","WTO","NASA","ISRO","RBI",
    "Google","Apple","Microsoft","Facebook","Twitter","Meta",
    "White House","Department","Ministry","Committee","Council",
}
_LOC_WORDS = {
    "Washington","New York","London","Moscow","Beijing","Paris",
    "Berlin","Tokyo","Delhi","Mumbai","Islamabad","Kabul","Tehran",
    "Baghdad","Jerusalem","Brussels","Geneva","California","Texas",
    "Florida","Ukraine","Russia","China","India","Pakistan",
    "Israel","Iran","Iraq","Bangladesh","Sri Lanka","Nepal",
}


def _extract_headline(lines: List[str]) -> str:
    for line in lines:
        line = line.strip()
        if not line or line.startswith("http"):
            continue
        if len(line.split()) <= 25:
            return line
    return lines[0].strip() if lines else "None"


def _simple_ner(text: str):
    chunks = set(re.findall(r"(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", text))
    orgs   = [t for t in chunks if any(w in t for w in _ORG_WORDS)]
    locs   = [t for t in chunks if any(w in t for w in _LOC_WORDS)]
    excl   = set(orgs) | set(locs)
    people = [
        t for t in chunks
        if t not in excl
        and len(t.split()) in (2, 3)
        and not re.search(r"\b(The|A|An|This|That|These|Those)\b", t)
    ]
    return sorted(people)[:15], sorted(orgs)[:10], sorted(locs)[:10]


def _detect_suspicious(text: str, source: str) -> List[str]:
    flags = []
    caps  = _CAPS_RE.findall(text)
    if len(caps) > 3:
        flags.append(f"Excessive ALL-CAPS ({', '.join(set(caps[:5]))})")
    hits = set(_SENSATIONAL_RE.findall(text))
    if hits:
        flags.append(f"Sensational language ({', '.join(hits)})")
    if source == "None":
        flags.append("No identifiable source")
    return flags


def parse_text(raw_text: str, visual_headline: str = "", visual_body: str = "") -> dict:
    """Extract structured fields from raw OCR text."""
    lines = [l for l in raw_text.splitlines() if l.strip()]
    # Also split on sentence boundaries for single-line OCR output
    if len(lines) <= 1 and raw_text:
        lines = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_text) if s.strip()]

    if not lines:
        return {}

    if visual_headline:
        headline = visual_headline
        body     = visual_body if visual_body else "None"
    else:
        headline   = _extract_headline(lines)
        body_lines = lines[1:] if len(lines) > 1 else []
        body       = " ".join(body_lines).strip() or "None"

    source_m   = _SOURCE_RE.search(raw_text)
    outlet_m   = _OUTLET_RE.search(raw_text)
    source     = (source_m.group(1).strip() if source_m
                  else (outlet_m.group(0).strip() if outlet_m else "None"))

    people, orgs, locs = _simple_ner(raw_text)
    dates               = list(dict.fromkeys(_DATE_RE.findall(raw_text)))
    suspicious          = _detect_suspicious(raw_text, source)

    return dict(
        headline=headline, body=body,
        dates=dates, people=people,
        organizations=orgs, locations=locs,
        source=source, suspicious_elements=suspicious,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 7. MASTER PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def process_image(
    image_path: str,
    mode: str        = "auto",
    engine: str      = "auto",
    confidence: float = 0.4,
) -> ImageTextResult:
    """
    Full pipeline: image -> preprocessing -> OCR -> captioning -> NER -> result.

    mode:
      'auto'    - OCR always; captioning only for scene/photo images
      'ocr'     - OCR only
      'caption' - captioning only (no OCR)
      'both'    - OCR + captioning always
    """
    t0 = time.time()

    if not Path(image_path).exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    # ── Decide what to run ────────────────────────────────────────────────────
    if mode == "auto":
        img_type     = detect_image_type(image_path)
        run_ocr_flag = True
        run_cap_flag = (img_type == "scene")
        print(f"\n[AUTO-DETECT] {img_type.upper()} -> "
              f"OCR=yes | Captioning={'yes' if run_cap_flag else 'no'}")
    else:
        img_type     = "unknown"
        run_ocr_flag = mode in ("ocr", "both")
        run_cap_flag = mode in ("caption", "both")

    # ── OCR ───────────────────────────────────────────────────────────────────
    ocr_data = run_ocr(image_path, engine, confidence) if run_ocr_flag else {}
    ocr_text = ocr_data.get("filtered_text", "")
    
    visual_headline, visual_body = "", ""
    if ocr_data.get("engine_used") == "easyocr" and "easyocr_result" in ocr_data:
        easy_res = ocr_data["easyocr_result"]
        visual_headline = easy_res.get("headline", "")
        visual_body     = easy_res.get("body", "")

    parsed = parse_text(ocr_text, visual_headline, visual_body) if ocr_text else {}

    # ── Captioning ────────────────────────────────────────────────────────────
    caption = run_captioning(image_path) if run_cap_flag else ""

    # ── Build combined_text ───────────────────────────────────────────────────
    parts = []
    if ocr_text.strip():
        parts.append(f"[OCR]: {ocr_text.strip()}")
    if caption.strip():
        parts.append(f"[Scene]: {caption.strip()}")
    combined = " ".join(parts)

    detection = classify_text(combined, parsed.get("suspicious_elements", []), parsed.get("source", "None")).to_dict()

    return ImageTextResult(
        combined_text       = combined,
        headline            = parsed.get("headline", "None"),
        body                = parsed.get("body", "None"),
        dates               = parsed.get("dates", []),
        people              = parsed.get("people", []),
        organizations       = parsed.get("organizations", []),
        locations           = parsed.get("locations", []),
        source              = parsed.get("source", "None"),
        suspicious_elements = parsed.get("suspicious_elements", []),
        image_path          = image_path,
        image_type          = img_type,
        engine_used         = ocr_data.get("engine_used", ""),
        ocr_region_count    = ocr_data.get("region_count", 0),
        caption             = caption,
        processing_time_sec = round(time.time() - t0, 2),
        raw_ocr_text        = ocr_text,
        detection           = detection,
    )


# ── Integration stub ──────────────────────────────────────────────────────────
def get_credibility_score(result: ImageTextResult) -> float:
    """
    Plug your model in here.
    Receives the full ImageTextResult; use result.combined_text as input.
    Should return float 0.0 (fake) to 1.0 (credible).

    Example:
        from your_model import predict
        return predict(result.combined_text)
    """
    raise NotImplementedError("Replace this with your credibility model call.")


# ══════════════════════════════════════════════════════════════════════════════
# 8. BATCH PROCESSING
# ══════════════════════════════════════════════════════════════════════════════

SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}


def process_folder(
    folder: str,
    mode: str          = "auto",
    engine: str        = "auto",
    output_dir: Optional[str] = None,
    fmt: str           = "txt",
) -> List[ImageTextResult]:
    """Process every supported image in a folder."""
    folder_path = Path(folder)
    out_path    = Path(output_dir) if output_dir else folder_path / "ocr_results"
    out_path.mkdir(parents=True, exist_ok=True)

    images = sorted(
        p for p in folder_path.iterdir()
        if p.suffix.lower() in SUPPORTED_EXT
    )
    if not images:
        print(f"[BATCH] No supported images found in {folder}")
        return []

    print(f"[BATCH] Found {len(images)} image(s). Output -> {out_path}")
    results = []
    for img_path in images:
        print(f"\n[BATCH] -- {img_path.name} --")
        try:
            res = process_image(str(img_path), mode=mode, engine=engine)
        except Exception as e:
            print(f"  X Error: {e}")
            continue

        stem = img_path.stem
        if fmt == "json":
            out_file = out_path / f"{stem}_ocr.json"
            out_file.write_text(json.dumps(res.to_dict(), indent=2))
        else:
            out_file = out_path / f"{stem}_ocr.txt"
            out_file.write_text(res.to_text())

        print(f"  Saved -> {out_file.name} ({res.processing_time_sec}s)")
        results.append(res)

    print(f"\n[BATCH] Done. {len(results)}/{len(images)} succeeded.")
    return results


# ══════════════════════════════════════════════════════════════════════════════
# 9. CLI
# ══════════════════════════════════════════════════════════════════════════════

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Image to Text pipeline for fake news detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single image, auto mode (default)
  python image_to_text.py --image article.jpg

  # Force both OCR + captioning
  python image_to_text.py --image photo.jpg --mode both

  # Use both OCR engines (EasyOCR + Tesseract), save as JSON
  python image_to_text.py --image scan.jpg --engine both --format json --save

  # Batch process a folder
  python image_to_text.py --folder ./news_images --output ./results

  # Batch, JSON output, EasyOCR only
  python image_to_text.py --folder ./imgs --engine easyocr --format json
        """,
    )
    grp = p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--image",  help="Path to a single image")
    grp.add_argument("--folder", help="Path to a folder (batch mode)")

    p.add_argument("--mode",   default="auto",
                   choices=["auto", "ocr", "caption", "both"],
                   help="Processing mode (default: auto)")
    p.add_argument("--engine", default="auto",
                   choices=["auto", "easyocr", "tesseract", "both"],
                   help="OCR engine(s) to use (default: auto)")
    p.add_argument("--confidence", type=float, default=0.4,
                   help="EasyOCR confidence threshold 0-1 (default: 0.4)")
    p.add_argument("--format", dest="fmt",
                   choices=["txt", "json"], default="txt",
                   help="Output format (default: txt)")
    p.add_argument("--output", help="Directory to save output files")
    p.add_argument("--save",  action="store_true",
                   help="Save output to file (single image mode)")
    p.add_argument("--score", action="store_true",
                   help="Run credibility model stub on result")
    return p


def main():
    args = _build_parser().parse_args()

    if args.image:
        result = process_image(
            args.image,
            mode=args.mode,
            engine=args.engine,
            confidence=args.confidence,
        )

        formatted = (result.to_text() if args.fmt == "txt"
                     else json.dumps(result.to_dict(), indent=2))

        print(f"\n{'='*60}")
        print(formatted)
        print(f"{'='*60}")
        print(f"  Engine       : {result.engine_used}")
        print(f"  Image type   : {result.image_type}")
        print(f"  OCR regions  : {result.ocr_region_count}")
        print(f"  Time taken   : {result.processing_time_sec}s")
        print(f"{'='*60}\n")

        if args.score:
            try:
                score = get_credibility_score(result)
                print(f"  Credibility Score: {score:.4f}")
            except NotImplementedError:
                print("  [INFO] Plug your model into "
                      "get_credibility_score() to enable scoring.")

        if args.save:
            out_dir = Path(args.output) if args.output else Path(".")
            out_dir.mkdir(parents=True, exist_ok=True)
            ext      = "json" if args.fmt == "json" else "txt"
            out_file = out_dir / f"{Path(args.image).stem}_ocr.{ext}"
            out_file.write_text(formatted)
            print(f"  Saved -> {out_file}")

    else:
        process_folder(
            folder=args.folder,
            mode=args.mode,
            engine=args.engine,
            output_dir=args.output,
            fmt=args.fmt,
        )


if __name__ == "__main__":
    main()
