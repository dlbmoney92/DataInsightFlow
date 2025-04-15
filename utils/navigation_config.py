import streamlit as st

# Icons for navigation using material design icons or similar
HOME_ICON = '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor"><path d="M220-180h150v-250h220v250h150v-390L480-765 220-570v390Zm-60 60v-480l320-240 320 240v480H530v-250H430v250H160Zm320-353Z"/></svg>'
UPLOAD_ICON = '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor"><path d="M440-320v-326L336-542l-56-56 200-200 200 200-56 56-104-104v326h-80ZM240-160q-33 0-56.5-23.5T160-240v-120h80v120h480v-120h80v120q0 33-23.5 56.5T720-160H240Z"/></svg>'
PREVIEW_ICON = '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor"><path d="M480-320q75 0 127.5-52.5T660-500q0-75-52.5-127.5T480-680q-75 0-127.5 52.5T300-500q0 75 52.5 127.5T480-320Zm0-72q-45 0-76.5-31.5T372-500q0-45 31.5-76.5T480-608q45 0 76.5 31.5T588-500q0 45-31.5 76.5T480-392Zm0 192q-146 0-266-81.5T40-500q54-137 174-218.5T480-800q146 0 266 81.5T920-500q-54 137-174 218.5T480-200Zm0-300Zm0 220q113 0 207.5-59.5T832-500q-50-101-144.5-160.5T480-720q-113 0-207.5 59.5T128-500q50 101 144.5 160.5T480-280Z"/></svg>'
ANALYZE_ICON = '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor"><path d="M120-120v-720h720v720H120Zm60-520h600v-140H180v140Zm220 260h380v-200H400v200Zm0 200h380v-140H400v140Zm-220 0h160v-400H180v400Zm60-60h40v-280h-40v280Zm160 0h260v-20H400v20Zm0-260h260v-20H400v20Z"/></svg>'
TRANSFORM_ICON = '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor"><path d="M320-240 80-480l240-240 57 57-184 184 183 183-56 56Zm320 0-57-57 184-184-183-183 56-56 240 240-240 240Z"/></svg>'
INSIGHTS_ICON = '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor"><path d="m678-134-46-46 60-60h-57q-64 0-121-24.5T401-343L287-229q-9 9-21 9t-21-9q-9-9-9-21t9-21l114-114q-25-39-39-83.5T306-548v-83h-26q-9 0-15-5t-8-13l-14-62q-3-14 6-25t23-11h180q14 0 23 11t6 25l-14 62q-2 8-8 13t-15 5h-26v83q0 35 10 68t29 60q47-25 76-72t29-102v-11q0-9 6-15t15-6h80q9 0 15 6t6 15v11q0 94-47 174t-127 127l60 60-46 46ZM480-822q-29 0-49.5-20.5T410-892q0-29 20.5-49.5T480-962q29 0 49.5 20.5T550-892q0 29-20.5 49.5T480-822Z"/></svg>'
EXPORT_ICON = '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor"><path d="M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h280v80H200v560h560v-280h80v280q0 33-23.5 56.5T760-120H200Zm280-360ZM640-760v120h120l-400 400-56-56 400-400H580v-120h60Z"/></svg>'
VERSION_ICON = '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor"><path d="M480-120q-151 0-255.5-104.5T120-480q0-151 104.5-255.5T480-840q149 0 253 102.5T839-486h-82q-13-106-93.5-180T480-740q-109 0-184.5 75.5T220-480q0 109 75.5 184.5T480-220q97 0 170-57.5T739-420H480v-80h280v280h-81v-156q-44 76-121 126t-168 50h-22Z"/></svg>'
AI_ICON = '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor"><path d="M160-200v-80h80v-280q0-83 50-147.5T420-792v-28q0-25 17.5-42.5T480-880q25 0 42.5 17.5T540-820v28q80 20 130 84.5T720-560v280h80v80H160Zm320-300Zm0 420q-33 0-56.5-23.5T400-160h160q0 33-23.5 56.5T480-80ZM320-280h320v-280q0-66-47-113t-113-47q-66 0-113 47t-47 113v280Z"/></svg>'
DATASET_ICON = '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor"><path d="M480-120q-33 0-56.5-23.5T400-200v-560q0-33 23.5-56.5T480-840h320q33 0 56.5 23.5T880-760v560q0 33-23.5 56.5T800-120H480Zm0-80h320v-560H480v560ZM160-280q-33 0-56.5-23.5T80-360v-400q0-33 23.5-56.5T160-840h120q33 0 56.5 23.5T360-760v400q0 33-23.5 56.5T280-280H160Zm0-80h120v-400H160v400Zm0 0v-400 400Zm320 0h320-320Z"/></svg>'
LOGIN_ICON = '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor"><path d="M480-120q-138 0-240.5-91.5T122-440h82q14 104 92.5 172T480-200q117 0 198.5-81.5T760-480q0-117-81.5-198.5T480-760q-69 0-129 32t-101 88h110v80H120v-240h80v94q51-64 124.5-99T480-840q75 0 140.5 28.5t114 77q48.5 48.5 77 114T840-480q0 75-28.5 140.5t-77 114q-48.5 48.5-114 77T480-120Zm112-192L480-424v-216h80v168l88 88-56 56Z"/></svg>'
SIGNUP_ICON = '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor"><path d="M720-400v-120H600v-80h120v-120h80v120h120v80H800v120h-80Zm-360-80q-66 0-113-47t-47-113q0-66 47-113t113-47q66 0 113 47t47 113q0 66-47 113t-113 47ZM40-160v-112q0-33 17-62t47-44q51-26 115-44t141-18h14q6 0 12 1-8 18-13.5 37.5T364-360h-4q-71 0-127.5 18T150-306q-9 5-14.5 14t-5.5 20v32h250q8 21 19 41.5t25 38.5H40Zm320-320q33 0 56.5-23.5T440-560q0-33-23.5-56.5T360-640q-33 0-56.5 23.5T280-560q0 33 23.5 56.5T360-480Z"/></svg>'
USER_ICON = '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor"><path d="M234-276q51-39 114-61.5T480-360q69 0 132 22.5T726-276q35-41 54.5-93T800-480q0-133-93.5-226.5T480-800q-133 0-226.5 93.5T160-480q0 59 19.5 111t54.5 93Zm246-164q-59 0-99.5-40.5T340-580q0-59 40.5-99.5T480-720q59 0 99.5 40.5T620-580q0 59-40.5 99.5T480-440Zm0 360q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm0-80q53 0 100-15.5t86-44.5q-39-29-86-44.5T480-280q-53 0-100 15.5T294-220q39 29 86 44.5T480-160Zm0-360q26 0 43-17t17-43q0-26-17-43t-43-17q-26 0-43 17t-17 43q0 26 17 43t43 17Zm0-60Zm0 360Z"/></svg>'
ADMIN_ICON = '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor"><path d="M680-280q25 0 42.5-17.5T740-340q0-25-17.5-42.5T680-400q-25 0-42.5 17.5T620-340q0 25 17.5 42.5T680-280Zm0 120q31 0 57-14.5t42-38.5q-22-13-47-20t-52-7q-27 0-52 7t-47 20q16 24 42 38.5t57 14.5ZM480-80q-139-35-229.5-159.5T160-516v-284l320-120 320 120v189q-14-7-28.5-12T740-630v-148l-260-96-260 96v264q0 118 75 212.5T480-180q7 16 17 30.5T517-120q-8 3-17 5t-20 2v33Zm200-200q-83 0-141.5 58.5T480-80q0 83 58.5 141.5T680-280q83 0 141.5-58.5T880-480q0-83-58.5-141.5T680-680q-83 0-141.5 58.5T480-480q0 83 58.5 141.5T680-280Zm0-80Zm-67 210Z"/></svg>'
PAYMENT_ICON = '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor"><path d="M280-240q-33 0-56.5-23.5T200-320v-320q0-33 23.5-56.5T280-720h400q33 0 56.5 23.5T760-640v320q0 33-23.5 56.5T680-240H280Zm0-80h400v-320H280v320Zm200 0q25 0 42.5-17.5T540-380q0-25-17.5-42.5T480-440q-25 0-42.5 17.5T420-380q0 25 17.5 42.5T480-320ZM280-560h400v-80H280v80Zm0 0v-80 80Zm0 240v-320 320Z"/></svg>'
CONTACT_ICON = '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor"><path d="M160-160q-33 0-56.5-23.5T80-240v-480q0-33 23.5-56.5T160-800h640q33 0 56.5 23.5T880-720v480q0 33-23.5 56.5T800-160H160Zm320-280L160-640v400h640v-400L480-440Zm0-80 320-200H160l320 200Zm-320 80v0 400-400Z"/></svg>'

