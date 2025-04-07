#!/bin/bash

# List of pages to update
PAGES=("pages/03_EDA_Dashboard.py" "pages/04_Data_Transformation.py" "pages/05_Insights_Dashboard.py" "pages/06_Export_Reports.py" "pages/07_Version_History.py" "pages/08_AI_Learning.py")

# Authentication code to add
AUTH_CODE="
# Check authentication first
if not require_auth():
    st.stop()  # Stop if not authenticated

# Show user info if authenticated
if \"user\" in st.session_state:
    st.sidebar.success(f\"Logged in as: {st.session_state.user.get('email', 'User')}\")
    st.sidebar.info(f\"Subscription: {st.session_state.subscription_tier.capitalize()}\")
"

# Import statement to add
IMPORT="from utils.auth_redirect import require_auth"

# Process each file
for page in "${PAGES[@]}"; do
  echo "Processing $page"
  
  # Check if file exists
  if [ -f "$page" ]; then
    # Check if file already has the import
    if ! grep -q "from utils.auth_redirect import require_auth" "$page"; then
      # Add import statement after the last import line
      sed -i "/^import/,/^[^import]/ {
        /^[^import]/ i\\$IMPORT
      }" "$page"
    fi
    
    # Add authentication code after page_config if it exists, or after imports if not
    if grep -q "st.set_page_config" "$page"; then
      # Add after page_config
      sed -i "/st.set_page_config/,/^[^[:space:]]/ {
        /^[^[:space:]]/ i\\$AUTH_CODE
      }" "$page"
    else
      # Add after last import
      sed -i "/^import/,/^[^import]/ {
        /^[^import]/ i\\$AUTH_CODE
      }" "$page"
    fi
    
    echo "Updated $page"
  else
    echo "File $page not found!"
  fi
done

echo "Authentication update complete!"