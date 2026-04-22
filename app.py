import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Satimo 1 Performance Dashboard", layout="wide")

# App Title
st.markdown(
    '<h1 style="white-space: nowrap; overflow: hidden; text-overflow: clip; font-size: 34px;">Satimo 1 Chamber Performance - Interactive Dashboard</h1>', 
    unsafe_allow_html=True
)

# 1. Sidebar - Dashboard Controls
st.sidebar.markdown('<h2 style="color:#022af2;">Dashboard Controls</h2>', unsafe_allow_html=True)

# Selection for Passive Validation
passive_type = st.sidebar.selectbox(
    "Select Passive Validation Type:",
    ["None", "Yearly", "Quarterly", "Monthly", "Wideband Dipole - Chamber Comparison"]
)

# Selection for Active Validation
active_type = st.sidebar.selectbox(
    "Select Active Validation Type:",
    ["None", "LTE TRP"]
)

# --- DATA LOADING FUNCTIONS ---

@st.cache_data
def load_passive_data(file_name, is_comparison=False):
    """Parses standard Passive Validation files."""
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
                        val_id, val_ref, val_meas = str(row['ID_Col']).strip(), str(row['Ref_Col']).strip(), str(row['Meas_Col']).strip()
                        if val_id.startswith(('SD', 'WD', 'SH')) and len(val_id) > 2:
                            current_unit, current_date = val_id, (val_meas if val_meas != 'nan' else 'Current Date')
                            continue
                        if current_unit:
                            try:
                                all_parsed_data.append({'Dipole': current_unit, 'Date_Label': current_date, 'Frequency (MHz)': float(val_id), 'Reference Efficiency (dB)': float(val_ref), 'Date Efficiency (dB)': float(val_meas)})
                            except ValueError: pass
                else:
                    chamber_name = str(df_raw.iloc[start_row+1, c]).strip()
                    chamber_date = str(df_raw.iloc[start_row+1, c+1]).strip()
                    if chamber_name == "Satimo1": chamber_name = "Satimo 1"
                    unit_name = str(df_raw.iloc[0, 0]).split(':')[-1].strip().replace("Proxicast #4", "Proxicast Dipole #4")
                    
                    data_cols = df_raw.iloc[start_row+2:, c:c+2].copy()
                    data_cols.columns = ['Freq_Col', 'Eff_Col']
                    for _, row in data_cols.iterrows():
                        try:
                            all_parsed_data.append({'Dipole': unit_name, 'Chamber': chamber_name, 'Chamber_Date': chamber_date, 'Frequency (MHz)': float(row['Freq_Col']), 'Efficiency': float(row['Eff_Col'])})
                        except ValueError: pass
        return pd.DataFrame(all_parsed_data)
    except Exception: return None

@st.cache_data
def load_active_trp_data(file_name):
    """Parses the LTE TRP Active validation file."""
    try:
        df_raw = pd.read_csv(file_name, header=None)
        # Extract date from row 4, col 4
        date_val = str(df_raw.iloc[4, 4]).strip()
        # Data starts from row 8 (B71 Low)
        data = df_raw.iloc[8:, 2:5].copy()
        data.columns = ['Band/Chan', 'Frequency (MHz)', 'TRP (dBm)']
        data = data.dropna(subset=['Band/Chan'])
        data['Frequency (MHz)'] = pd.to_numeric(data['Frequency (MHz)'], errors='coerce')
        data['TRP (dBm)'] = pd.to_numeric(data['TRP (dBm)'], errors='coerce')
        data['Date'] = date_val
        return data.dropna(subset=['Frequency (MHz)', 'TRP (dBm)'])
    except Exception: return None

# --- MAIN LOGIC ---

# 1. Handle Active Selection (Priority if selected)
if active_type != "None":
    st.markdown('<h3 style="color:#022af2;"><b>Active Reference Quarterly - LTE TRP</b></h3>', unsafe_allow_html=True)
    file_name = "Satimo 1 Chamber - Active Trend Charts - Satimo1 - Active Reference Quarterly - LTE TRP.csv"
    df_active = load_active_trp_data(file_name)
    
    if df_active is not None and not df_active.empty:
        date_label = df_active['Date'].iloc[0]
        
        # Helper for styling active plots
        def create_active_plot(x_col, title_text):
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_active[x_col], 
                y=df_active['TRP (dBm)'],
                mode='lines+markers',
                name=f"<b>LTE TRP</b> ({date_label})",
                line=dict(color='#022af2', width=2)
            ))
            fig.update_layout(
                title=dict(text=f"<b>{title_text}</b>", font=dict(size=24)),
                xaxis_title=f"<b>{x_col}</b>", 
                yaxis_title="<b>TRP (dBm)</b>",
                hovermode="x unified", template="plotly_white", height=500,
                legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02, font=dict(size=14)),
                margin=dict(t=80, b=50, l=50, r=150),
                xaxis=dict(title_font=dict(size=18), tickfont=dict(size=12, weight='bold'), showgrid=True, gridcolor='silver', gridwidth=1, showline=True, linewidth=1, linecolor='black', mirror=True),
                yaxis=dict(title_font=dict(size=18), tickfont=dict(size=12, weight='bold'), showgrid=True, gridcolor='silver', gridwidth=1, zeroline=True, zerolinewidth=3, zerolinecolor='black', showline=True, linewidth=1, linecolor='black', mirror=True)
            )
            return fig

        st.plotly_chart(create_active_plot('Band/Chan', "LTE (Band/Chan) vs TRP"), use_container_width=True)
        st.plotly_chart(create_active_plot('Frequency (MHz)', "LTE (Frequency (MHz)) vs TRP"), use_container_width=True)
    else:
        st.error("Could not load Active LTE TRP data.")

