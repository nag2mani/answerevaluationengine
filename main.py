from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

from src.ocr_processor import OCRProcessor
from src.evaluation_engine import EvaluationEngine
from src.models import (
    AnswerSheetUpload, 
    ExtractedText, 
    EvaluationResult, 
    EvaluationRequest
)

app = FastAPI(
    title="Answer Evaluation Engine",
    description="AI-powered handwritten answer sheet evaluation system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
os.makedirs("static", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize processors
ocr_processor = OCRProcessor()
evaluation_engine = EvaluationEngine()

class HealthResponse(BaseModel):
    status: str
    version: str
    ocr_available: bool

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main UI"""
    return templates.TemplateResponse("index.html", {"request": {}})

@app.get("/health")
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        ocr_available=ocr_processor.is_available()
    )

@app.post("/api/extract-text")
async def extract_text(
    file: UploadFile = File(...),
    question_number: Optional[int] = Form(None),
    total_questions: Optional[int] = Form(5)
) -> ExtractedText:
    """
    Extract handwritten text from uploaded answer sheet
    Supports: PDF, PNG, JPG, JPEG, DOCX
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    # Save uploaded file temporarily
    temp_dir = Path("uploads")
    temp_dir.mkdir(exist_ok=True)
    
    file_path = temp_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process with OCR
        extracted = ocr_processor.process_file(
            str(file_path), 
            question_number=question_number,
            total_questions=total_questions
        )
        
        return extracted
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        # Clean up
        if file_path.exists():
            file_path.unlink()

@app.post("/api/evaluate")
async def evaluate_answer(request: EvaluationRequest) -> EvaluationResult:
    """
    Evaluate student answer against model answer and checked copies
    """
    try:
        result = evaluation_engine.evaluate(
            student_answer=request.student_answer,
            model_answer=request.model_answer,
            question=request.question,
            max_marks=request.max_marks,
            checked_copies=request.checked_copies or []
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@app.post("/api/batch-evaluate")
async def batch_evaluate(
    files: List[UploadFile] = File(...),
    model_answer: str = Form(...),
    question: str = Form(...),
    max_marks: int = Form(10)
) -> List[EvaluationResult]:
    """
    Batch evaluate multiple answer sheets
    """
    results = []
    
    for file in files:
        if not file.filename:
            continue
            
        temp_path = Path("uploads") / f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        
        try:
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Extract text
            extracted = ocr_processor.process_file(str(temp_path))
            
            # Evaluate
            result = evaluation_engine.evaluate(
                student_answer=extracted.full_text,
                model_answer=model_answer,
                question=question,
                max_marks=max_marks
            )
            results.append(result)
            
        except Exception as e:
            # Add error result
            results.append(EvaluationResult(
                extracted_text="",
                score=0.0,
                max_marks=max_marks,
                confidence=0.0,
                feedback=f"Error processing {file.filename}: {str(e)}",
                keywords_matched=[],
                similarity_breakdown={}
            ))
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    return results

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)