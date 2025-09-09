#!/usr/bin/env python3
"""
Script to run the Streamlit web interface
"""

import subprocess
import sys
import os

def main():
    print("Starting AI Marksheet Extraction Streamlit App...")
    print("The app will be available at: http://localhost:8501")
    print("Press Ctrl+C to stop the app")
    
    try:
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\nShutting down Streamlit app...")
    except Exception as e:
        print(f"Error running Streamlit: {e}")

if __name__ == "__main__":
    main()
