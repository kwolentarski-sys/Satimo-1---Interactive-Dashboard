import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# --- PAGE CONFIGURATION ---
# Updated for Satimo 2
st.set_page_config(page_title="Satimo 2 Dashboard", layout="wide")

# Custom CSS for Sidebar Background and styling
st.markdown(
    """
    <style>
        /* Change Sidebar Background Color to Baseline #cbcbcb */
        [data-testid="stSidebar"] {
            background-color: #cbcbcb;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# App Title: Updated to Satimo 2 and maintained nowrap baseline
st.markdown(
    '<h1 style="white-space: nowrap; overflow: hidden; text-overflow: clip; font-size: 34px;">Satimo 2 Chamber Performance - Interactive Dashboard</h1>', 
    unsafe_allow_html=True
)

# --- DATA LOADING FUNCTIONS ---
# Functions preserved from Satimo 1 baseline for consistent parsing

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
                        if chamber_name == "Satimo2": chamber_name = "Satimo 2"
                        unit_name = str(df_raw.iloc[0, 0]).split(':')[-1].strip()
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
    """Parses Active LTE TRP data file."""
    if not os.path.exists(file_name):
        return None, "3/3/26"
    try:
        df_raw = pd.read_csv(file_name, header=None)
        data = df_raw.iloc[8:, 2:5].copy()
        data.columns = ['Band/Chan', 'Frequency (Mhz)', 'TRP (dBm)']
        data = data.dropna()
        data['Frequency (Mhz)'] = pd.to_numeric(data['Frequency (Mhz)'], errors='coerce')
        data['TRP (dBm)'] = pd.to_numeric(data['TRP (dBm)'], errors='coerce')
        try:
            date_val = str(df_raw.iloc[4, 4]).strip()
        except:
            date_val = "3/3/26"
        return data.dropna(), date_val
    except Exception: return None, "3/3/26"

# --- SIDEBAR CONTROLS ---

st.sidebar.markdown('<h2 style="color:#022af2; font-size: 32px;">Dashboard Controls</h2>', unsafe_allow_html=True)

# 1. Passive Selection
st.sidebar.markdown("**Select Passive Validation Type:**")
validation_type = st.sidebar.selectbox(
    "Select Passive Validation Type:",
    ["None", "Yearly", "Quarterly", "Monthly", "Wideband Dipole - Chamber Comparison"],
    label_visibility="collapsed"
)

# 2. Dynamic Unit Selection (Update file names when Satimo 2 data is ready)
selected_unit = None
df_passive = None
if validation_type != "None":
    passive_files = {
        "Yearly": 'Satimo 2 - Passive - Dipoles Yearly.csv',
        "Quarterly": 'Satimo 2 - Passive - Dipoles Quarterly.csv',
        "Monthly": 'Satimo 2 - Passive - Horns Monthly.csv',
        "Wideband Dipole - Chamber Comparison": 'Wideband Dipole - Chamber Comparison.csv'
    }
    is_comp = (validation_type == "Wideband Dipole - Chamber Comparison")
    df_passive = load_and_clean_data(passive_files.get(validation_type, ""), is_comparison=is_comp)
    
    if df_passive is not None and not df_passive.empty:
        units = df_passive['Dipole'].unique()
        label_text = "Select Dipole:" if validation_type != 'Monthly' else "Select a Horn:"
        st.sidebar.markdown(f"**{label_text}**")
        selected_unit = st.sidebar.selectbox(label_text, units, label_visibility="collapsed")

# 3. Active Selection
st.sidebar.markdown("**Select Active Validation Type:**")
is_active_disabled = (validation_type != "None")
active_validation_type = st.sidebar.selectbox(
    "Select Active Validation Type:",
    ["None", "LTE TRP"],
    label_visibility="collapsed",
    disabled=is_active_disabled,
    index=0 if is_active_disabled else 0 
)

# --- MAIN DASHBOARD LOGIC ---

# 1. Handle Active Selection (Clean Slate for Satimo 2)
if active_validation_type == "LTE TRP" and not is_active_disabled:
    st.markdown('<h3 style="color:#022af2; margin-bottom: 0px;"><b>Quarterly - Active Reference - LTE TRP (Satimo 2)</b></h3>', unsafe_allow_html=True)
    
    active_file = "Satimo 2 - Active - LTE TRP.csv"
    df_active, active_date = load_active_trp_data(active_file)
    
    if df_active is not None and not df_active.empty:
        # TRP TREND GRAPH (Standard UI)
        fig_imei = go.Figure()
        fig_imei.add_trace(go.Scatter(x=df_active['Band/Chan'], y=df_active['TRP (dBm)'], mode='lines+markers', name=f"<b>{active_date}</b>", line=dict(color='#022af2', width=2)))
        
        fig_imei.update_layout(
            title=dict(text="<b>LTE TRP Active Trend - Satimo 2</b>", font=dict(color='black', size=22), x=0.5, xanchor='center'), 
            template="plotly_white", height=450, margin=dict(t=80, b=50, l=50, r=150),
            plot_bgcolor="#e9f1ff", paper_bgcolor="#e9f1ff",
            showlegend=True,
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02, font=dict(color='black', size=18, weight='bold')),
            xaxis=dict(title=dict(text="<b>Band/Chan</b>", font=dict(size=20, color='black')), tickfont=dict(weight='bold', color='black', size=18), showline=True, linewidth=1, linecolor='black', mirror=True, showgrid=True, gridcolor='gray'),
            yaxis=dict(title=dict(text="<b>TRP (dBm)</b>", font=dict(size=20, color='black')), tickfont=dict(weight='bold', color='black', size=18), zeroline=True, zerolinewidth=3, zerolinecolor='black', showline=True, linewidth=1, linecolor='black', mirror=True, showgrid=True, gridcolor='gray')
        )
        st.plotly_chart(fig_imei, use_container_width=True)
    else:
        st.info("Awaiting Satimo 2 Active TRP Data Upload.")

# 2. Handle Passive Selection (Baseline UI)
if validation_type != "None" and df_passive is not None:
    st.markdown(f'<h3 style="color:#022af2;"><b>Satimo 2 - Passive Validation Measurements</b></h3>', unsafe_allow_html=True)
    
    if selected_unit:
        subset_p = df_passive[df_passive['Dipole'] == selected_unit].copy()
        if not subset_p.empty:
            # Baseline metrics logic preserved
            fig_p = go.Figure()
            date_label_p = str(subset_p["Date_Label"].iloc[0])
            fig_p.add_trace(go.Scatter(x=subset_p['Frequency (MHz)'], y=subset_p['Reference Efficiency (dB)'], mode='lines+markers', name="<b>Reference Data - NIST</b>", line=dict(color='red', width=2, dash='dash')))
            fig_p.add_trace(go.Scatter(x=subset_p['Frequency (MHz)'], y=subset_p['Date Efficiency (dB)'], mode='lines+markers', name=f'<b>{date_label_p}</b>', line=dict(color='#022af2', width=2)))
            
            min_f_p, max_f_p = int(subset_p['Frequency (MHz)'].min()), int(subset_p['Frequency (MHz)'].max())
            fig_p.update_layout(
                title=dict(text=f"<b>{selected_unit}</b> <span style='font-size: 20px;'>({min_f_p}-{max_f_p} MHz)</span> <b>- Passive Trend</b>", font=dict(size=26), x=0.5, xanchor='center'),
                xaxis_title="<b>Frequency (MHz)</b>", yaxis_title="<b>Efficiency (dB)</b>",
                hovermode="x unified", template="plotly_white", height=560, plot_bgcolor="#e9f1ff", paper_bgcolor="#e9f1ff",
                legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02, font=dict(size=18, weight='bold')), margin=dict(t=100, b=50, l=50, r=150),
                xaxis=dict(title_font=dict(color='black', size=20), tickfont=dict(color='black', size=18, weight='bold'), showgrid=True, gridcolor='silver', gridwidth=1, showline=True, linewidth=1, linecolor='black', mirror=True),
                yaxis=dict(title_font=dict(color='black', size=20), tickfont=dict(color='black', size=18, weight='bold'), showgrid=True, gridcolor='silver', gridwidth=1, zeroline=True, zerolinewidth=3, zerolinecolor='black', showline=True, linewidth=1, linecolor='black', mirror=True)
            )
            st.plotly_chart(fig_p, use_container_width=True)