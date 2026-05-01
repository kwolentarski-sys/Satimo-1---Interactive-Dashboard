import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json

# Configure the dashboard layout
st.set_page_config(page_title="San Diego Chambers Interactive Dashboard", layout="wide")

# Inject custom HTML/CSS for the Sidebar Background Color
st.markdown(
    """
    <style>
        /* Change the Sidebar Background Color */
        [data-testid="stSidebar"] {
            background-color: #cbcbcb;
        }
    </style>
    """, 
    unsafe_allow_html=True
)

# Function to load JSON data
def load_data(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

# Dictionary to map antenna names to their frequency ranges for titles
ANTENNA_RANGES = {
    # Dipoles
    "Dipole SD450": "400 - 500 MHz",
    "Dipole SD665": "625 - 700 MHz",
    "Dipole SD740": "690 - 800 MHz",
    "Dipole SD836": "810 - 855 MHz",
    "Dipole SD850": "800 - 950 MHz",
    "Dipole SD880": "860 - 920 MHz",
    "Dipole SD900": "850 - 950 MHz",
    "Dipole SD945": "925 - 980 MHz",
    "Dipole SD1230": "1165 - 1295 MHz",
    "Dipole SD1500": "1400 - 1600 MHz",
    "Dipole SD1575": "1500 - 1630 MHz",
    "Dipole SD1730": "1640 - 1705 MHz",
    "Dipole SD1800": "1700 - 1915 MHz",
    "Dipole SD1900": "1800 - 2000 MHz",
    "Dipole SD2000": "1900 - 2100 MHz",
    "Dipole SD2140": "2005 - 2330 MHz",
    "Dipole SD2450": "2300 - 2650 MHz",
    "Dipole SD2600": "2500 - 2950 MHz",
    "Dipole SD3500": "3400 - 3600 MHz",
    "Dipole SD5150": "4900 - 5400 MHz",
    "Dipole SD5500": "5000 - 6000 MHz",
    "Dipole SD5650": "5405 - 5900 MHz",
    "Dipole WD6000": "6000 - 8000 MHz",
    
    # Horns
    "Horn SH400": "400 - 6000 MHz",
    "Horn SH2000": "2000 - 8500 MHz",
    "Horn SH8000": "8000 - 40000 MHz",
    
    # Wideband
    "Proxicast Dipole #4": "600 - 6000 MHz"
}

# Sidebar for Dashboard Controls
st.sidebar.markdown(
    "<h2 style='font-size: 2rem; color: #0000ff;'>Dashboard Controls</h2>", 
    unsafe_allow_html=True
)

# Use placeholders to strictly control the vertical layout order
ph_chamber = st.sidebar.empty()
ph_passive_type = st.sidebar.empty()
ph_antenna = st.sidebar.empty()
ph_active_type = st.sidebar.empty()
ph_active_range = st.sidebar.empty()

# 0. Chamber Selection Toggle
chamber_choice = ph_chamber.selectbox(
    "**Select Chamber:**",
    ("Satimo 1", "Satimo 2", "Satimo 3", "Rohde & Schwarz"),
    index=1 # Defaults to Satimo 2
)

# Add the main title, Google logo, and dynamic subtitle tightly packed together
st.markdown(
    f"""
    <div style='display: flex; justify-content: space-between; align-items: center; padding-bottom: 0px;'>
        <h1 style='font-size: 32px; margin: 0; padding: 0;'>San Diego Antenna Chambers</h1>
        <img src='https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg' style='height: 35px;' alt='Google'>
    </div>
    <h2 style='font-size: 26px; color: #000000; margin-top: 0px; padding-top: 0px; margin-bottom: 20px;'>{chamber_choice} - Interactive Dashboard</h2>
    """, 
    unsafe_allow_html=True
)

# 1. Passive Dataset Selection Toggle 
dataset_choice = ph_passive_type.selectbox(
    "**Select Passive Validation Type:**",
    ("🔵 None", "Yearly Dipoles", "Quarterly Dipoles", "Monthly Horns", "Wideband Dipole Chamber Comparison")
)

# Set dynamic options for Active Validation based on the selected Chamber
if chamber_choice == "Satimo 3":
    active_validation_options = (
        "🔵 None", 
        "Bluetooth BDR", 
        "Bluetooth EDR2", 
        "WiFi 2.4 GHz", 
        "WiFi 5 GHz", 
        "GPS CW L1 L5"
    )
else:
    active_validation_options = (
        "🔵 None", 
        "LTE TRP", 
        "LTE TIS", 
        "Pixel Phone S4 with Dipoles", 
        "Phantom Wrist Dielectric Tracking"
    )

# 2. Active Dataset Selection Toggle 
active_dataset_choice = ph_active_type.selectbox(
    "**Select Active Validation Type:**",
    active_validation_options
)

# --- NEW: Test Descriptions Menu ---
st.sidebar.markdown("---") # Visual divider
test_desc_choice = st.sidebar.selectbox(
    "**Test Descriptions:**",
    ("🔵 None", "Pixel Phone S4 with Dipoles")
)

# Render the specific description based on user selection as a dedicated webpage
if test_desc_choice == "Pixel Phone S4 with Dipoles":
    try:
        with open("Pixel_Phone_S4_with_Dipoles.md", "r", encoding="utf-8") as f:
            md_content = f.read()
        # Render the markdown file contents in the main viewing area
        st.markdown(md_content, unsafe_allow_html=True)
    except FileNotFoundError:
        st.info("🏗️ **Page under construction.**\n\nWhen ready, simply upload **`Pixel_Phone_S4_with_Dipoles.md`** to GitHub and this webpage will populate automatically.")
    
    # Stop the rest of the script so the dashboard graphs don't render below the document
    st.stop()


# Map Chamber selection to file prefix
prefix_map = {
    "Satimo 1": "Satimo1_",
    "Satimo 2": "Satimo2_",
    "Satimo 3": "Satimo3_",
    "Rohde & Schwarz": "RS_"
}
prefix = prefix_map.get(chamber_choice, "Satimo2_")

# Map selection to the exact JSON files based on active/passive/chamber choice
target_file = None
if active_dataset_choice == "LTE TRP":
    target_file = f'{prefix}LTE_Reference_TRP_Quarterly.json'
elif active_dataset_choice == "LTE TIS":
    target_file = f'{prefix}LTE_Reference_TIS_Quarterly.json'
elif active_dataset_choice == "Pixel Phone S4 with Dipoles":
    if chamber_choice == "Satimo 1":
        target_file = 'Satimo1_Pixel_Phone_S4_Dipoles_Quarterly.json'I seem to be encountering an error. Can I try something else for you?
