"""
LLMO Analyzer - Main Streamlit Application
Professional-grade dashboard for LLMO scoring with Groq AI integration.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from llmo_analyzer.config import Config
from llmo_analyzer.groq_analyzer import AIEvaluation, GroqAnalyzer
from llmo_analyzer.heuristics import HeuristicAnalyzer, HeuristicScores
from llmo_analyzer.scraper import ScrapedContent, WebScraper

# Page configuration
st.set_page_config(
    page_title="LLMO Analyzer Pro",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
    }
    .recommendation-item {
        background: #e8f4f8;
        padding: 0.8rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        border-left: 4px solid #17a2b8;
    }
    .error-box {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #dc3545;
    }
    .success-box {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
</style>
""", unsafe_allow_html=True)


def create_gauge_chart(score: float, title: str, color: str = "#1f77b4") -> go.Figure:
    """Create a gauge chart for displaying scores."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': '#ffcccc'},
                {'range': [50, 75], 'color': '#ffffcc'},
                {'range': [75, 90], 'color': '#ccffcc'},
                {'range': [90, 100], 'color': '#99ff99'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font={'color': "darkblue", 'family': "Arial"}
    )
    
    return fig


def display_score_breakdown(heuristic_scores: HeuristicScores, ai_evaluation: AIEvaluation):
    """Display detailed score breakdown."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📊 Heuristic Scores")
        
        # Readability
        st.metric(
            "Readability",
            f"{heuristic_scores.readability_score:.1f}",
            f"Flesch: {heuristic_scores.flesch_reading_ease:.1f}"
        )
        
        # Structure
        st.metric(
            "Structure",
            f"{heuristic_scores.structure_score:.1f}",
            f"H1: {heuristic_scores.h1_count}, H2: {heuristic_scores.h2_count}"
        )
        
        # Technical
        schema_status = "✅" if heuristic_scores.has_json_ld else "❌"
        st.metric(
            "Technical SEO",
            f"{heuristic_scores.technical_score:.1f}",
            f"Schema: {schema_status}"
        )
    
    with col2:
        st.subheader("🤖 AI Evaluation")
        
        if ai_evaluation.error:
            st.error(ai_evaluation.error)
        else:
            st.metric(
                "Entity Clarity",
                f"{ai_evaluation.entity_clarity_score:.1f}"
            )
            st.metric(
                "Extractability",
                f"{ai_evaluation.extractability_score:.1f}"
            )
            st.metric(
                "Citation Potential",
                f"{ai_evaluation.citation_potential_score:.1f}"
            )
    
    with col3:
        st.subheader("📝 Content Stats")
        st.metric("Word Count", f"{heuristic_scores.word_count:,}")
        st.metric("Flesch-Kincaid Grade", f"{heuristic_scores.flesch_kincaid_grade:.1f}")
        
        content_quality = "🟢 Excellent" if heuristic_scores.word_count > 1000 else \
                         "🟡 Good" if heuristic_scores.word_count > 500 else "🟠 Needs Work"
        st.write(f"**Content Depth:** {content_quality}")


