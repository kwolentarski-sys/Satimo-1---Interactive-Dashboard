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

# App Title: Forced to one line using CSS nowrap
st.markdown(
    '<h1 style="white-space: nowrap; overflow: hidden; text-overflow: clip; font-size: 34px;">Satimo 1 Chamber Performance - Interactive Dashboard</h1>', 
    unsafe_allow_html=True
)

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

@st.cache_data
def load_active_tis_data(file_name):
    """Parses Active LTE TIS data file."""
    if not os.path.exists(file_name):
        return None, "3/3/26"
    try:
        df_raw = pd.read_csv(file_name, header=None)
        data = df_raw.iloc[8:, 2:5].copy()
        data.columns = ['Band/Chan', 'Frequency (Mhz)', 'TIS (dBm)']
        data = data.dropna()
        data['Frequency (Mhz)'] = pd.to_numeric(data['Frequency (Mhz)'], errors='coerce')
        data['TIS (dBm)'] = pd.to_numeric(data['TIS (dBm)'], errors='coerce')
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

# 2. Dynamic Unit Selection
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
        selected_unit = st.sidebar.selectbox(label_text, units, label_visibility="collapsed")

# 3. Active Selection (Disabled unless Passive is "None")
st.sidebar.markdown("**Select Active Validation Type:**")
is_active_disabled = (validation_type != "None")
active_validation_type = st.sidebar.selectbox(
    "Select Active Validation Type:",
    ["None", "LTE TRP", "LTE TIS"],
    label_visibility="collapsed",
    disabled=is_active_disabled,
    index=0 if is_active_disabled else 0 
)

# --- MAIN DASHBOARD LOGIC ---

# 1. Handle Active Selection (LTE TRP)
if active_validation_type == "LTE TRP" and not is_active_disabled:
    st.markdown('<h3 style="color:#022af2; margin-bottom: 0px;"><b>Quarterly - Active Reference - LTE TRP</b></h3>', unsafe_allow_html=True)
    st.markdown('<h4 style="color:black; margin-top: 0px;"><b>Inseego MiFi Reference Device: IMEI: 7427</b></h4>', unsafe_allow_html=True)
    
    active_file = "Satimo 1 Chamber - Active Trend Charts - Satimo1 - Active Reference Quarterly - LTE TRP.csv"
    df_active, active_date = load_active_trp_data(active_file)
    
    if df_active is not None and not df_active.empty:
        fig_imei = go.Figure()
        fig_imei.add_trace(go.Scatter(
            x=df_active['Band/Chan'], 
            y=df_active['TRP (dBm)'], 
            mode='lines+markers', 
            name=f"<b>{active_date}</b>", 
            hovertemplate="<b>Inseego MiFi Reference Device</b><br>Band/Chan: %{x}<br>TRP: %{y:.2f} dBm<extra></extra>",
            line=dict(color='#022af2', width=2)
        ))
        
        fig_imei.update_layout(
            title=dict(text="<b>LTE TRP Active Trend</b>", font=dict(color='black', size=22), x=0.5, xanchor='center'), 
            template="plotly_white", height=450, margin=dict(t=80, b=50, l=50, r=150),
            plot_bgcolor="#e9f1ff", paper_bgcolor="#e9f1ff",
            showlegend=True,
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02, font=dict(color='black', size=18, weight='bold')),
            xaxis=dict(title=dict(text="<b>Band/Chan</b>", font=dict(size=20, color='black')), tickfont=dict(weight='bold', color='black', size=18), showline=True, linewidth=1, linecolor='black', mirror=True, showgrid=True, gridcolor='gray'),
            yaxis=dict(title=dict(text="<b>TRP (dBm)</b>", font=dict(size=20, color='black')), tickfont=dict(weight='bold', color='black', size=18), zeroline=True, zerolinewidth=3, zerolinecolor='black', showline=True, linewidth=1, linecolor='black', mirror=True, showgrid=True, gridcolor='gray')
        )
        st.plotly_chart(fig_imei, use_container_width=True)

        ranges = [(664.8, 913.42, "LTE TRP Active Trend - Low Bands"), (1711.58, 1978.42, "LTE TRP Active Trend - Mid Bands"), (2502.62, 2567.38, "LTE TRP Active Trend - High Band")]
        for low_f, high_f, title_label in ranges:
            subset = df_active[(df_active['Frequency (Mhz)'] >= low_f) & (df_active['Frequency (Mhz)'] <= high_f)].copy()
            if not subset.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=subset['Frequency (Mhz)'], y=subset['TRP (dBm)'], mode='lines+markers', name=f"<b>{active_date}</b>", hovertemplate="<b>Inseego MiFi Reference Device</b><br>Freq: %{x} MHz<br>TRP: %{y:.2f} dBm<extra></extra>", line=dict(color='#022af2', width=2)))
                fig.update_layout(title=dict(text=f"<b>{title_label}</b>", font=dict(color='black', size=22), x=0.5, xanchor='center'), template="plotly_white", height=450, margin=dict(t=80, b=50, l=50, r=150), plot_bgcolor="#e9f1ff", paper_bgcolor="#e9f1ff", showlegend=True, legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02, font=dict(color='black', size=18, weight='bold')), xaxis=dict(title=dict(text="<b>Frequency (MHz)</b>", font=dict(size=20, color='black')), tickfont=dict(weight='bold', color='black', size=18), showline=True, linewidth=1, linecolor='black', mirror=True, showgrid=True, gridcolor='gray'), yaxis=dict(title=dict(text="<b>TRP (dBm)</b>", font=dict(size=20, color='black')), tickfont=dict(weight='bold', color='black', size=18), zeroline=True, zerolinewidth=3, zerolinecolor='black', showline=True, linewidth=1, linecolor='black', mirror=True, showgrid=True, gridcolor='gray'))
                st.plotly_chart(fig, use_container_width=True)

