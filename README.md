# Factify

Factify is a fake-news analysis app with a React frontend, an Express upload API, and a Python OCR pipeline for extracting text from uploaded images.

The current working path is image upload -> OCR extraction -> extracted text and entities rendered in the frontend.

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
- Return structured extraction data including `headline`, `body`, `combined_text`, entities, and suspicious elements
- Render extracted text directly in the analysis panel after upload

## Architecture

```text
React frontend (Vite, port 3000)
        |
        v
Express API (port 3001)
        |
        v
Python OCR pipeline (EasyOCR / Tesseract helpers)
```

## Image OCR Flow

1. Upload an image from the landing page.
2. The frontend posts it to `/api/analyze-image`.
3. The backend stores the file temporarily and runs `src/ml/ocr/test_image_to_text.py`.
4. The OCR result is returned to the UI and rendered in the analysis panel, including extracted text and detected entities.

## Project Structure

```text
Factify/
├── src/backend/          # Express API server
├── src/frontend/         # React + Vite application
├── src/ml/ocr/           # Python OCR pipeline
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

## Verification

```bash
npm run lint
npm run build
./scripts/test_backend.sh
curl http://localhost:3001/api/health
```

## Current Status

- Image upload and OCR extraction are wired end to end
- The frontend currently shows real OCR output for image analysis
- Text and URL tabs are still placeholder UI and do not call a backend analysis service yet
- OCR dependencies require Python packages from `requirements.txt`; Tesseract availability still depends on the local machine
