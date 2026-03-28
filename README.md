# Factify

Factify is an independent fake-news analysis application with a React frontend, an Express backend, a Python ML layer, and an internal C++ credibility engine.

It supports three live inputs:

- raw text
- uploaded news images
- article URLs

Each analysis returns:

- a blended verdict: `Likely Original`, `Unverified`, or `Likely Fake / False`
- the `.keras` model score
- deterministic algorithm-engine scores
- extracted text, entities, and explanation lines

## Stack

- Frontend: React 19 + Vite + TypeScript
- Backend: Express
- ML / extraction: Python
- Deterministic scoring: internal C++ credibility engine

## Quick Start

```bash
npm install
pip3 install -r requirements.txt
npm run dev:all
```

Frontend: `http://localhost:3000`  
Backend: `http://localhost:3001`

## Build Notes

Factify can compile the credibility bridge automatically on first analysis request, but you can also build it explicitly:

```bash
npm run build:bridge
```

The compiled bridge is written to `build/factify_credibility_bridge` and is ignored by Git.

## Features

- Text analysis through `src/ml/text/analyze_text.py`
- Image OCR analysis through `src/ml/ocr/test_image_to_text.py`
- URL scraping through `src/ml/scraper/text_scraper.py`
- `.keras` model inference from `src/ml/models/fake_news_detector.keras`
- Exact internal C++ scoring through a local bridge binary
- UI breakdown of model verdict, algorithm score, explanations, and evidence

## API

- `GET /api/health`
- `POST /api/analyze-text`
  body: `{ "text": "..." }`
- `POST /api/analyze-image`
  multipart field: `image`
- `POST /api/analyze-url`
  body: `{ "url": "https://..." }`

## Project Structure

```text
Factify/
├── src/
│   ├── backend/                  # Express API
│   ├── frontend/                 # React UI
│   └── ml/
│       ├── algorithms/
│       │   ├── credibility_bridge.cpp
│       │   └── credibility_engine.py
│       ├── models/
│       │   ├── fake_news_detector.keras
│       │   └── fake_news_predictor.py
│       ├── ocr/
│       ├── scraper/
│       └── text/
├── vendor/
│   └── factify_engine/           # Internal C++ credibility engine + data
├── scripts/
│   ├── build_credibility_bridge.sh
│   └── test_backend.sh
├── requirements.txt
├── package.json
└── README.md
```

## Verification

```bash
npm run lint
npm run build
npm run build:bridge
python3 src/ml/text/analyze_text.py --text "According to the official statement..."
curl http://localhost:3001/api/health
```

## Notes

- The deterministic scoring path now prefers the exact internal C++ credibility engine.
- The Python `credibility_engine.py` path remains as a fallback if the bridge is unavailable.
- The `.keras` model is active, but prediction quality would improve further if the original training tokenizer/vectorizer is added to the repo.
- OCR quality still depends on local Python dependencies and, for Tesseract mode, a local Tesseract install.
