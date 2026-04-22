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

passive_type = st.sidebar.selectbox(
    "Select Passive Validation Type:",
    ["None", "Yearly", "Quarterly", "Monthly", "Wideband Dipole - Chamber Comparison"]
)

active_type = st.sidebar.selectbox(
    "Select Active Validation Type:",
    ["None", "LTE TRP"]
)

# --- DYNAMIC PARSING FUNCTIONS ---

@st.cache_data
def load_active_trp_data(file_name):
    """Robustly parses the LTE TRP Active validation file by searching for headers."""
    try:
        df_raw = pd.read_csv(file_name, header=None)
        
        # 1. Find the header row (Band Chan / Frequency / TRP)
        header_row = None
        for r in range(len(df_raw)):
            row_vals = [str(x).strip().lower() for x in df_raw.iloc[r].values]
            if "band chan" in row_vals and "frequency (mhz)" in row_vals:
                header_row = r
                break
        
        if header_row is None:
            return None, "Could not locate 'Band Chan' header in CSV."

        # 2. Extract Date (usually in the header row or nearby)
        # We look for a date-like string in the header row
        date_val = "Unknown Date"
        for val in df_raw.iloc[header_row].values:
            if "/" in str(val):
                date_val = str(val).strip()
                break

        # 3. Extract Data starting after the TRP (dBm) row (usually 2 rows below headers)
        data_start = header_row + 1
        # Detect where TRP (dBm) label is to find the column indices
        cols = [str(x).strip().lower() for x in df_raw.iloc[header_row].values]
        band_idx = cols.index("band chan")
        freq_idx = cols.index("frequency (mhz)")
        
        # TRP is often in the same col as Date or adjacent. 
        # In your file, it appears in column 4.
        trp_idx = 4 

        data = df_raw.iloc[data_start:, [band_idx, freq_idx, trp_idx]].copy()
        data.columns = ['Band/Chan', 'Frequency (MHz)', 'TRP (dBm)']
        
        # Clean and Convert
        data['Band/Chan'] = data['Band/Chan'].astype(str).str.strip()
        data['Frequency (MHz)'] = pd.to_numeric(data['Frequency (MHz)'], errors='coerce')
        data['TRP (dBm)'] = pd.to_numeric(data['TRP (dBm)'], errors='coerce')
        data['Date'] = date_val
        
        final_df = data.dropna(subset=['Frequency (MHz)', 'TRP (dBm)'])
        
        if final_df.empty:
            return None, "Data was found but numerical conversion failed (empty set)."
            
        return final_df, None
    except Exception as e:
        return None, str(e)

# (Passive data function remains the same as previously established)
@st.cache_data
def load_passive_data(file_name, is_comparison=False):
    try:
        df_raw = pd.read_csv(file_name, header=None)
        all_parsed_data = []
        keywords = ["Dipoles", "Horn", "Chamber"]
        for c in range(len(df_raw.columns)):
            start_row = None
            for r in range(min(15, len(df_raw))):
                if str(df_raw.iloc[r, c]).strip() in keywords:
                    start_row = r
                    break
            if start_row is not None:
                if not is_comparison:
                    data_cols = df_raw.iloc[start_row:, c:c+3].copy()
                    data_cols.columns = ['ID_Col', 'Ref_Col', 'Meas_Col']
                    unit, date = None, None
                    for _, row in data_cols.iterrows():
                        v_id = str(row['ID_Col']).strip()
                        if v_id.startswith(('SD', 'WD', 'SH')) and len(v_id) > 2:
                            unit, date = v_id, str(row['Meas_Col']).strip() if str(row['Meas_Col']).strip() != 'nan' else 'Current'
                            continue
                        if unit:
                            try: all_parsed_data.append({'Dipole': unit, 'Date_Label': date, 'Frequency (MHz)': float(v_id), 'Reference Efficiency (dB)': float(row['Ref_Col']), 'Date Efficiency (dB)': float(row['Meas_Col'])})
                            except: pass
                else:
                    chamber = str(df_raw.iloc[start_row+1, c]).strip().replace("Satimo1", "Satimo 1")
                    c_date = str(df_raw.iloc[start_row+1, c+1]).strip()
                    unit = str(df_raw.iloc[0, 0]).split(':')[-1].strip().replace("Proxicast #4", "Proxicast Dipole #4")
                    d_cols = df_raw.iloc[start_row+2:, c:c+2].copy()
                    d_cols.columns = ['F', 'E']
                    for _, row in d_cols.iterrows():
                        try: all_parsed_data.append({'Dipole': unit, 'Chamber': chamber, 'Chamber_Date': c_date, 'Frequency (MHz)': float(row['F']), 'Efficiency': float(row['E'])})
                        except: pass
        return pd.DataFrame(all_parsed_data)
    except: return None

