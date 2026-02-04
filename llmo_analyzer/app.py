"""
LLMO Analyzer - Check how AI-friendly a webpage is
"""

import streamlit as st

from llmo_analyzer.config import Config
from llmo_analyzer.groq_analyzer import AIEvaluation, GroqAnalyzer
from llmo_analyzer.heuristics import HeuristicAnalyzer, HeuristicScores
from llmo_analyzer.scraper import ScrapedContent, WebScraper

st.set_page_config(
    page_title="LLMO Analyzer",
    page_icon="🤖",
    layout="wide"
)


def get_rating(score: float) -> str:
    """Get rating label for score."""
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Fair"
    else:
        return "Poor"


def get_rating_color(score: float) -> str:
    """Get color for score."""
    if score >= 80:
        return "#28a745"
    elif score >= 60:
        return "#17a2b8"
    elif score >= 40:
        return "#ffc107"
    else:
        return "#dc3545"


def display_category(name: str, score: float, description: str, recommendations: list[str], good_points: list[str] = None):
    """Display a category with expandable details."""
    rating = get_rating(score)
    color = get_rating_color(score)
    
    # Main display
    st.markdown(f"""
    <div style="border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin: 10px 0; background: white;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <h3 style="margin: 0; font-size: 1.3rem; color: #333;">{name}</h3>
            <div style="text-align: right;">
                <div style="font-size: 1.1rem; font-weight: bold; color: {color};">{rating}</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #333;">{score:.0f}%</div>
            </div>
        </div>
        <div style="background: #f0f0f0; border-radius: 4px; height: 8px; margin: 10px 0;">
            <div style="background: {color}; width: {score}%; height: 100%; border-radius: 4px;"></div>
        </div>
        <p style="color: #666; margin: 10px 0;">{description}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Expandable details
    with st.expander("View Analysis Details"):
        if good_points:
            st.write("**Good Points:**")
            for point in good_points:
                st.write(f"- {point}")
        
        if recommendations:
            st.write("**Recommendations:**")
            for rec in recommendations:
                st.write(f"- {rec}")
        
        if not good_points and not recommendations:
            st.write("No specific recommendations.")


def analyze_single_url(url: str) -> tuple[ScrapedContent, HeuristicScores, AIEvaluation]:
    """Analyze a single URL."""
    scraper = WebScraper(timeout=Config.REQUEST_TIMEOUT)
    heuristic_analyzer = HeuristicAnalyzer()
    
    with st.spinner("Scraping..."):
        content = scraper.scrape(url)
    
    if content.error:
        return content, None, None
    
    with st.spinner("Scoring..."):
        heuristic_scores = heuristic_analyzer.analyze(content)
    
    with st.spinner("AI analysis..."):
        try:
            groq_analyzer = GroqAnalyzer()
            ai_evaluation = groq_analyzer.analyze(content)
        except ValueError as e:
            ai_evaluation = AIEvaluation(error=str(e))
    
    return content, heuristic_scores, ai_evaluation


def main():
    st.title("LLMO Analyzer")
    st.write("Check how AI-friendly a webpage is")
    
    with st.sidebar:
        st.header("Settings")
        
        api_key = st.text_input(
            "Groq API Key",
            value=Config.GROQ_API_KEY or "",
            type="password"
        )
        
        if api_key:
            Config.GROQ_API_KEY = api_key
        
        st.divider()
        st.write("Checks: Content Structure, Metadata, Readability, Entity Clarity, Extractability, Citation")
    
    url = st.text_input("URL", placeholder="https://example.com")
    
    if st.button("Analyze", type="primary") and url:
        content, heuristic_scores, ai_evaluation = analyze_single_url(url)
        
        if content.error:
            st.error(content.error)
        else:
            # Calculate overall score first
            total_score = 0.0
            count = 0
            if heuristic_scores:
                total_score += heuristic_scores.structure_score + heuristic_scores.technical_score + heuristic_scores.readability_score
                count += 3
            if ai_evaluation and not ai_evaluation.error:
                total_score += ai_evaluation.entity_clarity_score + ai_evaluation.extractability_score + ai_evaluation.citation_potential_score
                count += 3
            
            if count > 0:
                overall = total_score / count
                overall_rating = get_rating(overall)
                overall_color = get_rating_color(overall)
                
                # Display overall score at the top
                st.markdown(f"""
                <div style="border: 2px solid {overall_color}; border-radius: 12px; padding: 30px; margin: 20px 0; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); text-align: center;">
                    <div style="font-size: 1.2rem; color: #666; margin-bottom: 10px;">Overall Score</div>
                    <div style="font-size: 4rem; font-weight: bold; color: {overall_color};">{overall:.0f}%</div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: {overall_color};">{overall_rating}</div>
                    <div style="background: white; border-radius: 8px; height: 12px; margin: 15px auto; max-width: 400px; border: 1px solid #ddd;">
                        <div style="background: {overall_color}; width: {overall}%; height: 100%; border-radius: 8px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Display categories
            st.subheader("Analysis Results")
            
            # Content Structure
            display_category(
                "Content Structure",
                heuristic_scores.structure_score,
                "Evaluates how well the content is structured for LLMs to parse and understand.",
                [
                    "Use clear headings and subheadings with proper hierarchy (H1, H2, H3)",
                    "Break content into logical sections and paragraphs",
                    "Use bullet points and numbered lists for better parsing",
                    f"Found {heuristic_scores.h1_count} H1, {heuristic_scores.h2_count} H2, {heuristic_scores.h3_count} H3 tags"
                ] if heuristic_scores.structure_score < 80 else ["Good heading structure detected."]
            )
            
            # Metadata Optimization
            metadata_score = heuristic_scores.technical_score
            display_category(
                "Metadata Optimization",
                metadata_score,
                "Checks if the page has proper metadata that helps LLMs understand the context.",
                [
                    "Add a descriptive meta description" if not heuristic_scores.has_meta_description else "Meta description present",
                    "Use semantic schema markup for better context" if not heuristic_scores.has_json_ld else f"JSON-LD schema found ({heuristic_scores.json_ld_count} items)",
                    "Add proper Open Graph tags" if not heuristic_scores.has_meta_description else "Open Graph likely present"
                ]
            )
            
            # Readability
            display_category(
                "Readability",
                heuristic_scores.readability_score,
                "Analyzes how easy it is for LLMs to process and understand the text content.",
                [
                    f"Flesch Reading Ease: {heuristic_scores.flesch_reading_ease:.1f}",
                    f"Flesch-Kincaid Grade: {heuristic_scores.flesch_kincaid_grade:.1f}",
                    "Use shorter sentences (aim for under 20 words)" if heuristic_scores.readability_score < 60 else "Sentence length is good",
                    "Simplify language and avoid jargon" if heuristic_scores.readability_score < 60 else "Language complexity is appropriate"
                ]
            )
            
            # Entity Clarity (AI)
            if ai_evaluation and not ai_evaluation.error:
                display_category(
                    "Entity Clarity",
                    ai_evaluation.entity_clarity_score,
                    "Measures how clearly brands, products, and concepts are defined for AI understanding.",
                    ai_evaluation.ai_recommendations if ai_evaluation.entity_clarity_score < 70 else ["Entity definitions are clear."]
                )
                
                # Extractability (AI)
                display_category(
                    "Extractability",
                    ai_evaluation.extractability_score,
                    "Evaluates how easily content can be chunked and retrieved by RAG systems.",
                    ["Content structure could be improved for better extraction"] if ai_evaluation.extractability_score < 70 else ["Content is well-structured for extraction."]
                )
                
                # Citation Potential (AI)
                display_category(
                    "Citation Potential",
                    ai_evaluation.citation_potential_score,
                    "Assesses if the content is authoritative enough for AI to cite as reference.",
                    ["Add more authoritative sources and citations"] if ai_evaluation.citation_potential_score < 70 else ["Content appears authoritative."]
                )
            else:
                st.info("AI analysis not available. Add Groq API key for full analysis.")
            
            # View content
            with st.expander("View Extracted Content"):
                st.write(f"**Title:** {content.title}")
                st.write(f"**Meta Description:** {content.meta_description or 'None'}")
                st.write(f"**Word Count:** {heuristic_scores.word_count:,}")
                st.write(f"**JSON-LD Items:** {heuristic_scores.json_ld_count}")
                st.text_area("Content Preview", content.content[:2000] + "...", height=150)


if __name__ == "__main__":
    main()
