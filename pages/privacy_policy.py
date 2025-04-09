import streamlit as st
from utils.custom_navigation import render_navigation, initialize_navigation

# Set the page configuration
st.set_page_config(
    page_title="Privacy Policy | Analytics Assist",
    page_icon="🔒",
    layout="wide"
)

# Hide Streamlit's default menu and navigation
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stSidebarNav"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# Initialize navigation
initialize_navigation()

# Render custom navigation bar
render_navigation()

# Additional sidebar elements
with st.sidebar:
    # Developer login form and logout are handled by the render_navigation function
    pass

def app():
    st.title("Privacy Policy")
    
    st.write("""
    ## Analytics Assist Privacy Policy
    
    **Last Updated: April 7, 2025**
    
    Analytics Assist ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our data analytics platform.
    
    ### 1. Information We Collect
    
    #### 1.1 Personal Information
    We may collect personal information that you voluntarily provide to us when you register for an account, such as:
    - Your name
    - Email address
    - Payment information
    - Company information (if applicable)
    
    #### 1.2 Usage Data
    We may automatically collect certain information about how you interact with our platform, including:
    - IP address
    - Browser type
    - Device information
    - Pages visited
    - Features used
    - Time and date of your visits
    
    #### 1.3 User Data
    We collect and process the data you upload to our platform for analysis. This may include business data, personal data, or other types of data depending on your use of our services.
    
    ### 2. How We Use Your Information
    
    We may use the information we collect for various purposes, including:
    
    #### 2.1 To Provide and Maintain Our Service
    - Create and manage your account
    - Process your payments
    - Provide the analytics services you request
    - Improve our platform and user experience
    
    #### 2.2 To Communicate With You
    - Send you service updates and announcements
    - Respond to your inquiries and support requests
    - Send marketing communications (with your consent)
    
    #### 2.3 For AI and Machine Learning Purposes
    - Train and improve our AI models to enhance our services
    - Generate insights and recommendations based on your data
    - Customize the platform experience to your preferences
    
    ### 3. Data Storage and Security
    
    #### 3.1 Data Storage
    We store your data on secure servers and use industry-standard measures to protect your information from unauthorized access, loss, misuse, or alteration.
    
    #### 3.2 Data Retention
    We retain your personal information and account data for as long as your account is active or as needed to provide you services. We retain your uploaded data according to our data retention policy or your specific instructions.
    
    #### 3.3 Security Measures
    We implement various security measures to protect your information, including:
    - Encryption of transmitted data
    - Regular security assessments
    - Access controls and authentication
    - Data backup procedures
    
    ### 4. Sharing Your Information
    
    #### 4.1 Service Providers
    We may share your information with third-party service providers who perform services on our behalf, such as payment processing, data analysis, email delivery, and hosting services.
    
    #### 4.2 Business Transfers
    If we are involved in a merger, acquisition, or sale of all or a portion of our assets, your information may be transferred as part of that transaction.
    
    #### 4.3 Legal Requirements
    We may disclose your information if required to do so by law or in response to valid requests by public authorities.
    
    ### 5. Your Data Protection Rights
    
    Depending on your location, you may have certain rights regarding your personal information, including:
    
    - The right to access your personal information
    - The right to correct inaccurate or incomplete information
    - The right to delete your personal information
    - The right to restrict or object to processing of your personal information
    - The right to data portability
    - The right to withdraw consent
    
    To exercise these rights, please contact us using the information provided in the "Contact Us" section.
    
    ### 6. Cookies and Tracking Technologies
    
    We use cookies and similar tracking technologies to collect and track information about how you use our platform. You can instruct your browser to refuse all cookies or to indicate when a cookie is being sent.
    
    ### 7. Third-Party Links
    
    Our platform may contain links to third-party websites or services. We are not responsible for the content or privacy practices of these third-party sites.
    
    ### 8. Children's Privacy
    
    Our platform is not intended for individuals under the age of 16. We do not knowingly collect personal information from children under 16. If you are a parent or guardian and believe your child has provided us with personal information, please contact us.
    
    ### 9. International Data Transfers
    
    Your information may be transferred to and processed in countries other than the country in which you reside. These countries may have data protection laws that are different from those in your country.
    
    ### 10. Changes to This Privacy Policy
    
    We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the "Last Updated" date.
    
    ### 11. AI Learning and Data Processing
    
    #### 11.1 AI Training
    We use anonymized and aggregated data to train our AI systems. This helps us improve the accuracy of our analytics, predictions, and recommendations.
    
    #### 11.2 Feedback Collection
    When you provide feedback on AI-generated insights or transformations, we collect this feedback to improve our AI systems and tailor recommendations to your preferences.
    
    #### 11.3 Opt-Out Rights
    You can opt-out of having your data used for AI training purposes by adjusting your preferences in your account settings or by contacting us.
    
    ### 12. Contact Us
    
    If you have any questions about this Privacy Policy, please contact us at:
    
    **Email:** dariusbell@bellcontractingservices.com
    
    
    ---
    
    By using our platform, you acknowledge that you have read and understood this Privacy Policy.
    """)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back to Home", use_container_width=True):
            st.switch_page("app.py")
    with col2:
        if st.button("View Terms of Service", use_container_width=True):
            st.switch_page("pages/terms_of_service.py")

if __name__ == "__main__":
    app()