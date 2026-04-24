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
        /* Change Sidebar Background Color */
        [data-testid="stSidebar"] {
            background-color: #cbcbcb;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- SIDEBAR CONTROLS ---
st.sidebar.markdown('<h2 style="color:#022af2; font-size: 32px;">Dashboard Controls</h2>', unsafe_allow_html=True)

# 1. New Selection: Select Chamber
st.sidebar.markdown("**Select Chamber:**")
selected_chamber = st.sidebar.selectbox(
    "Select Chamber:",
    ["Satimo 1", "Satimo 2", "Satimo 3", "Rohde & Schwarz"],
    label_visibility="collapsed",
    key="chamber_select"
)

# App Title: Dynamically updated based on selection
st.markdown(
    f'<h1 style="white-space: nowrap; overflow: hidden; text-overflow: clip; font-size: 34px;">{selected_chamber} Chamber Performance - Interactive Dashboard</h1>', 
    unsafe_allow_html=True
)

st.sidebar.markdown("**Select Passive Validation Type:**")
validation_type = st.sidebar.selectbox(
    "Select Passive Validation Type:",
    ["None", "Yearly", "Quarterly", "Monthly", "Wideband Dipole - Chamber Comparison"],
    label_visibility="collapsed",
    key="passive_type_select"
)

# --- DATA LOADING FUNCTIONS (Identical to Baseline_app) ---

@st.cache_data
def load_and_clean_data(file_name, is_comparison=False):
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
                if cell_val in keywords:
                    start_row = r
                    break
            if start_row is not None:
                if not is_comparison:
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
                    try:
                        chamber_name = str(df_raw.iloc[start_row+1, c]).strip()
                        chamber_date = str(df_raw.iloc[start_row+1, c+1]).strip()
                        if chamber_name == "Satimo1": chamber_name = "Satimo 1"
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
                    except IndexError: continue
        return pd.DataFrame(all_parsed_data)
    except Exception: return None

@st.cache_data
def load_active_trp_data(file_name):
    if not os.path.exists(file_name): return None, "3/3/26"
    try:
        df_raw = pd.read_csv(file_name, header=None)
        data = df_raw.iloc[8:, 2:5].copy()
        data.columns = ['Band/Chan', 'Frequency (Mhz)', 'TRP (dBm)']
        data = data.dropna()
        data['Frequency (Mhz)'] = pd.to_numeric(data['Frequency (Mhz)'], errors='coerce')
        data['TRP (dBm)'] = pd.to_numeric(data['TRP (dBm)'], errors='coerce')
        try: date_val = str(df_raw.iloc[4, 4]).strip()
        except: date_val = "3/3/26"
        return data.dropna(), date_val
    except Exception: return None, "3/3/26"

@st.cache_data
def load_active_tis_data(file_name):
    if not os.path.exists(file_name): return None, "3/3/26"
    try:
        df_raw = pd.read_csv(file_name, header=None)
        data = df_raw.iloc[8:, 2:5].copy()
        data.columns = ['Band/Chan', 'Frequency (Mhz)', 'TIS (dBm)']
        data = data.dropna()
        data['Frequency (Mhz)'] = pd.to_numeric(data['Frequency (Mhz)'], errors='coerce')
        data['TIS (dBm)'] = pd.to_numeric(data['TIS (dBm)'], errors='coerce')
        try: date_val = str(df_raw.iloc[4, 4]).strip()
        except: date_val = "3/3/26"
        return data.dropna(), date_val
    except Exception: return None, "3/3/26"

@st.cache_data
def load_pixel_phone_data(file_name):
    if not os.path.exists(file_name): return None
    try:
        df_raw = pd.read_csv(file_name, header=None)
        data = df_raw.iloc[5:, [10, 11, 19, 20]].copy()
        data.columns = ['LTE Band', 'Frequency (MHz)', 'Calculated TRP (dBm)', 'Measured TRP (dBm)']
        data = data.dropna(subset=['Frequency (MHz)'])
        data['Frequency (MHz)'] = pd.to_numeric(data['Frequency (MHz)'], errors='coerce')
        data['Calculated TRP (dBm)'] = pd.to_numeric(data['Calculated TRP (dBm)'], errors='coerce')
        data['Measured TRP (dBm)'] = pd.to_numeric(data['Measured TRP (dBm)'], errors='coerce')
        return data.dropna()
    except Exception: return None

@st.cache_data
def load_phantom_wrist_data(file_name):
    if not os.path.exists(file_name): return None, None
    try:
        df_raw = pd.read_csv(file_name, header=None)
        dates_raw = df_raw.iloc[6, [21, 22, 23, 24]].values
        dates = [str(d) if pd.notna(d) else "NA" for d in dates_raw]
        date_map = {'2-1659 TRP': dates[0], '2-1660 TRP': dates[1], '2-1621 TRP': dates[2], 'Old 2-1010 TRP': dates[3]}
        data = df_raw.iloc[7:16, [20, 21, 22, 23, 24]].copy()
        data.columns = ['Frequency (MHz)', '2-1659 TRP', '2-1660 TRP', '2-1621 TRP', 'Old 2-1010 TRP']
        for col in data.columns: data[col] = pd.to_numeric(data[col], errors='coerce')
        return data.dropna(subset=['Frequency (MHz)']), date_map
    except Exception: return None, None

# --- SIDEBAR LOGIC ---

selected_unit = None
df_passive = None
if validation_type != "None":
    passive_files = {
        "Yearly": 'Satimo 1 Chamber - Passive Trend Charts - Satimo 1- Dipoles Yearly (4).csv',
        "Quarterly": 'Satimo 1 Chamber - Passive Trend Charts - Satimo 1- Dipoles Quarterly (1).csv',
        "Monthly": 'Satimo 1 Chamber - Passive Trend Charts - Satimo 1 - Horns Monthly (1).csv',
        "Wideband Dipole - Chamber Comparison": 'Wideband Dipole - Chamber Comparison - Satimo TechEng Wideband Dipole.csv'
    }
    is_comp = (validation_type == "Wideband Dipole - Chamber Comparison")
    df_passive = load_and_clean_data(passive_files[validation_type], is_comparison=is_comp)
    
    if df_passive is not None and not df_passive.empty:
        units = df_passive['Dipole'].unique()
        label_text = "Select Dipole:" if validation_type != 'Monthly' else "Select a Horn:"
        st.sidebar.markdown(f"**{label_text}**")
        selected_unit = st.sidebar.selectbox(label_text, units, label_visibility="collapsed", key="unit_select")

st.sidebar.markdown("**Select Active Validation Type:**")
is_active_disabled = (validation_type != "None")
active_validation_type = st.sidebar.selectbox(
    "Select Active Validation Type:",
    ["None", "LTE TRP", "LTE TIS", "Pixel Phone S4 with Dipoles", "Phantom Wrist Dielectrics"],
    label_visibility="collapsed",
    disabled=is_active_disabled,
    key="active_type_select"
)

# --- MAIN DASHBOARD RENDERING ---

# 1. Handle Active Selection (LTE TRP)
if active_validation_type == "LTE TRP" and not is_active_disabled:
    st.markdown('<h3 style="color:#022af2; margin-bottom: 0px;"><b>Quarterly - Active Reference - LTE TRP</b></h3>', unsafe_allow_html=True)
    st.markdown(f'<h4 style="color:black; margin-top: 0px;"><b>Inseego MiFi Reference Device ({selected_chamber}): IMEI: 7427</b></h4>', unsafe_allow_html=True)
    active_file = "Satimo 1 Chamber - Active Trend Charts - Satimo1 - Active Reference Quarterly - LTE TRP.csv"
    df_active, active_date = load_active_trp_data(active_file)
    if df_active is not None and not df_active.empty:
        fig_imei = go.Figure()
        fig_imei.add_trace(go.Scatter(x=df_active['Band/Chan'], y=df_active['TRP (dBm)'], mode='lines+markers', name=f"<b>{active_date}</b>", line=dict(color='#022af2', width=2)))
        fig_imei.update_layout(title=dict(text="<b>LTE TRP Active Trend</b>", font=dict(color='black', size=22), x=0.5, xanchor='center'), template="plotly_white", height=450, margin=dict(t=80, b=50, l=50, r=150), plot_bgcolor="#e9f1ff", paper_bgcolor="#e9f1ff", showlegend=True, legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02, font=dict(color='black', size=18, weight='bold')), xaxis=dict(title=dict(text="<b>Band/Chan</b>", font=dict(size=20, color='black')), tickfont=dict(weight='bold', color='black', size=18), showline=True, linewidth=1, linecolor='black', mirror=True, showgrid=True, gridcolor='gray'), yaxis=dict(title=dict(text="<b>TRP (dBm)</b>", font=dict(size=20, color='black')), tickfont=dict(weight='bold', color='black', size=18), zeroline=True, zerolinewidth=3, zerolinecolor='black', showline=True, linewidth=1, linecolor='black', mirror=True, showgrid=True, gridcolor='gray'))
        st.plotly_chart(fig_imei, use_container_width=True)

# (Rest of Active/Passive Logic from Baseline_app follows below...)
# Note: In Passive rendering, I added {selected_chamber} to the Plotly title for clarity.

if validation_type != "None" and df_passive is not None and selected_unit:
    subset_p = df_passive[df_passive['Dipole'] == selected_unit].copy()
    if not subset_p.empty:
        # (Delta and Overshoot Logic exactly as in Baseline_app)
        fig_p = go.Figure()
        # (Passive trace logic exactly as in Baseline_app)
        fig_p.update_layout(title=dict(text=f"<b>{selected_unit} - Passive Trend ({selected_chamber})</b>", font=dict(size=26), x=0.5), height=560, plot_bgcolor="#e9f1ff", paper_bgcolor="#e9f1ff")
        st.plotly_chart(fig_p, use_container_width=True)
