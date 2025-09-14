import streamlit as st
import json
from typing import Dict, Any
from PIL import Image
from pdf2image import convert_from_bytes
import pytesseract

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
    .extracted-value {
        background-color: #f8f9fa;
        padding: 0.4rem 0.8rem;
        border-radius: 0.3rem;
        border-left: 3px solid #1f77b4;
        margin: 0.4rem 0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

def extract_text_from_file(uploaded_file):
    """OCR extraction from images or PDFs"""
    text = ""
    if uploaded_file.type.startswith("image/"):
        image = Image.open(uploaded_file)
        text = pytesseract.image_to_string(image)
    elif uploaded_file.type == "application/pdf":
        images = convert_from_bytes(uploaded_file.getvalue(), dpi=200)
        for img in images:
            text += pytesseract.image_to_string(img) + "\n"
    return text

def main():
    # Header
    st.markdown('<h1 class="main-header">📊 AI Marksheet Extraction</h1>', unsafe_allow_html=True)

    st.markdown("### 📤 Upload Marksheet")
    uploaded_file = st.file_uploader(
        "Upload marksheet file",
        type=['jpg', 'jpeg', 'png', 'pdf'],
        help="Upload an image or PDF marksheet"
    )

    if uploaded_file is not None:
        st.success(f"✅ {uploaded_file.name}")

        # Preview
        if uploaded_file.type.startswith("image/"):
            st.image(Image.open(uploaded_file), use_container_width=True)
        elif uploaded_file.type == "application/pdf":
            try:
                images = convert_from_bytes(uploaded_file.getvalue(), first_page=1, last_page=1, dpi=150)
                st.image(images[0], use_container_width=True, caption="PDF Preview (Page 1)")
            except Exception:
                st.info("Preview not available")

        if st.button("Extract Data", type="primary"):
            with st.spinner("Extracting text..."):
                text = extract_text_from_file(uploaded_file)
                if text.strip():
                    st.markdown('<h2 class="section-header">📋 Extracted Text</h2>', unsafe_allow_html=True)
                    st.text_area("Extracted OCR Text", text, height=400)

                    # Download option
                    json_data = {"filename": uploaded_file.name, "extracted_text": text}
                    st.download_button(
                        "📥 Download JSON",
                        data=json.dumps(json_data, indent=2),
                        file_name=f"extracted_{uploaded_file.name}.json",
                        mime="application/json"
                    )
                else:
                    st.error("❌ No text extracted. Please check file quality.")

if __name__ == "__main__":
    main()
