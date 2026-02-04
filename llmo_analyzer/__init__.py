"""
LLMO Analyzer - A utility to analyze AI-friendliness of web content.
"""

__version__ = "1.0.0"

from llmo_analyzer.config import Config
from llmo_analyzer.scraper import ScrapedContent, WebScraper
from llmo_analyzer.heuristics import HeuristicScores, HeuristicAnalyzer
from llmo_analyzer.groq_analyzer import AIEvaluation, GroqAnalyzer

__all__ = [
    "Config",
    "ScrapedContent",
    "WebScraper",
    "HeuristicScores",
    "HeuristicAnalyzer",
    "AIEvaluation",
    "GroqAnalyzer",
]
