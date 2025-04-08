import streamlit as st
from utils.custom_navigation import render_navigation, initialize_navigation

# Set the page configuration
st.set_page_config(
    page_title="Terms of Service | Analytics Assist",
    page_icon="📜",
    layout="wide"
)

# Initialize navigation
initialize_navigation()

# Render custom navigation bar
render_navigation()

# Additional sidebar elements
with st.sidebar:
    # Developer login form and logout are handled by the render_navigation function
    pass

def app():
    st.title("Terms of Service")
    
    st.write("""
    ## Analytics Assist Terms of Service
    
    **Last Updated: April 7, 2025**
    
    Welcome to Analytics Assist. Please read these Terms of Service ("Terms") carefully as they contain important information about your legal rights, remedies, and obligations. By accessing or using the Analytics Assist platform, you agree to comply with and be bound by these Terms.
    
    ### 1. Acceptance of Terms
    
    By accessing or using our platform, you agree to be bound by these Terms and our Privacy Policy. If you do not agree to these Terms, you may not access or use our platform.
    
    ### 2. Changes to Terms
    
    We may modify these Terms at any time. Your continued use of our platform after any such changes constitutes your acceptance of the new Terms.
    
    ### 3. Service Description
    
    Analytics Assist is a data analytics platform that allows users to upload, analyze, transform, and visualize data. We offer various subscription tiers with different features and capabilities.
    
    ### 4. Account Registration
    
    To access certain features of our platform, you must register for an account. You agree to provide accurate, current, and complete information during the registration process and to update such information to keep it accurate, current, and complete.
    
    ### 5. Data Privacy and Security
    
    #### 5.1 Data Ownership
    You retain all rights to your data. We do not claim ownership of any data you upload to our platform.
    
    #### 5.2 Data Usage
    By uploading data to our platform, you grant us a license to use, process, and analyze your data solely for the purpose of providing our services to you.
    
    #### 5.3 Data Security
    We implement reasonable security measures to protect your data. However, no method of transmission over the Internet or method of electronic storage is 100% secure.
    
    ### 6. Subscription and Payments
    
    #### 6.1 Free Trial
    We may offer a free trial period for certain subscription tiers. After the trial period, you will be charged according to the pricing plan you selected unless you cancel your subscription before the end of the trial period.
    
    #### 6.2 Billing
    You agree to pay all fees associated with your account. Fees are non-refundable except as required by law or as explicitly stated in these Terms.
    
    #### 6.3 Subscription Changes
    You may upgrade or downgrade your subscription at any time. Changes to your subscription will take effect immediately or at the end of your current billing cycle, depending on the type of change.
    
    ### 7. Acceptable Use
    
    #### 7.1 Prohibited Activities
    You agree not to:
    - Use our platform for any illegal purpose
    - Upload, transmit, or distribute any content that violates any law or infringes any third-party rights
    - Attempt to gain unauthorized access to our platform or systems
    - Use our platform to transmit viruses or other harmful code
    - Interfere with or disrupt the integrity or performance of our platform
    
    #### 7.2 Content Guidelines
    You are solely responsible for all data and content that you upload to our platform. You agree not to upload content that:
    - Is illegal, harmful, threatening, abusive, harassing, defamatory, or invasive of another's privacy
    - Infringes any patent, trademark, trade secret, copyright, or other intellectual property rights
    - Contains sensitive personal information of others without their consent
    
    ### 8. Intellectual Property
    
    #### 8.1 Our Intellectual Property
    Our platform and its original content, features, and functionality are owned by Analytics Assist and are protected by international copyright, trademark, patent, trade secret, and other intellectual property laws.
    
    #### 8.2 License to Use Platform
    We grant you a limited, non-exclusive, non-transferable, revocable license to use our platform for your personal or business purposes in accordance with these Terms.
    
    ### 9. Termination
    
    We may terminate or suspend your account and access to our platform immediately, without prior notice or liability, for any reason, including, without limitation, if you breach these Terms.
    
    ### 10. Limitation of Liability
    
    To the maximum extent permitted by law, we shall not be liable for any indirect, incidental, special, consequential, or punitive damages resulting from your use of or inability to use our platform.
    
    ### 11. Governing Law
    
    These Terms shall be governed by and construed in accordance with the laws of the jurisdiction in which our company is registered, without regard to its conflict of law provisions.
    
    ### 12. Contact Us
    
    If you have any questions about these Terms, please contact us at dariusbell@bellcontractingservices.com.
    
    ### 13. AI and Machine Learning Features
    
    #### 13.1 AI Learning
    Our platform includes AI-powered features that learn from user interactions to improve the service. You acknowledge that by using these features, you are contributing to the learning and improvement of our AI systems.
    
    #### 13.2 AI-Generated Content
    Content generated by our AI systems is provided "as is" without any warranties. You are responsible for reviewing and validating all AI-generated content before using it for your purposes.
    
    ### 14. Data Retention and Deletion
    
    #### 14.1 Data Retention
    We will retain your data for as long as your account is active or as needed to provide you services.
    
    #### 14.2 Data Deletion
    Upon termination of your account, we will delete or anonymize your data within a reasonable time period, except as required by law.
    
    ### 15. Third-Party Services
    
    Our platform may integrate with third-party services. Your use of these services may be subject to additional terms and conditions provided by the third-party service providers.
    
    ---
    
    By using Analytics Assist, you acknowledge that you have read, understood, and agree to be bound by these Terms of Service.
    """)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back to Home", use_container_width=True):
            st.switch_page("app.py")
    with col2:
        if st.button("View Privacy Policy", use_container_width=True):
            st.session_state.create_privacy_policy = True
            st.rerun()
    
    # Check if we need to create a privacy policy page
    if "create_privacy_policy" in st.session_state and st.session_state.create_privacy_policy:
        st.session_state.create_privacy_policy = False
        st.switch_page("pages/privacy_policy.py")

if __name__ == "__main__":
    app()