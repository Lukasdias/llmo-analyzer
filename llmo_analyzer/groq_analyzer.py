"""
LLMO Analyzer - Groq AI Evaluation Module
Uses Groq's high-speed LLMs to evaluate content for AI-friendliness.
"""

import json
from dataclasses import dataclass
from typing import Optional

from groq import Groq, RateLimitError, APIConnectionError, APIStatusError

from llmo_analyzer.config import Config
from llmo_analyzer.scraper import ScrapedContent


@dataclass
class AIEvaluation:
    """Container for AI evaluation scores."""
    entity_clarity_score: float = 0.0
    entity_clarity_reasoning: str = ""
    
    extractability_score: float = 0.0
    extractability_reasoning: str = ""
    
    citation_potential_score: float = 0.0
    citation_potential_reasoning: str = ""
    
    overall_ai_score: float = 0.0
    ai_recommendations: list[str] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.ai_recommendations is None:
            self.ai_recommendations = []


class GroqAnalyzer:
    """Analyzes content using Groq's high-speed LLMs."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Groq analyzer.
        
        Args:
            api_key: Groq API key. If None, uses GROQ_API_KEY from environment.
        """
        self.api_key = api_key or Config.GROQ_API_KEY
        if not self.api_key:
            raise ValueError("Groq API key is required. Set GROQ_API_KEY environment variable.")
        
        self.client = Groq(api_key=self.api_key)
        self.model = Config.GROQ_MODEL
    
    def analyze(self, content: ScrapedContent) -> AIEvaluation:
        """
        Analyze content using Groq's LLM.
        
        Args:
            content: The scraped content to analyze
            
        Returns:
            AIEvaluation object with AI-assessed scores
        """
        if content.error:
            return AIEvaluation(error=f"Cannot analyze: {content.error}")
        
        # Prepare content summary (limit to avoid token overflow)
        text_content = content.content
        if len(text_content) > Config.MAX_CONTENT_LENGTH:
            text_content = text_content[:Config.MAX_CONTENT_LENGTH] + "..."
        
        # Prepare the prompt
        system_prompt = """You are an expert AI Content Evaluator specializing in Large Language Model Optimization (LLMO).
Your task is to analyze web content and evaluate its "AI-friendliness" - how well it can be understood, processed, and utilized by AI systems like RAG pipelines, chatbots, and search engines.

Evaluate the content on three dimensions:

1. **Entity Clarity** (0-100): Are brand names, products, services, and key concepts clearly defined and unambiguous? AI systems need clear entity recognition.

2. **Extractability** (0-100): How easily can this content be chunked, embedded, and retrieved by a RAG system? Consider structure, semantic coherence, and information density.

3. **Citation Potential** (0-100): Is this content authoritative, factual, and well-sourced enough that an AI would confidently cite it as a reference?

Provide your evaluation as a JSON object with this exact structure:
{
  "entity_clarity": {
    "score": <number 0-100>,
    "reasoning": "<2-3 sentences explaining the score>"
  },
  "extractability": {
    "score": <number 0-100>,
    "reasoning": "<2-3 sentences explaining the score>"
  },
  "citation_potential": {
    "score": <number 0-100>,
    "reasoning": "<2-3 sentences explaining the score>"
  },
  "recommendations": [
    "<specific recommendation 1>",
    "<specific recommendation 2>"
  ]
}

Be objective and critical. Scores of 80+ should be reserved for truly excellent AI-friendly content."""

        user_prompt = f"""Analyze the following web content for AI-friendliness:

**URL**: {content.url}
**Title**: {content.title}
**Word Count**: {content.word_count}

**Content**:
{text_content}

Provide your evaluation in the exact JSON format specified in your instructions."""

        try:
            # Make API call to Groq
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,  # Lower temperature for more consistent scoring
                max_tokens=Config.MAX_TOKENS_FOR_AI,
                timeout=Config.REQUEST_TIMEOUT
            )
            
            # Parse the JSON response
            result = json.loads(response.choices[0].message.content)
            
            # Extract scores and reasoning
            evaluation = AIEvaluation()
            
            entity_data = result.get("entity_clarity", {})
            evaluation.entity_clarity_score = float(entity_data.get("score", 0))
            evaluation.entity_clarity_reasoning = entity_data.get("reasoning", "")
            
            extractability_data = result.get("extractability", {})
            evaluation.extractability_score = float(extractability_data.get("score", 0))
            evaluation.extractability_reasoning = extractability_data.get("reasoning", "")
            
            citation_data = result.get("citation_potential", {})
            evaluation.citation_potential_score = float(citation_data.get("score", 0))
            evaluation.citation_potential_reasoning = citation_data.get("reasoning", "")
            
            # Get AI recommendations
            evaluation.ai_recommendations = result.get("recommendations", [])
            
            # Calculate overall AI score
            evaluation.overall_ai_score = (
                evaluation.entity_clarity_score * Config.WEIGHT_AI_ENTITY +
                evaluation.extractability_score * Config.WEIGHT_AI_EXTRACTABILITY +
                evaluation.citation_potential_score * Config.WEIGHT_AI_CITATION
            ) / (Config.WEIGHT_AI_ENTITY + Config.WEIGHT_AI_EXTRACTABILITY + Config.WEIGHT_AI_CITATION)
            
            return evaluation
            
        except RateLimitError:
            return AIEvaluation(
                error="Rate limit exceeded. Please wait a moment and try again."
            )
        except APIConnectionError:
            return AIEvaluation(
                error="Connection error. Could not reach Groq API. Please check your internet connection."
            )
        except APIStatusError as e:
            return AIEvaluation(
                error=f"Groq API error ({e.status_code}): {e.message}"
            )
        except json.JSONDecodeError as e:
            return AIEvaluation(
                error=f"Error parsing AI response: {str(e)}"
            )
        except Exception as e:
            return AIEvaluation(
                error=f"Unexpected error during AI analysis: {str(e)}"
            )