def display_recommendations(heuristic_scores: HeuristicScores, ai_evaluation: AIEvaluation):
    """Display actionable recommendations."""
    st.subheader("🎯 Actionable Recommendations")
    
    all_recommendations = []
    
    # Add heuristic recommendations
    all_recommendations.extend(heuristic_scores.recommendations)
    
    # Add AI recommendations
    if ai_evaluation.ai_recommendations:
        all_recommendations.extend([f"🤖 {rec}" for rec in ai_evaluation.ai_recommendations])
    
    # Display in a table format
    if all_recommendations:
        df = pd.DataFrame({
            'Priority': [f"{i+1}" for i in range(len(all_recommendations))],
            'Recommendation': all_recommendations
        })
        
        st.dataframe(
            df,
            column_config={
                "Priority": st.column_config.NumberColumn("Priority", width="small"),
                "Recommendation": st.column_config.TextColumn("Recommendation", width="large")
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.success("✅ No major issues found! Your content is well-optimized for LLMs.")


def analyze_single_url(url: str) -> tuple[ScrapedContent, HeuristicScores, AIEvaluation]:
    """Analyze a single URL and return all results."""
    # Initialize components
    scraper = WebScraper(timeout=Config.REQUEST_TIMEOUT)
    heuristic_analyzer = HeuristicAnalyzer()
    
    # Scrape content
    with st.spinner("🔍 Scraping website content..."):
        content = scraper.scrape(url)
    
    if content.error:
        return content, None, None
    
    # Calculate heuristic scores
    with st.spinner("📊 Calculating heuristic scores..."):
        heuristic_scores = heuristic_analyzer.analyze(content)
    
    # Get AI evaluation
    with st.spinner("🤖 Analyzing with Groq AI..."):
        try:
            groq_analyzer = GroqAnalyzer()
            ai_evaluation = groq_analyzer.analyze(content)
        except ValueError as e:
            ai_evaluation = AIEvaluation(error=str(e))
    
    return content, heuristic_scores, ai_evaluation


def main():
    """Main application function."""
    # Header
    st.markdown('<div class="main-header">🤖 LLMO Analyzer Pro</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Professional-grade Large Language Model Optimization scoring with Groq AI</div>',
        unsafe_allow_html=True
    )
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input
        api_key = st.text_input(
            "Groq API Key",
            value=Config.GROQ_API_KEY or "",
            type="password",
            help="Get your API key from https://console.groq.com/keys"
        )
        
        if api_key:
            Config.GROQ_API_KEY = api_key
        
        st.divider()
        
        # Mode selection
        mode = st.radio(
            "Analysis Mode",
            ["Single URL", "Comparison Mode"],
            help="Compare two URLs side-by-side or analyze a single URL"
        )
        
        st.divider()
        
        # Info
        st.info("""
        **About LLMO Score**
        
        This tool evaluates how "AI-friendly" your content is:
        - **Readability**: How easy is it to read?
        - **Structure**: Is it well-organized with headings?
        - **Technical**: Does it have proper schema markup?
        - **AI Evaluation**: Groq AI assesses entity clarity, extractability, and citation potential
        """)
    
    # Validate configuration
    config_errors = Config.validate()
    if config_errors and mode == "Single URL":  # Only show config errors in single mode initially
        for error in config_errors:
            st.error(error)
        st.info("💡 Please add your Groq API key in the sidebar to use AI evaluation features.")
    
    # Main content area
    if mode == "Single URL":
        st.header("🔍 Single URL Analysis")
        
        url = st.text_input(
            "Enter URL to analyze",
            placeholder="https://example.com",
            help="Enter a valid HTTP or HTTPS URL"
        )
        
        analyze_button = st.button("🚀 Analyze URL", type="primary", use_container_width=True)
        
        if analyze_button and url:
            content, heuristic_scores, ai_evaluation = analyze_single_url(url)
            
            if content.error:
                st.markdown(f'<div class="error-box">❌ {content.error}</div>', unsafe_allow_html=True)
            else:
                # Calculate total score
                total_score = 0.0
                if heuristic_scores:
                    total_score += heuristic_scores.overall_heuristic_score * 0.6
                if ai_evaluation and not ai_evaluation.error:
                    total_score += ai_evaluation.overall_ai_score * 0.4
                
                # Display main score gauge
                st.plotly_chart(
                    create_gauge_chart(total_score, "Overall LLMO Score", "#1f77b4"),
                    use_container_width=True
                )
                
                # Score interpretation
                if total_score >= 80:
                    st.markdown(
                        '<div class="success-box">🌟 <strong>Excellent!</strong> Your content is highly optimized for LLMs and AI systems.</div>',
                        unsafe_allow_html=True
                    )
                elif total_score >= 60:
                    st.markdown(
                        '<div class="success-box">✅ <strong>Good</strong> Your content is fairly AI-friendly with room for improvement.</div>',
                        unsafe_allow_html=True
                    )
                elif total_score >= 40:
                    st.markdown(
                        '<div class="error-box">⚠️ <strong>Fair</strong> Your content needs optimization to be more AI-friendly.</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        '<div class="error-box">🚨 <strong>Needs Work</strong> Significant improvements needed for AI optimization.</div>',
                        unsafe_allow_html=True
                    )
                
                # Detailed breakdown
                display_score_breakdown(heuristic_scores, ai_evaluation)
                
                # Recommendations
                display_recommendations(heuristic_scores, ai_evaluation)
                
                # Expandable details
                with st.expander("📄 View Extracted Content"):
                    st.write(f"**Title:** {content.title}")
                    st.write(f"**Meta Description:** {content.meta_description or 'Not found'}")
                    st.write(f"**JSON-LD Schema:** {len(content.json_ld)} items found")
                    st.text_area("Content Preview", content.content[:2000] + "...", height=200)
    
    else:  # Comparison Mode
        st.header("⚖️ Comparison Mode")
        st.write("Compare two URLs side-by-side to see which is more AI-friendly.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            url1 = st.text_input("First URL", placeholder="https://example1.com", key="url1")
        
        with col2:
            url2 = st.text_input("Second URL", placeholder="https://example2.com", key="url2")
        
        compare_button = st.button("⚖️ Compare URLs", type="primary", use_container_width=True)
        
        if compare_button and url1 and url2:
            # Analyze both URLs
            with st.spinner("Analyzing first URL..."):
                content1, heuristic1, ai1 = analyze_single_url(url1)
            
            with st.spinner("Analyzing second URL..."):
                content2, heuristic2, ai2 = analyze_single_url(url2)
            
            # Display comparison
            comp_col1, comp_col2 = st.columns(2)
            
            with comp_col1:
                st.subheader("🔗 URL 1")
                st.write(f"**{content1.title}**")
                
                if content1.error:
                    st.error(content1.error)
                elif heuristic1:
                    score1 = heuristic1.overall_heuristic_score * 0.6
                    if ai1 and not ai1.error:
                        score1 += ai1.overall_ai_score * 0.4
                    
                    st.plotly_chart(
                        create_gauge_chart(score1, "LLMO Score", "#ff7f0e"),
                        use_container_width=True
                    )
                    
                    st.metric("Readability", f"{heuristic1.readability_score:.1f}")
                    st.metric("Structure", f"{heuristic1.structure_score:.1f}")
                    st.metric("Technical", f"{heuristic1.technical_score:.1f}")
                    if ai1 and not ai1.error:
                        st.metric("AI Score", f"{ai1.overall_ai_score:.1f}")
            
            with comp_col2:
                st.subheader("🔗 URL 2")
                st.write(f"**{content2.title}**")
                
                if content2.error:
                    st.error(content2.error)
                elif heuristic2:
                    score2 = heuristic2.overall_heuristic_score * 0.6
                    if ai2 and not ai2.error:
                        score2 += ai2.overall_ai_score * 0.4
                    
                    st.plotly_chart(
                        create_gauge_chart(score2, "LLMO Score", "#2ca02c"),
                        use_container_width=True
                    )
                    
                    st.metric("Readability", f"{heuristic2.readability_score:.1f}")
                    st.metric("Structure", f"{heuristic2.structure_score:.1f}")
                    st.metric("Technical", f"{heuristic2.technical_score:.1f}")
                    if ai2 and not ai2.error:
                        st.metric("AI Score", f"{ai2.overall_ai_score:.1f}")
            
            # Winner announcement
            if not content1.error and not content2.error and heuristic1 and heuristic2:
                st.divider()
                
                score1 = heuristic1.overall_heuristic_score * 0.6
                if ai1 and not ai1.error:
                    score1 += ai1.overall_ai_score * 0.4
                
                score2 = heuristic2.overall_heuristic_score * 0.6
                if ai2 and not ai2.error:
                    score2 += ai2.overall_ai_score * 0.4
                
                if score1 > score2:
                    winner_diff = score1 - score2
                    st.success(f"🏆 **URL 1 wins!** It's {winner_diff:.1f} points more AI-friendly than URL 2.")
                elif score2 > score1:
                    winner_diff = score2 - score1
                    st.success(f"🏆 **URL 2 wins!** It's {winner_diff:.1f} points more AI-friendly than URL 1.")
                else:
                    st.info("🤝 **It's a tie!** Both URLs have identical LLMO scores.")


if __name__ == "__main__":
    main()
