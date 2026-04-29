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
    ("None", "Yearly Dipoles", "Quarterly Dipoles", "Monthly Horns", "Wideband Dipole Chamber Comparison")
)

# 2. Active Dataset Selection Toggle 
active_dataset_choice = ph_active_type.selectbox(
    "**Select Active Validation Type:**",
    ("None", "LTE TRP", "LTE TIS", "Pixel Phone S4 with Dipoles", "Phantom Wrist Dielectric Tracking")
)

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
        target_file = 'Satimo1_Pixel_Phone_S4_Dipoles_Quarterly.json'
    else:
        target_file = f'{prefix}Pixel_Phone_S4_Dipoles_Quarterly.json'
elif active_dataset_choice == "Phantom Wrist Dielectric Tracking":
    target_file = f'{prefix}Phantom_Wrist_Dielectric_Quarterly.json'
elif dataset_choice == "Yearly Dipoles":
    target_file = f'{prefix}Dipoles_Yearly.json'
elif dataset_choice == "Quarterly Dipoles":
    target_file = f'{prefix}Dipoles_Quarterly.json'
elif dataset_choice == "Monthly Horns":
    target_file = f'{prefix}Horns_Monthly.json'
elif dataset_choice == "Wideband Dipole Chamber Comparison":
    target_file = 'Chambers_Wideband_Dipole_Comparison.json' # Global file

# Stop execution and prompt the user if both are "None"
if not target_file:
    st.info("👈 Please select an Active or Passive Validation Type from the sidebar to view data.")
    st.stop()

# Known files list for "under construction" fallback logic
known_files = [
    'Chambers_Wideband_Dipole_Comparison.json', 
    'Satimo1_Dipoles_Yearly.json', 
    'Satimo1_LTE_Reference_TRP_Quarterly.json', 
    'Satimo1_Pixel_Phone_S4_Dipoles_Quarterly.json',
    'Satimo1_Phantom_Wrist_Dielectric_Quarterly.json'
]

# Load the selected dataset with friendly fallback for missing files
try:
    raw_data = load_data(target_file)
except FileNotFoundError:
    if chamber_choice != "Satimo 2" and target_file not in known_files:
        st.info(f"🏗️ **{chamber_choice} is under construction.**\n\nWhen ready, simply upload **`{target_file}`** to GitHub and this dashboard will populate automatically.")
    else:
        st.error(f"Please ensure the file '{target_file}' is saved in the same directory as this script.")
    st.stop()
except json.JSONDecodeError:
    st.error(f"Error reading '{target_file}'. Please ensure it is valid JSON syntax.")
    st.stop()


# --- ROUTING LOGIC BASED ON DATASET TYPE ---

