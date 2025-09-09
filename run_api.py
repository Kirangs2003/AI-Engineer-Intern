#!/usr/bin/env python3
"""
Script to run the AI Marksheet Extraction API server
"""

import uvicorn
from api import app

if __name__ == "__main__":
    print("Starting AI Marksheet Extraction API...")
    print("API will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
