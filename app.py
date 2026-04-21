import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- DASHBOARD CONFIG ---
st.set_page_config(page_title="Satimo 1 Passive Trend", layout="wide")
st.title("📡 Satimo 1: Dipole Efficiency Analysis")
st.markdown("Automated comparison against **NIST Reference Data** with ±0.5 dB tolerance checks.")

@st.cache_data
def load_and_clean_data(file_name):
    """Parses the stacked layout of the Satimo passive trend CSV."""
    df_raw = pd.read_csv(file_name, header=None)
    data_cols = df_raw.iloc[:, 9:12].copy()
    data_cols.columns = ['Col9', 'Col10', 'Col11']

    dipole_data = []
    current_dipole, current_date = None, None

    for _, row in data_cols.iterrows():
        c9, c10, c11 = str(row['Col9']).strip(), str(row['Col10']).strip(), str(row['Col11']).strip()
        
        # Detect new Dipole Section (e.g., SD665)
        if c9.startswith('SD') and len(c9) > 2 and c9[2].isdigit():
            current_dipole, current_date = c9, (c11 if c11 != 'nan' else 'Unknown Date')
            continue
                
        try:
            freq, ref, meas = float(c9), float(c10), float(c11)
            delta = meas - ref
            dipole_data.append({
                'Dipole': current_dipole,
                'Date_Label': current_date,
                'Frequency (MHz)': freq,
                'Reference (dB)': ref,
                'Measured (dB)': meas,
                'Delta (dB)': delta,
                'Status': 'PASS' if abs(delta) <= 0.5 else 'FAIL'
            })
        except ValueError:
            pass

    return pd.DataFrame(dipole_data)

# --- LOAD DATA ---
file_name = 'Satimo 1 Chamber - Passive Trend Charts - Satimo 1- Dipoles Yearly (4).csv'

try:
    df = load_and_clean_data(file_name)
    
    # --- SIDEBAR ---
    st.sidebar.header("Navigation")
    selected_dipole = st.sidebar.selectbox("Select Dipole:", df['Dipole'].unique())
    subset = df[df['Dipole'] == selected_dipole]
    
    # --- METRICS ---
    max_drift = subset['Delta (dB)'].abs().max()
    avg_eff = subset['Measured (dB)'].mean()
    status_color = "normal" if max_drift <= 0.5 else "inverse"

    col1, col2, col3 = st.columns(3)
    col1.metric("Selected Dipole", selected_dipole)
    col2.metric("Max Drift (dB)", f"{max_drift:.2f}", delta=f"{max_drift:.2f}", delta_color=status_color)
    col3.metric("Measurement Date", subset["Date_Label"].iloc[0])

    # --- VISUALIZATION ---
    # Create subplots: Efficiency Plot and Delta Plot
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.1, subplot_titles=("Efficiency (dB)", "Drift from Reference (dB)"))

    # 1. Efficiency Comparison
    fig.add_trace(go.Scatter(x=subset['Frequency (MHz)'], y=subset['Reference (dB)'],
                             name='NIST Reference', line=dict(color='#1f77b4', width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=subset['Frequency (MHz)'], y=subset['Measured (dB)'],
                             name='Measured', line=dict(color='#ff7f0e', width=2)), row=1, col=1)

    # 2. Delta / Error Plot
    fig.add_trace(go.Scatter(x=subset['Frequency (MHz)'], y=subset['Delta (dB)'],
                             name='Delta (Error)', fill='tozeroy', line=dict(color='gray')), row=2, col=1)
    
    # Add Tolerance Lines (+/- 0.5 dB)
    for limit in [0.5, -0.5]:
        fig.add_hline(y=limit, line_dash="dash", line_color="red", annotation_text=f"Limit {limit}dB", row=2, col=1)

    fig.update_layout(height=700, template="plotly_white", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    # --- DATA TABLE WITH CONDITIONAL FORMATTING ---
    if st.checkbox("Show Detailed Analysis Table"):
        def color_status(val):
            color = 'red' if val == 'FAIL' else 'green'
            return f'color: {color}'
        
        st.dataframe(subset.style.applymap(color_status, subset=['Status']))

except FileNotFoundError:
    st.error(f"File `{file_name}` not found. Ensure it's in your GitHub repo/directory.")