if active_dataset_choice == "Phantom Wrist Dielectric Tracking":
    # --- Logic for the Phantom Wrist Dielectric Data ---
    
    device_name = list(raw_data.keys())[0] if isinstance(raw_data, dict) else "Unknown Device"
    
    if isinstance(raw_data, dict):
        ref_info = raw_data[device_name].get("Reference", "N/A")
        test_date = raw_data[device_name].get("Date", "N/A")
        measurements = raw_data[device_name].get("Data", [])
    else:
        ref_info = "N/A"
        test_date = "N/A"
        measurements = raw_data
        
    if measurements:
        df = pd.DataFrame(measurements)
        
        # Convert frequencies to numeric, coercing text rows (like "TRP Freqs Ascending") to NaN
        df['Frequency (MHz)'] = pd.to_numeric(df['Frequency (MHz)'], errors='coerce')
        
        # The file separates standard Phantom data from FreeSpace data.
        # We can isolate them based on the presence of the Old TRP column.
        df_phantom = df[df['Old 2-1010 TRP'].notna() & (df['Old 2-1010 TRP'] != "")].copy()
        df_freespace = df[df['Old 2-1010 TRP'].isna() | (df['Old 2-1010 TRP'] == "")].copy()
        
        # Drop rows where frequency is missing (cleaning up formatting gaps)
        df_phantom = df_phantom.dropna(subset=['Frequency (MHz)'])
        df_freespace = df_freespace.dropna(subset=['Frequency (MHz)'])
        
        # Convert all relevant TRP columns to numeric
        trp_cols = ['2-1659 TRP', '2-1660 TRP', '2-1621 TRP', 'Old 2-1010 TRP']
        for col in trp_cols:
            if col in df_phantom.columns:
                df_phantom[col] = pd.to_numeric(df_phantom[col].replace("", float("NaN")), errors='coerce')
                
        if '2-1659 TRP' in df_freespace.columns:
            df_freespace['2-1659 TRP'] = pd.to_numeric(df_freespace['2-1659 TRP'].replace("FreeSpace", float("NaN")), errors='coerce')

        st.markdown(f"<h3 style='color: #0000ff;'>Quarterly - Phantom Wrist Dielectric Tracking</h3>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 20px; padding-bottom: 5px;'><b>{device_name}</b></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 16px; padding-bottom: 10px;'><b>Reference:</b> {ref_info} | <b>Test Date:</b> {test_date}</div>", unsafe_allow_html=True)

        # --- First Graph: Phantom Dielectric Tracking (Frequency) ---
        fig1 = go.Figure()
        colors = ['#0000ff', '#00aa00', '#ff0000', '#ff8800'] # Blue, Green, Red, Orange
        
        for i, col in enumerate(trp_cols):
            if col in df_phantom.columns:
                has_data = df_phantom[col].notna().any()
                trace_name = f'<b>{col}</b>' if has_data else f'<b>{col} (NA)</b>'
                
                # We still add the trace even if empty so it appears in the legend as NA
                fig1.add_trace(go.Scatter(
                    x=df_phantom['Frequency (MHz)'], 
                    y=df_phantom[col] if has_data else [None]*len(df_phantom),
                    mode='lines+markers',
                    name=trace_name,
                    text=df_phantom['Band Chan'],
                    hovertemplate="<b>%{text}</b><br>Freq: %{x} MHz<br>TRP: %{y:.2f} dBm<extra></extra>" if has_data else "<b>%{text}</b><br>Freq: %{x} MHz<br>No Data<extra></extra>",
                    line=dict(color=colors[i % len(colors)]),
                    marker=dict(size=8)
                ))
            
        fig1.update_layout(
            title=dict(
                text="<b>Phantom Dielectric Tracking (Frequency)</b>", 
                font=dict(size=22, color="#000000"),
                x=0.5,
                xanchor='center'
            ),
            xaxis_title="<b>Frequency (MHz)</b>",
            yaxis_title="<b>Total Radiated Power (dBm)</b>",
            xaxis_title_font=dict(size=16, color="#000000"),
            yaxis_title_font=dict(size=16, color="#000000"),
            legend=dict(font=dict(size=14, color="#000000")),
            hovermode="x unified",
            plot_bgcolor="#e9f1ff",
            paper_bgcolor="#e9f1ff",
            margin=dict(l=20, r=20, t=60, b=20)
        )
        
        fig1.update_xaxes(
            tickfont=dict(size=14, color="#000000"), 
            tickprefix="<b>", ticksuffix="</b>",
            showline=True, linewidth=2, linecolor='black', mirror=True,
            showgrid=True, gridcolor='#999999'
        )
        fig1.update_yaxes(
            tickfont=dict(size=14, color="#000000"), 
            tickprefix="<b>", ticksuffix="</b>",
            showline=True, linewidth=2, linecolor='black', mirror=True,
            showgrid=True, gridcolor='#999999'
        )

        st.plotly_chart(fig1, use_container_width=True)
        
        # --- Second Graph: Free Space TRP (LTE Band/Chan) ---
        fig2 = go.Figure()
        
        if not df_freespace.empty and '2-1659 TRP' in df_freespace.columns:
            if df_freespace['2-1659 TRP'].notna().any():
                fig2.add_trace(go.Scatter(
                    x=df_freespace['Band Chan'], 
                    y=df_freespace['2-1659 TRP'],
                    mode='lines+markers',
                    name='<b>Free Space TRP</b>',
                    text=df_freespace['Frequency (MHz)'],
                    hovertemplate="<b>%{x}</b><br>Freq: %{text} MHz<br>TRP: %{y:.2f} dBm<extra></extra>",
                    line=dict(color='#0000ff'),
                    marker=dict(color='#0000ff', size=8)
                ))
            
        fig2.update_layout(
            title=dict(
                text="<b>Free Space TRP (LTE Band/Chan)</b>", 
                font=dict(size=22, color="#000000"),
                x=0.5,
                xanchor='center'
            ),
            xaxis_title="<b>LTE Band / Channel</b>",
            yaxis_title="<b>Total Radiated Power (dBm)</b>",
            xaxis_title_font=dict(size=16, color="#000000"),
            yaxis_title_font=dict(size=16, color="#000000"),
            legend=dict(font=dict(size=14, color="#000000")),
            hovermode="x unified",
            plot_bgcolor="#e9f1ff",
            paper_bgcolor="#e9f1ff",
            margin=dict(l=20, r=20, t=60, b=20)
        )
        
        fig2.update_xaxes(
            tickfont=dict(size=14, color="#000000"), 
            tickprefix="<b>", ticksuffix="</b>",
            showline=True, linewidth=2, linecolor='black', mirror=True,
            showgrid=True, gridcolor='#999999'
        )
        fig2.update_yaxes(
            tickfont=dict(size=14, color="#000000"), 
            tickprefix="<b>", ticksuffix="</b>",
            showline=True, linewidth=2, linecolor='black', mirror=True,
            showgrid=True, gridcolor='#999999'
        )

        st.plotly_chart(fig2, use_container_width=True)
        
    else:
        st.warning(f"No valid measurement data could be parsed for Phantom Wrist Tracking in {chamber_choice}.")

