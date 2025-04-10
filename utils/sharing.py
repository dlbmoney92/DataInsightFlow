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
    
    # For local development environment, use a relative URL
    # This ensures the shared content is accessible locally
    share_link = f"/pages/shared_content.py?id={share_id}"
    
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
    # Always create an absolute URL for sharing
    if share_url.startswith('/'):
        # For production environment, use the Replit domain
        base_url = "https://analytics-assist.replit.app"
        full_url = f"{base_url}{share_url}"
    else:
        full_url = share_url
    
    encoded_url = quote(full_url)
    encoded_title = quote(title)
    encoded_summary = quote(summary or f"Check out this data insight from Analytics Assist: {title}")
    
    # Create properly formatted social media sharing links
    return {
        'linkedin': f"https://www.linkedin.com/shareArticle?mini=true&url={encoded_url}&title={encoded_title}&summary={encoded_summary}&source=AnalyticsAssist",
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
    # Make the share link absolute
    if share_link.startswith('/'):
        # Create the full URL with the base domain
        base_url = "https://analytics-assist.replit.app"
        absolute_share_link = f"{base_url}{share_link}"
    else:
        absolute_share_link = share_link
    
    with st.container(border=True):
        st.subheader(f"Share {content_type.title()}")
        
        # Show the shareable link in a text input
        st.text_input("Shareable Link", absolute_share_link, disabled=True, key=f"share_input_{hash(share_link)}")
        
        col1, col2 = st.columns(2)
        with col1:
            # Create a unique ID for each copy button
            copy_button_id = f"copy_button_{hash(share_link)}"
            
            # Add JavaScript for copying to clipboard
            copy_js = f"""
            <script>
            function copyToClipboard{hash(share_link)}() {{
                const el = document.createElement('textarea');
                el.value = "{absolute_share_link}";
                document.body.appendChild(el);
                el.select();
                document.execCommand('copy');
                document.body.removeChild(el);
                
                // Show the success message
                document.getElementById('copy_success_{hash(share_link)}').style.display = 'block';
                setTimeout(function() {{
                    document.getElementById('copy_success_{hash(share_link)}').style.display = 'none';
                }}, 3000);
            }}
            </script>
            <button id="{copy_button_id}" 
                onclick="copyToClipboard{hash(share_link)}()" 
                style="background-color: #1E88E5; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; width: 100%;">
                📋 Copy Link
            </button>
            <div id="copy_success_{hash(share_link)}" style="display: none; color: green; margin-top: 5px;">
                ✅ Link copied to clipboard!
            </div>
            """
            
            # Render the button with JS
            st.markdown(copy_js, unsafe_allow_html=True)
                
        with col2:
            if st.button("✉️ Email Link", key=f"email_{content_type}_{hash(share_link)}"):
                subject = f"Analytics Assist: {title}"
                body = f"Check out this {content_type} from Analytics Assist: {absolute_share_link}"
                st.markdown(f'<a href="mailto:?subject={quote(subject)}&body={quote(body)}" target="_blank">Send Email</a>', unsafe_allow_html=True)
                
        if include_social:
            st.markdown("### Share on Social Media")
            st.write("Share this content with colleagues and friends on your favorite platforms.")
            
            social_links = get_social_share_links(title, absolute_share_link, summary)
            
            # CSS for styled buttons
            st.markdown("""
            <style>
            .social-buttons {
                display: flex;
                justify-content: center;
                gap: 20px;
                margin: 15px 0;
            }
            .social-button {
                text-decoration: none;
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 8px 12px;
                border-radius: 8px;
                transition: all 0.3s ease;
                background: rgba(0, 0, 0, 0.03);
            }
            .social-button:hover {
                background: rgba(0, 0, 0, 0.08);
                transform: translateY(-2px);
            }
            .social-icon {
                font-size: 28px;
                margin-bottom: 5px;
            }
            .social-name {
                font-size: 12px;
                color: #555;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Using SVG logos for social media buttons
            
            # LinkedIn SVG logo
            linkedin_logo = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#0077b5">
                <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" />
            </svg>"""

            # Twitter/X SVG logo
            twitter_logo = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#1DA1F2">
                <path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z" />
            </svg>"""

            # Facebook SVG logo
            facebook_logo = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#4267B2">
                <path d="M9 8h-3v4h3v12h5v-12h3.642l.358-4h-4v-1.667c0-.955.192-1.333 1.115-1.333h2.885v-5h-3.808c-3.596 0-5.192 1.583-5.192 4.615v3.385z" />
            </svg>"""

            # Email SVG logo
            email_logo = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#555555">
                <path d="M12 12.713l-11.985-9.713h23.97l-11.985 9.713zm0 2.574l-12-9.725v15.438h24v-15.438l-12 9.725z" />
            </svg>"""
            
            # Generate HTML for social buttons with SVG logos
            html = """
            <div class="social-buttons">
                <a href="{linkedin}" target="_blank" class="social-button" title="Share on LinkedIn">
                    <div class="social-icon">{linkedin_logo}</div>
                    <div class="social-name">LinkedIn</div>
                </a>
                <a href="{twitter}" target="_blank" class="social-button" title="Share on Twitter">
                    <div class="social-icon">{twitter_logo}</div>
                    <div class="social-name">Twitter</div>
                </a>
                <a href="{facebook}" target="_blank" class="social-button" title="Share on Facebook">
                    <div class="social-icon">{facebook_logo}</div>
                    <div class="social-name">Facebook</div>
                </a>
                <a href="{email}" target="_blank" class="social-button" title="Share via Email">
                    <div class="social-icon">{email_logo}</div>
                    <div class="social-name">Email</div>
                </a>
            </div>
            """.format(
                linkedin=social_links["linkedin"],
                twitter=social_links["twitter"],
                facebook=social_links["facebook"],
                email=social_links["email"],
                linkedin_logo=linkedin_logo,
                twitter_logo=twitter_logo,
                facebook_logo=facebook_logo,
                email_logo=email_logo
            )
            
            st.markdown(html, unsafe_allow_html=True)

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