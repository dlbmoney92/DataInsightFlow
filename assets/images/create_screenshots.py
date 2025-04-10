import matplotlib.pyplot as plt
import numpy as np
import io
import base64
from PIL import Image
import matplotlib.gridspec as gridspec
import pandas as pd
import random

# Set a consistent style
plt.style.use('ggplot')

# 1. DATA PREVIEW SCREENSHOT
fig = plt.figure(figsize=(8, 4))
fig.patch.set_facecolor('#f0f2f6')

# Create a sample dataframe preview
data = {
    'Date': ['2025-01-01', '2025-01-02', '2025-01-03', '2025-01-04', '2025-01-05'],
    'Revenue': [1420, 1650, 1340, 1890, 1760],
    'Expenses': [980, 1020, 950, 1100, 1050],
    'Customers': [47, 53, 42, 65, 58]
}
df = pd.DataFrame(data)

# Plot the table
ax = plt.subplot(111)
ax.axis('tight')
ax.axis('off')
table = ax.table(cellText=df.values, colLabels=df.columns, loc='center', 
                 cellLoc='center', colColours=['#e8f4fc']*len(df.columns))
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 1.5)

# Add statistics summary text box
props = dict(boxstyle='round', facecolor='white', alpha=0.8)
stats_text = "Data Summary:\n" + \
             "Records: 5\n" + \
             "Columns: 4\n" + \
             "Missing Values: 0\n" + \
             "Numeric Columns: 3\n" + \
             "Text Columns: 1"
ax.text(0.75, 0.3, stats_text, transform=ax.transAxes, fontsize=8,
        verticalalignment='top', bbox=props)

ax.set_title("Data Preview", fontsize=14, fontweight='bold', color='#2c3e50', pad=20)
plt.tight_layout()
plt.savefig("data_preview_screenshot.png", dpi=100, bbox_inches='tight')
plt.close()

# 2. EDA DASHBOARD SCREENSHOT
fig = plt.figure(figsize=(8, 4))
gs = gridspec.GridSpec(2, 2, height_ratios=[1, 1], figure=fig)
fig.patch.set_facecolor('#f0f2f6')

# Create a correlation matrix
ax1 = fig.add_subplot(gs[0, 0])
corr_data = np.array([[1.0, 0.7, 0.3], [0.7, 1.0, 0.5], [0.3, 0.5, 1.0]])
im = ax1.imshow(corr_data, cmap='coolwarm')
ax1.set_xticks(np.arange(3))
ax1.set_yticks(np.arange(3))
ax1.set_xticklabels(['Revenue', 'Expenses', 'Customers'], fontsize=8)
ax1.set_yticklabels(['Revenue', 'Expenses', 'Customers'], fontsize=8)
ax1.set_title('Correlation Matrix', fontsize=10)
plt.colorbar(im, ax=ax1, fraction=0.046, pad=0.04)

# Create a histogram
ax2 = fig.add_subplot(gs[0, 1])
x = np.random.normal(size=1000)
ax2.hist(x, bins=20, alpha=0.7, color='#3498db')
ax2.set_title('Revenue Distribution', fontsize=10)
ax2.set_xlabel('Value', fontsize=8)
ax2.set_ylabel('Frequency', fontsize=8)

# Create a scatter plot
ax3 = fig.add_subplot(gs[1, 0])
x = np.random.uniform(low=500, high=1000, size=50)
y = x * 0.6 + np.random.normal(0, 50, 50)
ax3.scatter(x, y, alpha=0.7, c='#2ecc71')
ax3.set_title('Expenses vs Revenue', fontsize=10)
ax3.set_xlabel('Expenses', fontsize=8)
ax3.set_ylabel('Revenue', fontsize=8)

# Create a box plot
ax4 = fig.add_subplot(gs[1, 1])
data = [np.random.normal(loc=i*100, scale=20, size=100) for i in range(1, 4)]
ax4.boxplot(data, labels=['Revenue', 'Expenses', 'Profit'])
ax4.set_title('Value Distributions', fontsize=10)
ax4.set_ylabel('Amount ($)', fontsize=8)