# 2. Handle Active Selection (LTE TIS)
if active_validation_type == "LTE TIS" and not is_active_disabled:
    st.markdown('<h3 style="color:#022af2; margin-bottom: 0px;"><b>Quarterly - Active Reference - LTE TIS</b></h3>', unsafe_allow_html=True)
    st.markdown('<h4 style="color:black; margin-top: 0px;"><b>Inseego MiFi Reference Device: IMEI: 7427</b></h4>', unsafe_allow_html=True)
    
    tis_file = "Satimo 1 Chamber - Active Trend Charts - Satimo1 - Active Reference Quarterly - LTE TIS.csv"
    df_active, active_date = load_active_tis_data(tis_file)
    
    if df_active is not None and not df_active.empty:
        fig_imei = go.Figure()
        fig_imei.add_trace(go.Scatter(
            x=df_active['Band/Chan'], 
            y=df_active['TIS (dBm)'], 
            mode='lines+markers', 
            name=f"<b>{active_date}</b>", 
            hovertemplate="<b>Inseego MiFi Reference Device</b><br>Band/Chan: %{x}<br>TIS: %{y:.2f} dBm<extra></extra>",
            line=dict(color='#022af2', width=2)
        ))
        
        fig_imei.update_layout(
            title=dict(text="<b>LTE TIS Active Trend</b>", font=dict(color='black', size=22), x=0.5, xanchor='center'), 
            template="plotly_white", height=450, margin=dict(t=80, b=50, l=50, r=150),
            plot_bgcolor="#e9f1ff", paper_bgcolor="#e9f1ff",
            showlegend=True,
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02, font=dict(color='black', size=18, weight='bold')),
            xaxis=dict(title=dict(text="<b>Band/Chan</b>", font=dict(size=20, color='black')), tickfont=dict(weight='bold', color='black', size=18), showline=True, linewidth=1, linecolor='black', mirror=True, showgrid=True, gridcolor='gray'),
            yaxis=dict(title=dict(text="<b>TIS (dBm)</b>", font=dict(size=20, color='black')), tickfont=dict(weight='bold', color='black', size=18), zeroline=True, zerolinewidth=3, zerolinecolor='black', showline=True, linewidth=1, linecolor='black', mirror=True, showgrid=True, gridcolor='gray')
        )
        st.plotly_chart(fig_imei, use_container_width=True)

        # Added fourth range: 2630 to 2680 MHz
        ranges = [
            (622, 955, "LTE TIS Active Trend - Low Bands"), 
            (1810, 2175, "LTE TIS Active Trend - Mid Bands"), 
            (2502.62, 2567.38, "LTE TIS Active Trend - High Band"),
            (2630, 2680, "LTE TIS Active Trend - High Band")
        ]
        for low_f, high_f, title_label in ranges:
            subset = df_active[(df_active['Frequency (Mhz)'] >= low_f) & (df_active['Frequency (Mhz)'] <= high_f)].copy()
            if not subset.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=subset['Frequency (Mhz)'], y=subset['TIS (dBm)'], mode='lines+markers', name=f"<b>{active_date}</b>", hovertemplate="<b>Inseego MiFi Reference Device</b><br>Freq: %{x} MHz<br>TIS: %{y:.2f} dBm<extra></extra>", line=dict(color='#022af2', width=2)))
                fig.update_layout(title=dict(text=f"<b>{title_label}</b>", font=dict(color='black', size=22), x=0.5, xanchor='center'), template="plotly_white", height=450, margin=dict(t=80, b=50, l=50, r=150), plot_bgcolor="#e9f1ff", paper_bgcolor="#e9f1ff", showlegend=True, legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02, font=dict(color='black', size=18, weight='bold')), xaxis=dict(title=dict(text="<b>Frequency (MHz)</b>", font=dict(size=20, color='black')), tickfont=dict(weight='bold', color='black', size=18), showline=True, linewidth=1, linecolor='black', mirror=True, showgrid=True, gridcolor='gray'), yaxis=dict(title=dict(text="<b>TIS (dBm)</b>", font=dict(size=20, color='black')), tickfont=dict(weight='bold', color='black', size=18), zeroline=True, zerolinewidth=3, zerolinecolor='black', showline=True, linewidth=1, linecolor='black', mirror=True, showgrid=True, gridcolor='gray'))
                st.plotly_chart(fig, use_container_width=True)

