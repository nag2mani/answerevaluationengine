import PyPDF2
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import cv2
import numpy as np
from pathlib import Path
import time
from typing import Dict, Tuple, Optional

class PDFProcessor:
    """Simplified PDF processor using PyPDF2 + fallback to images"""
    
    def __init__(self):
        self.tesseract_config = '--oem 3 --psm 6'
    
    def extract_text_from_pdf(self, pdf_path: str) -> Tuple[str, float, Dict[int, str]]:
        """Try to extract text directly from PDF, fallback to OCR if needed"""
        try:
            # First try direct text extraction
            text = self._extract_text_direct(pdf_path)
            
            if text and len(text.strip()) > 50:  # If we got meaningful text
                return text, 0.85, {1: text}
            
            # Fallback to image-based OCR
            return self._extract_with_ocr(pdf_path)
            
        except Exception as e:
            print(f"PDF extraction error: {e}")
            return self._extract_with_ocr(pdf_path)
    
    def _extract_text_direct(self, pdf_path: str) -> str:
        """Extract text directly from PDF using PyPDF2"""
        text_parts = []
        
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")
        
        return "\n\n".join(text_parts)
    
    def _extract_with_ocr(self, pdf_path: str) -> Tuple[str, float, Dict[int, str]]:
        """Convert PDF pages to images and run OCR"""
        try:
            images = convert_from_path(pdf_path, dpi=200)  # Lower DPI for speed
            full_text = []
            question_segments = {}
            total_confidence = 0.0
            
            for i, image in enumerate(images):
                # Preprocess image
                processed = self._preprocess_image(image)
                
                # OCR
                page_text = pytesseract.image_to_string(processed, config=self.tesseract_config)
                full_text.append(f"--- Page {i+1} ---\n{page_text}")
                question_segments[i+1] = page_text.strip()
                
                # Rough confidence
                total_confidence += self._estimate_confidence(page_text)
            
            avg_confidence = total_confidence / len(images) if images else 0.5
            return "\n".join(full_text), avg_confidence, question_segments
            
        except Exception as e:
            print(f"OCR fallback failed: {e}")
            return "", 0.0, {}
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Basic preprocessing for OCR"""
        if image.mode != 'L':
            image = image.convert('L')
        
        # Convert to numpy for OpenCV
        img_array = np.array(image)
        
        # Simple preprocessing
        blurred = cv2.GaussianBlur(img_array, (3, 3), 0)
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return Image.fromarray(binary)
    
    def _estimate_confidence(self, text: str) -> float:
        """Very basic confidence estimation"""
        if not text or len(text.strip()) < 10:
            return 0.3
        word_count = len(text.split())
        if word_count > 50:
            return 0.8
        elif word_count > 20:
            return 0.65
        return 0.5