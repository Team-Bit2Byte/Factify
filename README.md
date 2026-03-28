# Factify

Factify is a fake-news analysis app with a React frontend, an Express API, and Python extraction pipelines for both image OCR and URL text scraping.

The codebase currently supports two live analysis flows:
- image upload -> OCR extraction -> extracted text rendered in the frontend
- URL input -> article scraping -> extracted text rendered in the frontend

## Quick Start

```bash
npm install
pip3 install -r requirements.txt
npm run dev:all
```

Frontend runs on `http://localhost:3000` and the backend API runs on `http://localhost:3001`.

## Features

- Upload `jpeg`, `jpg`, `png`, `webp`, and `avif` images up to `10MB`
- Run OCR through the Python pipeline in `src/ml/ocr/test_image_to_text.py`
- Scrape article text from links through `src/ml/scraper/text_scraper.py`
- Return structured extraction data including `headline`, `body`, `combined_text`, entities, and suspicious elements
- Render extracted text directly in the analysis panel for both image and URL analysis

## Architecture

```text
React frontend (Vite, port 3000)
        |
        v
Express API (port 3001)
        |
        +--> Python OCR pipeline (EasyOCR / Tesseract helpers)
        |
        +--> Python URL scraper (Trafilatura + curl_cffi fallback)
```

## Image OCR Flow

1. Upload an image from the landing page.
2. The frontend posts it to `/api/analyze-image`.
3. The backend stores the file temporarily and runs `src/ml/ocr/test_image_to_text.py`.
4. The OCR result is returned to the UI and rendered in the analysis panel, including extracted text and detected entities.

## URL Scraping Flow

1. Paste a URL into the URL tab on the landing page.
2. The frontend posts it to `/api/analyze-url`.
3. The backend validates the link and runs `src/ml/scraper/text_scraper.py`.
4. The scraper fetches the page, extracts the article body, and returns the cleaned text plus lightweight metadata.
5. The frontend renders the extracted article text in the same analysis panel used for image results.

## Project Structure

```text
Factify/
├── src/backend/          # Express API server
├── src/frontend/         # React + Vite application
├── src/ml/ocr/           # Python OCR pipeline
├── src/ml/scraper/       # Python URL text scraper
├── src/ml/algorithms/    # Additional scoring experiments
├── scripts/              # Repo scripts
├── requirements.txt      # Python dependencies
└── package.json          # Node scripts and dependencies
```

## Scripts

```bash
npm run dev         # Frontend only
npm run dev:server  # Backend only
npm run dev:all     # Frontend + backend
npm run build       # Production build
npm run lint        # Type check
./scripts/test_backend.sh
```

## API

- `GET /api/health` returns backend health status
- `POST /api/analyze-image` accepts a multipart form field named `image`
- `POST /api/analyze-url` accepts JSON in the form `{ "url": "https://..." }`

## Verification

```bash
npm run lint
npm run build
./scripts/test_backend.sh
curl http://localhost:3001/api/health
```

## Current Status

- Image upload and OCR extraction are wired end to end
- URL scraping and extracted-text rendering are wired end to end
- The frontend currently shows real extracted text for both image and URL analysis
- The text tab is still placeholder UI and does not call a backend analysis service yet
- OCR dependencies require Python packages from `requirements.txt`; Tesseract availability still depends on the local machine
- URL scraping depends on `trafilatura` and uses `curl_cffi` as a fetch fallback for stricter sites
