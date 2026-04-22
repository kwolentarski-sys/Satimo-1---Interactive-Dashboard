import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Satimo 1 Dashboard", layout="wide")

# App Title: Forced to one line using CSS nowrap
st.markdown(
    '<h1 style="white-space: nowrap; overflow: hidden; text-overflow: clip; font-size: 34px;">Satimo 1 Chamber Performance - Interactive Dashboard</h1>', 
    unsafe_allow_html=True
)

# 1. Sidebar - Dashboard Controls
st.sidebar.markdown('<h2 style="color:#022af2;">Dashboard Controls</h2>', unsafe_allow_html=True)

validation_type = st.sidebar.selectbox(
    "Select Passive Validation Type:",
    ["Yearly", "Quarterly", "Monthly", "Wideband Dipole - Chamber Comparison"]
)

# Dynamic Sub-title based on selection
title_map = {
    "Yearly": "Yearly - Passive Dipole Validation Measurements",
    "Quarterly": "Quarterly - Passive Dipole Validation Measurements",
    "Monthly": "Monthly - Passive Horn Validation Measurements",
    "Wideband Dipole - Chamber Comparison": "Wideband Dipole - Chamber Comparison"
}
st.markdown(f'<h3 style="color:#022af2;"><b>{title_map[validation_type]}</b></h3>', unsafe_allow_html=True)

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
                    # Standard 3-column group (ID, Reference, Measured)
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
                    # Comparison 2-column format (Frequency, Efficiency)
                    try:
                        chamber_name = str(df_raw.iloc[start_row+1, c]).strip()
                        chamber_date = str(df_raw.iloc[start_row+1, c+1]).strip()
                        if chamber_name == "Satimo1": chamber_name = "Satimo 1"
                        
                        # Extraction and rename for Proxicast Dipole #4
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
    except Exception as e:
        st.error(f"Error parsing file: {e}")
        return None

# Mapping files
files = {
    "Yearly": 'Satimo 1 Chamber - Passive Trend Charts - Satimo 1- Dipoles Yearly (4).csv',
    "Quarterly": 'Satimo 1 Chamber - Passive Trend Charts - Satimo 1- Dipoles Quarterly (1).csv',
    "Monthly": 'Satimo 1 Chamber - Passive Trend Charts - Satimo 1 - Horns Monthly (1).csv',
    "Wideband Dipole - Chamber Comparison": 'Wideband Dipole - Chamber Comparison - Satimo TechEng Wideband Dipole.csv'
}

is_comp = (validation_type == "Wideband Dipole - Chamber Comparison")
df = load_and_clean_data(files[validation_type], is_comparison=is_comp)

if df is not None and not df.empty:
    if is_comp:
        units = df['Dipole'].unique()
        selected_unit = st.sidebar.selectbox("Select Dipole:", units)
        subset = df[df['Dipole'] == selected_unit].copy()
        unit_display_name = selected_unit
    else:
        units = df['Dipole'].unique()
        selected_unit = st.sidebar.selectbox(f"Select a {'Horn' if validation_type == 'Monthly' else 'Dipole'}:", units)
        subset = df[df['Dipole'] == selected_unit].copy()
        if not subset.empty:
            date_label = subset["Date_Label"].iloc[0]
            unit_display_name = selected_unit
        else:
            subset = pd.DataFrame()

    if not subset.empty:
        # Metrics: Calculations only for non-comparison types
        if not is_comp:
            subset['Abs_Diff'] = (subset['Reference Efficiency (dB)'] - subset['Date Efficiency (dB)']).abs()
            max_val = subset['Abs_Diff'].max()
            max_diff_idx = subset['Abs_Diff'].idxmax()
            max_freq = subset.loc[max_diff_idx, 'Frequency (MHz)']
            above_0_subset = subset[subset['Date Efficiency (dB)'] > 0]
            
            st.write(f"**Maximum Difference From Reference NIST:** {max_val:.2f} dB at {max_freq} MHz")
            if not above_0_subset.empty:
                max_above_idx = above_0_subset['Date Efficiency (dB)'].idxmax()
                st.markdown(f'**Maximum Overshoot Above 0 dB:** <span style="color:red;">{above_0_subset.loc[max_above_idx, "Date Efficiency (dB)"]:.2f} dB at {above_0_subset.loc[max_above_idx, "Frequency (MHz)"]} MHz</span>', unsafe_allow_html=True)
            else: 
                st.markdown('**Maximum Overshoot Above 0 dB:** <span style="color:green;">None</span>', unsafe_allow_html=True)
        
        fig = go.Figure()
        
        if is_comp:
            chamber_styles = {
                "Satimo 1": {"color": "red", "dash": "solid"},
                "Satimo 2": {"color": "#022af2", "dash": "solid"},
                "Satimo 3": {"color": "#2ca02c", "dash": "solid"}
            }
            
            for chamber in ["Satimo 1", "Satimo 2", "Satimo 3"]:
                ch_data = subset[subset['Chamber'] == chamber]
                if not ch_data.empty:
                    ch_date = ch_data['Chamber_Date'].iloc[0]
                    style = chamber_styles.get(chamber, {"color": "gray", "dash": "solid"})
                    fig.add_trace(go.Scatter(
                        x=ch_data['Frequency (MHz)'], 
                        y=ch_data['Efficiency'],
                        mode='lines+markers',
                        name=f"<b>{chamber}</b> ({ch_date})",
                        line=dict(color=style['color'], width=2, dash=style['dash'])
                    ))
        else:
            fig.add_trace(go.Scatter(
                x=subset['Frequency (MHz)'], 
                y=subset['Reference Efficiency (dB)'], 
                mode='lines+markers', 
                name="<b>Reference Data - NIST</b>&nbsp;&nbsp;&nbsp;", 
                line=dict(color='red', width=2, dash='dash')
            ))
            fig.add_trace(go.Scatter(
                x=subset['Frequency (MHz)'], 
                y=subset['Date Efficiency (dB)'], 
                mode='lines+markers', 
                name=f'<b>{date_label}</b>', 
                line=dict(color='#022af2', width=2)
            ))
        
        min_f = int(subset['Frequency (MHz)'].min())
        max_f = int(subset['Frequency (MHz)'].max())
        
        # Define background color based on selection
        bg_color = "#e9f1ff" if not is_comp else "white"

        fig.update_layout(
            title=dict(text=f"<b>{unit_display_name}</b> <span style='font-size: 20px;'>({min_f}-{max_f} MHz)</span>", font=dict(size=30)),
            xaxis_title="<b>Frequency (MHz)</b>", yaxis_title="<b>Efficiency (dB)</b>",
            hovermode="x unified", template="plotly_white", height=560,
            plot_bgcolor=bg_color,
            paper_bgcolor=bg_color,
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02, font=dict(size=16)),
            margin=dict(t=100, b=50, l=50, r=150),
            xaxis=dict(title_font=dict(color='black', size=20), tickfont=dict(color='black', size=14, weight='bold'), showgrid=True, gridcolor='silver', gridwidth=1, showline=True, linewidth=1, linecolor='black', mirror=True),
            yaxis=dict(title_font=dict(color='black', size=20), tickfont=dict(color='black', size=14, weight='bold'), showgrid=True, gridcolor='silver', gridwidth=1, zeroline=True, zerolinewidth=3, zerolinecolor='black', showline=True, linewidth=1, linecolor='black', mirror=True)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No matching frequency data found for this selection.")
else:
    st.error(f"Please ensure the data files are uploaded to the directory.")
