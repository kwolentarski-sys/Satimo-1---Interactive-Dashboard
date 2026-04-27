import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json

# Configure the dashboard layout
st.set_page_config(page_title="Antenna Efficiency Dashboard", layout="wide")

st.title("📡 Antenna Test Data: Frequency vs. Efficiency")

# Load the JSON data
@st.cache_data
def load_data():
    with open('Satimo 2 Chamber_Passive Trend Charts_Dipoles Yearly.json', 'r') as f:
        return json.load(f)

try:
    data = load_data()
except FileNotFoundError:
    st.error("Please ensure your 'Satimo 2 Chamber_Passive Trend Charts_Dipoles Yearly.json' file is in the same directory as this script.")
    st.stop()

# Extract dipole names to populate the dropdown
dipole_names = [d['dipole_name'] for d in data]

# Sidebar for test configuration and selection
st.sidebar.header("Test Configuration")
selected_dipole = st.sidebar.selectbox("Select Device Under Test (DUT)", dipole_names)

# Filter the dataset based on user selection
selected_data = next(item for item in data if item["dipole_name"] == selected_dipole)
df = pd.DataFrame(selected_data['measurements'])

# Display key metrics for the active DUT
st.subheader(f"Analyzing: {selected_dipole}")
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
