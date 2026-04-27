import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json

# Configure the dashboard layout
st.set_page_config(page_title="Antenna Efficiency Dashboard", layout="wide")

st.title("📡 Satimo 2 Chamber Performance - Interactive Dashboard")

# Function to load JSON data efficiently
@st.cache_data
def load_data(filename):
    with open(filename, 'r') as f:
        return json.load(f)

# Sidebar for Dashboard Controls
st.sidebar.header("Dashboard Controls")

# 1. Dataset Selection Toggle
dataset_choice = st.sidebar.radio(
    "Select Test Cadence",
    ("Yearly Dipoles", "Quarterly Dipoles")
)

# Map selection to the correct JSON file
if dataset_choice == "Yearly Dipoles":
    target_file = 'Satimo 2 Chamber_Passive Trend Charts_Dipoles Yearly.json'
else:
    target_file = 'Satimo2_Passive Trends_Dipoles_Quarterly.json'

# Load the selected dataset
try:
    data = load_data(target_file)
except FileNotFoundError:
    st.error(f"Please ensure '{target_file}' is in the same directory as this script.")
    st.stop()

# Extract dipole names based on the currently loaded dataset
dipole_names = [d['dipole_name'] for d in data]

# 2. DUT Selection (Dynamically populates based on dataset)
selected_dipole = st.sidebar.selectbox("Select Device Under Test (DUT)", dipole_names)

# Filter the dataset based on user selection
selected_data = next(item for item in data if item["dipole_name"] == selected_dipole)
df = pd.DataFrame(selected_data['measurements'])

# Display key metrics for the active DUT
st.subheader(f"Analyzing: {selected_dipole} ({dataset_choice})")
st.markdown(f"**Reference Source:** {selected_data['reference']} | **Test Date:** {selected_data['date']}")

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
