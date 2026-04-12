import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import re
import time
from datetime import datetime

from .models import EvaluationResult, SimilarityBreakdown

class EvaluationEngine:
    def __init__(self):
        # Initialize sentence transformer for semantic similarity
        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_available = True
        except Exception as e:
            print(f"Warning: Could not load embedding model: {e}")
            self.embedding_available = False
            self.model = None
        
        # Common academic keywords by subject (can be extended)
        self.subject_keywords = {
            'default': ['explain', 'describe', 'discuss', 'compare', 'analyze', 
                       'define', 'state', 'list', 'give', 'what', 'how', 'why'],
            'computer_science': ['algorithm', 'function', 'class', 'database', 'network',
                               'memory', 'processor', 'code', 'program', 'data', 'system'],
            'physics': ['force', 'energy', 'motion', 'velocity', 'acceleration', 'mass',
                       'gravity', 'momentum', 'work', 'power', 'electric'],
            'chemistry': ['reaction', 'element', 'compound', 'molecule', 'acid', 'base',
                         'oxidation', 'reduction', 'bond', 'atom'],
            'biology': ['cell', 'organism', 'gene', 'dna', 'protein', 'evolution',
                       'ecosystem', 'species', 'tissue', 'organ']
        }
    
    def evaluate(
        self,
        student_answer: str,
        model_answer: str,
        question: str,
        max_marks: int = 10,
        checked_copies: Optional[List[str]] = None,
        subject: str = 'default'
    ) -> EvaluationResult:
        """Main evaluation function combining multiple scoring methods"""
        start_time = time.time()
        
        if not student_answer or not student_answer.strip():
            return self._create_empty_result(
                "No text could be extracted from the answer sheet.", 
                max_marks
            )
        
        # Clean inputs
        student_clean = self._clean_text(student_answer)
        model_clean = self._clean_text(model_answer)
        
        if not student_clean:
            return self._create_empty_result(
                "Extracted text appears to be empty or unreadable.", 
                max_marks
            )
        
        # Calculate different similarity scores
        semantic_score = self._calculate_semantic_similarity(student_clean, model_clean)
        keyword_score = self._calculate_keyword_match(student_clean, model_clean, subject)
        length_score = self._calculate_length_similarity(student_clean, model_clean)
        structure_score = self._calculate_structure_similarity(student_clean, model_clean)
        
        # Combined score (weighted average)
        weights = {
            'semantic': 0.5,
            'keyword': 0.25,
            'length': 0.1,
            'structure': 0.15
        }
        
        final_score = (
            semantic_score * weights['semantic'] +
            keyword_score * weights['keyword'] +
            length_score * weights['length'] +
            structure_score * weights['structure']
        )
        
        # Convert to marks (out of max_marks)
        marks_obtained = round(final_score * max_marks, 1)
        
        # Generate feedback
        feedback = self._generate_feedback(
            marks_obtained, max_marks, semantic_score, keyword_score,
            student_clean, model_clean, question
        )
        
        # Find matched keywords
        keywords_matched = self._extract_matched_keywords(student_clean, model_clean, subject)
        
        processing_time = time.time() - start_time
        
        similarity_breakdown = {
            "semantic_similarity": round(semantic_score, 3),
            "keyword_match_score": round(keyword_score, 3),
            "length_similarity": round(length_score, 3),
            "structure_similarity": round(structure_score, 3),
            "overall_score": round(final_score, 3)
        }
        
        return EvaluationResult(
            extracted_text=student_clean,
            score=marks_obtained,
            max_marks=max_marks,
            confidence=round(semantic_score * 0.7 + 0.3, 2),  # Confidence based on semantic score
            feedback=feedback,
            keywords_matched=keywords_matched,
            similarity_breakdown=similarity_breakdown,
            processing_time=round(processing_time, 2),
            timestamp=datetime.now()
        )
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity using embeddings"""
        if not self.embedding_available or not text1 or not text2:
            # Fallback to simple word overlap
            return self._simple_text_similarity(text1, text2)
        
        try:
            embeddings = self.model.encode([text1, text2])
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return float(max(0.0, min(1.0, similarity)))
        except:
            return self._simple_text_similarity(text1, text2)
    
    def _simple_text_similarity(self, text1: str, text2: str) -> float:
        """Fallback similarity using word overlap"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_keyword_match(self, student_text: str, model_text: str, subject: str = 'default') -> float:
        """Calculate keyword matching score"""
        student_lower = student_text.lower()
        model_lower = model_text.lower()
        
        # Get relevant keywords
        keywords = self.subject_keywords.get(subject, self.subject_keywords['default'])
        
        # Extract important words from model answer
        model_words = set(re.findall(r'\b\w+\b', model_lower))
        important_keywords = [word for word in model_words if len(word) > 3]
        
        if not important_keywords:
            return 0.5  # Default score
        
        # Count matches
        matches = sum(1 for keyword in important_keywords if keyword in student_lower)
        score = matches / len(important_keywords)
        
        return min(1.0, score * 1.2)  # Boost slightly for keyword matches
    
    def _calculate_length_similarity(self, text1: str, text2: str) -> float:
        """Compare answer lengths (reasonable length gets better score)"""
        len1 = len(text1.split())
        len2 = len(text2.split())
        
        if len2 == 0:
            return 0.5
        
        ratio = min(len1, len2) / max(len1, len2)
        return ratio
    
    def _calculate_structure_similarity(self, student_text: str, model_text: str) -> float:
        """Compare structural elements like bullet points, numbered lists"""
        student_has_bullets = bool(re.search(r'^\s*[\-\•\•]\s', student_text, re.MULTILINE))
        model_has_bullets = bool(re.search(r'^\s*[\-\•\•]\s', model_text, re.MULTILINE))
        
        student_has_numbers = bool(re.search(r'^\s*\d+\.', student_text, re.MULTILINE))
        model_has_numbers = bool(re.search(r'^\s*\d+\.', model_text, re.MULTILINE))
        
        score = 0.5  # Base score
        
        if student_has_bullets and model_has_bullets:
            score += 0.2
        if student_has_numbers and model_has_numbers:
            score += 0.2
        
        return min(1.0, score)
    
    def _generate_feedback(
        self, 
        marks: float, 
        max_marks: int, 
        semantic_score: float,
        keyword_score: float,
        student_text: str,
        model_text: str,
        question: str
    ) -> str:
        """Generate human-like feedback"""
        percentage = (marks / max_marks) * 100
        
        if percentage >= 85:
            feedback = f"Excellent answer! You scored {marks}/{max_marks}. "
            feedback += "Your response demonstrates strong understanding and covers all key points."
        elif percentage >= 70:
            feedback = f"Good work! Score: {marks}/{max_marks}. "
            feedback += "You have covered most important concepts. Consider adding more specific examples."
        elif percentage >= 50:
            feedback = f"Average performance. Score: {marks}/{max_marks}. "
            feedback += "You understood the basic concepts but missed some key points. Review the model answer."
        else:
            feedback = f"Needs improvement. Score: {marks}/{max_marks}. "
            feedback += "Please review the core concepts. Your answer lacks several important points."
        
        # Add specific suggestions
        if semantic_score < 0.6:
            feedback += " Focus more on conceptual understanding."
        if keyword_score < 0.5:
            feedback += " Include more domain-specific terminology."
        
        return feedback.strip()
    
    def _extract_matched_keywords(self, student_text: str, model_text: str, subject: str) -> List[str]:
        """Extract keywords that appear in both answers"""
        student_lower = student_text.lower()
        model_lower = model_text.lower()
        
        keywords = self.subject_keywords.get(subject, self.subject_keywords['default'])
        matched = []
        
        for keyword in keywords:
            if keyword in student_lower and keyword in model_lower:
                matched.append(keyword)
        
        # Also extract longer important words from model answer that appear in student answer
        model_words = re.findall(r'\b\w{4,}\b', model_lower)
        for word in model_words:
            if word in student_lower and word not in matched and word not in keywords:
                matched.append(word)
                if len(matched) >= 8:  # Limit results
                    break
        
        return matched[:10]  # Return top 10 matched keywords
    
    def _clean_text(self, text: str) -> str:
        """Clean text for evaluation"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?()-]', '', text)
        return text.strip()
    
    def _create_empty_result(self, message: str, max_marks: int) -> EvaluationResult:
        """Create result for failed extraction"""
        return EvaluationResult(
            extracted_text="",
            score=0.0,
            max_marks=max_marks,
            confidence=0.0,
            feedback=message,
            keywords_matched=[],
            similarity_breakdown={
                "semantic_similarity": 0.0,
                "keyword_match_score": 0.0,
                "length_similarity": 0.0,
                "structure_similarity": 0.0,
                "overall_score": 0.0
            },
            timestamp=datetime.now()
        )