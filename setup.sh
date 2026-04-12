#!/bin/bash
# ================================================
# Answer Evaluation Engine - Setup Script
# One-time setup for new users
# ================================================

echo "🚀 Answer Evaluation Engine Setup"
echo "================================="

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "📦 Virtual environment already exists"
fi

# Activate and install dependencies
echo "📥 Installing dependencies..."
source venv/bin/activate

pip install -q fastapi uvicorn python-multipart pydantic pytesseract pdf2image pillow PyPDF2 \
    sentence-transformers scikit-learn numpy python-docx opencv-python-headless requests

echo "📁 Creating project directories..."
mkdir -p uploads templates static

# Check Tesseract
echo "🔍 Checking Tesseract OCR..."
if command -v tesseract &> /dev/null; then
    echo "✅ Tesseract OCR is installed: $(tesseract --version | head -1)"
else
    echo "⚠️  Tesseract OCR not found. Please install it:"
    echo "   macOS: brew install tesseract"
    echo "   Ubuntu: sudo apt install tesseract-ocr"
fi

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "🚀 Quick commands:"
echo "   ./run start     # Start the server"
echo "   ./run status    # Check status"
echo "   ./run stop      # Stop the server"
echo ""
echo "🌐 UI will be available at: http://localhost:8000"
echo "========================================"