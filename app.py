import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json

# Configure the dashboard layout
st.set_page_config(page_title="Antenna Efficiency Dashboard", layout="wide")

# Inject custom HTML/CSS to shrink the title and fit it on one line
st.markdown(
    "<h1 style='font-size: 2.2rem;'>📡 Satimo 2 Chamber Performance - Interactive Dashboard</h1>", 
    unsafe_allow_html=True
)

# Function to load JSON data
def load_data(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

# Sidebar for Dashboard Controls
st.sidebar.header("Dashboard Controls")

# 1. Dataset Selection Toggle
dataset_choice = st.sidebar.selectbox(
    "Select Passive Validation Type:",
    ("Yearly Dipoles", "Quarterly Dipoles")
)

# Map selection to the exact JSON files
if dataset_choice == "Yearly Dipoles":
    target_file = 'Satimo 2 Chamber_Passive Trend Charts_Dipoles Yearly.json'
else:
    target_file = 'Satimo2_Passive Trends_Dipoles_Quarterly.json'

# Load the selected dataset
try:
    raw_data = load_data(target_file)
except FileNotFoundError:
    st.error(f"Please ensure the file '{target_file}' is saved in the same directory as this script.")
    st.stop()
except json.JSONDecodeError:
    st.error(f"Error reading '{target_file}'. Please ensure it is valid JSON.")
    st.stop()

# --- ROBUST DATA NORMALIZER ---
# This ensures that no matter how the JSON was saved (list, single dict, or wrapped dict), 
# it gets converted into a flat list of dipole dictionaries.
data = []
if isinstance(raw_data, list):
    data = raw_data
elif isinstance(raw_data, dict):
    if "dipole_name" in raw_data:
        # It's a single dipole object, wrap it in a list
        data = [raw_data]
    else:
        # It is wrapped in a parent object (e.g., {"dipoles": [...]})
        for key, value in raw_data.items():
            if isinstance(value, list):
                data = value
                break

if not data:
    st.error("Could not find valid dipole data in the selected file. Please check the JSON structure.")
    st.stop()
# ------------------------------

# Extract dipole names safely
try:
    dipole_names = [d['dipole_name'] for d in data]
except TypeError:
    st.error("Data structure error: The JSON file contains unexpected formatting that could not be normalized.")
    st.stop()

# 2. DUT Selection
selected_dipole = st.sidebar.selectbox("Select Dipole:", dipole_names)

# Filter the dataset based on user selection
selected_data = next((item for item in data if item.get("dipole_name") == selected_dipole), None)

if selected_data and 'measurements' in selected_data:
    df = pd.DataFrame(selected_data['measurements'])

    # Display key metrics for the active DUT
    st.subheader(f"Analyzing: {selected_dipole} ({dataset_choice})")
    st.markdown(f"**Reference Source:** {selected_data.get('reference', 'N/A')} | **Test Date:** {selected_data.get('date', 'N/A')}")

    # Build the interactive Plotly chart
    fig = go.Figure()

    # Plot Reference Data
    fig.add_trace(go.Scatter(
        x=df['frequency_mhz'], 
        y=df['efficiency_db_ref'],
        mode='lines+markers',
        name='Reference Efficiency (dB)',
        line=dict(dash='dash')
    ))

    # Plot Measured Data
    fig.add_trace(go.Scatter(
        x=df['frequency_mhz'], 
        y=df['efficiency_db_measured'],
        mode='lines+markers',
        name='Measured Efficiency (dB)'
    ))

    # Format the chart axes and layout
    fig.update_layout(
        xaxis_title="Frequency (MHz)",
        yaxis_title="Efficiency (dB)",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20)
    )

    # Render the chart
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No measurements found for the selected dipole.")
