from pydantic import BaseModel, Field
from typing import List, Optional, Union
from enum import Enum

class BoundingBox(BaseModel):
    """Bounding box coordinates for extracted fields"""
    x: Optional[float] = Field(default=None, description="X coordinate (left)")
    y: Optional[float] = Field(default=None, description="Y coordinate (top)")
    width: Optional[float] = Field(default=None, description="Width of the bounding box")
    height: Optional[float] = Field(default=None, description="Height of the bounding box")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Confidence score for the bounding box")

class FieldType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    DATE = "date"
    GRADE = "grade"

class ExtractedField(BaseModel):
    value: Union[str, int, float, None] = Field(description="The extracted value")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    field_type: FieldType = Field(description="Type of the field")
    bounding_box: Optional[BoundingBox] = Field(default=None, description="Bounding box coordinates if available")

class CandidateDetails(BaseModel):
    name: Optional[ExtractedField] = None
    father_name: Optional[ExtractedField] = None
    mother_name: Optional[ExtractedField] = None
    roll_number: Optional[ExtractedField] = None
    registration_number: Optional[ExtractedField] = None
    date_of_birth: Optional[ExtractedField] = None
    exam_year: Optional[ExtractedField] = None
    board_university: Optional[ExtractedField] = None
    institution: Optional[ExtractedField] = None

class SubjectMarks(BaseModel):
    subject: ExtractedField
    max_marks: Optional[ExtractedField] = None
    max_credits: Optional[ExtractedField] = None
    obtained_marks: Optional[ExtractedField] = None
    obtained_credits: Optional[ExtractedField] = None
    grade: Optional[ExtractedField] = None

class OverallResult(BaseModel):
    total_marks: Optional[ExtractedField] = None
    max_total_marks: Optional[ExtractedField] = None
    percentage: Optional[ExtractedField] = None
    cgpa: Optional[ExtractedField] = None
    grade: Optional[ExtractedField] = None
    division: Optional[ExtractedField] = None
    result_status: Optional[ExtractedField] = None

class IssueDetails(BaseModel):
    issue_date: Optional[ExtractedField] = None
    issue_place: Optional[ExtractedField] = None

class MarksheetExtractionResponse(BaseModel):
    candidate_details: CandidateDetails
    subject_marks: List[SubjectMarks]
    overall_result: OverallResult
    issue_details: IssueDetails
    extraction_metadata: dict = Field(default_factory=dict)
    confidence_calibration: Optional[dict] = Field(default=None, description="Confidence calibration information")

class BatchExtractionRequest(BaseModel):
    """Request model for batch processing"""
    files: List[str] = Field(description="List of file paths or URLs to process")
    include_bounding_boxes: bool = Field(default=False, description="Whether to include bounding box coordinates")

class BatchExtractionResponse(BaseModel):
    """Response model for batch processing"""
    results: List[MarksheetExtractionResponse] = Field(description="List of extraction results")
    total_processed: int = Field(description="Total number of files processed")
    successful: int = Field(description="Number of successful extractions")
    failed: int = Field(description="Number of failed extractions")
    processing_time: float = Field(description="Total processing time in seconds")

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
