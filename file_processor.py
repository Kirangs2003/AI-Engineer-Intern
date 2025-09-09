import io
import base64
from PIL import Image
import PyPDF2
from typing import Union, Tuple
import streamlit as st

# Try to import pdf2image, fallback to text extraction if not available
try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

class FileProcessor:
    """Handles file processing for images and PDFs"""
    
    @staticmethod
    def process_image(file_content: bytes) -> str:
        """Convert image to base64 string for Gemini API"""
        try:
            # Open image with PIL
            image = Image.open(io.BytesIO(file_content))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to base64
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            return img_base64
        except Exception as e:
            raise ValueError(f"Error processing image: {str(e)}")
    
    @staticmethod
    def process_pdf(file_content: bytes) -> str:
        """Extract first page of PDF and convert to base64 image or text"""
        try:
            # First, try to extract text content
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            
            if len(pdf_reader.pages) == 0:
                raise ValueError("PDF has no pages")
            
            # Get first page
            first_page = pdf_reader.pages[0]
            text_content = first_page.extract_text()
            
            # Check if we have meaningful text content (more than just whitespace)
            if text_content and text_content.strip() and len(text_content.strip()) > 10:
                return f"PDF_TEXT_CONTENT:{text_content}"
            
            # If no meaningful text content, convert to image
            if PDF2IMAGE_AVAILABLE:
                try:
                    # Convert PDF to images
                    images = convert_from_bytes(file_content, first_page=1, last_page=1, dpi=200)
                    
                    if images:
                        # Convert first page to base64
                        img = images[0]
                        buffered = io.BytesIO()
                        img.save(buffered, format="JPEG", quality=85)
                        img_base64 = base64.b64encode(buffered.getvalue()).decode()
                        return img_base64
                    else:
                        raise ValueError("Could not convert PDF to image")
                        
                except Exception as img_error:
                    raise ValueError(f"PDF appears to be image-based but could not convert to image: {str(img_error)}")
            else:
                raise ValueError("No text content found in PDF and pdf2image not available for image conversion")
            
        except Exception as e:
            raise ValueError(f"Error processing PDF: {str(e)}")
    
    @staticmethod
    def process_file(file_content: bytes, file_extension: str) -> Tuple[str, str]:
        """
        Process uploaded file and return base64 content and content type
        
        Returns:
            Tuple of (content, content_type) where content_type is either 'image' or 'pdf_text'
        """
        file_extension = file_extension.lower()
        
        if file_extension in ['.jpg', '.jpeg', '.png', '.webp']:
            base64_content = FileProcessor.process_image(file_content)
            return base64_content, 'image'
        elif file_extension == '.pdf':
            content = FileProcessor.process_pdf(file_content)
            # Check if the content is actually an image (base64) or text
            if content.startswith('PDF_TEXT_CONTENT:'):
                return content, 'pdf_text'
            else:
                # It's a base64 image from PDF conversion
                return content, 'image'
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    @staticmethod
    def validate_file_size(file_content: bytes, max_size: int) -> bool:
        """Validate file size"""
        return len(file_content) <= max_size