plt.suptitle("EDA Dashboard", fontsize=14, fontweight='bold', color='#2c3e50', y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("eda_dashboard_screenshot.png", dpi=100, bbox_inches='tight')
plt.close()

# 3. DATA TRANSFORMATION SCREENSHOT
fig = plt.figure(figsize=(8, 4))
gs = gridspec.GridSpec(2, 3, height_ratios=[1, 1], figure=fig)
fig.patch.set_facecolor('#f0f2f6')

# Create a before transformation box
ax1 = fig.add_subplot(gs[0, 0])
ax1.axis('off')
props = dict(boxstyle='round', facecolor='white', alpha=0.9)
before_text = "Before Transformation:\n\n" + \
              "Column: Revenue\n" + \
              "Type: Numeric\n" + \
              "Missing: 2%\n" + \
              "Range: $1,200-$2,100"
ax1.text(0.5, 0.5, before_text, transform=ax1.transAxes, fontsize=8,
        verticalalignment='center', horizontalalignment='center', bbox=props)
ax1.set_title("Original Data", fontsize=10)

# Create a transformation visualization
ax2 = fig.add_subplot(gs[0, 1])
ax2.axis('off')
transformation_text = "Transformation Applied:\n\n" + \
                     "Min-Max Scaling\n" + \
                     "Fill missing values (mean)\n" + \
                     "Apply log transformation"
                     
props = dict(boxstyle='round', facecolor='#e8f4fc', alpha=0.9)
ax2.text(0.5, 0.5, transformation_text, transform=ax2.transAxes, fontsize=8,
        verticalalignment='center', horizontalalignment='center', bbox=props)
ax2.set_title("Process", fontsize=10)

# Create an after transformation box
ax3 = fig.add_subplot(gs[0, 2])
ax3.axis('off')
props = dict(boxstyle='round', facecolor='white', alpha=0.9)
after_text = "After Transformation:\n\n" + \
              "Column: Revenue_Scaled\n" + \
              "Type: Numeric\n" + \
              "Missing: 0%\n" + \
              "Range: 0.0-1.0"
ax3.text(0.5, 0.5, after_text, transform=ax3.transAxes, fontsize=8,
        verticalalignment='center', horizontalalignment='center', bbox=props)
ax3.set_title("Transformed Data", fontsize=10)

# Create a before/after histogram comparison
ax4 = fig.add_subplot(gs[1, 0:2])
x1 = np.random.exponential(scale=1.0, size=1000)
x2 = np.log(x1 + 1)
ax4.hist(x1, bins=20, alpha=0.5, label='Before', color='#e74c3c')
ax4.hist(x2, bins=20, alpha=0.5, label='After', color='#2ecc71')
ax4.set_title('Distribution Before & After', fontsize=10)
ax4.set_xlabel('Value', fontsize=8)
ax4.set_ylabel('Frequency', fontsize=8)
ax4.legend(fontsize=8)

# Create AI suggestions box
ax5 = fig.add_subplot(gs[1, 2])
ax5.axis('off')
suggestions_text = "AI Suggestions:\n\n" + \
                 "• Apply normalization\n" + \
                 "• Remove outliers\n" + \
                 "• Create new feature\n" + \
                 "• Group categories"
props = dict(boxstyle='round', facecolor='#f9e79f', alpha=0.9)
ax5.text(0.5, 0.5, suggestions_text, transform=ax5.transAxes, fontsize=8,
        verticalalignment='center', horizontalalignment='center', bbox=props)
ax5.set_title("AI Recommendations", fontsize=10)

plt.suptitle("Data Transformation", fontsize=14, fontweight='bold', color='#2c3e50', y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("data_transformation_screenshot.png", dpi=100, bbox_inches='tight')
plt.close()

# 4. INSIGHTS DASHBOARD SCREENSHOT
fig = plt.figure(figsize=(8, 4))
gs = gridspec.GridSpec(2, 2, figure=fig)
fig.patch.set_facecolor('#f0f2f6')

# Create an insights box
ax1 = fig.add_subplot(gs[0, 0])
ax1.axis('off')
insights_text = "Key Insights:\n\n" + \
              "• Revenue peaks on weekends\n" + \
              "• 30% increase in new customers\n" + \
              "• Strong correlation between\n" + \
              "  marketing spend and sales\n" + \
              "• Product A outperforms others"
props = dict(boxstyle='round', facecolor='white', alpha=0.9)
ax1.text(0.5, 0.5, insights_text, transform=ax1.transAxes, fontsize=8,
        verticalalignment='center', horizontalalignment='center', bbox=props)
ax1.set_title("AI-Generated Insights", fontsize=10)

# Create a time series chart
ax2 = fig.add_subplot(gs[0, 1])
dates = pd.date_range(start='2025-01-01', periods=30)
values = [100 + i*10 + random.randint(-30, 30) for i in range(30)]
ax2.plot(dates, values, marker='o', markersize=3, linewidth=2, color='#3498db')
ax2.set_title('Monthly Revenue Trend', fontsize=10)
ax2.set_xlabel('Date', fontsize=8)
ax2.set_ylabel('Revenue', fontsize=8)
plt.setp(ax2.get_xticklabels(), rotation=45, ha='right', fontsize=6)

# Create a bar chart
ax3 = fig.add_subplot(gs[1, 0])
products = ['Product A', 'Product B', 'Product C', 'Product D']
sales = [1200, 900, 750, 950]
ax3.bar(products, sales, color='#9b59b6')
ax3.set_title('Sales by Product', fontsize=10)
ax3.set_xlabel('Product', fontsize=8)
ax3.set_ylabel('Sales', fontsize=8)
plt.setp(ax3.get_xticklabels(), rotation=45, ha='right', fontsize=6)

# Create an anomaly detection plot
ax4 = fig.add_subplot(gs[1, 1])
x = np.arange(50)
y = 100 + 10 * np.sin(x/5) + np.random.normal(0, 5, 50)
# Add an anomaly
y[35] = 180
ax4.plot(x, y, color='#2ecc71')
ax4.scatter(35, y[35], color='red', s=50, zorder=5)
ax4.set_title('Anomaly Detection', fontsize=10)
ax4.set_xlabel('Day', fontsize=8)
ax4.set_ylabel('Value', fontsize=8)
# Add an arrow pointing to the anomaly
ax4.annotate('Anomaly', xy=(35, y[35]), xytext=(38, 160),
            arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5),
            fontsize=8)

plt.suptitle("Insights Dashboard", fontsize=14, fontweight='bold', color='#2c3e50', y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("insights_dashboard_screenshot.png", dpi=100, bbox_inches='tight')
plt.close()

# 5. EXPORT REPORTS SCREENSHOT
fig = plt.figure(figsize=(8, 4))
gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1], figure=fig)
fig.patch.set_facecolor('#f0f2f6')

