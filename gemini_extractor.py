import google.generativeai as genai
import json
import base64
import time
import statistics
from typing import Dict, Any, List, Optional
from models import MarksheetExtractionResponse, ExtractedField, FieldType, BoundingBox
from config import GEMINI_API_KEY
from file_processor import FileProcessor

class GeminiMarksheetExtractor:
    """Extract marksheet data using Gemini API"""
    
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Confidence calibration parameters
        self.confidence_history = []
        self.calibration_threshold = 0.1  # Minimum confidence difference for calibration
    
    def create_extraction_prompt(self) -> str:
        """Create the prompt for marksheet extraction"""
        return """
        You are an expert at extracting information from marksheets and academic documents. 
        Analyze the provided image or text content and extract the following information with high accuracy.
        
        For each field, provide:
        1. The extracted value (or null if not found)
        2. A confidence score between 0.0 and 1.0 based on how clearly the information is visible/readable
        
        Extract the following information:
        
        CANDIDATE DETAILS:
        - Name (full name of the student)
        - Father's Name (if present)
        - Mother's Name (if present)
        - Roll Number
        - Registration Number
        - Date of Birth (in DD/MM/YYYY or DD-MM-YYYY format)
        - Exam Year
        - Board/University name
        - Institution/School name
        
        SUBJECT-WISE MARKS:
        For each subject found, extract:
        - Subject name
        - Maximum marks or credits
        - Obtained marks or credits
        - Grade (if present)
        
        OVERALL RESULT:
        - Total marks obtained
        - Maximum total marks
        - Percentage
        - CGPA (if present)
        - Overall grade
        - Division/Class
        - Result status (Pass/Fail/First Class/etc.)
        
        ISSUE DETAILS:
        - Issue date
        - Issue place
        
        IMPORTANT INSTRUCTIONS:
        1. Be very careful with numbers - ensure accuracy
        2. If a field is not clearly visible or ambiguous, set confidence low
        3. For dates, standardize to DD/MM/YYYY format
        4. For grades, preserve the exact format as shown
        5. If multiple subjects are present, extract all of them
        6. If you see placeholder text like "XXXXXX", "---", or "N/A", extract it as-is but set confidence to 0.1
        7. For missing or unclear fields, set value to null and confidence to 0.0
        8. Return the response in the exact JSON format specified below
        
        Return ONLY a valid JSON response in this exact format:
        {
            "candidate_details": {
                "name": {"value": "extracted_value", "confidence": 0.95, "field_type": "string"},
                "father_name": {"value": "extracted_value", "confidence": 0.90, "field_type": "string"},
                "mother_name": {"value": "extracted_value", "confidence": 0.90, "field_type": "string"},
                "roll_number": {"value": "extracted_value", "confidence": 0.95, "field_type": "string"},
                "registration_number": {"value": "extracted_value", "confidence": 0.90, "field_type": "string"},
                "date_of_birth": {"value": "DD/MM/YYYY", "confidence": 0.85, "field_type": "date"},
                "exam_year": {"value": "YYYY", "confidence": 0.95, "field_type": "string"},
                "board_university": {"value": "extracted_value", "confidence": 0.90, "field_type": "string"},
                "institution": {"value": "extracted_value", "confidence": 0.85, "field_type": "string"}
            },
            "subject_marks": [
                {
                    "subject": {"value": "Subject Name", "confidence": 0.95, "field_type": "string"},
                    "max_marks": {"value": 100, "confidence": 0.90, "field_type": "number"},
                    "obtained_marks": {"value": 85, "confidence": 0.95, "field_type": "number"},
                    "grade": {"value": "A", "confidence": 0.90, "field_type": "grade"}
                }
            ],
            "overall_result": {
                "total_marks": {"value": 425, "confidence": 0.95, "field_type": "number"},
                "max_total_marks": {"value": 500, "confidence": 0.95, "field_type": "number"},
                "percentage": {"value": 85.0, "confidence": 0.95, "field_type": "number"},
                "grade": {"value": "A", "confidence": 0.90, "field_type": "grade"},
                "division": {"value": "First Class", "confidence": 0.85, "field_type": "string"},
                "result_status": {"value": "Pass", "confidence": 0.95, "field_type": "string"}
            },
            "issue_details": {
                "issue_date": {"value": "DD/MM/YYYY", "confidence": 0.80, "field_type": "date"},
                "issue_place": {"value": "City, State", "confidence": 0.75, "field_type": "string"}
            }
        }
        
        If any field is not found or unclear, set the value to null and confidence to 0.0.
        """
    
    def extract_from_image(self, base64_image: str) -> MarksheetExtractionResponse:
        """Extract data from image using Gemini API"""
        try:
            prompt = self.create_extraction_prompt()
            
            # Create the image part
            image_data = {
                "mime_type": "image/jpeg",
                "data": base64_image
            }
            
            # Generate content
            response = self.model.generate_content([prompt, image_data])
            
            # Parse the response
            response_text = response.text.strip()
            
            # Clean up the response (remove markdown formatting if present)
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            # Parse JSON
            extracted_data = json.loads(response_text)
            
            # Convert to Pydantic model
            return MarksheetExtractionResponse(**extracted_data)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response from Gemini: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error extracting data from image: {str(e)}")
    
    def extract_from_text(self, text_content: str) -> MarksheetExtractionResponse:
        """Extract data from text content using Gemini API"""
        try:
            prompt = self.create_extraction_prompt()
            
            # Add the text content to the prompt
            full_prompt = f"{prompt}\n\nTEXT CONTENT TO ANALYZE:\n{text_content}"
            
            # Generate content
            response = self.model.generate_content(full_prompt)
            
            # Parse the response
            response_text = response.text.strip()
            
            # Clean up the response
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            # Parse JSON
            extracted_data = json.loads(response_text)
            
            # Convert to Pydantic model
            return MarksheetExtractionResponse(**extracted_data)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response from Gemini: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error extracting data from text: {str(e)}")
    
    def extract_marksheet_data(self, content: str, content_type: str) -> MarksheetExtractionResponse:
        """Main extraction method that handles both images and text"""
        if content_type == 'image':
            return self.extract_from_image(content)
        elif content_type == 'pdf_text':
            return self.extract_from_text(content)
        else:
            raise ValueError(f"Unsupported content type: {content_type}")
    
    def calibrate_confidence(self, extracted_data: MarksheetExtractionResponse) -> dict:
        """Apply confidence calibration based on historical data"""
        calibration_info = {
            "method": "Historical Average Calibration",
            "original_confidence": {},
            "calibrated_confidence": {},
            "calibration_factor": 1.0,
            "sample_size": len(self.confidence_history)
        }
        
        # Collect all confidence scores from current extraction
        all_confidences = []
        self._collect_confidences(extracted_data, all_confidences)
        
        if all_confidences:
            avg_confidence = statistics.mean(all_confidences)
            calibration_info["original_confidence"]["average"] = avg_confidence
            
            # If we have historical data, apply calibration
            if len(self.confidence_history) > 10:
                historical_avg = statistics.mean(self.confidence_history[-50:])  # Last 50 extractions
                calibration_factor = historical_avg / avg_confidence if avg_confidence > 0 else 1.0
                calibration_info["calibration_factor"] = calibration_factor
                
                # Apply calibration to all fields
                self._apply_calibration(extracted_data, calibration_factor)
                calibration_info["calibrated_confidence"]["average"] = statistics.mean(all_confidences)
            
            # Update confidence history
            self.confidence_history.extend(all_confidences)
            if len(self.confidence_history) > 1000:  # Keep only last 1000 scores
                self.confidence_history = self.confidence_history[-1000:]
        
        return calibration_info
    
    def _collect_confidences(self, data: MarksheetExtractionResponse, confidences: List[float]):
        """Recursively collect all confidence scores"""
        if hasattr(data, '__dict__'):
            for value in data.__dict__.values():
                if isinstance(value, ExtractedField) and value.confidence is not None:
                    confidences.append(value.confidence)
                elif isinstance(value, list):
                    for item in value:
                        self._collect_confidences(item, confidences)
                elif hasattr(value, '__dict__'):
                    self._collect_confidences(value, confidences)
    
    def _apply_calibration(self, data: MarksheetExtractionResponse, factor: float):
        """Apply calibration factor to all confidence scores"""
        if hasattr(data, '__dict__'):
            for value in data.__dict__.values():
                if isinstance(value, ExtractedField) and value.confidence is not None:
                    value.confidence = min(1.0, value.confidence * factor)
                elif isinstance(value, list):
                    for item in value:
                        self._apply_calibration(item, factor)
                elif hasattr(value, '__dict__'):
                    self._apply_calibration(value, factor)
    
    def batch_extract(self, file_contents: List[bytes], file_extensions: List[str]) -> List[MarksheetExtractionResponse]:
        """Extract data from multiple files in batch"""
        results = []
        
        for content, extension in zip(file_contents, file_extensions):
            try:
                # Process file
                processed_content, content_type = FileProcessor.process_file(content, extension)
                
                # Extract data
                extracted_data = self.extract_marksheet_data(processed_content, content_type)
                
                # Apply confidence calibration
                calibration_info = self.calibrate_confidence(extracted_data)
                extracted_data.confidence_calibration = calibration_info
                
                results.append(extracted_data)
                
            except Exception as e:
                # Create error response
                from models import CandidateDetails, OverallResult, IssueDetails
                error_response = MarksheetExtractionResponse(
                    candidate_details=CandidateDetails(),
                    subject_marks=[],
                    overall_result=OverallResult(),
                    issue_details=IssueDetails(),
                    extraction_metadata={"error": str(e), "status": "failed"}
                )
                results.append(error_response)
        
        return results
