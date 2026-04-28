import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json

# Configure the dashboard layout
st.set_page_config(page_title="Antenna Efficiency Dashboard", layout="wide")

# Inject custom HTML/CSS for title shrinking and Sidebar Background Color
st.markdown(
    """
    <style>
        /* Shrink the main title to fit on one line */
        h1 {
            font-size: 2.2rem !important;
        }
        
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

# Sidebar for Dashboard Controls
st.sidebar.markdown(
    "<h2 style='font-size: 1.5rem; color: #0000ff;'>Dashboard Controls</h2>", 
    unsafe_allow_html=True
)

# 1. Dataset Selection Toggle
dataset_choice = st.sidebar.selectbox(
    "Select Passive Validation Type:",
    ("Yearly Dipoles", "Quarterly Dipoles", "Monthly Horns", "Wideband Dipole Chamber Comparison")
)

# Map selection to the exact JSON files
if dataset_choice == "Yearly Dipoles":
    target_file = 'Satimo2_Dipoles_Yearly.json'
elif dataset_choice == "Quarterly Dipoles":
    target_file = 'Satimo2_Dipoles_Quarterly.json'
elif dataset_choice == "Monthly Horns":
    target_file = 'Satimo2_Horns_Monthly.json'
else:
    target_file = 'Chambers_Wideband_Dipole_Comparison.json'

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

if dataset_choice == "Wideband Dipole Chamber Comparison":
    # --- Logic for the Multi-Chamber Comparison Data ---
    
    # Add the dropdown specifically for this view to maintain UI consistency
    selected_antenna = st.sidebar.selectbox("Select Antenna:", ["Proxicast Dipole #4"])
    
    st.subheader(f"Analyzing: {selected_antenna} (Chamber Comparison)")
    
    # Safely extract and format dates
    dates = [f"{k}: {v.get('Date', 'N/A')}" for k, v in raw_data.items() if isinstance(v, dict)]
    if dates:
        st.markdown("**Test Dates:** " + " | ".join(dates))
    
    fig = go.Figure()
    
    # Loop through each chamber in the JSON (Satimo1, Satimo 2, Satimo 3)
    for chamber_name, chamber_data in raw_data.items():
        if isinstance(chamber_data, dict) and "Data" in chamber_data:
            # Extract frequency and efficiency
            freqs = []
            effs = []
            for row in chamber_data["Data"]:
                try:
                    # Catch 'Frequency (Mhz)' or 'Frequency (MHz)'
                    f_key = next((k for k in row.keys() if 'Frequency' in k), None)
                    e_key = next((k for k in row.keys() if 'Efficiency' in k), None)
                    
                    if f_key and e_key:
                        freqs.append(float(row[f_key]))
                        effs.append(float(row[e_key]))
                except (ValueError, TypeError):
                    continue
            
            # Add a trace for this specific chamber, with bolded name
            if freqs and effs:
                fig.add_trace(go.Scatter(
                    x=freqs, 
                    y=effs,
                    mode='lines+markers',
                    name=f"<b>{chamber_name}</b>"
                ))
    
    if not fig.data:
        st.warning("No valid measurement data could be parsed for the chamber comparison.")
    else:
        # Add a bold 0 dB horizontal reference line
        fig.add_hline(y=0, line_width=3, line_color="black")
        
        # Update layout for Main Title, Axis Titles, Background Color, and Legend Font
        fig.update_layout(
            title=dict(
                text="<b>Satimo 2 Chamber Performance - Interactive Dashboard</b>", 
                font=dict(size=22, color="#000000"),
                x=0.5,
                xanchor='center'
            ),
            xaxis_title="<b>Frequency (MHz)</b>",
            yaxis_title="<b>Efficiency (dB)</b>",
            xaxis_title_font=dict(size=16, color="#000000"),
            yaxis_title_font=dict(size=16, color="#000000"),
            legend=dict(font=dict(size=14, color="#000000")),
            hovermode="x unified",
            plot_bgcolor="#e9f1ff",
            margin=dict(l=20, r=20, t=60, b=20)
        )
        # Update layout for Axis Numbers (Ticks), Plot Border, and Darker Grid Lines
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
    # --- Standard Logic for Dipoles & Horns (Ref vs Measured) ---
    
    data = []
    
    # Catch double-encoded JSON
    if isinstance(raw_data, str):
        try:
            raw_data = json.loads(raw_data)
        except json.JSONDecodeError:
            pass 

    if isinstance(raw_data, list):
        data = raw_data
    elif isinstance(raw_data, dict):
        if any(isinstance(v, dict) and "Data" in v for v in raw_data.values()):
            for dev_name, dev_info in raw_data.items():
                measurements = []
                for row in dev_info.get("Data", []):
                    try:
                        measurements.append({
                            "frequency_mhz": float(row.get("Frequency (MHz)", 0)),
                            "efficiency_db_ref": float(row.get("Efficiency (dB)", 0)),
                            "efficiency_db_measured": float(row.get("Efficiency (dB)_3", 0))
                        })
                    except (ValueError, TypeError):
                        continue
                
                data.append({
                    "dipole_name": dev_name,
                    "reference": dev_info.get("Reference", "N/A"),
                    "date": dev_info.get("Date", "N/A"),
                    "measurements": measurements
                })
        elif "dipole_name" in raw_data:
            data = [raw_data]
        else:
            for key, value in raw_data.items():
                if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                    data = value
                    break

    if not data:
        st.error(f"⚠️ **Data Structure Error in `{target_file}`**")
        st.warning("The app could not find valid measurement data. Please check the file formatting.")
        st.stop()

    try:
        antenna_names = [d.get('dipole_name', 'Unknown Antenna') for d in data]
    except (TypeError, KeyError):
        st.error("Data structure error: The JSON file is missing the identifying names.")
        st.stop()

    # 2. Antenna Selection
    selected_antenna = st.sidebar.selectbox("Select Antenna:", antenna_names)

    # Filter dataset
    selected_data = next((item for item in data if item.get("dipole_name") == selected_antenna), None)

    if selected_data and 'measurements' in selected_data:
        df = pd.DataFrame(selected_data['measurements'])

        test_date = selected_data.get('date', 'N/A')

        st.subheader(f"Analyzing: {selected_antenna} ({dataset_choice})")
        st.markdown(f"**Reference Source:** {selected_data.get('reference', 'N/A')} | **Test Date:** {test_date}")

        fig = go.Figure()

        # Added HTML tags to bold the trace name
        fig.add_trace(go.Scatter(
            x=df['frequency_mhz'], 
            y=df['efficiency_db_ref'],
            mode='lines+markers',
            name='<b>Reference Efficiency - NIST (dB)</b>',
            line=dict(dash='dash')
        ))

        # Dynamically inject the date and bold the trace name
        fig.add_trace(go.Scatter(
            x=df['frequency_mhz'], 
            y=df['efficiency_db_measured'],
            mode='lines+markers',
            name=f'<b>Measured Efficiency {test_date}</b>'
        ))

        # Add a bold 0 dB horizontal reference line
        fig.add_hline(y=0, line_width=3, line_color="black")

        # Update layout for Main Title, Axis Titles, Background Color, and Legend Font
        fig.update_layout(
            title=dict(
                text="<b>Satimo 2 Chamber Performance - Interactive Dashboard</b>", 
                font=dict(size=22, color="#000000"),
                x=0.5,
                xanchor='center'
            ),
            xaxis_title="<b>Frequency (MHz)</b>",
            yaxis_title="<b>Efficiency (dB)</b>",
            xaxis_title_font=dict(size=16, color="#000000"),
            yaxis_title_font=dict(size=16, color="#000000"),
            legend=dict(font=dict(size=14, color="#000000")),
            hovermode="x unified",
            plot_bgcolor="#e9f1ff",
            margin=dict(l=20, r=20, t=60, b=20)
        )
        # Update layout for Axis Numbers (Ticks), Plot Border, and Darker Grid Lines
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
        st.warning("No measurements found for the selected antenna.")
