#!/bin/bash
# Run the LLMO Analyzer

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Run: python3 -m venv venv"
    exit 1
fi

source venv/bin/activate
streamlit run app.py