# --- UI LOGIC ---

if active_type == "LTE TRP":
    st.markdown('<h3 style="color:#022af2;"><b>Active Reference Quarterly - LTE TRP</b></h3>', unsafe_allow_html=True)
    fname = "Satimo 1 Chamber - Active Trend Charts - Satimo1 - Active Reference Quarterly - LTE TRP.csv"
    df_active, err = load_active_trp_data(fname)
    
    if df_active is not None:
        date_label = df_active['Date'].iloc[0]
        
        def plot_active(x_col, title):
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_active[x_col], y=df_active['TRP (dBm)'],
                mode='lines+markers', name=f"<b>LTE TRP</b> ({date_label})",
                line=dict(color='#022af2', width=2)
            ))
            fig.update_layout(
                title=dict(text=f"<b>{title}</b>", font=dict(size=24)),
                xaxis_title=f"<b>{x_col}</b>", yaxis_title="<b>TRP (dBm)</b>",
                hovermode="x unified", template="plotly_white", height=500,
                legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02, font=dict(size=14)),
                margin=dict(t=80, b=50, l=50, r=180),
                xaxis=dict(tickfont=dict(weight='bold')),
                yaxis=dict(tickfont=dict(weight='bold'), zeroline=True, zerolinewidth=3, zerolinecolor='black')
            )
            return fig

        st.plotly_chart(plot_active('Band/Chan', "LTE (Band/Chan) vs TRP"), use_container_width=True)
        st.plotly_chart(plot_active('Frequency (MHz)', "LTE (Frequency (MHz)) vs TRP"), use_container_width=True)
    else:
        st.error(f"Error loading Active TRP data: {err}")

elif passive_type != "None":
    # (Existing Passive Logic)
    tmap = {"Yearly": "Yearly - Passive Dipole Validation", "Quarterly": "Quarterly - Passive Dipole Validation", "Monthly": "Monthly - Passive Horn Validation", "Wideband Dipole - Chamber Comparison": "Wideband Dipole - Chamber Comparison"}
    st.markdown(f'<h3 style="color:#022af2;"><b>{tmap[passive_type]}</b></h3>', unsafe_allow_html=True)
    f_map = {"Yearly": 'Satimo 1 Chamber - Passive Trend Charts - Satimo 1- Dipoles Yearly (4).csv', "Quarterly": 'Satimo 1 Chamber - Passive Trend Charts - Satimo 1- Dipoles Quarterly (1).csv', "Monthly": 'Satimo 1 Chamber - Passive Trend Charts - Satimo 1 - Horns Monthly (1).csv', "Wideband Dipole - Chamber Comparison": 'Wideband Dipole - Chamber Comparison - Satimo TechEng Wideband Dipole.csv'}
    
    df_p = load_passive_data(f_map[passive_type], is_comparison=(passive_type == "Wideband Dipole - Chamber Comparison"))
    if df_p is not None and not df_p.empty:
        unit = st.sidebar.selectbox("Select Unit:", df_p['Dipole'].unique())
        sub = df_p[df_p['Dipole'] == unit].copy()
        fig = go.Figure()
        if passive_type == "Wideband Dipole - Chamber Comparison":
            styles = {"Satimo 1": "red", "Satimo 2": "#022af2", "Satimo 3": "#2ca02c"}
            for cham in ["Satimo 1", "Satimo 2", "Satimo 3"]:
                ch_d = sub[sub['Chamber'] == cham]
                if not ch_d.empty:
                    fig.add_trace(go.Scatter(x=ch_d['Frequency (MHz)'], y=ch_d['Efficiency'], mode='lines+markers', name=f"<b>{cham}</b> ({ch_d['Chamber_Date'].iloc[0]})", line=dict(color=styles.get(cham, 'gray'), width=2)))
        else:
            d_lab = sub["Date_Label"].iloc[0]
            fig.add_trace(go.Scatter(x=sub['Frequency (MHz)'], y=sub['Reference Efficiency (dB)'], mode='lines+markers', name="<b>Reference Data - NIST</b>", line=dict(color='red', width=2, dash='dash')))
            fig.add_trace(go.Scatter(x=sub['Frequency (MHz)'], y=sub['Date Efficiency (dB)'], mode='lines+markers', name=f'<b>{d_lab}</b>', line=dict(color='#022af2', width=2)))
        
        fig.update_layout(height=560, template="plotly_white", legend=dict(orientation="v", x=1.02), margin=dict(r=180), yaxis=dict(zeroline=True, zerolinewidth=3, zerolinecolor='black', tickfont=dict(weight='bold')), xaxis=dict(tickfont=dict(weight='bold')))
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Please select a Validation Type from the sidebar.")
