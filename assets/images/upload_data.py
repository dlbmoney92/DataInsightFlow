import matplotlib.pyplot as plt
import numpy as np
import io
import base64
from PIL import Image

# Create a simple image for Upload Data page
fig, ax = plt.subplots(figsize=(8, 4))
fig.patch.set_facecolor('#f0f2f6')

# Draw a file upload zone
ax.add_patch(plt.Rectangle((0.2, 0.3), 0.6, 0.4, fill=True, alpha=0.8, color='white', ec='#ddd'))

# Add an upload icon
upload_icon = plt.Circle((0.5, 0.5), 0.1, color='#3498db', alpha=0.7)
ax.add_patch(upload_icon)

# Add a text label
ax.text(0.5, 0.3, "Drop files here or click to upload", 
        ha='center', va='center', fontsize=12, color='#555')
ax.text(0.5, 0.73, "Supported formats: CSV, Excel, JSON, TXT", 
        ha='center', va='center', fontsize=10, color='#777')

# Draw sample dataset options
y_pos = 0.15
for i, name in enumerate(["Sales Data", "Customer Survey", "Weather History"]):
    ax.add_patch(plt.Rectangle((0.2 + i*0.2, y_pos), 0.18, 0.07, fill=True, alpha=0.9, 
                              color='#e8f4fc', ec='#ddd', linewidth=1))
    ax.text(0.29 + i*0.2, y_pos + 0.035, name, ha='center', va='center', fontsize=7, color='#333')

ax.text(0.1, 0.18, "Or use a sample dataset:", ha='left', va='center', fontsize=9, color='#555')

# Set axis properties
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')
ax.set_title("Upload Data", fontsize=14, fontweight='bold', color='#2c3e50', pad=20)

# Save the image
plt.tight_layout()
plt.savefig("upload_data_screenshot.png", dpi=100, bbox_inches='tight')
plt.close()

print("Upload Data screenshot created successfully")