import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import docx
from pathlib import Path
import time
from typing import Dict, List, Optional, Tuple

from .models import ExtractedText
from .pdf_processor import PDFProcessor

class OCRProcessor:
    def __init__(self):
        self.tesseract_config = '--oem 3 --psm 6'
        self.pdf_processor = PDFProcessor()
        self.supported_formats = {'.pdf', '.png', '.jpg', '.jpeg', '.docx', '.doc'}
        
    def is_available(self) -> bool:
        """Check if Tesseract is available"""
        try:
            version = pytesseract.get_tesseract_version()
            print(f"✅ Tesseract OCR available: {version}")
            return True
        except Exception as e:
            print(f"❌ Tesseract not available: {e}")
            return False
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results on handwritten text"""
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Convert to numpy array for OpenCV processing
            img_array = np.array(image)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(img_array, (5, 5), 0)
            
            # Adaptive thresholding - good for handwriting
            binary = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY_INV, 11, 2
            )
            
            # Noise removal
            kernel = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            
            # Convert back to PIL Image
            processed = Image.fromarray(cleaned)
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(processed)
            enhanced = enhancer.enhance(1.8)
            
            return enhanced
        except Exception as e:
            print(f"Image preprocessing error: {e}")
            return image
    
    def extract_from_image(self, image_path: str) -> Tuple[str, float]:
        """Extract text from image file"""
        try:
            image = Image.open(image_path)
            processed_image = self.preprocess_image(image)
            
            # OCR with config optimized for handwriting
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(processed_image, config=custom_config)
            confidence = self._get_confidence(processed_image, text)
            
            return text.strip(), confidence
            
        except Exception as e:
            print(f"Error processing image {image_path}: {e}")
            return "", 0.0
    
    def extract_from_pdf(self, pdf_path: str) -> Tuple[str, float, Dict[int, str]]:
        """Extract text from PDF using dedicated processor"""
        return self.pdf_processor.extract_text_from_pdf(pdf_path)
    
    def extract_from_docx(self, docx_path: str) -> Tuple[str, float]:
        """Extract text from DOCX files"""
        try:
            doc = docx.Document(docx_path)
            full_text = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text and paragraph.text.strip():
                    full_text.append(paragraph.text.strip())
            
            text = "\n".join(full_text)
            confidence = 0.9 if text.strip() else 0.3  # High confidence for digital text
            
            return text, confidence
            
        except Exception as e:
            print(f"Error processing DOCX {docx_path}: {e}")
            return "", 0.0
    
    def _get_confidence(self, image: Image.Image, text: str) -> float:
        """Estimate OCR confidence based on text quality"""
        try:
            if not text or len(text.strip()) < 5:
                return 0.3
            
            # Count words and characters for quality estimation
            words = len(text.split())
            chars = len(text.strip())
            
            if words > 30:
                return 0.85
            elif words > 10:
                return 0.7
            elif words > 3:
                return 0.55
            else:
                return 0.4
        except:
            return 0.5
    
    def detect_file_type(self, file_path: str) -> str:
        """Detect file type from extension"""
        ext = Path(file_path).suffix.lower()
        if ext == '.pdf':
            return 'pdf'
        elif ext in ['.docx', '.doc']:
            return 'docx'
        elif ext in ['.png', '.jpg', '.jpeg', '.tiff']:
            return 'image'
        return 'unknown'
    
    def process_file(
        self, 
        file_path: str, 
        question_number: Optional[int] = None,
        total_questions: int = 5
    ) -> ExtractedText:
        """Main method to process any supported file type"""
        start_time = time.time()
        file_type = self.detect_file_type(file_path)
        
        if file_type == 'pdf':
            full_text, confidence, question_segments = self.extract_from_pdf(file_path)
        elif file_type == 'docx':
            full_text, confidence = self.extract_from_docx(file_path)
            question_segments = {1: full_text}
        elif file_type == 'image':
            full_text, confidence = self.extract_from_image(file_path)
            question_segments = {1: full_text}
        else:
            # Default to image processing
            full_text, confidence = self.extract_from_image(file_path)
            question_segments = {1: full_text}
        
        processing_time = time.time() - start_time
        cleaned_text = self._clean_text(full_text)
        
        # Select focused text if question number provided
        if question_number and question_number in question_segments:
            focused_text = question_segments[question_number]
        else:
            focused_text = cleaned_text
        
        return ExtractedText(
            full_text=full_text,
            cleaned_text=cleaned_text,
            confidence=round(confidence, 3),
            pages_processed=len(question_segments),
            question_segments=question_segments,
            processing_time=round(processing_time, 2),
            file_type=file_type
        )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('--- Page'):
                line = ' '.join(line.split())
                if line:
                    cleaned_lines.append(line)
        
        cleaned = ' '.join(cleaned_lines)
        
        # Replace common OCR mistakes
        replacements = {
            ' | ': ' I ',
            ' 1 ': ' I ',
            ' 0 ': ' O ',
        }
        
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)
        
        return cleaned.strip()