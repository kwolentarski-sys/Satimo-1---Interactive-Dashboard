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

# Updated: Change label to "Select Passive Validation Type"
validation_type = st.sidebar.selectbox(
    "Select Passive Validation Type:",
    ["Yearly", "Quarterly", "Monthly"]
)

# Dynamic Sub-title based on selection
title_map = {
    "Yearly": "Yearly - Passive Dipole Validation Measurements",
    "Quarterly": "Quarterly - Passive Dipole Validation Measurements",
    "Monthly": "Monthly - Passive Horn Validation Measurements"
}
sub_title_text = title_map[validation_type]
st.markdown(f'<h3 style="color:#022af2;"><b>{sub_title_text}</b></h3>', unsafe_allow_html=True)

@st.cache_data
def load_and_clean_data(file_name):
    """Dynamically finds and parses Satimo passive trend data across multiple column blocks."""
    try:
        df_raw = pd.read_csv(file_name, header=None)
        all_parsed_data = []

        # Scan all columns to find data blocks starting with "Dipoles" or "Horn"
        for c in range(len(df_raw.columns)):
            start_row = None
            for r in range(min(15, len(df_raw))):
                cell_val = str(df_raw.iloc[r, c]).strip()
                if cell_val in ["Dipoles", "Horn"]:
                    start_row = r
                    break
            
            if start_row is not None:
                # Extract the 3-column group (Identifier, Reference, Measured)
                data_cols = df_raw.iloc[start_row:, c:c+3].copy()
                data_cols.columns = ['ID_Col', 'Ref_Col', 'Meas_Col']

                current_unit = None
                current_date = None

                for _, row in data_cols.iterrows():
                    val_id = str(row['ID_Col']).strip()
                    val_ref = str(row['Ref_Col']).strip()
                    val_meas = str(row['Meas_Col']).strip()
                    
                    # Detect SD/WD (Dipoles) or SH (Horns) identifiers
                    is_new_header = (val_id.startswith(('SD', 'WD', 'SH'))) and len(val_id) > 2 and any(char.isdigit() for char in val_id)
                    
                    if is_new_header:
                        current_unit = val_id
                        current_date = val_meas if val_meas != 'nan' else 'Current Date'
                        continue
                            
                    if current_unit:
                        try:
                            freq = float(val_id)
                            ref_eff = float(val_ref)
                            date_eff = float(val_meas)
                            all_parsed_data.append({
                                'Dipole': current_unit, 
                                'Date_Label': current_date,
                                'Frequency (MHz)': freq,
                                'Reference Efficiency (dB)': ref_eff,
                                'Date Efficiency (dB)': date_eff
                            })
                        except ValueError:
                            pass
                            
        return pd.DataFrame(all_parsed_data)
    except FileNotFoundError:
        return None

# Mapping selections to filenames verbatim
files = {
    "Yearly": 'Satimo 1 Chamber - Passive Trend Charts - Satimo 1- Dipoles Yearly (4).csv',
    "Quarterly": 'Satimo 1 Chamber - Passive Trend Charts - Satimo 1- Dipoles Quarterly (1).csv',
    "Monthly": 'Satimo 1 Chamber - Passive Trend Charts - Satimo 1 - Horns Monthly (1).csv'
}

file_name = files[validation_type]
df = load_and_clean_data(file_name)

if df is not None and not df.empty:
    # Sidebar control for specific Unit (Dipole or Horn)
    units = df['Dipole'].unique()
    selected_unit = st.sidebar.selectbox(f"Select a {'Horn' if validation_type == 'Monthly' else 'Dipole'} to View:", units)
    
    subset = df[df['Dipole'] == selected_unit].copy()
    date_label = subset["Date_Label"].iloc[0]

    # --- CALCULATIONS ---
    subset['Abs_Diff'] = (subset['Reference Efficiency (dB)'] - subset['Date Efficiency (dB)']).abs()
    max_diff_idx = subset['Abs_Diff'].idxmax()
    max_val = subset.loc[max_diff_idx, 'Abs_Diff']
    max_freq = subset.loc[max_diff_idx, 'Frequency (MHz)']

    above_0_subset = subset[subset['Date Efficiency (dB)'] > 0]
    min_f = int(subset['Frequency (MHz)'].min())
    max_f = int(subset['Frequency (MHz)'].max())

    st.write(f"**Maximum Difference From Reference NIST:** {max_val:.2f} dB at {max_freq} MHz")
    
    if not above_0_subset.empty:
        max_above_idx = above_0_subset['Date Efficiency (dB)'].idxmax()
        max_above_val = above_0_subset.loc[max_above_idx, 'Date Efficiency (dB)']
        max_above_freq = above_0_subset.loc[max_above_idx, 'Frequency (MHz)']
        st.markdown(f'**Maximum Overshoot Above 0 dB:** <span style="color:red;">{max_above_val:.2f} dB at {max_above_freq} MHz</span>', unsafe_allow_html=True)
    else:
        st.markdown('**Maximum Overshoot Above 0 dB:** <span style="color:green;">None</span>', unsafe_allow_html=True)
    
    # 3. Build Interactive Plotly Graph
    fig = go.Figure()
    
    # NIST Reference Line
    fig.add_trace(go.Scatter(
        x=subset['Frequency (MHz)'], y=subset['Reference Efficiency (dB)'],
        mode='lines+markers', name='<b>Reference Data - NIST</b>&nbsp;&nbsp;&nbsp;',
        line=dict(color='red', width=3, dash='dash')
    ))
    
    # Measured Data Line
    fig.add_trace(go.Scatter(
        x=subset['Frequency (MHz)'], y=subset['Date Efficiency (dB)'],
        mode='lines+markers', name=f'<b>{date_label}</b>',
        line=dict(color='#022af2', width=3)
    ))
    
    fig.update_layout(
        title=dict(
            text=f"<b>{'Horn' if validation_type == 'Monthly' else 'Dipole'} {selected_unit}</b> <span style='font-size: 20px;'>({min_f}-{max_f} MHz)</span>",
            font=dict(size=30)
        ),
        xaxis_title="<b>Frequency (MHz)</b>",
        yaxis_title="<b>Efficiency (dB)</b>",
        hovermode="x unified",
        template="plotly_white",
        height=560,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.12,
            xanchor="center", x=0.5, font=dict(size=18)
        ),
        margin=dict(t=130, b=50, l=50, r=50),
        xaxis=dict(
            title_font=dict(color='black', size=20), 
            tickfont=dict(color='black', size=14, weight='bold'),
            showgrid=True, gridcolor='silver', gridwidth=1,
            showline=True, linewidth=1, linecolor='black', mirror=True
        ),
        yaxis=dict(
            title_font=dict(color='black', size=20), 
            tickfont=dict(color='black', size=14, weight='bold'),
            showgrid=True, gridcolor='silver', gridwidth=1,
            zeroline=True, zerolinewidth=3, zerolinecolor='black',
            showline=True, linewidth=1, linecolor='black', mirror=True
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error(f"Please ensure the data file for {validation_type} is uploaded to the directory.")
