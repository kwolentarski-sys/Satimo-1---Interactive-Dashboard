import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Satimo 1 Dashboard", layout="wide")

# App Title: Forced to one line using CSS nowrap
st.markdown(
    '<h1 style="white-space: nowrap; overflow: hidden; text-overflow: clip;">Satimo 1 Chamber - Interactive Dashboard</h1>', 
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
                        val_id, val_ref, val_meas = str(row['ID_Col']).strip(), str(row['Ref_Col']).strip(), str(row['Meas_Col']).strip()
                        if val_id.startswith(('SD', 'WD', 'SH')) and len(val_id) > 2:
                            current_unit, current_date = val_id, (val_meas if val_meas != 'nan' else 'Current Date')
                            continue
                        if current_unit:
                            try:
                                all_parsed_data.append({'Dipole': current_unit, 'Date_Label': current_date, 'Frequency (MHz)': float(val_id), 'Reference Efficiency (dB)': float(val_ref), 'Date Efficiency (dB)': float(val_meas)})
                            except ValueError: pass
                else:
                    # Comparison 2-column format (Frequency, Efficiency)
                    chamber_name = str(df_raw.iloc[start_row+1, c]).strip()
                    if chamber_name == "Satimo1": chamber_name = "Satimo 1"
                    
                    unit_name = str(df_raw.iloc[0, 0]).split(':')[-1].strip()
                    data_cols = df_raw.iloc[start_row+2:, c:c+2].copy()
                    data_cols.columns = ['Freq_Col', 'Eff_Col']
                    for _, row in data_cols.iterrows():
                        try:
                            all_parsed_data.append({'Dipole': unit_name, 'Chamber': chamber_name, 'Frequency (MHz)': float(row['Freq_Col']), 'Efficiency': float(row['Eff_Col'])})
                        except ValueError: pass
        return pd.DataFrame(all_parsed_data)
    except Exception: return None

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
        date_label, unit_display_name = subset["Date_Label"].iloc[0], selected_unit

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
        
        # 3. Build Interactive Plotly Graph
        fig = go.Figure()
        
        if is_comp:
            # Satimo 1 is solid red, Satimo 2 blue, Satimo 3 green
            chamber_styles = {
                "Satimo 1": {"color": "red", "dash": "solid"},
                "Satimo 2": {"color": "#022af2", "dash": "solid"},
                "Satimo 3": {"color": "#2ca02c", "dash": "solid"}
            }
            
            for chamber in ["Satimo 1", "Satimo 2", "Satimo 3"]:
                ch_data = subset[subset['Chamber'] == chamber]
                if not ch_data.empty:
                    style = chamber_styles.get(chamber, {"color": "gray", "dash": "solid"})
                    fig.add_trace(go.Scatter(
                        x=ch_data['Frequency (MHz)'], 
                        y=ch_data['Efficiency'],
                        mode='lines+markers',
                        name=f"<b>{chamber}</b>&nbsp;&nbsp;&nbsp;",
                        line=dict(color=style['color'], width=3, dash=style['dash'])
                    ))
        else:
            # Standard Plot: NIST Reference (Dashed) and Measured Date (Solid Blue)
            fig.add_trace(go.Scatter(
                x=subset['Frequency (MHz)'], 
                y=subset['Reference Efficiency (dB)'], 
                mode='lines+markers', 
                name="<b>Reference Data - NIST</b>&nbsp;&nbsp;&nbsp;", 
                line=dict(color='red', width=3, dash='dash')
            ))
            fig.add_trace(go.Scatter(
                x=subset['Frequency (MHz)'], 
                y=subset['Date Efficiency (dB)'], 
                mode='lines+markers', 
                name=f'<b>{date_label}</b>', 
                line=dict(color='#022af2', width=3)
            ))
        
        min_f, max_f = int(subset['Frequency (MHz)'].min()), int(subset['Frequency (MHz)'].max())
        fig.update_layout(
            title=dict(text=f"<b>{unit_display_name}</b> <span style='font-size: 20px;'>({min_f}-{max_f} MHz)</span>", font=dict(size=30)),
            xaxis_title="<b>Frequency (MHz)</b>", yaxis_title="<b>Efficiency (dB)</b>",
            hovermode="x unified", template="plotly_white", height=560,
            legend=dict(orientation="h", yanchor="bottom", y=1.12, xanchor="center", x=0.5, font=dict(size=18)),
            margin=dict(t=130, b=50, l=50, r=50),
            xaxis=dict(title_font=dict(color='black', size=20), tickfont=dict(color='black', size=14, weight='bold'), showgrid=True, gridcolor='silver', gridwidth=1, showline=True, linewidth=1, linecolor='black', mirror=True),
            yaxis=dict(title_font=dict(color='black', size=20), tickfont=dict(color='black', size=14, weight='bold'), showgrid=True, gridcolor='silver', gridwidth=1, zeroline=True, zerolinewidth=3, zerolinecolor='black', showline=True, linewidth=1, linecolor='black', mirror=True)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No matching frequency data found for this selection.")
else:
    st.error(f"Please ensure the data file for {validation_type} is uploaded to the directory.")
