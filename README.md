# 📄 Answer Evaluation Engine

An AI-powered system for evaluating handwritten student answer sheets using OCR and semantic similarity scoring.

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+**
- **Tesseract OCR** (for handwritten text extraction)
  - macOS: `brew install tesseract`
  - Ubuntu: `sudo apt install tesseract-ocr`

### Setup & Usage

```bash
# 1. First-time setup (only once)
./setup.sh

# 2. Start the platform
./run start

# 3. Open in browser
# → http://localhost:8000
```

### Available Commands

```bash
./run start      # Start the server
./run stop       # Stop the server
./run restart    # Restart the server
./run status     # Check server status
./run logs       # View server logs
./run help       # Show help information
```

---

## 📋 Project Structure

This project has been **simplified to 2 main executable files**:

### Core Files
- **`setup.sh`** - One-time setup script (installs dependencies, creates virtual environment)
- **`run`** - Main CLI command for managing the platform
- **`requirements.txt`** - Python dependencies
- **`main.py`** - FastAPI backend application
- **`README.md`** - This documentation

### Supporting Directories
- **`src/`** - Core Python modules:
  - `ocr_processor.py` - Handwritten text extraction with preprocessing
  - `evaluation_engine.py` - Rule-based + semantic similarity scoring
  - `models.py` - Data models and Pydantic schemas
  - `pdf_processor.py` - PDF handling with fallback mechanisms
- **`templates/`** - HTML templates (modern dark UI)
- **`static/`** - Static assets
- **`uploads/`** - Temporary storage for uploaded files
- **`venv/`** - Python virtual environment

---

## 🧠 How It Works (MVP)

**Rule-based + Similarity Scoring Approach:**

1. **Upload Phase**
   - Supports: PDF, PNG, JPG, JPEG, DOCX
   - Drag & drop interface

2. **OCR Processing**
   - Uses **Tesseract OCR** optimized for handwritten text
   - Image preprocessing (contrast enhancement, noise removal, adaptive thresholding)
   - Multi-page PDF support with question segmentation
   - Confidence scoring for OCR quality

3. **Evaluation Engine**
   - **Semantic Similarity**: SentenceTransformers (`all-MiniLM-L6-v2`) embeddings + cosine similarity
   - **Keyword Matching**: Academic domain-specific keywords
   - **Structure Analysis**: Bullet points, numbered lists, length comparison
   - **Weighted Scoring**: 50% semantic + 25% keywords + 15% structure + 10% length

4. **Output**
   - Score (out of max marks)
   - Confidence percentage with visual meter
   - Human-like feedback with specific suggestions
   - Keyword highlights showing matches
   - Detailed similarity breakdown

---

## ✨ Features

### User Features
- **Modern Dark UI** with Tailwind CSS and smooth animations
- **Smart File Upload** with drag & drop support
- **Real-time OCR** with visible extracted text
- **Interactive Scoring** with confidence visualization
- **Detailed Feedback** with improvement suggestions
- **Keyword Analysis** showing what matched the model answer
- **Scoring Breakdown** showing how marks were calculated

### Technical Features
- **Hybrid Scoring**: Combines semantic embeddings with rule-based heuristics
- **Robust OCR**: Multiple fallback mechanisms for different document types
- **Background Server**: Runs independently with simple CLI management
- **Clean Architecture**: Well-organized Python modules
- **Production Ready**: Proper error handling and logging

---

## 📊 Supported Formats

- **PDF** - Scanned answer sheets (multi-page supported)
- **Images** - PNG, JPG, JPEG (handwritten preferred)
- **Documents** - DOCX (digital text)

**Best Results**: Clear, well-lit scanned copies with legible handwriting.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI (high performance)
- **OCR**: Tesseract with OpenCV preprocessing
- **AI/ML**: SentenceTransformers, scikit-learn, NumPy
- **Frontend**: HTML + Tailwind CSS + vanilla JavaScript
- **Document Processing**: PyPDF2, python-docx, pdf2image
- **Deployment**: Simple background server with CLI interface

---

## 📈 Future Improvements

- LLM-based evaluation (beyond rule-based)
- Fine-tuned models for specific subjects
- Multi-language support
- Database integration for storing results
- Batch processing dashboard
- API authentication and user management

---

## 📜 License

This project is licensed under the **MIT License**.

---

## 🌟 Vision

To build a **scalable AI evaluation engine** that becomes the standard for academic assessment worldwide, combining the accuracy of human evaluators with the speed and consistency of AI.

---

**Made with ❤️ for educators and students**

**Current Version**: Rule-based + Similarity Scoring (MVP)