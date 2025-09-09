import streamlit as st
import requests
import json
import os
from typing import Dict, Any
import base64
from io import BytesIO
from PIL import Image

# Page configuration
st.set_page_config(
    page_title="AI Marksheet Extraction",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 600;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #2c3e50;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
    }
    .confidence-high {
        color: #27ae60;
        font-weight: 600;
    }
    .confidence-medium {
        color: #f39c12;
        font-weight: 600;
    }
    .confidence-low {
        color: #e74c3c;
        font-weight: 600;
    }
    .extracted-value {
        background-color: #f8f9fa;
        padding: 0.4rem 0.8rem;
        border-radius: 0.3rem;
        border-left: 3px solid #1f77b4;
        margin: 0.4rem 0;
        font-size: 0.9rem;
    }
    .stSidebar {
        background-color: #fafafa;
    }
</style>
""", unsafe_allow_html=True)

def get_confidence_class(confidence: float) -> str:
    """Get CSS class based on confidence score"""
    if confidence >= 0.8:
        return "confidence-high"
    elif confidence >= 0.5:
        return "confidence-medium"
    else:
        return "confidence-low"

def display_extracted_field(field_name: str, field_data: Dict[str, Any], key_prefix: str = ""):
    """Display an extracted field with confidence score"""
    if field_data and field_data.get('value') is not None:
        value = field_data['value']
        confidence = field_data.get('confidence', 0.0)
        field_type = field_data.get('field_type', 'string')
        
        # Check if value is placeholder text
        is_placeholder = str(value).upper() in ['XXXXXX', '---', 'N/A', 'NULL', 'NOT AVAILABLE']
        
        confidence_class = get_confidence_class(confidence)
        
        # Add warning for placeholder data
        placeholder_warning = ""
        if is_placeholder and confidence < 0.5:
            placeholder_warning = '<br><span style="color: #f39c12; font-size: 0.8em;">⚠️ Placeholder data detected</span>'
        
        st.markdown(f"""
        <div class="extracted-value">
            <strong>{field_name}:</strong> {value}{placeholder_warning}<br>
            <span class="{confidence_class}">Confidence: {confidence:.2f}</span> | 
            <em>Type: {field_type}</em>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="extracted-value">
            <strong>{field_name}:</strong> <em>Not found</em><br>
            <span class="confidence-low">Confidence: 0.00</span>
        </div>
        """, unsafe_allow_html=True)

def display_subject_marks(subject_marks: list):
    """Display subject-wise marks in a clean format"""
    if not subject_marks:
        st.info("No subject marks found.")
        return
    
    for i, subject in enumerate(subject_marks):
        subject_name = subject.get('subject', {}).get('value', f'Subject {i+1}')
        with st.expander(f"📖 {subject_name}"):
            col1, col2 = st.columns(2)
            
            with col1:
                display_extracted_field("Subject", subject.get('subject', {}))
                display_extracted_field("Max Marks", subject.get('max_marks', {}))
                display_extracted_field("Obtained Marks", subject.get('obtained_marks', {}))
            
            with col2:
                display_extracted_field("Max Credits", subject.get('max_credits', {}))
                display_extracted_field("Obtained Credits", subject.get('obtained_credits', {}))
                display_extracted_field("Grade", subject.get('grade', {}))

def main():
    # Header
    st.markdown('<h1 class="main-header">📊 AI Marksheet Extraction</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        # Default values
        api_url = "http://localhost:8000"
        max_file_size = 10
        
        # Processing mode selection
        st.markdown("### 🔧 Processing Mode")
        processing_mode = st.radio(
            "Choose processing mode:",
            ["Single File", "Batch Processing"],
            help="Single file processes one marksheet at a time. Batch processing handles multiple files simultaneously."
        )
    
    # Main content
    if processing_mode == "Single File":
        st.markdown("### 📤 Upload Marksheet")
        
        # Custom file uploader with correct size limit
        st.markdown(f"**Choose a marksheet file** (Max size: {max_file_size} MB)")
        
        # Add custom CSS to hide the 200MB text
        st.markdown("""
        <style>
        .uploadedFile {
            display: none;
        }
        .stFileUploader > div > div > div > div {
            font-size: 0.8rem;
        }
        .stFileUploader > div > div > div > div:contains("200MB") {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Upload marksheet file",
            type=['jpg', 'jpeg', 'png', 'pdf', 'webp'],
            help=f"Max size: {max_file_size} MB",
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            process_single_file(uploaded_file, api_url, max_file_size)
    
    else:  # Batch Processing
        st.markdown("### 📤 Batch Upload Marksheets")
        st.markdown(f"**Choose multiple marksheet files** (Max {max_file_size} MB each, up to 10 files)")
        
        uploaded_files = st.file_uploader(
            "Upload marksheet files",
            type=['jpg', 'jpeg', 'png', 'pdf', 'webp'],
            accept_multiple_files=True,
            help=f"Max size: {max_file_size} MB per file, up to 10 files total",
            label_visibility="collapsed"
        )
        
        if uploaded_files:
            if len(uploaded_files) > 10:
                st.error("Maximum 10 files allowed for batch processing")
                return
            
            process_batch_files(uploaded_files, api_url, max_file_size)

def process_single_file(uploaded_file, api_url, max_file_size):
    """Process a single marksheet file"""
    # Display file info
    col1, col2 = st.columns([2, 1])
    with col1:
        st.success(f"✅ {uploaded_file.name}")
    with col2:
        st.info(f"📏 {uploaded_file.size / (1024*1024):.2f} MB")
    
    # Check file size
    if uploaded_file.size > max_file_size * 1024 * 1024:
        st.error(f"File size exceeds the maximum allowed size of {max_file_size} MB")
        return
    
    # Display preview for images and PDFs
    if uploaded_file.type.startswith('image/'):
        st.markdown("### 👁️ Preview")
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True)
    elif uploaded_file.type == 'application/pdf':
        st.markdown("### 👁️ Preview")
        try:
            # Convert PDF to image for preview
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(uploaded_file.getvalue(), first_page=1, last_page=1, dpi=150)
            if images:
                st.image(images[0], use_container_width=True, caption="PDF Preview (Page 1)")
            else:
                st.info("Could not generate PDF preview")
        except Exception as e:
            st.info(f"PDF preview not available: {str(e)}")
    
    # Extract button
    if st.button("Extract Data", type="primary"):
        with st.spinner("Extracting data from marksheet..."):
            try:
                # Prepare file for API
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                
                # Make API request
                response = requests.post(f"{api_url}/extract", files=files)
                
                if response.status_code == 200:
                    extracted_data = response.json()
                    
                    # Display results
                    st.markdown('<h2 class="section-header">📋 Extracted Data</h2>', unsafe_allow_html=True)
                    
                    # Candidate Details
                    st.markdown("### 👤 Candidate Details")
                    candidate_details = extracted_data.get('candidate_details', {})
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        display_extracted_field("Name", candidate_details.get('name', {}))
                        display_extracted_field("Father's Name", candidate_details.get('father_name', {}))
                        display_extracted_field("Mother's Name", candidate_details.get('mother_name', {}))
                        display_extracted_field("Roll Number", candidate_details.get('roll_number', {}))
                        display_extracted_field("Registration Number", candidate_details.get('registration_number', {}))
                    
                    with col2:
                        display_extracted_field("Date of Birth", candidate_details.get('date_of_birth', {}))
                        display_extracted_field("Exam Year", candidate_details.get('exam_year', {}))
                        display_extracted_field("Board/University", candidate_details.get('board_university', {}))
                        display_extracted_field("Institution", candidate_details.get('institution', {}))
                    
                    # Subject Marks
                    st.markdown("### 📚 Subject Marks")
                    subject_marks = extracted_data.get('subject_marks', [])
                    display_subject_marks(subject_marks)
                    
                    # Overall Result
                    st.markdown("### 🏆 Overall Result")
                    overall_result = extracted_data.get('overall_result', {})
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        display_extracted_field("Total Marks", overall_result.get('total_marks', {}))
                        display_extracted_field("Max Total Marks", overall_result.get('max_total_marks', {}))
                        display_extracted_field("Percentage", overall_result.get('percentage', {}))
                    
                    with col2:
                        display_extracted_field("CGPA", overall_result.get('cgpa', {}))
                        display_extracted_field("Grade", overall_result.get('grade', {}))
                        display_extracted_field("Division", overall_result.get('division', {}))
                        display_extracted_field("Result Status", overall_result.get('result_status', {}))
                    
                    # Issue Details
                    st.markdown("### 📅 Issue Details")
                    issue_details = extracted_data.get('issue_details', {})
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        display_extracted_field("Issue Date", issue_details.get('issue_date', {}))
                    with col2:
                        display_extracted_field("Issue Place", issue_details.get('issue_place', {}))
                    
                    # Download JSON
                    st.markdown("### 💾 Download Results")
                    json_str = json.dumps(extracted_data, indent=2)
                    st.download_button(
                        label="📥 Download JSON",
                        data=json_str,
                        file_name=f"extracted_data_{uploaded_file.name}.json",
                        mime="application/json"
                    )
                    
                else:
                    error_data = response.json()
                    st.error(f"Error: {error_data.get('error', 'Unknown error')}")
                    if 'detail' in error_data:
                        st.error(f"Details: {error_data['detail']}")
            
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the API. Please make sure the API server is running.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