# Create a report preview
ax1 = fig.add_subplot(gs[0, 0])
ax1.axis('off')
# Draw a report document
ax1.add_patch(plt.Rectangle((0.1, 0.1), 0.8, 0.8, fill=True, color='white', ec='#ddd'))
# Add title text
ax1.text(0.5, 0.85, "Sales Performance Report", ha='center', fontsize=10, fontweight='bold')
# Add horizontal line
ax1.axhline(y=0.82, xmin=0.2, xmax=0.8, color='#ddd', linewidth=1)
# Add chart placeholder
ax1.add_patch(plt.Rectangle((0.2, 0.5), 0.6, 0.25, fill=True, color='#f2f2f2', ec='#ddd'))
ax1.text(0.5, 0.62, "[ Chart Placeholder ]", ha='center', fontsize=8, color='#777')
# Add text placeholder
ax1.text(0.2, 0.45, "Executive Summary:", fontsize=8, fontweight='bold')
ax1.text(0.2, 0.4, "Lorem ipsum dolor sit amet, consectetur adipiscing elit...", fontsize=6)
ax1.text(0.2, 0.35, "Sed do eiusmod tempor incididunt ut labore et dolore...", fontsize=6)
# Add table placeholder
y_pos = 0.25
for i in range(3):
    ax1.add_patch(plt.Rectangle((0.2, y_pos - i*0.05), 0.6, 0.04, fill=True, 
                               color='#f2f2f2' if i % 2 == 0 else '#e6e6e6', ec='#ddd'))
ax1.text(0.5, 0.2, "[ Table Data ]", ha='center', fontsize=8, color='#777')
ax1.set_title("Report Preview", fontsize=10)

# Create export options panel
ax2 = fig.add_subplot(gs[0, 1])
ax2.axis('off')

formats = ['PDF Report', 'Excel Workbook', 'CSV Data', 'HTML Page', 'Image Files']
descriptions = ['Complete report with visuals', 'Data & charts in Excel', 'Raw data export',
                'Interactive web report', 'PNG/JPG visualizations']
y_positions = [0.8, 0.65, 0.5, 0.35, 0.2]

for format, desc, y in zip(formats, descriptions, y_positions):
    # Create format option
    props = dict(boxstyle='round', facecolor='white', alpha=0.9)
    ax2.text(0.2, y, format, fontsize=9, fontweight='bold')
    ax2.text(0.2, y-0.05, desc, fontsize=7, color='#666')
    # Add checkbox
    checkbox = plt.Rectangle((0.1, y-0.01), 0.03, 0.03, fill=True, 
                            color='#3498db' if y > 0.4 else 'white', ec='#777')
    ax2.add_patch(checkbox)
    # Add checkmark if selected
    if y > 0.4:
        ax2.text(0.115, y-0.01, "✓", fontsize=8, color='white', ha='center', va='center')

