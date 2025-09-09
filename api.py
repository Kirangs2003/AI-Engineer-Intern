from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import time
from typing import Dict, Any, List, Optional
import uvicorn

from models import MarksheetExtractionResponse, ErrorResponse, BatchExtractionRequest, BatchExtractionResponse, CandidateDetails, OverallResult, IssueDetails
from file_processor import FileProcessor
from gemini_extractor import GeminiMarksheetExtractor
from config import MAX_FILE_SIZE, ALLOWED_EXTENSIONS
from auth import get_api_key, get_optional_api_key

app = FastAPI(
    title="AI Marksheet Extraction API",
    description="Extract structured data from marksheet images and PDFs using AI",
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

# Initialize the extractor
try:
    extractor = GeminiMarksheetExtractor()
except ValueError as e:
    print(f"Warning: {e}")
    extractor = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI Marksheet Extraction API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "gemini_api_configured": extractor is not None,
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
        "supported_formats": list(ALLOWED_EXTENSIONS)
    }

@app.post("/extract", response_model=MarksheetExtractionResponse)
async def extract_marksheet(
    file: UploadFile = File(...),
    include_bounding_boxes: bool = Form(False),
    api_key: Optional[str] = Depends(get_optional_api_key)
):
    """
    Extract marksheet data from uploaded file
    
    Args:
        file: Uploaded marksheet file (JPG, PNG, or PDF)
        
    Returns:
        Extracted marksheet data with confidence scores
    """
    if not extractor:
        raise HTTPException(
            status_code=500,
            detail="Gemini API not configured. Please set GEMINI_API_KEY environment variable."
        )
    
    # Validate file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed types: {list(ALLOWED_EXTENSIONS)}"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Validate file size
        if not FileProcessor.validate_file_size(file_content, MAX_FILE_SIZE):
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)} MB"
            )
        
        # Process file
        content, content_type = FileProcessor.process_file(file_content, file_extension)
        
        # Extract data using Gemini
        extracted_data = extractor.extract_marksheet_data(content, content_type)
        
        # Apply confidence calibration
        calibration_info = extractor.calibrate_confidence(extracted_data)
        extracted_data.confidence_calibration = calibration_info
        
        # Add metadata
        extracted_data.extraction_metadata = {
            "filename": file.filename,
            "file_size": len(file_content),
            "content_type": content_type,
            "processing_status": "success",
            "include_bounding_boxes": include_bounding_boxes,
            "api_key_used": api_key is not None
        }
        
        return extracted_data
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/batch-extract", response_model=BatchExtractionResponse)
async def batch_extract_marksheets(
    files: List[UploadFile] = File(...),
    include_bounding_boxes: bool = Form(False),
    api_key: Optional[str] = Depends(get_optional_api_key)
):
    """
    Extract marksheet data from multiple uploaded files in batch
    
    Args:
        files: List of uploaded marksheet files
        include_bounding_boxes: Whether to include bounding box coordinates
        api_key: API key for authentication (optional)
        
    Returns:
        Batch extraction results with statistics
    """
    if not extractor:
        raise HTTPException(
            status_code=500,
            detail="Gemini API not configured. Please set GEMINI_API_KEY environment variable."
        )
    
    if len(files) > 10:  # Limit batch size
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 files allowed per batch request"
        )
    
    # Log API key usage (if provided)
    if api_key:
        print(f"Batch processing request with API key: {api_key[:10]}...")
    else:
        print("Batch processing request without API key (public access)")
    
    start_time = time.time()
    results = []
    successful = 0
    failed = 0
    
    try:
        # Process all files
        file_contents = []
        file_extensions = []
        
        for file in files:
            # Validate file extension
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension not in ALLOWED_EXTENSIONS:
                failed += 1
                error_response = MarksheetExtractionResponse(
                    candidate_details=CandidateDetails(),
                    subject_marks=[],
                    overall_result=OverallResult(),
                    issue_details=IssueDetails(),
                    extraction_metadata={
                        "filename": file.filename,
                        "error": f"Unsupported file type: {file_extension}",
                        "status": "failed"
                    }
                )
                results.append(error_response)
                continue
            
            # Read file content
            file_content = await file.read()
            
            # Validate file size
            if not FileProcessor.validate_file_size(file_content, MAX_FILE_SIZE):
                failed += 1
                error_response = MarksheetExtractionResponse(
                    candidate_details=CandidateDetails(),
                    subject_marks=[],
                    overall_result=OverallResult(),
                    issue_details=IssueDetails(),
                    extraction_metadata={
                        "filename": file.filename,
                        "error": f"File size exceeds maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)} MB",
                        "status": "failed"
                    }
                )
                results.append(error_response)
                continue
            
            file_contents.append(file_content)
            file_extensions.append(file_extension)
        
        # Batch extract using Gemini
        if file_contents:
            batch_results = extractor.batch_extract(file_contents, file_extensions)
            
            # Update metadata for each result
            for i, result in enumerate(batch_results):
                if i < len(files):
                    result.extraction_metadata.update({
                        "filename": files[i].filename,
                        "file_size": len(file_contents[i]),
                        "include_bounding_boxes": include_bounding_boxes,
                        "api_key_used": True,
                        "batch_processing": True
                    })
                    
                    if result.extraction_metadata.get("status") != "failed":
                        successful += 1
                    else:
                        failed += 1
                
                results.append(result)
        
        processing_time = time.time() - start_time
        
        return BatchExtractionResponse(
            results=results,
            total_processed=len(files),
            successful=successful,
            failed=failed,
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch processing error: {str(e)}")

@app.get("/api-key")
async def get_api_key_info(api_key: Optional[str] = Depends(get_optional_api_key)):
    """Get information about API key usage"""
    if api_key:
        return {
            "api_key_provided": True,
            "api_key_valid": True,
            "permissions": ["single_extract", "batch_extract"],
            "rate_limit": "100 requests per hour"
        }
    else:
        return {
            "api_key_provided": False,
            "message": "No API key required for basic operations",
            "permissions": ["single_extract", "batch_extract"],
            "note": "All endpoints are publicly accessible"
        }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=exc.detail).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc)
        ).dict()
    )

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