def process_batch_files(uploaded_files, api_url, max_file_size):
    """Process multiple marksheet files in batch"""
    # Display file info
    st.markdown(f"### 📁 Selected Files ({len(uploaded_files)} files)")
    
    # Check file sizes
    valid_files = []
    for file in uploaded_files:
        if file.size > max_file_size * 1024 * 1024:
            st.error(f"❌ {file.name}: File size exceeds {max_file_size} MB")
        else:
            valid_files.append(file)
            st.success(f"✅ {file.name} ({file.size / (1024*1024):.2f} MB)")
    
    if not valid_files:
        st.error("No valid files to process")
        return
    
    # Batch extract button
    if st.button("🚀 Process All Files", type="primary"):
        with st.spinner(f"Processing {len(valid_files)} files..."):
            try:
                # Prepare files for API
                files = []
                for file in valid_files:
                    files.append(("files", (file.name, file.getvalue(), file.type)))
                
                # Make batch API request (no authentication required)
                response = requests.post(f"{api_url}/batch-extract", files=files)
                
                if response.status_code == 200:
                    batch_data = response.json()
                    
                    # Display batch results
                    st.markdown('<h2 class="section-header">📊 Batch Processing Results</h2>', unsafe_allow_html=True)
                    
                    # Summary statistics
                    st.markdown("### 📈 Summary")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Files", batch_data.get('total_processed', 0))
                    with col2:
                        st.metric("Successful", batch_data.get('successful', 0))
                    with col3:
                        st.metric("Failed", batch_data.get('failed', 0))
                    with col4:
                        processing_time = batch_data.get('processing_time', 0)
                        st.metric("Processing Time", f"{processing_time:.2f}s")
                    
                    # Individual results
                    st.markdown("### 📋 Individual Results")
                    results = batch_data.get('results', [])
                    
                    for i, result in enumerate(results):
                        # Get status from extraction_metadata
                        metadata = result.get('extraction_metadata', {})
                        status = metadata.get('status', 'success')
                        filename = metadata.get('filename', f'File {i+1}')
                        
                        with st.expander(f"📄 {filename} - {status}"):
                            if status == 'success':
                                # The result IS the extracted data (MarksheetExtractionResponse)
                                candidate_details = result.get('candidate_details', {})
                                
                                # Candidate Details
                                st.markdown("#### 👤 Candidate Details")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    display_extracted_field("Name", candidate_details.get('name', {}))
                                    display_extracted_field("Roll Number", candidate_details.get('roll_number', {}))
                                with col2:
                                    display_extracted_field("Exam Year", candidate_details.get('exam_year', {}))
                                    display_extracted_field("Board/University", candidate_details.get('board_university', {}))
                                
                                # Overall Result
                                st.markdown("#### 🏆 Overall Result")
                                overall_result = result.get('overall_result', {})
                                display_extracted_field("Total Marks", overall_result.get('total_marks', {}))
                                display_extracted_field("Percentage", overall_result.get('percentage', {}))
                                display_extracted_field("Grade", overall_result.get('grade', {}))
                                
                            else:
                                error_msg = metadata.get('error', 'Unknown error')
                                st.error(f"Error: {error_msg}")
                    
                    # Download batch results
                    st.markdown("### 💾 Download Batch Results")
                    json_str = json.dumps(batch_data, indent=2)
                    st.download_button(
                        label="📥 Download Batch JSON",
                        data=json_str,
                        file_name=f"batch_extraction_results_{len(valid_files)}_files.json",
                        mime="application/json"
                    )
                    
                else:
                    error_data = response.json()
                    st.error(f"Batch processing failed: {error_data.get('error', 'Unknown error')}")
                    if 'detail' in error_data:
                        st.error(f"Details: {error_data['detail']}")
            
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the API. Please make sure the API server is running.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    


if __name__ == "__main__":
    main()