# 2. Handle Passive Selection (If no Active or specifically selected)
elif passive_type != "None":
    title_map = {
        "Yearly": "Yearly - Passive Dipole Validation Measurements",
        "Quarterly": "Quarterly - Passive Dipole Validation Measurements",
        "Monthly": "Monthly - Passive Horn Validation Measurements",
        "Wideband Dipole - Chamber Comparison": "Wideband Dipole - Chamber Comparison"
    }
    st.markdown(f'<h3 style="color:#022af2;"><b>{title_map[passive_type]}</b></h3>', unsafe_allow_html=True)
    
    files = {
        "Yearly": 'Satimo 1 Chamber - Passive Trend Charts - Satimo 1- Dipoles Yearly (4).csv',
        "Quarterly": 'Satimo 1 Chamber - Passive Trend Charts - Satimo 1- Dipoles Quarterly (1).csv',
        "Monthly": 'Satimo 1 Chamber - Passive Trend Charts - Satimo 1 - Horns Monthly (1).csv',
        "Wideband Dipole - Chamber Comparison": 'Wideband Dipole - Chamber Comparison - Satimo TechEng Wideband Dipole.csv'
    }
    
    is_comp = (passive_type == "Wideband Dipole - Chamber Comparison")
    df = load_passive_data(files[passive_type], is_comparison=is_comp)
    
    if df is not None and not df.empty:
        if is_comp:
            units = df['Dipole'].unique()
            selected_unit = st.sidebar.selectbox("Select Dipole:", units)
            subset = df[df['Dipole'] == selected_unit].copy()
            unit_display_name = selected_unit
        else:
            units = df['Dipole'].unique()
            selected_unit = st.sidebar.selectbox(f"Select a {'Horn' if passive_type == 'Monthly' else 'Dipole'}:", units)
            subset = df[df['Dipole'] == selected_unit].copy()
            date_label, unit_display_name = subset["Date_Label"].iloc[0], selected_unit

        if not subset.empty:
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
                chamber_styles = {"Satimo 1": "red", "Satimo 2": "#022af2", "Satimo 3": "#2ca02c"}
                for chamber in ["Satimo 1", "Satimo 2", "Satimo 3"]:
                    ch_data = subset[subset['Chamber'] == chamber]
                    if not ch_data.empty:
                        ch_date = ch_data['Chamber_Date'].iloc[0]
                        fig.add_trace(go.Scatter(x=ch_data['Frequency (MHz)'], y=ch_data['Efficiency'], mode='lines+markers', name=f"<b>{chamber}</b> ({ch_date})", line=dict(color=chamber_styles.get(chamber, 'gray'), width=2)))
            else:
                fig.add_trace(go.Scatter(x=subset['Frequency (MHz)'], y=subset['Reference Efficiency (dB)'], mode='lines+markers', name="<b>Reference Data - NIST</b>", line=dict(color='red', width=2, dash='dash')))
                fig.add_trace(go.Scatter(x=subset['Frequency (MHz)'], y=subset['Date Efficiency (dB)'], mode='lines+markers', name=f'<b>{date_label}</b>', line=dict(color='#022af2', width=2)))
            
            min_f, max_f = int(subset['Frequency (MHz)'].min()), int(subset['Frequency (MHz)'].max())
            fig.update_layout(
                title=dict(text=f"<b>{unit_display_name}</b> <span style='font-size: 20px;'>({min_f}-{max_f} MHz)</span>", font=dict(size=30)),
                xaxis_title="<b>Frequency (MHz)</b>", yaxis_title="<b>Efficiency (dB)</b>",
                hovermode="x unified", template="plotly_white", height=560,
                legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02, font=dict(size=16)),
                margin=dict(t=100, b=50, l=50, r=150),
                xaxis=dict(tickfont=dict(weight='bold')),
                yaxis=dict(tickfont=dict(weight='bold'), zeroline=True, zerolinewidth=3, zerolinecolor='black')
            )
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Please select a Validation Type from the sidebar to begin.")