# Developer mode functionality has been removed
def is_developer_mode():
    """Developer mode has been disabled."""
    return False

def set_developer_mode(enabled=True):
    """Developer mode has been disabled."""
    pass

def get_navigation_items():
    """Get the appropriate navigation items based on user role."""
    # Check if user is logged in
    is_logged_in = st.session_state.get("logged_in", False)
    
    # Basic navigation items (available to all)
    nav_items = [
        {
            "name": "Home",
            "url": "/",
            "icon": HOME_ICON,
        }
    ]
    
    # Items for logged in users
    if is_logged_in:
        # Get user's subscription tier
        subscription_tier = st.session_state.get("subscription_tier", "free")
        
        # Regular user navigation items
        user_items = [
            {
                "name": "Upload Data",
                "url": "/pages/01_Upload_Data.py",
                "icon": UPLOAD_ICON,
            },
            {
                "name": "Data Preview",
                "url": "/pages/02_Data_Preview.py",
                "icon": PREVIEW_ICON,
            },
            {
                "name": "EDA Dashboard",
                "url": "/pages/03_EDA_Dashboard.py",
                "icon": ANALYZE_ICON,
            },
            {
                "name": "Data Transformation",
                "url": "/pages/04_Data_Transformation.py",
                "icon": TRANSFORM_ICON,
            },
            {
                "name": "Insights Dashboard",
                "url": "/pages/05_Insights_Dashboard.py",
                "icon": INSIGHTS_ICON,
            },
            {
                "name": "Export Reports",
                "url": "/pages/06_Export_Reports.py",
                "icon": EXPORT_ICON,
            },
            {
                "name": "Version History",
                "url": "/pages/07_Version_History.py",
                "icon": VERSION_ICON,
            },
            {
                "name": "AI Learning",
                "url": "/pages/08_AI_Learning.py",
                "icon": AI_ICON,
            },
            {
                "name": "Dataset Management",
                "url": "/pages/09_Dataset_Management.py",
                "icon": DATASET_ICON,
            },
        ]
        
        nav_items.extend(user_items)
        
        # Add account/subscription management
        nav_items.append({
            "name": "Account",
            "url": "/pages/account.py",
            "icon": USER_ICON,
        })
        
        nav_items.append({
            "name": "Subscription",
            "url": "/pages/subscription.py",
            "icon": PAYMENT_ICON,
        })
        
        # Add user guide page
        nav_items.append({
            "name": "User Guide",
            "url": "/pages/user_guide.py",
            "icon": '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor"><path d="M560-80v-80h120v-80H400v-80h280v-80H400v-80h280v-80H400v-80h280v-80H400v-80h280v-40q0-33 23.5-56.5T760-920h120v840H560Zm-240 0q-33 0-56.5-23.5T240-160v-640q0-33 23.5-56.5T320-880h120v120H320v600h120v120H320Zm0-760v600-600Zm360 680h40v-680h-40v680Z"/></svg>',
        })
        
        # Add contact us page
        nav_items.append({
            "name": "Contact Us",
            "url": "/pages/contact_us.py",
            "icon": CONTACT_ICON,
        })
        
        # Add feedback page
        nav_items.append({
            "name": "Feedback",
            "url": "/pages/user_feedback.py",
            "icon": '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor"><path d="M792-56 612-236q-30 26-69.959 41T460-180q-91.743 0-170.371-39T180-319q-51-61-75.5-138.5T80-600q0-42 8-83.5t24-81.5l244 243v71h72l71 71 54-54-45-45q20-11 36-28t24-38l62 62L792-56ZM419-495l-28-28q-11-11-28-11t-28 11q-11 11-11 28t11 28l28 28q11 11 28 11t28-11q11-11 11-28t-11-28ZM763-56l-31-31 84-202-149-149q-3 5-6 9.5t-7 9.5q-14-8-25-19.5T610-460q12-16 16.5-33.5T631-528l-55-55q-12 5-24 7.5t-22 2.5q-8 0-15-1.5t-15-3.5l-36-36q17-9 30-23t20-32l-85-85 31-31 303 303 124 125-124 301Z"/></svg>',
        })
        
        # Add admin pages for admin users only
        is_admin = st.session_state.get("is_admin", False)
        if is_admin:
            admin_items = [
                {
                    "name": "Admin Feedback",
                    "url": "/pages/admin_feedback.py",
                    "icon": ADMIN_ICON,
                },
                {
                    "name": "Admin Analytics",
                    "url": "/pages/admin_analytics.py",
                    "icon": '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor"><path d="M120-240v-80h720v80H120Zm40-160q-17 0-28.5-11.5T120-440v-240q0-17 11.5-28.5T160-720h160q17 0 28.5 11.5T360-680v240q0 17-11.5 28.5T320-400H160Zm280 0q-17 0-28.5-11.5T400-440v-400q0-17 11.5-28.5T440-880h160q17 0 28.5 11.5T640-840v400q0 17-11.5 28.5T600-400H440Zm280 0q-17 0-28.5-11.5T680-440v-120q0-17 11.5-28.5T720-600h160q17 0 28.5 11.5T920-560v120q0 17-11.5 28.5T880-400H720Z"/></svg>',
                }
            ]
            nav_items.extend(admin_items)
    else:
        # No navigation items for non-logged in users (only home)
        pass
    
    return nav_items

# Developer authentication has been removed
def authenticate_developer(username, password):
    """Developer authentication has been disabled."""
    return False