import streamlit as st
import pandas as pd
import json
import base64
import plotly.graph_objects as go
from urllib.parse import quote

# Set page config
st.set_page_config(
    page_title="Shared Analytics - Analytics Assist",
    page_icon="📊",
    layout="wide"
)

# Add Open Graph and social media metadata to improve sharing previews
def get_social_metadata(title, description, image_url=None):
    """Generate HTML meta tags for social media platforms"""
    default_image = "https://analyticsassist.replit.app/assets/logo.png"
    image = image_url or default_image
    
    return f"""
    <!-- Primary Meta Tags -->
    <title>{title}</title>
    <meta name="title" content="{title}">
    <meta name="description" content="{description}">

    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://analyticsassist.replit.app/">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:image" content="{image}">

    <!-- Twitter -->
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:url" content="https://analyticsassist.replit.app/">
    <meta property="twitter:title" content="{title}">
    <meta property="twitter:description" content="{description}">
    <meta property="twitter:image" content="{image}">
    
    <!-- LinkedIn -->
    <meta property="og:site_name" content="Analytics Assist">
    <meta property="og:type" content="article">
    """

# Hide Streamlit's default navigation and menu
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Custom CSS
st.markdown("""
<style>
    .share-header {
        background: linear-gradient(to right, #1e3c72, #2a5298);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .share-footer {
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #eee;
        text-align: center;
    }
    .cta-button {
        background: linear-gradient(to right, #4b6cb7, #182848);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        text-decoration: none;
        display: inline-block;
        margin-top: 1rem;
    }
    .plotly-figure {
        border: 1px solid #eee;
        border-radius: 8px;
        padding: 1rem;
    }
    .metadata {
        color: #666;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

def app():
    # Extract the share ID from the URL query parameter
    share_id = ""
    if "id" in st.query_params:
        share_id = st.query_params["id"]
    
    if not share_id:
        # No share ID provided
        st.markdown('<div class="share-header"><h1>Shared Content</h1><p>No content ID provided. This link may be invalid or expired.</p></div>', unsafe_allow_html=True)
        
        # Add generic social media tags for the main page
        generic_metadata = get_social_metadata(
            title="Analytics Assist - Data Analytics Platform",
            description="An AI-powered data analysis platform that transforms complex datasets into meaningful insights."
        )
        st.markdown(generic_metadata, unsafe_allow_html=True)
        
        display_signup_cta()
        return
    
    # Retrieve the shared content
    # In a real implementation, this would be fetched from a database
    # For demo purposes, we use session state, but this won't work across sessions
    shared_content = st.session_state.get("shared_content", {}).get(share_id)
    
    if not shared_content:
        # Share ID not found
        st.markdown('<div class="share-header"><h1>Shared Content</h1><p>This shared content has expired or does not exist.</p></div>', unsafe_allow_html=True)
        
        # Add generic social media tags for the main page
        generic_metadata = get_social_metadata(
            title="Analytics Assist - Data Analytics Platform",
            description="An AI-powered data analysis platform that transforms complex datasets into meaningful insights."
        )
        st.markdown(generic_metadata, unsafe_allow_html=True)
        
        display_signup_cta()
        return
    
    # Render the shared content based on its type
    content_type = shared_content.get("content_type")
    data = shared_content.get("data")
    created_at = pd.to_datetime(shared_content.get("created_at"))
    
    # Get content title and description for metadata
    title = data.get("title", f"Shared {content_type.title()}")
    
    # Create description based on content type
    if content_type == "report":
        description = data.get("summary", f"A data analysis report created with Analytics Assist on {created_at.strftime('%B %d, %Y')}")
    elif content_type == "visualization":
        description = data.get("description", f"A data visualization created with Analytics Assist on {created_at.strftime('%B %d, %Y')}")
    elif content_type == "insight":
        description = data.get("text", "")[:150] + "..." if len(data.get("text", "")) > 150 else data.get("text", "")
    else:
        description = f"Shared content from Analytics Assist - {created_at.strftime('%B %d, %Y')}"
    
    # Add social media metadata tags to the page
    social_metadata = get_social_metadata(title, description)
    st.markdown(social_metadata, unsafe_allow_html=True)
    
    # Header with title
    st.markdown(f'<div class="share-header"><h1>{title}</h1><p class="metadata">Shared on {created_at.strftime("%B %d, %Y at %I:%M %p")}</p></div>', unsafe_allow_html=True)
    
    # Render based on content type
    if content_type == "visualization":
        render_visualization(data)
    elif content_type == "report":
        render_report(data)
    elif content_type == "insight":
        render_insight(data)
    else:
        st.warning(f"Unknown content type: {content_type}")
    
    # Add footer with CTA
    display_signup_cta()

def render_visualization(data):
    """Render a shared visualization"""
    # Extract data from the visualization
    fig_data = data.get("figure")
    description = data.get("description", "")
    
    if fig_data:
        # Convert back to a plotly figure
        fig = go.Figure(fig_data)
        
        # Add branding if not already present
        if not any("Generated with Analytics Assist" in ann.get("text", "") for ann in fig.layout.annotations or []):
            from utils.sharing import add_branding_to_figure
            fig = add_branding_to_figure(fig)
        
        # Display the figure
        st.markdown('<div class="plotly-figure">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Display description if available
        if description:
            st.markdown(f"### Description\n{description}")
    else:
        st.error("Visualization data is missing or invalid.")

def render_report(data):
    """Render a shared report"""
    # Extract data from the report
    html_content = data.get("html")
    charts = data.get("charts", [])
    text_content = data.get("text", "")
    
    # Display HTML content if available (wrapped in an iframe for safety)
    if html_content:
        encoded_html = base64.b64encode(html_content.encode()).decode()
        st.markdown(f'<iframe srcdoc="{encoded_html}" width="100%" height="600px"></iframe>', unsafe_allow_html=True)
        
        # Add download options
        st.write("### Download Options")
        col1, col2 = st.columns(2)
        
        with col1:
            # HTML download
            html_href = f'<a href="data:text/html;base64,{encoded_html}" download="report.html">Download as HTML</a>'
            st.markdown(html_href, unsafe_allow_html=True)
            
        with col2:
            # PDF download
            from utils.export import generate_pdf_download_link
            
            if st.button("Generate PDF"):
                with st.spinner("Generating PDF..."):
                    try:
                        pdf_href = generate_pdf_download_link(html_content, "report.pdf")
                        st.markdown(pdf_href, unsafe_allow_html=True)
                        st.success("PDF generated successfully!")
                    except Exception as e:
                        st.error(f"Error generating PDF: {str(e)}")
                        st.info("Please try the HTML download option instead.")
    
    # Display text content
    if text_content:
        st.markdown(text_content)
    
    # Display charts
    for i, chart in enumerate(charts):
        if isinstance(chart, dict) and "figure" in chart:
            fig = go.Figure(chart["figure"])
            st.plotly_chart(fig, use_container_width=True)
            if "caption" in chart:
                st.caption(chart["caption"])

def render_insight(data):
    """Render a shared insight"""
    # Extract data from the insight
    insight_text = data.get("text", "")
    importance = data.get("importance", 3)
    category = data.get("category", "General")
    source = data.get("source", "AI Analysis")
    
    # Create stars based on importance
    stars = "⭐" * importance
    
    # Display the insight
    st.markdown(f"{stars} **{category}**")
    st.markdown(f"### {data.get('title', 'Insight')}")
    st.markdown(insight_text)
    st.markdown(f"*Source: {source}*")
    
    # Display related visualizations if available
    visualizations = data.get("visualizations", [])
    if visualizations:
        st.markdown("### Supporting Visualizations")
        for viz in visualizations:
            if isinstance(viz, dict) and "figure" in viz:
                fig = go.Figure(viz["figure"])
                st.plotly_chart(fig, use_container_width=True)
                if "caption" in viz:
                    st.caption(viz["caption"])

def display_signup_cta():
    """Display a CTA to sign up for Analytics Assist"""
    st.markdown("""
    <div class="share-footer">
        <h3>Want to create your own data insights?</h3>
        <p>Analytics Assist helps you analyze data, generate insights, and create beautiful visualizations with AI assistance.</p>
        <a href="/" class="cta-button">Try Analytics Assist</a>
    </div>
    """, unsafe_allow_html=True)

# Run the app
app()