"""
LLMO Analyzer - Check how AI-friendly a webpage is
"""

import pandas as pd
import plotly.graph_objects as go
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

def create_gauge_chart(score: float, title: str, color: str = "#1f77b4") -> go.Figure:
    """Create a gauge chart for displaying scores."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#333"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 1,
            'bordercolor': "#ccc",
            'steps': [
                {'range': [0, 50], 'color': '#ffcccc'},
                {'range': [50, 75], 'color': '#ffffcc'},
                {'range': [75, 90], 'color': '#ccffcc'},
                {'range': [90, 100], 'color': '#99ff99'}
            ],
            'threshold': {
                'line': {'color': "#333", 'width': 2},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="white",
        font={'color': "#333", 'family': "Arial"}
    )
    
    return fig


def display_score_breakdown(heuristic_scores: HeuristicScores, ai_evaluation: AIEvaluation):
    """Display detailed score breakdown."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Heuristics")
        st.metric("Readability", f"{heuristic_scores.readability_score:.1f}")
        st.metric("Structure", f"{heuristic_scores.structure_score:.1f}")
        st.metric("Technical", f"{heuristic_scores.technical_score:.1f}")
    
    with col2:
        st.subheader("AI Scores")
        if ai_evaluation.error:
            st.error(ai_evaluation.error)
        else:
            st.metric("Entity Clarity", f"{ai_evaluation.entity_clarity_score:.1f}")
            st.metric("Extractability", f"{ai_evaluation.extractability_score:.1f}")
            st.metric("Citation", f"{ai_evaluation.citation_potential_score:.1f}")
    
    with col3:
        st.subheader("Stats")
        st.metric("Words", f"{heuristic_scores.word_count:,}")
        st.metric("Flesch-Kincaid", f"{heuristic_scores.flesch_kincaid_grade:.1f}")
        st.write(f"Schema: {'Yes' if heuristic_scores.has_json_ld else 'No'}")


def display_recommendations(heuristic_scores: HeuristicScores, ai_evaluation: AIEvaluation):
    """Display recommendations."""
    st.subheader("Recommendations")
    
    all_recs = heuristic_scores.recommendations + ai_evaluation.ai_recommendations
    
    if all_recs:
        for i, rec in enumerate(all_recs, 1):
            st.write(f"{i}. {rec}")
    else:
        st.write("Looks good!")


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
    st.title("🤖 LLMO Analyzer")
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
        
        mode = st.radio("Mode", ["Single URL", "Compare"])
        
        st.divider()
        st.write("Checks readability, structure, schema markup, and AI usability")
    
    if mode == "Single URL":
        url = st.text_input("URL", placeholder="https://example.com")
        
        if st.button("Analyze", type="primary") and url:
            content, heuristic_scores, ai_evaluation = analyze_single_url(url)
            
            if content.error:
                st.error(content.error)
            else:
                total_score = 0.0
                if heuristic_scores:
                    total_score += heuristic_scores.overall_heuristic_score * 0.6
                if ai_evaluation and not ai_evaluation.error:
                    total_score += ai_evaluation.overall_ai_score * 0.4
                
                st.plotly_chart(
                    create_gauge_chart(total_score, "Score", "#1f77b4"),
                    use_container_width=True
                )
                
                if total_score >= 80:
                    st.success("Good AI optimization")
                elif total_score >= 60:
                    st.info("Decent, could improve")
                elif total_score >= 40:
                    st.warning("Needs work")
                else:
                    st.error("Poor AI optimization")
                
                display_score_breakdown(heuristic_scores, ai_evaluation)
                display_recommendations(heuristic_scores, ai_evaluation)
                
                with st.expander("View content"):
                    st.write(f"Title: {content.title}")
                    st.write(f"Meta: {content.meta_description or 'None'}")
                    st.text_area("Content", content.content[:2000] + "...", height=150)
    
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            url1 = st.text_input("URL 1", key="url1")
        
        with col2:
            url2 = st.text_input("URL 2", key="url2")
        
        if st.button("Compare", type="primary") and url1 and url2:
            with st.spinner("Analyzing URL 1..."):
                content1, h1, ai1 = analyze_single_url(url1)
            
            with st.spinner("Analyzing URL 2..."):
                content2, h2, ai2 = analyze_single_url(url2)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("URL 1")
                if h1:
                    score1 = h1.overall_heuristic_score * 0.6
                    if ai1 and not ai1.error:
                        score1 += ai1.overall_ai_score * 0.4
                    st.plotly_chart(create_gauge_chart(score1, "Score", "#1f77b4"), use_container_width=True)
                    st.metric("Score", f"{score1:.1f}")
            
            with col2:
                st.subheader("URL 2")
                if h2:
                    score2 = h2.overall_heuristic_score * 0.6
                    if ai2 and not ai2.error:
                        score2 += ai2.overall_ai_score * 0.4
                    st.plotly_chart(create_gauge_chart(score2, "Score", "#2ca02c"), use_container_width=True)
                    st.metric("Score", f"{score2:.1f}")
            
            if h1 and h2:
                if score1 > score2:
                    st.success(f"URL 1 is better by {score1 - score2:.1f} points")
                elif score2 > score1:
                    st.success(f"URL 2 is better by {score2 - score1:.1f} points")
                else:
                    st.info("Tie")


if __name__ == "__main__":
    main()