elif active_dataset_choice == "Pixel Phone S4 with Dipoles":
    # --- Logic for the Pixel Phone S4 Data ---
    
    # Normalize data structure to handle both List (Satimo 2) and Dict (Satimo 1) formats
    normalized_data = []
    if isinstance(raw_data, dict):
        for key, val in raw_data.items():
            if isinstance(val, dict) and "Data" in val:
                normalized_data.extend(val["Data"])
    elif isinstance(raw_data, list):
        normalized_data = raw_data
        
    if len(normalized_data) > 0:
        df = pd.DataFrame(normalized_data)
        
        # Normalize column names if they are abbreviated in the JSON
        if "Calculated TRP (dBm)" in df.columns:
            df.rename(columns={"Calculated TRP (dBm)": "Calculated Total Radiated Power (dBm)"}, inplace=True)
        if "Measured TRP (dBm)" in df.columns:
            df.rename(columns={"Measured TRP (dBm)": "Measured Total Radiated Power (dBm)"}, inplace=True)
            
        # Ensure correct numerical types for plotting
        df['Frequency (MHz)'] = df['Frequency (MHz)'].astype(float)
        df['Calculated Total Radiated Power (dBm)'] = df['Calculated Total Radiated Power (dBm)'].astype(float)
        df['Measured Total Radiated Power (dBm)'] = df['Measured Total Radiated Power (dBm)'].astype(float)
        df['Delta (Calc vs Meas) (dB)'] = df['Delta (Calc vs Meas) (dB)'].astype(float)
        
        st.markdown(f"<h3 style='color: #0000ff;'>Quarterly - Pixel Phone S4 Validation Measurements</h3>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 20px; padding-bottom: 10px;'><b>Device:</b> Pixel Phone S4 with Dipoles</div>", unsafe_allow_html=True)
        
        # Calculate Maximum Delta
        max_delta_idx = df['Delta (Calc vs Meas) (dB)'].abs().idxmax()
        max_delta_val = df.loc[max_delta_idx, 'Delta (Calc vs Meas) (dB)']
        max_delta_freq = df.loc[max_delta_idx, 'Frequency (MHz)']
        max_delta_band = df.loc[max_delta_idx, 'LTE Band']
        
        delta_html = f"<b>Maximum Delta (Calc vs Meas):</b> {max_delta_val:.2f} dB at {max_delta_freq:g} MHz ({max_delta_band})"
        st.markdown(f"<div style='font-size: 18px; line-height: 1.4; margin-bottom: 10px;'>{delta_html}</div>", unsafe_allow_html=True)
        
        # --- Graph: Band/Chan vs TRP ---
        fig = go.Figure()
        
        # Calculated TRP (Red Dashed Line)
        fig.add_trace(go.Scatter(
            x=df['LTE Band'], 
            y=df['Calculated Total Radiated Power (dBm)'],
            mode='lines+markers',
            name='<b>Calculated TRP (dBm)</b>',
            text=df['Frequency (MHz)'],
            customdata=df['Delta (Calc vs Meas) (dB)'],
            hovertemplate="<b>%{x}</b><br>Freq: %{text} MHz<br>Calc TRP: %{y:.2f} dBm<br>Delta: %{customdata:.2f} dB<extra></extra>",
            line=dict(dash='dash', color='#ff0000'),
            marker=dict(color='#ff0000', size=8)
        ))
        
        # Measured TRP (Solid Blue Line)
        fig.add_trace(go.Scatter(
            x=df['LTE Band'], 
            y=df['Measured Total Radiated Power (dBm)'],
            mode='lines+markers',
            name='<b>Measured TRP (dBm)</b>',
            text=df['Frequency (MHz)'],
            customdata=df['Delta (Calc vs Meas) (dB)'],
            hovertemplate="<b>%{x}</b><br>Freq: %{text} MHz<br>Meas TRP: %{y:.2f} dBm<br>Delta: %{customdata:.2f} dB<extra></extra>",
            line=dict(color='#0000ff'),
            marker=dict(color='#0000ff', size=8)
        ))
        
        fig.update_layout(
            title=dict(
                text="<b>Pixel Phone S4 - Calc vs Meas TRP (LTE Band/Chan)</b>", 
                font=dict(size=22, color="#000000"),
                x=0.5,
                xanchor='center'
            ),
            xaxis_title="<b>LTE Band / Channel</b>",
            yaxis_title="<b>Total Radiated Power (dBm)</b>",
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
        st.warning(f"No valid measurement data could be parsed for Pixel Phone S4 in {chamber_choice}.")

elif active_dataset_choice == "LTE TRP":
    # --- Logic for the Active LTE TRP Data ---
    
    # Normalize data structure to handle both List (Satimo 2) and Dict (Satimo 1) formats
    normalized_data = []
    if isinstance(raw_data, dict):
        for key, val in raw_data.items():
            if isinstance(val, dict) and "Data" in val:
                freq_range = val.get("Reference", "Unknown Range")
                device_name = key.split(" - ")[0] if " - " in key else "Unknown Device"
                normalized_data.append({
                    "Frequency_Range": freq_range,
                    "Device": device_name,
                    "Date": val.get("Date", "N/A"),
                    "Measurements": val.get("Data", [])
                })
    elif isinstance(raw_data, list):
        normalized_data = raw_data
    
    # Extract the available frequency ranges from the JSON
    freq_ranges = [d.get("Frequency_Range", "Unknown") for d in normalized_data if isinstance(d, dict)]
    if not freq_ranges:
        st.error(f"⚠️ Invalid data structure for LTE TRP in {chamber_choice}.")
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
        for item in normalized_data:
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
            st.markdown(f"<h3 style='color: #0000ff;'>Quarterly - Active Validation Measurements - LTE TRP</h3>", unsafe_allow_html=True)
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
        selected_data = next((item for item in normalized_data if item.get("Frequency_Range") == selected_range), None)
        
        if selected_data and "Measurements" in selected_data:
            df = pd.DataFrame(selected_data["Measurements"])
            # Ensure data is plotted numerically
            df['Frequency (Mhz)'] = df['Frequency (Mhz)'].astype(float)
            df['TRP (dBm)'] = df['TRP (dBm)'].astype(float)
            
            test_date = selected_data.get('Date', 'N/A')
            device_name = selected_data.get('Device', 'Unknown Device')
            
            # Dashboard Headers
            st.markdown(f"<h3 style='color: #0000ff;'>Quarterly - Active Validation Measurements - LTE TRP</h3>", unsafe_allow_html=True)
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
                tickfont=dict(size=14, color="#000000"), 
                tickprefix="<b>", ticksuffix="</b>",
                showline=True, linewidth=2, linecolor='black', mirror=True,
                showgrid=True, gridcolor='#999999'
            )

            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("No measurements found for the selected frequency range.")

