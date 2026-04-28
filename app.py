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

# 1. Dataset Selection Toggle (Now Bold)
dataset_choice = st.sidebar.selectbox(
    "**Select Passive Validation Type:**",
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
    
    # Antenna Selection Toggle (Now Bold)
    selected_antenna = st.sidebar.selectbox("**Select Antenna:**", ["Proxicast Dipole #4"])
    
    st.markdown("<h3 style='color: #0000ff;'>Wideband - Chamber Comparison Measurements</h3>", unsafe_allow_html=True)
        
    # Pre-calculate the maximum overshoot across all chambers
    max_overshoot_val = 0
    max_overshoot_freq = None
    max_overshoot_chamber = None
    
    for chamber_name, chamber_data in raw_data.items():
        if isinstance(chamber_data, dict) and "Data" in chamber_data:
            for row in chamber_data["Data"]:
                try:
                    f_key = next((k for k in row.keys() if 'Frequency' in k), None)
                    e_key = next((k for k in row.keys() if 'Efficiency' in k), None)
                    if f_key and e_key:
                        f_val = float(row[f_key])
                        e_val = float(row[e_key])
                        if e_val > 0 and e_val > max_overshoot_val:
                            max_overshoot_val = e_val
                            max_overshoot_freq = f_val
                            max_overshoot_chamber = chamber_name
                except (ValueError, TypeError):
                    continue
                    
    # Display the Overshoot Subtitle with conditional color formatting
    if max_overshoot_val > 0:
        overshoot_html = f"<b>Maximum Overshoot Above 0 dB:</b> <span style='color: #da0303;'>{max_overshoot_val:.2f} dB at {max_overshoot_freq:g} MHz ({max_overshoot_chamber})</span>"
    else:
        overshoot_html = "<b>Maximum Overshoot Above 0 dB:</b> <span style='color: #04c136; font-weight: bold;'>None</span>"
        
    st.markdown(
        f"<div style='font-size: 18px; line-height: 1.4; margin-bottom: 10px;'>"
        f"{overshoot_html}"
        f"</div>", 
        unsafe_allow_html=True
    )
    
    fig = go.Figure()
    
    # Loop through each chamber to plot the data
    for chamber_name, chamber_data in raw_data.items():
        if isinstance(chamber_data, dict) and "Data" in chamber_data:
            chamber_date = chamber_data.get('Date', 'N/A')
            freqs = []
            effs = []
            for row in chamber_data["Data"]:
                try:
                    f_key = next((k for k in row.keys() if 'Frequency' in k), None)
                    e_key = next((k for k in row.keys() if 'Efficiency' in k), None)
                    
                    if f_key and e_key:
                        freqs.append(float(row[f_key]))
                        effs.append(float(row[e_key]))
                except (ValueError, TypeError):
                    continue
            
            if freqs and effs:
                # Include the specific chamber's test date directly in the legend trace name
                fig.add_trace(go.Scatter(
                    x=freqs, 
                    y=effs,
                    mode='lines+markers',
                    name=f"<b>{chamber_name} ({chamber_date})</b>"
                ))
    
    if not fig.data:
        st.warning("No valid measurement data could be parsed for the chamber comparison.")
    else:
        fig.add_hline(y=0, line_width=3, line_color="black")
        
        # Build the dynamic title with frequency range
        freq_range = ANTENNA_RANGES.get(selected_antenna, "Passive Trend")
        chart_title_text = f"<b>{selected_antenna.replace('Dipole ', '')} ({freq_range}) - Passive Trend</b>"
        
        fig.update_layout(
            title=dict(
                text=chart_title_text, 
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
            paper_bgcolor="#e9f1ff",  # Extended background color
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
    # --- Standard Logic for Dipoles & Horns (Ref vs Measured) ---
    
    data = []
    
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

    # Antenna Selection Toggle (Now Bold)
    selected_antenna = st.sidebar.selectbox("**Select Antenna:**", antenna_names)

    selected_data = next((item for item in data if item.get("dipole_name") == selected_antenna), None)

    if selected_data and 'measurements' in selected_data:
        df = pd.DataFrame(selected_data['measurements'])
        test_date = selected_data.get('date', 'N/A')
        
        time_prefix = dataset_choice.split()[0]
        test_type_label = "Horn" if "Horn" in dataset_choice else "Dipole"
        
        st.markdown(f"<h3 style='color: #0000ff;'>{time_prefix} - {test_type_label} Validation Measurements</h3>", unsafe_allow_html=True)
        
        # Calculate Maximum Overshoot
        overshoot_df = df[df['efficiency_db_measured'] > 0]
        
        # Apply conditional color formatting
        if not overshoot_df.empty:
            max_idx = overshoot_df['efficiency_db_measured'].idxmax()
            max_val = overshoot_df.loc[max_idx, 'efficiency_db_measured']
            max_freq = overshoot_df.loc[max_idx, 'frequency_mhz']
            overshoot_html = f"<b>Maximum Overshoot Above 0 dB:</b> <span style='color: #da0303;'>{max_val:.2f} dB at {max_freq:g} MHz</span>"
        else:
            overshoot_html = "<b>Maximum Overshoot Above 0 dB:</b> <span style='color: #04c136; font-weight: bold;'>None</span>"

        # Calculate Maximum Delta from Reference NIST
        max_delta_idx = (df['efficiency_db_measured'] - df['efficiency_db_ref']).abs().idxmax()
        max_delta_val = abs(df.loc[max_delta_idx, 'efficiency_db_measured'] - df.loc[max_delta_idx, 'efficiency_db_ref'])
        max_delta_freq = df.loc[max_delta_idx, 'frequency_mhz']
        
        delta_html = f"<b>Maximum Delta - Reference NIST:</b> {max_delta_val:.2f} dB at {max_delta_freq:g} MHz"
        
        # Display both subtitles with smaller font and no line spacing between them
        st.markdown(
            f"<div style='font-size: 18px; line-height: 1.4; margin-bottom: 10px;'>"
            f"{overshoot_html}<br>{delta_html}"
            f"</div>", 
            unsafe_allow_html=True
        )

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df['frequency_mhz'], 
            y=df['efficiency_db_ref'],
            mode='lines+markers',
            name='<b>Reference Efficiency - NIST (dB)</b>',
            line=dict(dash='dash', color='#ff0000'),
            marker=dict(color='#ff0000')
        ))

        fig.add_trace(go.Scatter(
            x=df['frequency_mhz'], 
            y=df['efficiency_db_measured'],
            mode='lines+markers',
            name=f'<b>Measured Efficiency (dB) {test_date}</b>',
            line=dict(color='#0000ff'),
            marker=dict(color='#0000ff')
        ))

        fig.add_hline(y=0, line_width=3, line_color="black")

        # Build the dynamic title with frequency range
        freq_range = ANTENNA_RANGES.get(selected_antenna, "Passive Trend")
        clean_antenna_name = selected_antenna.replace("Dipole ", "").replace("Horn ", "")
        chart_title_text = f"<b>{clean_antenna_name} ({freq_range}) - Passive Trend</b>"

        fig.update_layout(
            title=dict(
                text=chart_title_text, 
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
            paper_bgcolor="#e9f1ff",  # Extended background color
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
        st.warning("No measurements found for the selected antenna.")
