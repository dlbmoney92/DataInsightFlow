import streamlit as st

def add_google_analytics():
    """Add Google Analytics tracking code to the app."""
    # Google Analytics measurement ID
    GA_TRACKING_ID = "G-LNS5P4X7H9"
    
    # Google Analytics tracking code - add it to the head section of the page
    ga_script = f"""
    <head>
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA_TRACKING_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{GA_TRACKING_ID}');
    </script>
    </head>
    """
    
    # Use HTML hack to inject the script before the Streamlit content
    st.markdown(ga_script, unsafe_allow_html=True)

def hide_default_navigation():
    """Hide default Streamlit navigation elements."""
    st.markdown("""
        <style>
            /* Hide sidebar navigation elements */
            section[data-testid="stSidebarNav"] {
                display: none !important;
            }
            
            /* Hide all the stSidebarNav elements more aggressively */
            div[data-testid="stSidebarNav"] {
                display: none !important;
            }
            
            /* Also hide specific sidebar nav items */
            [data-testid="stSidebarNavItems"] {
                display: none !important;
            }
            
            /* Target multipage menu items */
            .stApp [data-testid="stSidebarNav"] ul {
                display: none !important;
            }
            
            /* Hide hamburger dropdown menu items */
            ul.streamlit-nav {
                display: none !important;
            }
        </style>
    """, unsafe_allow_html=True)

def apply_global_css():
    """Apply global CSS styles to all pages."""
    # Apply custom styling without hiding Streamlit's navigation elements
    st.markdown("""
        <style>
            /* Hide only footer and hamburger menu, keep the navigation items visible */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            
            /* Custom styling for the whole app */
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            
            /* Custom styling for the sidebar */
            section[data-testid="stSidebar"] .css-17eq0hr {
                background-color: #f8f9fa;
            }
            
            /* Make sure buttons have proper cursor */
            button, [role="button"] {
                cursor: pointer !important;
            }
            
            /* Custom card style */
            .card {
                border-radius: 8px;
                padding: 20px;
                background-color: #ffffff;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 20px;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            
            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
            }
            
            /* Subscription plan cards */
            .plan-card {
                padding: 1rem;
                border-radius: 10px;
                background-color: white;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                height: 100%;
                display: flex;
                flex-direction: column;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            
            .plan-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
            }
            
            .plan-card h3 {
                margin-top: 0;
                font-size: 1.5rem;
                color: #1E3A8A;
            }
            
            .plan-card.highlight {
                border: 3px solid #3B82F6;
                position: relative;
            }
            
            .plan-card.highlight::before {
                content: 'MOST POPULAR';
                position: absolute;
                top: -12px;
                left: 50%;
                transform: translateX(-50%);
                background-color: #3B82F6;
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 0.7rem;
                font-weight: bold;
                letter-spacing: 0.5px;
            }
            
            .price {
                font-size: 2rem;
                font-weight: bold;
                margin: 1rem 0;
                color: #1E3A8A;
            }
            
            .price-period {
                font-size: 0.9rem;
                color: #6B7280;
                margin-top: -0.5rem;
            }
            
            .plan-features {
                list-style-type: none;
                padding: 0;
                margin: 1.5rem 0;
                flex-grow: 1;
            }
            
            .plan-features li {
                margin-bottom: 0.5rem;
                padding-left: 1.5rem;
                position: relative;
            }
            
            .plan-features li::before {
                content: '✓';
                position: absolute;
                left: 0;
                color: #3B82F6;
                font-weight: bold;
            }
            
            .plan-button {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 0.5rem 1rem;
                font-weight: 600;
                cursor: pointer;
                width: 100%;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                transition: background-color 0.2s;
            }
            
            .plan-button:hover {
                background-color: #2563EB;
            }
            
            /* Visual data flow animations */
            @keyframes flow-right {
                0% { transform: translateX(0); opacity: 0; }
                10% { opacity: 1; }
                90% { opacity: 1; }
                100% { transform: translateX(100px); opacity: 0; }
            }
            
            .flow-animation {
                position: relative;
                overflow: hidden;
            }
            
            .flow-particle {
                position: absolute;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background-color: #3B82F6;
                animation: flow-right 2s infinite;
            }
            
            /* Typography improvements */
            h1, h2, h3, h4, h5, h6 {
                color: #1E3A8A;
                font-weight: 600;
            }
            
            /* Checkbox customization */
            input[type="checkbox"] {
                cursor: pointer;
            }
            
            /* Fix for button hover effects */
            button:hover {
                opacity: 0.9;
            }
            
            /* Modal-like popup styles */
            .modal-container {
                max-width: 800px;
                margin: 2rem auto;
                background: white;
                border-radius: 10px;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
                padding: 2rem;
                position: relative;
            }
            
            .modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1.5rem;
            }
            
            .modal-title {
                font-size: 1.5rem;
                font-weight: 600;
                color: #1E3A8A;
                margin: 0;
            }
            
            .modal-close {
                font-size: 1.5rem;
                border: none;
                background: none;
                cursor: pointer;
                color: #6B7280;
            }
            
            .modal-body {
                margin-bottom: 1.5rem;
            }
            
            .modal-footer {
                display: flex;
                justify-content: flex-end;
                gap: 1rem;
            }
            
            /* Hide replit domain url in stStatusWidget */
            [data-testid="stStatusWidget"] {
                display: none !important;
            }
        </style>
    """, unsafe_allow_html=True)

def render_footer():
    """Render the global footer."""
    st.markdown("""
        <div style="
            margin-top: 4rem;
            padding-top: 1rem;
            border-top: 1px solid rgba(49, 51, 63, 0.2);
            text-align: center;
            font-size: 0.8rem;
            color: rgba(49, 51, 63, 0.6);
        ">
            <p>© 2025 Analytics Assist | 
                <a href="/pages/terms_of_service.py" target="_self" style="color: inherit; text-decoration: none;">Terms of Service</a> | 
                <a href="/pages/privacy_policy.py" target="_self" style="color: inherit; text-decoration: none;">Privacy Policy</a>
            </p>
        </div>
    """, unsafe_allow_html=True)