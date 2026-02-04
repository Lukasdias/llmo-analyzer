"""
LLMO Analyzer - Heuristic Scoring Module
Calculates local metrics for readability, structure, and technical SEO.
"""

from dataclasses import dataclass
from typing import Optional

import textstat

from llmo_analyzer.config import Config
from llmo_analyzer.scraper import ScrapedContent


@dataclass
class HeuristicScores:
    """Container for all heuristic scores."""
    # Readability Scores
    flesch_reading_ease: float = 0.0
    flesch_kincaid_grade: float = 0.0
    readability_score: float = 0.0  # Normalized 0-100
    
    # Structure Scores
    has_h1: bool = False
    has_h2: bool = False
    has_h3: bool = False
    h1_count: int = 0
    h2_count: int = 0
    h3_count: int = 0
    structure_score: float = 0.0  # Normalized 0-100
    
    # Technical Scores
    has_meta_description: bool = False
    has_meta_keywords: bool = False
    has_json_ld: bool = False
    json_ld_count: int = 0
    has_bullet_points: bool = False
    word_count: int = 0
    technical_score: float = 0.0  # Normalized 0-100
    
    # Overall
    overall_heuristic_score: float = 0.0
    
    # Recommendations
    recommendations: list[str] = None
    
    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


class HeuristicAnalyzer:
    """Analyzes content and calculates heuristic scores."""
    
    def analyze(self, content: ScrapedContent) -> HeuristicScores:
        """
        Analyze scraped content and calculate all heuristic scores.
        
        Args:
            content: The scraped content to analyze
            
        Returns:
            HeuristicScores object with all calculated metrics
        """
        if content.error:
            return HeuristicScores(
                recommendations=[f"Error: {content.error}"]
            )
        
        scores = HeuristicScores()
        
        # Calculate readability scores
        self._calculate_readability(content, scores)
        
        # Calculate structure scores
        self._calculate_structure(content, scores)
        
        # Calculate technical scores
        self._calculate_technical(content, scores)
        
        # Calculate overall score
        self._calculate_overall(scores)
        
        # Generate recommendations
        self._generate_recommendations(content, scores)
        
        return scores
    
    def _calculate_readability(self, content: ScrapedContent, scores: HeuristicScores) -> None:
        """Calculate readability metrics."""
        text = content.content
        
        if not text or len(text.split()) < 10:
            scores.flesch_reading_ease = 0.0
            scores.flesch_kincaid_grade = 0.0
            scores.readability_score = 0.0
            return
        
        # Calculate Flesch Reading Ease (higher is easier to read)
        scores.flesch_reading_ease = textstat.flesch_reading_ease(text)
        
        # Calculate Flesch-Kincaid Grade Level
        scores.flesch_kincaid_grade = textstat.flesch_kincaid_grade(text)
        
        # Normalize readability score to 0-100 scale
        # Flesch Reading Ease: 0-100 scale (60-70 is ideal for web content)
        fre = scores.flesch_reading_ease
        
        if fre >= Config.READABILITY_EXCELLENT:
            scores.readability_score = 100.0
        elif fre >= Config.READABILITY_GOOD:
            scores.readability_score = 80.0 + ((fre - Config.READABILITY_GOOD) / (Config.READABILITY_EXCELLENT - Config.READABILITY_GOOD)) * 20
        elif fre >= Config.READABILITY_FAIR:
            scores.readability_score = 50.0 + ((fre - Config.READABILITY_FAIR) / (Config.READABILITY_GOOD - Config.READABILITY_FAIR)) * 30
        elif fre > 0:
            scores.readability_score = (fre / Config.READABILITY_FAIR) * 50.0
        else:
            scores.readability_score = max(0.0, 50.0 + (fre / 10.0))  # Very difficult text gets lower score
    
    def _calculate_structure(self, content: ScrapedContent, scores: HeuristicScores) -> None:
        """Calculate structure metrics based on headings hierarchy."""
        headings = content.headings or {}
        
        scores.h1_count = len(headings.get('h1', []))
        scores.h2_count = len(headings.get('h2', []))
        scores.h3_count = len(headings.get('h3', []))
        
        scores.has_h1 = scores.h1_count > 0
        scores.has_h2 = scores.h2_count > 0
        scores.has_h3 = scores.h3_count > 0
        
        # Calculate structure score
        structure_points = 0.0
        
        # H1 presence (crucial for SEO and structure)
        if scores.has_h1:
            structure_points += 30.0
            # Bonus for exactly one H1 (best practice)
            if scores.h1_count == 1:
                structure_points += 10.0
        
        # H2 presence (important for content organization)
        if scores.has_h2:
            structure_points += 25.0
            # Bonus for multiple H2s
            if scores.h2_count >= 2:
                structure_points += 5.0
        
        # H3 presence (good for deep content)
        if scores.has_h3:
            structure_points += 15.0
        
        # Content length bonus
        word_count = content.word_count
        if word_count >= 1000:
            structure_points += 15.0
        elif word_count >= 500:
            structure_points += 10.0
        elif word_count >= 300:
            structure_points += 5.0
        
        scores.structure_score = min(100.0, structure_points)
    
    def _calculate_technical(self, content: ScrapedContent, scores: HeuristicScores) -> None:
        """Calculate technical SEO metrics."""
        scores.has_meta_description = content.meta_description is not None and len(content.meta_description) > 10
        scores.has_meta_keywords = content.meta_keywords is not None and len(content.meta_keywords) > 0
        scores.has_json_ld = len(content.json_ld) > 0
        scores.json_ld_count = len(content.json_ld)
        scores.has_bullet_points = content.has_bullet_points
        scores.word_count = content.word_count
        
        # Calculate technical score
        technical_points = 0.0
        
        # Meta description (important for SERP)
        if scores.has_meta_description:
            technical_points += 25.0
            desc_length = len(content.meta_description or "")
            if 120 <= desc_length <= 160:
                technical_points += 5.0  # Optimal length
        
        # Meta keywords (less important but still relevant)
        if scores.has_meta_keywords:
            technical_points += 10.0
        
        # JSON-LD structured data (very important for AI understanding)
        if scores.has_json_ld:
            technical_points += 30.0
            # Bonus for multiple structured data types
            if scores.json_ld_count >= 2:
                technical_points += 5.0
        
        # Bullet points (good for readability and AI extraction)
        if scores.has_bullet_points:
            technical_points += 15.0
        
        # Word count (content depth)
        if scores.word_count >= 1000:
            technical_points += 10.0
        elif scores.word_count >= 500:
            technical_points += 7.0
        elif scores.word_count >= 300:
            technical_points += 5.0
        elif scores.word_count >= 150:
            technical_points += 3.0
        
        scores.technical_score = min(100.0, technical_points)
    
    def _calculate_overall(self, scores: HeuristicScores) -> None:
        """Calculate weighted overall heuristic score."""
        scores.overall_heuristic_score = (
            scores.readability_score * Config.WEIGHT_READABILITY +
            scores.structure_score * Config.WEIGHT_STRUCTURE +
            scores.technical_score * Config.WEIGHT_TECHNICAL
        ) / (Config.WEIGHT_READABILITY + Config.WEIGHT_STRUCTURE + Config.WEIGHT_TECHNICAL)
    
    def _generate_recommendations(self, content: ScrapedContent, scores: HeuristicScores) -> None:
        """Generate actionable recommendations based on scores."""
        recommendations = []
        
        # Readability recommendations
        if scores.flesch_reading_ease < Config.READABILITY_FAIR:
            recommendations.append("📖 **Improve Readability**: Content is very difficult to read. Consider simplifying language and shortening sentences.")
        elif scores.flesch_reading_ease < Config.READABILITY_GOOD:
            recommendations.append("📖 **Enhance Readability**: Content is somewhat difficult. Use simpler words and shorter paragraphs.")
        
        # Structure recommendations
        if not scores.has_h1:
            recommendations.append("🏗️ **Add H1 Tag**: Include a single, descriptive H1 heading that clearly states the page topic.")
        elif scores.h1_count > 1:
            recommendations.append("🏗️ **Consolidate H1 Tags**: Use only one H1 tag per page for better SEO and structure.")
        
        if not scores.has_h2:
            recommendations.append("🏗️ **Add H2 Headings**: Break content into sections with H2 headings for better organization.")
        
        if not scores.has_h3 and content.word_count > 800:
            recommendations.append("🏗️ **Consider H3 Subsections**: For longer content, use H3 tags to create deeper structure.")
        
        # Technical recommendations
        if not scores.has_meta_description:
            recommendations.append("🔍 **Add Meta Description**: Include a compelling meta description (120-160 characters) for better SERP visibility.")
        
        if not scores.has_json_ld:
            recommendations.append("📋 **Add Schema Markup**: Implement JSON-LD structured data (Article, Product, Organization, etc.) to help AI understand your content.")
        
        if not scores.has_bullet_points:
            recommendations.append("• **Use Bullet Points**: Break up text with bulleted lists to improve scannability and AI extraction.")
        
        if content.word_count < 300:
            recommendations.append("📝 **Expand Content**: Consider adding more content (aim for 500+ words) to provide comprehensive information.")
        
        scores.recommendations = recommendations if recommendations else ["✅ **Great Job!** Your content follows LLMO best practices."]
