from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class AnswerSheetUpload(BaseModel):
    file: Any  # File upload
    question_number: Optional[int] = None
    total_questions: Optional[int] = 5
    student_id: Optional[str] = None

class ExtractedText(BaseModel):
    full_text: str
    cleaned_text: str
    confidence: float
    pages_processed: int
    question_segments: Dict[int, str]
    raw_ocr_output: Optional[str] = None
    processing_time: float
    file_type: str

class SimilarityBreakdown(BaseModel):
    semantic_similarity: float
    keyword_match_score: float
    length_similarity: float
    structure_similarity: float
    overall_score: float

class EvaluationResult(BaseModel):
    extracted_text: str
    score: float
    max_marks: int
    confidence: float
    feedback: str
    keywords_matched: List[str]
    similarity_breakdown: Dict[str, float]
    processing_time: Optional[float] = None
    timestamp: Optional[datetime] = None
    student_id: Optional[str] = None

class EvaluationRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    student_answer: str
    model_answer: str
    question: str
    max_marks: int = 10
    checked_copies: Optional[List[str]] = None
    student_id: Optional[str] = None