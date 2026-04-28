import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json

# Configure the dashboard layout
st.set_page_config(page_title="Antenna Efficiency Dashboard", layout="wide")

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

# Add the main title to the top of the page
st.markdown(
    "<h1 style='font-size: 29px;'>Satimo 2 Chamber Performance - Interactive Dashboard</h1>", 
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
    "Dipole SD740": "690 - 790 MHz",
    "Dipole SD850": "800 - 950 MHz",
    "Dipole SD900": "850 - 950 MHz",
    "Dipole SD1500": "1400 - 1600 MHz",
    "Dipole SD1800": "1700 - 1900 MHz",
    "Dipole SD1900": "1800 - 2000 MHz",
    "Dipole SD2000": "1900 - 2100 MHz",
    "Dipole SD2450": "2300 - 2600 MHz",
    "Dipole SD2600": "2500 - 2800 MHz",
    "Dipole SD3500": "3400 - 3600 MHz",
    "Dipole SD5500": "5000 - 6000 MHz",
    
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
ph_passive_type = st.sidebar.empty()
ph_antenna = st.sidebar.empty()
ph_active_type = st.sidebar.empty()
ph_active_range = st.sidebar.empty()

# 1. Passive Dataset Selection Toggle 
dataset_choice = ph_passive_type.selectbox(
    "**Select Passive Validation Type:**",
    ("None", "Yearly Dipoles", "Quarterly Dipoles", "Monthly Horns", "Wideband Dipole Chamber Comparison")
)

# 2. Active Dataset Selection Toggle 
active_dataset_choice = ph_active_type.selectbox(
    "**Select Active Validation Type:**",
    ("None", "LTE TRP", "LTE TIS")
)

# Map selection to the exact JSON files based on active/passive choice
target_file = None
if active_dataset_choice == "LTE TRP":
    target_file = 'Satimo2_LTE_Reference_TRP_Quarterly.json'
elif active_dataset_choice == "LTE TIS":
    target_file = 'Satimo2_LTE_Reference_TIS_Quarterly.json'
elif dataset_choice == "Yearly Dipoles":
    target_file = 'Satimo2_Dipoles_Yearly.json'
elif dataset_choice == "Quarterly Dipoles":
    target_file = 'Satimo2_Dipoles_Quarterly.json'
elif dataset_choice == "Monthly Horns":
    target_file = 'Satimo2_Horns_Monthly.json'
elif dataset_choice == "Wideband Dipole Chamber Comparison":
    target_file = 'Chambers_Wideband_Dipole_Comparison.json'

# Stop execution and prompt the user if both are "None"
if not target_file:
    st.info("👈 Please select an Active or Passive Validation Type from the sidebar to view data.")
    st.stop()

# Load the selected dataset
try:
    raw_data = load_data(target_file)
except FileNotFoundError:
    st.error(f"Please ensure the file '{target_file}' is saved in the same directory as this script.")
    st.stop()
except json.JSONDecodeError:
    st.error(f"Error reading '{target_file}'. Please ensure it is valid JSON syntax.")
    st.stop()


# --- ROUTING LOGIC BASED ON DATASET TYPE ---

if active_dataset_choice == "LTE TRP":
    # --- Logic for the Active LTE TRP Data ---
    
    # Extract the available frequency ranges from the JSON
    freq_ranges = [d.get("Frequency_Range", "Unknown") for d in raw_data if isinstance(d, dict)]
    if not freq_ranges:
        st.error("⚠️ Invalid data structure for LTE TRP.")
        st.stop()
    
    # Add the "LTE Band/Chan" option to trigger the new aggregate view
    freq_ranges.append("LTE Band/Chan")
        
    # Dropdown to filter by the frequency range
    selected_range = ph_active_range.selectbox("**Select Frequency Range:**", freq_ranges)
    
    if selected_range == "LTE Band/Chan":
        # --- NEW PAGE: Band/Chan vs TRP View ---
        all_measurements = []
        test_date = 'N/A'
        device_name = 'Unknown Device'
        
        # Aggregate all measurements across all frequency ranges
        for item in raw_data:
            if isinstance(item, dict):
                test_date = item.get('Date', test_date)
                device_name = item.get('Device', device_name)
                if "Measurements" in item:
                    all_measurements.extend(item["Measurements"])
                    
        if all_measurements:
            df = pd.DataFrame(all_measurements)
            df['Frequency (Mhz)'] = df['Frequency (Mhz)'].astype(float)
            df['TRP (dBm)'] = df['TRP (dBm)'].astype(float)
            
            # Dashboard Headers
            st.markdown(f"<h3 style='color: #0000ff;'>Quarterly - LTE TRP Validation Measurements</h3>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size: 20px; padding-bottom: 10px;'><b>Device:</b> {device_name} | <b>Test Date:</b> {test_date}</div>", unsafe_allow_html=True)
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df['Band Chan'], 
                y=df['TRP (dBm)'],
                mode='lines+markers',
                name=f'<b>TRP (dBm) {test_date}</b>',
                text=df['Frequency (Mhz)'],
                hovertemplate="<b>%{x}</b><br>Freq: %{text} MHz<br>TRP: %{y:.2f} dBm<extra></extra>",
                line=dict(color='#0000ff'),
                marker=dict(color='#0000ff', size=8)
            ))
            
            chart_title_text = f"<b>All Frequencies - Active TRP Trend (LTE Band/Chan)</b>"
            
            fig.update_layout(
                title=dict(
                    text=chart_title_text, 
                    font=dict(size=22, color="#000000"),
                    x=0.5,
                    xanchor='center'
                ),
                xaxis_title="<b>Band / Channel</b>",
                yaxis_title="<b>TRP (dBm)</b>",
                xaxis_title_font=dict(size=16, color="#000000"),
                yaxis_title_font=dict(size=16, color="#000000"),
                legend=dict(font=dict(size=14, color="#000000")),
                hovermode="x unified",
                plot_bgcolor="#e9f1ff",
                paper_bgcolor="#e9f1ff",
                margin=dict(l=20, r=20, t=60, b=20)
            )
            
            fig.update_xaxes(
                tickfont=dict(size=14, color="#000000"), 
                tickprefix="<b>", ticksuffix="</b>",
                showline=True, linewidth=2, linecolor='black', mirror=True,
                showgrid=True, gridcolor='#999999'
            )
            fig.update_yaxes(
                tickfont=dict(size=14, color="#000000"), 
                tickprefix="<b>", ticksuffix="</b>",
                showline=True, linewidth=2, linecolor='black', mirror=True,
                showgrid=True, gridcolor='#999999'
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No measurements found.")
            
    else:
        # --- Standard Logic: Frequency vs TRP ---
        selected_data = next((item for item in raw_data if item.get("Frequency_Range") == selected_range), None)
        
        if selected_data and "Measurements" in selected_data:
            df = pd.DataFrame(selected_data["Measurements"])
            # Ensure data is plotted numerically
            df['Frequency (Mhz)'] = df['Frequency (Mhz)'].astype(float)
            df['TRP (dBm)'] = df['TRP (dBm)'].astype(float)
            
            test_date = selected_data.get('Date', 'N/A')
            device_name = selected_data.get('Device', 'Unknown Device')
            
            # Dashboard Headers
            st.markdown(f"<h3 style='color: #0000ff;'>Quarterly - LTE TRP Validation Measurements</h3>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size: 20px; padding-bottom: 10px;'><b>Device:</b> {device_name} | <b>Test Date:</b> {test_date}</div>", unsafe_allow_html=True)
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df['Frequency (Mhz)'], 
                y=df['TRP (dBm)'],
                mode='lines+markers',
                name=f'<b>TRP (dBm) {test_date}</b>',
                text=df['Band Chan'],
                hovertemplate="<b>%{text}</b><br>Freq: %{x} MHz<br>TRP: %{y:.2f} dBm<extra></extra>",
                line=dict(color='#0000ff'),
                marker=dict(color='#0000ff', size=8)
            ))
            
            chart_title_text = f"<b>{selected_range} - Active TRP Trend (Frequency)</b>"
            
            fig.update_layout(
                title=dict(
                    text=chart_title_text, 
                    font=dict(size=22, color="#000000"),
                    x=0.5,
                    xanchor='center'
                ),
                xaxis_title="<b>Frequency (MHz)</b>",
                yaxis_title="<b>TRP (dBm)</b>",
                xaxis_title_font=dict(size=16, color="#000000"),
                yaxis_title_font=dict(size=16, color="#000000"),
                legend=dict(font=dict(size=14, color="#000000")),
                hovermode="x unified",
                plot_bgcolor="#e9f1ff",
                paper_bgcolor="#e9f1ff",
                margin=dict(l=20, r=20, t=60, b=20)
            )
            
            fig.update_xaxes(
                tickfont=dict(size=14, color="#000000"), 
                tickprefix="<b>", ticksuffix="</b>",
                showline=True, linewidth=2, linecolor='black', mirror=True,
                showgrid=True, gridcolor='#999999'
            )
            fig.update_yaxes(
