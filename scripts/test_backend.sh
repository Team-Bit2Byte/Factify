#!/bin/bash

echo "🧪 Testing Factify Backend Integration"
echo "======================================"
echo ""

# Check if node is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    exit 1
fi

echo "✅ Node.js is available"

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✅ Python 3 is available"

# Check Python dependencies
echo ""
echo "Checking Python dependencies..."
python3 -c "
try:
    import easyocr
    import cv2
    import PIL
    import torch
    import transformers
    import pytesseract
    import trafilatura
    import curl_cffi
    print('✅ All Python dependencies installed')
except ImportError as e:
    print(f'❌ Missing Python dependency: {e}')
    print('Run: pip3 install -r requirements.txt')
    exit(1)
"

# Check Node dependencies
echo ""
echo "Checking Node.js dependencies..."
if [ ! -d "node_modules" ]; then
    echo "❌ Node modules not installed"
    echo "Run: npm install"
    exit 1
fi

echo "✅ Node modules installed"

# Check required files
echo ""
echo "Checking required files..."
FILES=("src/backend/index.js" "src/ml/ocr/test_image_to_text.py" "src/ml/scraper/text_scraper.py" "src/frontend/services/api.ts" "src/frontend/pages/LandingPage.tsx")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file is missing"
        exit 1
    fi
done

echo ""
echo "✅ All checks passed!"
echo ""
echo "To start the servers:"
echo "  npm run dev:all     # Start both frontend and backend"
echo "  npm run dev:server  # Start backend only (port 3001)"
echo "  npm run dev         # Start frontend only (port 3000)"
echo ""
