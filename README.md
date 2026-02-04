# LLMO Analyzer

A simple Python utility to analyze how "AI-friendly" a webpage is. Uses Groq's fast LLM API to evaluate content alongside basic heuristics.

## What it does

- Scrapes a URL and extracts content + metadata
- Calculates readability, structure, and technical scores locally
- Sends a summary to Groq's LLM for AI-specific evaluation
- Displays results in a Streamlit dashboard

## Setup

```bash
# Install dependencies
source venv/bin/activate
pip install -r requirements.txt

# Set your Groq API key
export GROQ_API_KEY="your_key_here"
# Or add to .env file
```

Get a free API key: https://console.groq.com/keys

## Usage

```bash
# Run the analyzer
./run.sh
```

Or manually:
```bash
source venv/bin/activate && streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## Files

- `app.py` - Streamlit dashboard
- `scraper.py` - URL content extraction
- `heuristics.py` - Local scoring (readability, structure, technical)
- `groq_analyzer.py` - LLM evaluation via Groq API
- `config.py` - Settings and environment variables
- `run.sh` - Convenience script to launch the app

## Scoring

The LLMO Score is a weighted average:
- Readability (25%): Flesch Reading Ease
- Structure (25%): Headings hierarchy
- Technical (20%): Schema markup, meta tags
- Entity Clarity (10%): AI-assessed
- Extractability (10%): AI-assessed RAG potential
- Citation Potential (10%): AI-assessed authority

## Notes

- Requires Python 3.9+
- Uses `llama-3.3-70b-versatile` by default
- Content is truncated to ~10k characters for API calls