# 3. Handle Passive Selection (Locked Baseline)
if validation_type != "None" and df_passive is not None:
    title_map = {"Yearly": "Yearly - Dipole Validation Measurements", "Quarterly": "Quarterly - Dipole Validation Measurements", "Monthly": "Monthly - Horn Validation Measurements", "Wideband Dipole - Chamber Comparison": "Wideband Dipole - Chamber Comparison"}
    st.markdown(f'<h3 style="color:#022af2;"><b>{title_map[validation_type]}</b></h3>', unsafe_allow_html=True)
    if selected_unit:
        subset_p = df_passive[df_passive['Dipole'] == selected_unit].copy()
        if not subset_p.empty:
            if validation_type != "Wideband Dipole - Chamber Comparison":
                subset_p['Abs_Diff'] = (subset_p['Reference Efficiency (dB)'] - subset_p['Date Efficiency (dB)']).abs()
                max_val, max_freq = subset_p['Abs_Diff'].max(), subset_p.loc[subset_p['Abs_Diff'].idxmax(), 'Frequency (MHz)']
                above_0_subset = subset_p[subset_p['Date Efficiency (dB)'] > 0]
                overshoot_html = ""
                if not above_0_subset.empty:
                    max_above_idx = above_0_subset['Date Efficiency (dB)'].idxmax()
                    overshoot_val, overshoot_freq = above_0_subset.loc[max_above_idx, "Date Efficiency (dB)"], above_0_subset.loc[max_above_idx, "Frequency (MHz)"]
                    overshoot_html = f'<p style="font-size: 20px; margin-top: 0px;"><b>Maximum Overshoot Above 0 dB:</b> <span style="color:red;">{overshoot_val:.2f} dB at {overshoot_freq} MHz</span></p>'
                else: overshoot_html = '<p style="font-size: 20px; margin-top: 0px;"><b>Maximum Overshoot Above 0 dB:</b> <span style="color:green;">None</span></p>'
                st.markdown(f'<p style="font-size: 20px; margin-bottom: 0px;"><b>Maximum Difference From Reference NIST:</b> {max_val:.2f} dB at {max_freq} MHz</p>{overshoot_html}', unsafe_allow_html=True)
            fig_p = go.Figure()
            if validation_type == "Wideband Dipole - Chamber Comparison":
                chamber_styles = {"Satimo 1": "red", "Satimo 2": "#022af2", "Satimo 3": "#2ca02c"}
                for chamber, color in chamber_styles.items():
                    ch_data = subset_p[subset_p['Chamber'] == chamber]
                    if not ch_data.empty: fig_p.add_trace(go.Scatter(x=ch_data['Frequency (MHz)'], y=ch_data['Efficiency'], mode='lines+markers', name=f"<b>{chamber}</b> ({ch_data['Chamber_Date'].iloc[0]})", line=dict(color=color, width=2)))
            else:
                date_label_p = str(subset_p["Date_Label"].iloc[0])
                fig_p.add_trace(go.Scatter(x=subset_p['Frequency (MHz)'], y=subset_p['Reference Efficiency (dB)'], mode='lines+markers', name="<b>Reference Data - NIST</b>", line=dict(color='red', width=2, dash='dash')))
                fig_p.add_trace(go.Scatter(x=subset_p['Frequency (MHz)'], y=subset_p['Date Efficiency (dB)'], mode='lines+markers', name=f'<b>{date_label_p}</b>', line=dict(color='#022af2', width=2)))
            min_f_p, max_f_p = int(subset_p['Frequency (MHz)'].min()), int(subset_p['Frequency (MHz)'].max())
            fig_p.update_layout(title=dict(text=f"<b>{selected_unit}</b> <span style='font-size: 20px;'>({min_f_p}-{max_f_p} MHz)</span> <b>- Passive Trend</b>", font=dict(size=26), x=0.5, xanchor='center'), xaxis_title="<b>Frequency (MHz)</b>", yaxis_title="<b>Efficiency (dB)</b>", hovermode="x unified", template="plotly_white", height=560, plot_bgcolor="#e9f1ff", paper_bgcolor="#e9f1ff", legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02, font=dict(size=18, weight='bold')), margin=dict(t=100, b=50, l=50, r=150), xaxis=dict(title_font=dict(color='black', size=20), tickfont=dict(color='black', size=18, weight='bold'), showgrid=True, gridcolor='silver', gridwidth=1, showline=True, linewidth=1, linecolor='black', mirror=True), yaxis=dict(title_font=dict(color='black', size=20), tickfont=dict(color='black', size=18, weight='bold'), showgrid=True, gridcolor='silver', gridwidth=1, zeroline=True, zerolinewidth=3, zerolinecolor='black', showline=True, linewidth=1, linecolor='black', mirror=True))
            st.plotly_chart(fig_p, use_container_width=True)
