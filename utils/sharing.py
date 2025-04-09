import streamlit as st
import base64
import json
import uuid
import os
from urllib.parse import quote
import plotly.graph_objects as go
import pandas as pd
import io
import re

def create_share_link(content_type, content_id, data):
    """
    Create a shareable link for various content types
    
    Parameters:
    - content_type: Type of content ('report', 'visualization', 'insight')
    - content_id: Identifier for the content
    - data: The data to be shared (different format based on content_type)
    
    Returns:
    - share_link: A URL that can be used to access the shared content
    """
    # Create a unique ID for this share
    share_id = str(uuid.uuid4())
    
    # Encode the data based on content type
    if content_type == 'report':
        # For reports, this could be HTML or JSON
        encoded_data = base64.b64encode(json.dumps(data).encode()).decode()
    elif content_type == 'visualization':
        # For visualizations, this could be a Plotly figure
        encoded_data = base64.b64encode(json.dumps(data).encode()).decode()
    elif content_type == 'insight':
        # For insights, this could be structured text/JSON
        encoded_data = base64.b64encode(json.dumps(data).encode()).decode()
    else:
        raise ValueError(f"Unsupported content type: {content_type}")
    
    # Store the shared content in session state for temporary access
    if 'shared_content' not in st.session_state:
        st.session_state.shared_content = {}
    
    st.session_state.shared_content[share_id] = {
        'content_type': content_type,
        'content_id': content_id,
        'data': data,
        'created_at': pd.Timestamp.now().isoformat()
    }
    
    # Create a shareable link
    # In a real implementation, you'd want to store this in a database
    # and have a proper sharing mechanism, but for demo purposes this works
    host = os.environ.get('REPLIT_DEPLOYMENT_URL', 'https://analytics-assist.replit.app')
    share_link = f"{host}/pages/shared_content.py?id={share_id}"
    
    return share_link

def get_social_share_links(title, share_url, summary=None):
    """
    Generate social media sharing links
    
    Parameters:
    - title: Title of the content
    - share_url: URL to the shared content
    - summary: Optional summary text
    
    Returns:
    - dict of platform -> share URL
    """
    encoded_url = quote(share_url)
    encoded_title = quote(title)
    encoded_summary = quote(summary or f"Check out this data insight from Analytics Assist: {title}")
    
    return {
        'linkedin': f"https://www.linkedin.com/sharing/share-offsite/?url={encoded_url}&title={encoded_title}&summary={encoded_summary}",
        'twitter': f"https://twitter.com/intent/tweet?url={encoded_url}&text={encoded_summary}",
        'facebook': f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}&quote={encoded_summary}",
        'email': f"mailto:?subject={encoded_title}&body={encoded_summary}%0A%0A{encoded_url}"
    }

