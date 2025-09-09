# AI Marksheet Extraction API

An AI-powered API that extracts structured data from marksheet images and PDFs using Google's Gemini AI. The system provides confidence scores for each extracted field and includes a user-friendly Streamlit web interface.

## Features

- **Multi-format Support**: Handles JPG, PNG, WebP, and PDF files
- **AI-Powered Extraction**: Uses Google Gemini AI for accurate data extraction
- **Confidence Scoring**: Each extracted field includes a confidence score (0-1)
- **Structured Output**: Well-defined JSON schema for extracted data
- **Web Interface**: Streamlit-based UI for easy file upload and result visualization
- **REST API**: FastAPI-based API for programmatic access

## Extracted Fields

### Candidate Details
- Name, Father's Name, Mother's Name
- Roll Number, Registration Number
- Date of Birth, Exam Year
- Board/University, Institution

### Subject-wise Marks
- Subject name, Maximum marks/credits
- Obtained marks/credits, Grade

### Overall Result
- Total marks, Percentage, CGPA
- Grade, Division, Result status

### Issue Details
- Issue date, Issue place

## Installation

1. **Clone or download the project files**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Gemini API Key**:
   - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a `.env` file in the project root:
     ```
     GEMINI_API_KEY=your_actual_api_key_here
     ```

## Usage

### Option 1: Streamlit Web Interface (Recommended)

1. **Start the Streamlit app**:
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Open your browser** and go to `http://localhost:8501`

3. **Upload a marksheet** (JPG, PNG, or PDF) and click "Extract Data"

### Option 2: API Server

1. **Start the API server**:
   ```bash
   python api.py
   ```

2. **The API will be available at** `http://localhost:8000`

3. **API Documentation** is available at `http://localhost:8000/docs`

### API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health information
- `POST /extract` - Extract marksheet data

### Example API Usage

```python
import requests

# Upload and extract marksheet
with open('marksheet.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/extract', files=files)
    
if response.status_code == 200:
    data = response.json()
    print(data)
```

## File Requirements

- **Supported formats**: JPG, JPEG, PNG, WebP, PDF
- **Maximum file size**: 10 MB
- **Image quality**: Higher quality images yield better extraction results
- **PDF support**: Handles both text-based and image-based (scanned) PDFs

## Output Format

The API returns a structured JSON response with the following schema:

```json
{
  "candidate_details": {
    "name": {"value": "John Doe", "confidence": 0.95, "field_type": "string"},
    "roll_number": {"value": "12345", "confidence": 0.90, "field_type": "string"},
    // ... other fields
  },
  "subject_marks": [
    {
      "subject": {"value": "Mathematics", "confidence": 0.95, "field_type": "string"},
      "max_marks": {"value": 100, "confidence": 0.90, "field_type": "number"},
      "obtained_marks": {"value": 85, "confidence": 0.95, "field_type": "number"},
      "grade": {"value": "A", "confidence": 0.90, "field_type": "grade"}
    }
  ],
  "overall_result": {
    "percentage": {"value": 85.0, "confidence": 0.95, "field_type": "number"},
    "grade": {"value": "A", "confidence": 0.90, "field_type": "grade"}
  },
  "issue_details": {
    "issue_date": {"value": "15/06/2023", "confidence": 0.80, "field_type": "date"}
  }
}
```

## Configuration

Key configuration options in `config.py`:

- `MAX_FILE_SIZE`: Maximum file size (default: 10 MB)
- `ALLOWED_EXTENSIONS`: Supported file formats
- `API_HOST` and `API_PORT`: API server configuration

## Troubleshooting

### Common Issues

1. **"Gemini API not configured" error**:
   - Ensure you have set the `GEMINI_API_KEY` in your `.env` file
   - Verify the API key is valid and has proper permissions

2. **File upload errors**:
   - Check file size (must be ≤ 10 MB)
   - Ensure file format is supported (JPG, PNG, PDF)

3. **Poor extraction results**:
   - Use high-quality, clear images
   - Ensure the marksheet is properly oriented
   - Check that text is clearly visible

### API Connection Issues

If using the Streamlit interface with a separate API server:

1. Ensure the API server is running on the correct port
2. Check the API URL in the Streamlit sidebar
3. Verify firewall settings allow connections

## Dependencies

- `streamlit`: Web interface
- `google-generativeai`: Gemini AI integration
- `fastapi`: API framework
- `uvicorn`: ASGI server
- `pydantic`: Data validation
- `Pillow`: Image processing
- `PyPDF2`: PDF processing
- `python-dotenv`: Environment variable management

## License

This project is for educational and demonstration purposes.
