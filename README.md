# LLMO Analyzer

A simple Python utility to analyze how "AI-friendly" a webpage is. Uses Groq's fast LLM API to evaluate content alongside basic heuristics.

## Structure

```
llmo-analyzer/
├── llmo_analyzer/        # Main package
│   ├── __init__.py
│   ├── app.py           # Streamlit dashboard
│   ├── config.py        # Configuration
│   ├── scraper.py       # URL scraping
│   ├── heuristics.py    # Local scoring
│   └── groq_analyzer.py # LLM evaluation
├── scripts/
│   └── run.sh           # Launch script
├── tests/               # Test files
├── pyproject.toml       # Package config
├── requirements.txt     # Dependencies
└── README.md
```

## Setup

```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set your Groq API key
export GROQ_API_KEY="your_key_here"
```

Get a free API key: https://console.groq.com/keys

## Usage

```bash
./scripts/run.sh
```

Or manually:
```bash
source venv/bin/activate
streamlit run llmo_analyzer/app.py
```

## Scoring

- Readability (25%): Flesch Reading Ease
- Structure (25%): Headings hierarchy  
- Technical (20%): Schema markup, meta tags
- Entity Clarity (10%): AI-assessed
- Extractability (10%): AI-assessed
- Citation Potential (10%): AI-assessed
