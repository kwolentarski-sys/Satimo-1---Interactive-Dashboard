import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Satimo Dashboard", layout="wide")

# Custom CSS for Sidebar Background and styling
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            background-color: #cbcbcb;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- SIDEBAR CONTROLS ---
st.sidebar.markdown('<h2 style="color:#022af2; font-size: 32px;">Dashboard Controls</h2>', unsafe_allow_html=True)

# 1. Chamber Selection
st.sidebar.markdown("**Select Chamber:**")
selected_chamber = st.sidebar.selectbox(
    "Select Chamber:",
    ["Satimo 1", "Satimo 2", "Satimo 3"],
    label_visibility="collapsed",
    key="chamber_selector"
)

# App Title: Dynamic based on Chamber Selection
st.markdown(
    f'<h1 style="white-space: nowrap; overflow: hidden; text-overflow: clip; font-size: 34px;">{selected_chamber} Chamber Performance - Interactive Dashboard</h1>', 
    unsafe_allow_html=True
)

# 2. Passive Selection
st.sidebar.markdown("**Select Passive Validation Type:**")
validation_type = st.sidebar.selectbox(
    "Select Passive Validation Type:",
    ["None", "Yearly", "Quarterly", "Monthly", "Wideband Dipole - Chamber Comparison"],
    label_visibility="collapsed",
    key="passive_selector"
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

# [Rest of your loading functions go here, exactly as in Baseline_app]
# (load_active_trp_data, load_active_tis_data, load_pixel_phone_data, load_phantom_wrist_data)

# --- SIDEBAR LOGIC CONTINUED ---

selected_unit = None
df_passive = None

if validation_type != "None":
    # File map for Satimo 1
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
        selected_unit = st.sidebar.selectbox(label_text, units, label_visibility="collapsed", key="unit_selector")

st.sidebar.markdown("**Select Active Validation Type:**")
is_active_disabled = (validation_type != "None")
active_validation_type = st.sidebar.selectbox(
    "Select Active Validation Type:",
    ["None", "LTE TRP", "LTE TIS", "Pixel Phone S4 with Dipoles", "Phantom Wrist Dielectrics"],
    label_visibility="collapsed",
    disabled=is_active_disabled,
    key="active_selector"
)

# --- MAIN DASHBOARD RENDERING ---

# Ensure Active Selection triggers correctly for Satimo 1
if not is_active_disabled and active_validation_type != "None":
    # [Insert your Active Selection Graph Logic here]
    pass

# Ensure Passive Selection (Yearly, Quarterly, etc.) triggers correctly
if validation_type != "None" and df_passive is not None and selected_unit:
    subset_p = df_passive[df_passive['Dipole'] == selected_unit].copy()
    if not subset_p.empty:
        # Calculate Deltas
        if validation_type != "Wideband Dipole - Chamber Comparison":
            subset_p['Abs_Diff'] = (subset_p['Reference Efficiency (dB)'] - subset_p['Date Efficiency (dB)']).abs()
            max_val, max_freq = subset_p['Abs_Diff'].max(), subset_p.loc[subset_p['Abs_Diff'].idxmax(), 'Frequency (MHz)']
            st.markdown(f'<p style="font-size: 20px;"><b>Maximum Delta - Reference NIST:</b> {max_val:.2f} dB at {max_freq} MHz</p>', unsafe_allow_html=True)
        
        # Build Figure
        fig_p = go.Figure()
        if validation_type == "Wideband Dipole - Chamber Comparison":
            chamber_styles = {"Satimo 1": "red", "Satimo 2": "#022af2", "Satimo 3": "#2ca02c"}
            for chamber, color in chamber_styles.items():
                ch_data = subset_p[subset_p['Chamber'] == chamber]
                if not ch_data.empty: fig_p.add_trace(go.Scatter(x=ch_data['Frequency (MHz)'], y=ch_data['Efficiency'], mode='lines+markers', name=f"<b>{chamber}</b>", line=dict(color=color, width=2)))
        else:
            date_label_p = str(subset_p["Date_Label"].iloc[0])
            fig_p.add_trace(go.Scatter(x=subset_p['Frequency (MHz)'], y=subset_p['Reference Efficiency (dB)'], mode='lines+markers', name="<b>Reference NIST</b>", line=dict(color='red', width=2, dash='dash')))
            fig_p.add_trace(go.Scatter(x=subset_p['Frequency (MHz)'], y=subset_p['Date Efficiency (dB)'], mode='lines+markers', name=f'<b>{date_label_p}</b>', line=dict(color='#022af2', width=2)))
        
        fig_p.update_layout(title=dict(text=f"<b>{selected_unit} - Passive Trend ({selected_chamber})</b>", x=0.5), height=560, plot_bgcolor="#e9f1ff", paper_bgcolor="#e9f1ff")
        st.plotly_chart(fig_p, use_container_width=True)