elif active_dataset_choice == "LTE TIS":
    # --- Logic for the Active LTE TIS Data ---
    
    # Normalize data structure to handle both List (Satimo 2) and Dict (Satimo 1) formats
    normalized_data = []
    if isinstance(raw_data, dict):
        for key, val in raw_data.items():
            if isinstance(val, dict) and "Data" in val:
                freq_range = val.get("Reference", "Unknown Range")
                device_name = key.split(" - ")[0] if " - " in key else "Unknown Device"
                normalized_data.append({
                    "Frequency_Range": freq_range,
                    "Device": device_name,
                    "Date": val.get("Date", "N/A"),
                    "Measurements": val.get("Data", [])
                })
    elif isinstance(raw_data, list):
        normalized_data = raw_data
        
    # Fallback to assign Frequency_Range labels if they are missing in the JSON file
    for i, item in enumerate(normalized_data):
        if isinstance(item, dict) and "Frequency_Range" not in item:
            if i == 0:
                item["Frequency_Range"] = "LTE Low Frequencies"
            elif i == 1:
                item["Frequency_Range"] = "LTE Mid Frequencies"
            elif i == 2:
                item["Frequency_Range"] = "LTE High Frequencies"
            else:
                item["Frequency_Range"] = f"Range {i+1}"
    
    # Extract the frequency ranges
    freq_ranges = [d.get("Frequency_Range") for d in normalized_data if isinstance(d, dict)]
    if not freq_ranges:
        st.error(f"⚠️ Invalid data structure for LTE TIS in {chamber_choice}.")
        st.stop()
        
    # Add the "LTE Band/Chan" option to trigger the aggregate view
    freq_ranges.append("LTE Band/Chan")
        
    # Dropdown to filter by the frequency range
    selected_range = ph_active_range.selectbox("**Select Frequency Range:**", freq_ranges)
    
    if selected_range == "LTE Band/Chan":
        # --- NEW PAGE: Band/Chan vs TIS View ---
        all_measurements = []
        test_date = 'N/A'
        device_name = 'Unknown Device'
        
        # Aggregate all measurements across all frequency ranges
        for item in normalized_data:
            if isinstance(item, dict):
                test_date = item.get('Date', test_date)
                device_name = item.get('Device', device_name)
                if "Measurements" in item:
                    all_measurements.extend(item["Measurements"])
                    
        if all_measurements:
            df = pd.DataFrame(all_measurements)
            df['Frequency (Mhz)'] = df['Frequency (Mhz)'].astype(float)
            df['TIS (dBm)'] = df['TIS (dBm)'].astype(float)
            
            # Dashboard Headers
            st.markdown(f"<h3 style='color: #0000ff;'>Quarterly - LTE TIS Validation Measurements</h3>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size: 20px; padding-bottom: 10px;'><b>Device:</b> {device_name} | <b>Test Date:</b> {test_date}</div>", unsafe_allow_html=True)
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df['Band Chan'], 
                y=df['TIS (dBm)'],
                mode='lines+markers',
                name=f'<b>TIS (dBm) {test_date}</b>',
                text=df['Frequency (Mhz)'],
                hovertemplate="<b>%{x}</b><br>Freq: %{text} MHz<br>TIS: %{y:.2f} dBm<extra></extra>",
                line=dict(color='#0000ff'),
                marker=dict(color='#0000ff', size=8)
            ))
            
            chart_title_text = f"<b>All Frequencies - Active TIS Trend (LTE Band/Chan)</b>"
            
            fig.update_layout(
                title=dict(
                    text=chart_title_text, 
                    font=dict(size=22, color="#000000"),
                    x=0.5,
                    xanchor='center'
                ),
                xaxis_title="<b>Band / Channel</b>",
                yaxis_title="<b>TIS (dBm)</b>",
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
        # --- Standard Logic: Frequency vs TIS ---
        selected_data = next((item for item in normalized_data if item.get("Frequency_Range") == selected_range), None)
        
        if selected_data and "Measurements" in selected_data:
            df = pd.DataFrame(selected_data["Measurements"])
            # Ensure data is plotted numerically
            df['Frequency (Mhz)'] = df['Frequency (Mhz)'].astype(float)
            df['TIS (dBm)'] = df['TIS (dBm)'].astype(float)
            
            test_date = selected_data.get('Date', 'N/A')
            device_name = selected_data.get('Device', 'Unknown Device')
            
            # Dashboard Headers
            st.markdown(f"<h3 style='color: #0000ff;'>Quarterly - LTE TIS Validation Measurements</h3>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size: 20px; padding-bottom: 10px;'><b>Device:</b> {device_name} | <b>Test Date:</b> {test_date}</div>", unsafe_allow_html=True)
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df['Frequency (Mhz)'], 
                y=df['TIS (dBm)'],
                mode='lines+markers',
                name=f'<b>TIS (dBm) {test_date}</b>',
                text=df['Band Chan'],
                hovertemplate="<b>%{text}</b><br>Freq: %{x} MHz<br>TIS: %{y:.2f} dBm<extra></extra>",
                line=dict(color='#0000ff'),
                marker=dict(color='#0000ff', size=8)
            ))
            
            chart_title_text = f"<b>{selected_range} - Active TIS Trend (Frequency)</b>"
            
            fig.update_layout(
                title=dict(
                    text=chart_title_text, 
                    font=dict(size=22, color="#000000"),
                    x=0.5,
                    xanchor='center'
                ),
                xaxis_title="<b>Frequency (MHz)</b>",
                yaxis_title="<b>TIS (dBm)</b>",
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
            st.warning("No measurements found for the selected frequency range.")

elif dataset_choice == "Wideband Dipole Chamber Comparison":
    # --- Logic for the Multi-Chamber Comparison Data ---
    
    # Render Antenna Selection in its predefined slot above Active Validation
    selected_antenna = ph_antenna.selectbox("**Select Antenna:**", ["Proxicast Dipole #4"])
    
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
        overshoot_html = f"<b>Maximum Overshoot Above 0 dB:</b> <span style='color: #da0303;'>{max_overshoot_val:.2f} dB at {max_overshoot_freq:g} MHz</span>"
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
        st.warning(f"The app could not find valid measurement data in {chamber_choice}. Please check the file formatting.")
        st.stop()

    try:
        antenna_names = [d.get('dipole_name', 'Unknown Antenna') for d in data]
    except (TypeError, KeyError):
        st.error("Data structure error: The JSON file is missing the identifying names.")
        st.stop()

    # Render Antenna Selection in its predefined slot above Active Validation
    selected_antenna = ph_antenna.selectbox("**Select Antenna:**", antenna_names)

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
