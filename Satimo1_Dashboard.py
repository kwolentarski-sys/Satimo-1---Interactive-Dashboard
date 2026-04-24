import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Satimo 1 Dashboard", layout="wide")

# Custom CSS for Sidebar Background and styling
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            background-color: #cbcbcb;
        }
        .main-title {
            white-space: nowrap; 
            overflow: hidden; 
            text-overflow: clip; 
            font-size: 34px; 
            font-weight: bold;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<h1 class="main-title">Satimo 1 Chamber Performance - Interactive Dashboard</h1>', unsafe_allow_html=True)

# --- DATA LOADING FUNCTIONS ---

@st.cache_data
def load_and_clean_data(file_name, is_comparison=False):
    """Dynamically finds and parses Satimo data. Handles standard 3-col and comparison 2-col formats."""
    if not os.path.exists(file_name):
        return None
    try:
        df_raw = pd.read_csv(file_name, header=None)
        all_parsed_data = []
        keywords = ["Dipoles", "Horn", "Chamber"]
        
        for c in range(len(df_raw.columns)):
            start_row = None
            for r in range(min(15, len(df_raw))):
                cell_val = str(df_raw.iloc[r, c]).strip()
                if any(kw in cell_val for kw in keywords):
                    start_row = r
                    break
            
            if start_row is not None:
                if not is_comparison:
                    # Logic for standard validation files
                    data_cols = df_raw.iloc[start_row:, c:c+3].copy()
                    data_cols.columns = ['ID_Col', 'Ref_Col', 'Meas_Col']
                    current_unit, current_date = None, None
                    for _, row in data_cols.iterrows():
                        val_id = str(row['ID_Col']).strip()
                        val_ref = str(row['Ref_Col']).strip()
                        val_meas = str(row['Meas_Col']).strip()
                        if val_id.startswith(('SD', 'WD', 'SH')) and len(val_id) > 2:
                            current_unit, current_date = val_id, (val_meas if val_meas != 'nan' else 'Current Date')
                            continue
                        if current_unit:
                            try:
                                all_parsed_data.append({
                                    'Dipole': current_unit, 
                                    'Date_Label': current_date, 
                                    'Frequency (MHz)': float(val_id), 
                                    'Reference Efficiency (dB)': float(val_ref), 
                                    'Date Efficiency (dB)': float(val_meas)
                                })
                            except (ValueError, TypeError): continue
                else:
                    # Logic for Chamber Comparison
                    try:
                        chamber_name = str(df_raw.iloc[start_row+1, c]).strip()
                        chamber_date = str(df_raw.iloc[start_row+1, c+1]).strip()
                        if "Satimo1" in chamber_name: chamber_name = "Satimo 1"
                        
                        unit_name = str(df_raw.iloc[0, 0]).split(':')[-1].strip()
                        unit_name = unit_name.replace("Proxicast #4", "Proxicast Dipole #4")
                        
                        data_cols = df_raw.iloc[start_row+2:, c:c+2].copy()
                        data_cols.columns = ['Freq_Col', 'Eff_Col']
                        for _, row in data_cols.iterrows():
                            try:
                                all_parsed_data.append({
                                    'Dipole': unit_name, 
                                    'Chamber': chamber_name, 
                                    'Chamber_Date': chamber_date, 
                                    'Frequency (MHz)': float(row['Freq_Col']), 
                                    'Efficiency': float(row['Eff_Col'])
                                })
                            except (ValueError, TypeError): continue
                    except Exception: continue
        return pd.DataFrame(all_parsed_data)
    except Exception: return None

# (Note: Active TRP/TIS/Pixel loading functions remain largely same as your logic)
@st.cache_data
def load_active_trp_data(file_name):
    if not os.path.exists(file_name): return None, "N/A"
    try:
        df_raw = pd.read_csv(file_name, header=None)
        data = df_raw.iloc[8:, 2:5].copy()
        data.columns = ['Band/Chan', 'Frequency (Mhz)', 'TRP (dBm)']
        date_val = str(df_raw.iloc[4, 4]).strip() if len(df_raw) > 4 else "Unknown"
        return data.apply(pd.to_numeric, errors='coerce').dropna(), date_val
    except: return None, "N/A"

@st.cache_data
def load_active_tis_data(file_name):
    if not os.path.exists(file_name): return None, "N/A"
    try:
        df_raw = pd.read_csv(file_name, header=None)
        data = df_raw.iloc[8:, 2:5].copy()
        data.columns = ['Band/Chan', 'Frequency (Mhz)', 'TIS (dBm)']
        date_val = str(df_raw.iloc[4, 4]).strip()
        return data.apply(pd.to_numeric, errors='coerce').dropna(), date_val
    except: return None, "N/A"

@st.cache_data
def load_pixel_phone_data(file_name):
    if not os.path.exists(file_name): return None
    try:
        df_raw = pd.read_csv(file_name, header=None)
        data = df_raw.iloc[5:, [10, 11, 19, 20]].copy()
        data.columns = ['LTE Band', 'Frequency (MHz)', 'Calculated TRP (dBm)', 'Measured TRP (dBm)']
        return data.apply(pd.to_numeric, errors='coerce').dropna(subset=['Frequency (MHz)'])
    except: return None

@st.cache_data
def load_phantom_wrist_data(file_name):
    if not os.path.exists(file_name): return None, None
    try:
        df_raw = pd.read_csv(file_name, header=None)
        dates = [str(d) if pd.notna(d) else "NA" for d in df_raw.iloc[6, [21, 22, 23, 24]].values]
        date_map = {'2-1659 TRP': dates[0], '2-1660 TRP': dates[1], '2-1621 TRP': dates[2], 'Old 2-1010 TRP': dates[3]}
        data = df_raw.iloc[7:16, [20, 21, 22, 23, 24]].copy()
        data.columns = ['Frequency (MHz)', '2-1659 TRP', '2-1660 TRP', '2-1621 TRP', 'Old 2-1010 TRP']
        return data.apply(pd.to_numeric, errors='coerce').dropna(subset=['Frequency (MHz)']), date_map
    except: return None, None

# --- SIDEBAR ---
st.sidebar.markdown('<h2 style="color:#022af2; font-size: 32px;">Controls</h2>', unsafe_allow_html=True)

validation_type = st.sidebar.selectbox(
    "Select Passive Validation Type:",
    ["None", "Yearly", "Quarterly", "Monthly", "Wideband Dipole - Chamber Comparison"]
)

st.sidebar.divider()

is_active_disabled = (validation_type != "None")
active_validation_type = st.sidebar.selectbox(
    "Select Active Validation Type:",
    ["None", "LTE TRP", "LTE TIS", "Pixel Phone S4 with Dipoles", "Phantom Wrist Dielectrics"],
    disabled=is_active_disabled
)

# --- MAIN LOGIC ---

# PASSIVE SECTION
if validation_type != "None":
    passive_files = {
        "Yearly": 'Satimo 1 Chamber - Passive Trend Charts - Satimo 1- Dipoles Yearly (4).csv',
        "Quarterly": 'Satimo 1 Chamber - Passive Trend Charts - Satimo 1- Dipoles Quarterly (1).csv',
        "Monthly": 'Satimo 1 Chamber - Passive Trend Charts - Satimo 1 - Horns Monthly (1).csv',
        "Wideband Dipole - Chamber Comparison": 'Wideband Dipole - Chamber Comparison - Satimo TechEng Wideband Dipole.csv'
    }
    df_passive = load_and_clean_data(passive_files[validation_type], is_comparison=(validation_type == "Wideband Dipole - Chamber Comparison"))
    
    if df_passive is not None and not df_passive.empty:
        units = df_passive['Dipole'].unique()
        selected_unit = st.sidebar.selectbox("Select Device:", units)
        
        st.markdown(f'<h3 style="color:#022af2;"><b>{validation_type} Validation</b></h3>', unsafe_allow_html=True)
        subset = df_passive[df_passive['Dipole'] == selected_unit].copy()
        
        if not subset.empty:
            fig = go.Figure()
            if validation_type == "Wideband Dipole - Chamber Comparison":
                colors = {"Satimo 1": "red", "Satimo 2": "#022af2", "Satimo 3": "#2ca02c"}
                for chamber, color in colors.items():
                    ch_d = subset[subset['Chamber'] == chamber]
                    if not ch_d.empty:
                        fig.add_trace(go.Scatter(x=ch_d['Frequency (MHz)'], y=ch_d['Efficiency'], name=f"{chamber}", line=dict(color=color)))
            else:
                # Delta calculations
                subset['Abs_Diff'] = (subset['Reference Efficiency (dB)'] - subset['Date Efficiency (dB)']).abs()
                m_val, m_freq = subset['Abs_Diff'].max(), subset.loc[subset['Abs_Diff'].idxmax(), 'Frequency (MHz)']
                st.write(f"**Max Delta:** {m_val:.2f} dB at {m_freq} MHz")
                
                fig.add_trace(go.Scatter(x=subset['Frequency (MHz)'], y=subset['Reference Efficiency (dB)'], name="NIST Reference", line=dict(color='red', dash='dash')))
                fig.add_trace(go.Scatter(x=subset['Frequency (MHz)'], y=subset['Date Efficiency (dB)'], name=str(subset["Date_Label"].iloc[0]), line=dict(color='#022af2')))

            fig.update_layout(template="plotly_white", height=550, plot_bgcolor="#e9f1ff", paper_bgcolor="#e9f1ff")
            st.plotly_chart(fig, use_container_width=True)

# ACTIVE SECTION
if active_validation_type != "None" and not is_active_disabled:
    st.markdown(f'<h3 style="color:#022af2;"><b>Active Validation: {active_validation_type}</b></h3>', unsafe_allow_html=True)
    
    if active_validation_type == "LTE TRP":
        df_active, active_date = load_active_trp_data("Satimo 1 Chamber - Active Trend Charts - Satimo1 - Active Reference Quarterly - LTE TRP.csv")
        if df_active is not None:
            fig = go.Figure(go.Scatter(x=df_active['Frequency (Mhz)'], y=df_active['TRP (dBm)'], mode='lines+markers', name=active_date))
            fig.update_layout(title="LTE TRP Trend", plot_bgcolor="#e9f1ff", paper_bgcolor="#e9f1ff")
            st.plotly_chart(fig, use_container_width=True)
            
    elif active_validation_type == "Pixel Phone S4 with Dipoles":
        df_pixel = load_pixel_phone_data("Satimo 1 Chamber - Pixel Phone S4 with Dipoles - Satimo1.csv")
        if df_pixel is not None:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_pixel['Frequency (MHz)'], y=df_pixel['Calculated TRP (dBm)'], name="Calculated", line=dict(color='red', dash='dash')))
            fig.add_trace(go.Scatter(x=df_pixel['Frequency (MHz)'], y=df_pixel['Measured TRP (dBm)'], name="Measured", line=dict(color='#022af2')))
            st.plotly_chart(fig, use_container_width=True)
    
    # ... Other active types follow your logic pattern