def generate_share_card(title, content_type, share_link, include_social=True, summary=None):
    """
    Generate a UI card with sharing options
    
    Parameters:
    - title: Title of the content
    - content_type: Type of content ('report', 'visualization', 'insight')
    - share_link: URL to the shared content
    - include_social: Whether to include social sharing buttons
    - summary: Optional summary text
    
    Returns:
    - None (directly renders the card)
    """
    with st.container(border=True):
        st.subheader(f"Share {content_type.title()}")
        
        st.text_input("Shareable Link", share_link, disabled=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Copy Link", key=f"copy_{content_type}_{hash(share_link)}"):
                # Use JavaScript to copy to clipboard
                st.markdown(f"""
                <script>
                    navigator.clipboard.writeText("{share_link}");
                </script>
                """, unsafe_allow_html=True)
                st.success("Link copied to clipboard!")
                
        with col2:
            if st.button("✉️ Email Link", key=f"email_{content_type}_{hash(share_link)}"):
                subject = f"Analytics Assist: {title}"
                body = f"Check out this {content_type} from Analytics Assist: {share_link}"
                st.markdown(f'<a href="mailto:?subject={quote(subject)}&body={quote(body)}" target="_blank">Send Email</a>', unsafe_allow_html=True)
                
        if include_social:
            st.markdown("### Share on Social Media")
            
            social_links = get_social_share_links(title, share_link, summary)
            social_cols = st.columns(4)
            
            with social_cols[0]:
                st.markdown(f'<a href="{social_links["linkedin"]}" target="_blank">LinkedIn</a>', unsafe_allow_html=True)
            with social_cols[1]:
                st.markdown(f'<a href="{social_links["twitter"]}" target="_blank">Twitter</a>', unsafe_allow_html=True)
            with social_cols[2]:
                st.markdown(f'<a href="{social_links["facebook"]}" target="_blank">Facebook</a>', unsafe_allow_html=True)
            with social_cols[3]:
                st.markdown(f'<a href="{social_links["email"]}" target="_blank">Email</a>', unsafe_allow_html=True)

def export_visualization_with_branding(fig, title=None, format='png'):
    """
    Export a Plotly visualization with branding watermark
    
    Parameters:
    - fig: Plotly figure to export
    - title: Optional title to include
    - format: Export format ('png', 'svg', or 'pdf')
    
    Returns:
    - bytes: The image data for download
    """
    # Add the branding watermark
    fig = add_branding_to_figure(fig, title)
    
    # Export based on format
    if format == 'png':
        img_bytes = fig.to_image(format='png', scale=2)
        return img_bytes
    elif format == 'svg':
        return fig.to_image(format='svg')
    elif format == 'pdf':
        # For PDF, we need a bit more work
        import plotly.io as pio
        buffer = io.BytesIO()
        pio.write_image(fig, buffer, format='pdf')
        buffer.seek(0)
        return buffer.read()
    else:
        raise ValueError(f"Unsupported format: {format}")

def add_branding_to_figure(fig, title=None):
    """
    Add branding watermark to a Plotly figure
    
    Parameters:
    - fig: Plotly figure
    - title: Optional title to include
    
    Returns:
    - fig: Modified Plotly figure with branding
    """
    # Create a copy of the figure
    fig = go.Figure(fig)
    
    # Generate the branding text
    branding_text = "Generated with Analytics Assist • analytics-assist.replit.app"
    
    # Add title if provided
    if title:
        branding_text = f"{title}<br>{branding_text}"
    
    # Add the branding annotation
    fig.add_annotation(
        text=branding_text,
        x=0.5,
        y=-0.15,  # Position below the plot
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(
            size=10,
            color="gray"
        ),
        opacity=0.7,
        align="center"
    )
    
    # Adjust the layout to make room for the branding
    fig.update_layout(
        margin=dict(b=80)  # Increase bottom margin
    )
    
    return fig

def generate_qr_code(url, size=5):
    """
    Generate a QR code for a URL
    
    Parameters:
    - url: The URL to encode
    - size: Size of the QR code
    
    Returns:
    - qr_data: Base64 encoded PNG data for the QR code
    """
    import qrcode
    import io
    import base64
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_data = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    return qr_data

def generate_report_summary(df, insights=None, visualizations=None):
    """
    Generate a summary of a report for sharing
    
    Parameters:
    - df: DataFrame being analyzed
    - insights: Optional list of insights
    - visualizations: Optional list of visualization descriptions
    
    Returns:
    - summary: A summary string suitable for sharing
    """
    # Create basic stats summary
    rows, cols = df.shape
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    summary = f"Dataset: {rows} rows × {cols} columns • "
    summary += f"{len(numeric_cols)} numeric variables • {len(categorical_cols)} categorical variables"
    
    # Add insights if available
    if insights and len(insights) > 0:
        summary += "\n\nKey Insights:\n"
        for i, insight in enumerate(insights[:3], 1):  # Top 3 insights
            if isinstance(insight, dict) and 'title' in insight:
                summary += f"{i}. {insight['title']}\n"
            elif isinstance(insight, str):
                summary += f"{i}. {insight}\n"
    
    # Add visualizations if available
    if visualizations and len(visualizations) > 0:
        summary += "\nVisualizations include: "
        viz_descriptions = []
        for viz in visualizations[:2]:  # Top 2 visualizations
            if isinstance(viz, dict) and 'title' in viz:
                viz_descriptions.append(viz['title'])
            elif isinstance(viz, str):
                viz_descriptions.append(viz)
        summary += ", ".join(viz_descriptions)
    
    return summary