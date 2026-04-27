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
    target_file = 'Satimo2_Dipoles_Yearly.json'
else:
    target_file = 'Satimo2_Dipoles_Quarterly.json'

# Load the selected dataset
try:
    raw_data = load_data(target_file)
except FileNotFoundError:
    st.error(f"Please ensure the file '{target_file}' is saved in the same directory as this script.")
    st.stop()
except json.JSONDecodeError:
    st.error(f"Error reading '{target_file}'. Please ensure it is valid JSON syntax.")
    st.stop()

# --- ULTRA-ROBUST DATA NORMALIZER ---
data = []

# 1. Catch double-encoded JSON (where the data was saved as a literal string)
if isinstance(raw_data, str):
    try:
        raw_data = json.loads(raw_data)
    except json.JSONDecodeError:
        pass # Let the next steps catch the error

# 2. Extract the data based on its shape
if isinstance(raw_data, list):
    data = raw_data
elif isinstance(raw_data, dict):
    # Check if it's a single dipole dict
    if "dipole_name" in raw_data:
        data = [raw_data]
    else:
        # Check if the list of dipoles is wrapped inside a parent object (e.g., {"data": [...]})
        for key, value in raw_data.items():
            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                data = value
                break

# 3. Trigger Debugger if all extractions fail
if not data:
    st.error(f"⚠️ **Data Structure Error in `{target_file}`**")
    st.warning("The app could not find a valid list of dipoles. Here is exactly what Streamlit sees inside your file:")
    st.write("**Data Type Detected:**", type(raw_data).__name__)
    st.write("**Raw Content Preview:**", raw_data)
    st.stop()
# ------------------------------------

# Extract dipole names safely
try:
    dipole_names = [d['dipole_name'] for d in data]
except (TypeError, KeyError):
    st.error("Data structure error: The JSON file contains a list, but it is missing the 'dipole_name' keys.")
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