# Add export button
button = plt.Rectangle((0.25, 0.1), 0.5, 0.05, fill=True, color='#2ecc71', ec='#27ae60', alpha=0.9)
ax2.add_patch(button)
ax2.text(0.5, 0.125, "Generate & Download Report", ha='center', va='center', 
         color='white', fontsize=8, fontweight='bold')

ax2.set_title("Export Options", fontsize=10)

plt.suptitle("Export Reports", fontsize=14, fontweight='bold', color='#2c3e50', y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("export_reports_screenshot.png", dpi=100, bbox_inches='tight')
plt.close()

# 6. ACCOUNT MANAGEMENT SCREENSHOT
fig = plt.figure(figsize=(8, 4))
gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1], figure=fig)
fig.patch.set_facecolor('#f0f2f6')

# Create profile information panel
ax1 = fig.add_subplot(gs[0, 0])
ax1.axis('off')
# Add user avatar placeholder
circle = plt.Circle((0.2, 0.7), 0.1, fill=True, color='#bdc3c7')
ax1.add_patch(circle)
# Add user info
ax1.text(0.4, 0.75, "John Smith", fontsize=12, fontweight='bold')
ax1.text(0.4, 0.68, "john.smith@example.com", fontsize=9)
ax1.text(0.4, 0.62, "Pro Subscription", fontsize=9, color='#3498db', fontweight='bold')

# Add profile fields
fields = ['Full Name', 'Email Address', 'Company', 'Password']
y_pos = 0.45
for field in fields:
    ax1.add_patch(plt.Rectangle((0.15, y_pos), 0.7, 0.06, fill=True, color='white', ec='#ddd'))
    ax1.text(0.2, y_pos+0.03, field, fontsize=8, color='#777')
    if field != 'Password':
        value = "John Smith" if field == 'Full Name' else "john.smith@example.com" if field == 'Email Address' else "ACME Corp"
        ax1.text(0.5, y_pos+0.03, value, fontsize=8)
    else:
        ax1.text(0.5, y_pos+0.03, "••••••••", fontsize=8)
    y_pos -= 0.09

# Add save button
button = plt.Rectangle((0.4, 0.08), 0.2, 0.05, fill=True, color='#3498db')
ax1.add_patch(button)
ax1.text(0.5, 0.105, "Save Changes", ha='center', va='center', color='white', fontsize=8)

ax1.set_title("Profile Settings", fontsize=10)

# Create subscription panel
ax2 = fig.add_subplot(gs[0, 1])
ax2.axis('off')

# Add subscription info
subscription_box = plt.Rectangle((0.1, 0.65), 0.8, 0.25, fill=True, color='white', ec='#3498db', linewidth=2)
ax2.add_patch(subscription_box)
ax2.text(0.5, 0.85, "Pro Plan", ha='center', fontsize=12, fontweight='bold', color='#3498db')
ax2.text(0.5, 0.78, "$19.99/month", ha='center', fontsize=10)
ax2.text(0.5, 0.72, "Renewal: May 10, 2025", ha='center', fontsize=8, color='#777')
ax2.text(0.5, 0.67, "Unlimited datasets & reports", ha='center', fontsize=8, color='#777')

# Add plan options
plans = ['Basic', 'Pro', 'Enterprise']
prices = ['$9.99/mo', '$19.99/mo', '$49.99/mo']
colors = ['#bdc3c7', '#3498db', '#9b59b6']
y_pos = 0.5
for plan, price, color in zip(plans, prices, colors):
    # Create plan option
    ax2.add_patch(plt.Rectangle((0.1, y_pos), 0.8, 0.08, fill=True, color='white', ec=color))
    ax2.text(0.2, y_pos+0.04, plan, fontsize=9, fontweight='bold')
    ax2.text(0.2, y_pos+0.01, price, fontsize=8)
    # Add radio button
    radio = plt.Circle((0.8, y_pos+0.04), 0.01, fill=True, color=color if plan == 'Pro' else 'white', ec=color)
    ax2.add_patch(radio)
    y_pos -= 0.12

# Add change plan button
button = plt.Rectangle((0.35, 0.08), 0.3, 0.05, fill=True, color='#3498db')
ax2.add_patch(button)
ax2.text(0.5, 0.105, "Change Subscription", ha='center', va='center', color='white', fontsize=8)

ax2.set_title("Subscription Management", fontsize=10)

plt.suptitle("Account Management", fontsize=14, fontweight='bold', color='#2c3e50', y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("assets/images/account_management_screenshot.png", dpi=100, bbox_inches='tight')
plt.close()

print("All screenshots created successfully")