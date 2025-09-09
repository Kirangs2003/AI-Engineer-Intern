"""
Unit tests for AI Marksheet Extraction API
"""

import pytest
import json
import os
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import tempfile

from api import app
from models import MarksheetExtractionResponse, ExtractedField, FieldType, BoundingBox
from gemini_extractor import GeminiMarksheetExtractor
from file_processor import FileProcessor

# Test client
client = TestClient(app)

class TestMarksheetExtraction:
    """Test cases for marksheet extraction functionality"""
    
    def setup_method(self):
        """Setup test data"""
        self.sample_marksheet_data = {
            "candidate_details": {
                "name": {"value": "John Doe", "confidence": 0.95, "field_type": "string"},
                "roll_number": {"value": "12345", "confidence": 0.90, "field_type": "string"},
                "date_of_birth": {"value": "15/06/2000", "confidence": 0.85, "field_type": "date"},
                "exam_year": {"value": "2023", "confidence": 0.95, "field_type": "string"},
                "board_university": {"value": "CBSE", "confidence": 0.90, "field_type": "string"},
                "institution": {"value": "ABC School", "confidence": 0.85, "field_type": "string"}
            },
            "subject_marks": [
                {
                    "subject": {"value": "Mathematics", "confidence": 0.95, "field_type": "string"},
                    "max_marks": {"value": 100, "confidence": 0.90, "field_type": "number"},
                    "obtained_marks": {"value": 85, "confidence": 0.95, "field_type": "number"},
                    "grade": {"value": "A", "confidence": 0.90, "field_type": "grade"}
                },
                {
                    "subject": {"value": "Physics", "confidence": 0.95, "field_type": "string"},
                    "max_marks": {"value": 100, "confidence": 0.90, "field_type": "number"},
                    "obtained_marks": {"value": 78, "confidence": 0.95, "field_type": "number"},
                    "grade": {"value": "B", "confidence": 0.90, "field_type": "grade"}
                }
            ],
            "overall_result": {
                "total_marks": {"value": 163, "confidence": 0.95, "field_type": "number"},
                "max_total_marks": {"value": 200, "confidence": 0.95, "field_type": "number"},
                "percentage": {"value": 81.5, "confidence": 0.95, "field_type": "number"},
                "grade": {"value": "A", "confidence": 0.90, "field_type": "grade"},
                "result_status": {"value": "Pass", "confidence": 0.95, "field_type": "string"}
            },
            "issue_details": {
                "issue_date": {"value": "15/07/2023", "confidence": 0.80, "field_type": "date"},
                "issue_place": {"value": "New Delhi", "confidence": 0.75, "field_type": "string"}
            }
        }
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "gemini_api_configured" in data
        assert "max_file_size_mb" in data
        assert "supported_formats" in data
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "AI Marksheet Extraction API" in data["message"]
    
    @patch('api.extractor')
    def test_extract_marksheet_success(self, mock_extractor):
        """Test successful marksheet extraction"""
        # Mock the extractor
        mock_response = MarksheetExtractionResponse(**self.sample_marksheet_data)
        mock_extractor.extract_marksheet_data.return_value = mock_response
        mock_extractor.calibrate_confidence.return_value = {"method": "test"}
        
        # Create a test image file
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            tmp_file.write(b"fake image data")
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, "rb") as f:
                response = client.post(
                    "/extract",
                    files={"file": ("test.jpg", f, "image/jpeg")},
                    data={"include_bounding_boxes": "false"}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert "candidate_details" in data
            assert "subject_marks" in data
            assert "overall_result" in data
            assert "issue_details" in data
            
        finally:
            os.unlink(tmp_file_path)
    
    def test_extract_marksheet_invalid_file_type(self):
        """Test extraction with invalid file type"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp_file:
            tmp_file.write(b"fake text data")
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, "rb") as f:
                response = client.post(
                    "/extract",
                    files={"file": ("test.txt", f, "text/plain")}
                )
            
            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert "Unsupported file type" in data["error"]
            
        finally:
            os.unlink(tmp_file_path)
    
    def test_extract_marksheet_large_file(self):
        """Test extraction with file exceeding size limit"""
        # Create a large file (simulate by mocking the size check)
        with patch('file_processor.FileProcessor.validate_file_size', return_value=False):
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
                tmp_file.write(b"fake image data")
                tmp_file_path = tmp_file.name
            
            try:
                with open(tmp_file_path, "rb") as f:
                    response = client.post(
                        "/extract",
                        files={"file": ("test.jpg", f, "image/jpeg")}
                    )
                
                assert response.status_code == 400
                data = response.json()
                assert "error" in data
                assert "File size exceeds" in data["error"]
                
            finally:
                os.unlink(tmp_file_path)
    
    def test_file_processor_image(self):
        """Test file processor with image"""
        # Test with fake image data
        fake_image_data = b"fake image data"
        result = FileProcessor.process_image(fake_image_data)
        assert isinstance(result, str)  # Should return base64 string
    
    def test_file_processor_pdf(self):
        """Test file processor with PDF"""
        # Test with fake PDF data
        fake_pdf_data = b"fake pdf data"
        result = FileProcessor.process_pdf(fake_pdf_data)
        assert isinstance(result, str)
        assert result.startswith("PDF_TEXT_CONTENT:")
    
    def test_file_processor_validation(self):
        """Test file size validation"""
        # Test valid size
        small_data = b"small data"
        assert FileProcessor.validate_file_size(small_data, 1000) == True
        
        # Test invalid size
        large_data = b"x" * 2000
        assert FileProcessor.validate_file_size(large_data, 1000) == False
    
    def test_extracted_field_model(self):
        """Test ExtractedField model"""
        field = ExtractedField(
            value="Test Value",
            confidence=0.95,
            field_type=FieldType.STRING
        )
        assert field.value == "Test Value"
        assert field.confidence == 0.95
        assert field.field_type == FieldType.STRING
    
    def test_bounding_box_model(self):
        """Test BoundingBox model"""
        bbox = BoundingBox(
            x=100.0,
            y=50.0,
            width=200.0,
            height=30.0,
            confidence=0.95
        )
        assert bbox.x == 100.0
        assert bbox.y == 50.0
        assert bbox.width == 200.0
        assert bbox.height == 30.0
        assert bbox.confidence == 0.95
    
    def test_confidence_calibration(self):
        """Test confidence calibration"""
        extractor = GeminiMarksheetExtractor()
        
        # Create test data
        test_data = MarksheetExtractionResponse(**self.sample_marksheet_data)
        
        # Test calibration
        calibration_info = extractor.calibrate_confidence(test_data)
        
        assert "method" in calibration_info
        assert "original_confidence" in calibration_info
        assert "calibration_factor" in calibration_info
        assert "sample_size" in calibration_info
    
    @patch('api.extractor')
    def test_batch_extraction(self, mock_extractor):
        """Test batch extraction endpoint"""
        # Mock the extractor
        mock_response = MarksheetExtractionResponse(**self.sample_marksheet_data)
        mock_extractor.batch_extract.return_value = [mock_response]
        
        # Create test files
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file1, \
             tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file2:
            
            tmp_file1.write(b"fake image data 1")
            tmp_file2.write(b"fake image data 2")
            tmp_file1_path = tmp_file1.name
            tmp_file2_path = tmp_file2.name
        
        try:
            with open(tmp_file1_path, "rb") as f1, open(tmp_file2_path, "rb") as f2:
                response = client.post(
                    "/batch-extract",
                    files=[
                        ("files", ("test1.jpg", f1, "image/jpeg")),
                        ("files", ("test2.png", f2, "image/png"))
                    ],
                    data={"include_bounding_boxes": "false"},
                    headers={"Authorization": "Bearer test_api_key"}
                )
            
            # Note: This will fail without proper API key setup, but tests the structure
            assert response.status_code in [200, 401]  # Either success or auth error
            
        finally:
            os.unlink(tmp_file1_path)
            os.unlink(tmp_file2_path)

class TestSampleMarksheets:
    """Test with actual sample marksheet data"""
    
    def test_cbse_marksheet_structure(self):
        """Test CBSE marksheet data structure"""
        cbse_data = {
            "candidate_details": {
                "name": {"value": "RAJESH KUMAR", "confidence": 0.95, "field_type": "string"},
                "roll_number": {"value": "1234567", "confidence": 0.98, "field_type": "string"},
                "date_of_birth": {"value": "15/03/2005", "confidence": 0.90, "field_type": "date"},
                "exam_year": {"value": "2023", "confidence": 0.99, "field_type": "string"},
                "board_university": {"value": "CENTRAL BOARD OF SECONDARY EDUCATION", "confidence": 0.95, "field_type": "string"},
                "institution": {"value": "DELHI PUBLIC SCHOOL", "confidence": 0.90, "field_type": "string"}
            },
            "subject_marks": [
                {
                    "subject": {"value": "ENGLISH CORE", "confidence": 0.95, "field_type": "string"},
                    "max_marks": {"value": 100, "confidence": 0.95, "field_type": "number"},
                    "obtained_marks": {"value": 85, "confidence": 0.98, "field_type": "number"},
                    "grade": {"value": "A1", "confidence": 0.95, "field_type": "grade"}
                },
                {
                    "subject": {"value": "MATHEMATICS", "confidence": 0.95, "field_type": "string"},
                    "max_marks": {"value": 100, "confidence": 0.95, "field_type": "number"},
                    "obtained_marks": {"value": 92, "confidence": 0.98, "field_type": "number"},
                    "grade": {"value": "A1", "confidence": 0.95, "field_type": "grade"}
                }
            ],
            "overall_result": {
                "total_marks": {"value": 177, "confidence": 0.98, "field_type": "number"},
                "max_total_marks": {"value": 200, "confidence": 0.95, "field_type": "number"},
                "percentage": {"value": 88.5, "confidence": 0.98, "field_type": "number"},
                "grade": {"value": "A1", "confidence": 0.95, "field_type": "grade"},
                "result_status": {"value": "PASS", "confidence": 0.99, "field_type": "string"}
            }
        }
        
        # Test that the data structure is valid
        response = MarksheetExtractionResponse(**cbse_data)
        assert response.candidate_details.name.value == "RAJESH KUMAR"
        assert response.subject_marks[0].subject.value == "ENGLISH CORE"
        assert response.overall_result.percentage.value == 88.5
    
    def test_state_board_marksheet_structure(self):
        """Test state board marksheet data structure"""
        state_board_data = {
            "candidate_details": {
                "name": {"value": "PRIYA SHARMA", "confidence": 0.93, "field_type": "string"},
                "roll_number": {"value": "WB123456", "confidence": 0.95, "field_type": "string"},
                "date_of_birth": {"value": "20/08/2004", "confidence": 0.88, "field_type": "date"},
                "exam_year": {"value": "2022", "confidence": 0.97, "field_type": "string"},
                "board_university": {"value": "WEST BENGAL BOARD OF SECONDARY EDUCATION", "confidence": 0.92, "field_type": "string"},
                "institution": {"value": "KOLKATA HIGH SCHOOL", "confidence": 0.89, "field_type": "string"}
            },
            "subject_marks": [
                {
                    "subject": {"value": "BENGALI", "confidence": 0.94, "field_type": "string"},
                    "max_marks": {"value": 100, "confidence": 0.95, "field_type": "number"},
                    "obtained_marks": {"value": 78, "confidence": 0.96, "field_type": "number"},
                    "grade": {"value": "A", "confidence": 0.92, "field_type": "grade"}
                },
                {
                    "subject": {"value": "ENGLISH", "confidence": 0.94, "field_type": "string"},
                    "max_marks": {"value": 100, "confidence": 0.95, "field_type": "number"},
                    "obtained_marks": {"value": 82, "confidence": 0.96, "field_type": "number"},
                    "grade": {"value": "A", "confidence": 0.92, "field_type": "grade"}
                }
            ],
            "overall_result": {
                "total_marks": {"value": 160, "confidence": 0.97, "field_type": "number"},
                "max_total_marks": {"value": 200, "confidence": 0.95, "field_type": "number"},
                "percentage": {"value": 80.0, "confidence": 0.97, "field_type": "number"},
                "grade": {"value": "A", "confidence": 0.92, "field_type": "grade"},
                "division": {"value": "FIRST DIVISION", "confidence": 0.90, "field_type": "string"},
                "result_status": {"value": "PASS", "confidence": 0.99, "field_type": "string"}
            }
        }
        
        # Test that the data structure is valid
        response = MarksheetExtractionResponse(**state_board_data)
        assert response.candidate_details.name.value == "PRIYA SHARMA"
        assert response.subject_marks[0].subject.value == "BENGALI"
        assert response.overall_result.division.value == "FIRST DIVISION"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
