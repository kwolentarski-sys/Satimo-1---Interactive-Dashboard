import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Satimo 1 Dashboard", layout="wide")

# App Title: Forced to one line using CSS nowrap[cite: 1]
st.markdown(
    '<h1 style="white-space: nowrap; overflow: hidden; text-overflow: clip;">Satimo 1 Chamber - Interactive Dashboard</h1>', 
    unsafe_allow_html=True
)

# Updated: Sub-title changed to "Yearly - Passive Dipole Validation Measurements"[cite: 1]
st.markdown('<h3 style="color:#022af2;"><b>Yearly - Passive Dipole Validation Measurements</b></h3>', unsafe_allow_html=True)

@st.cache_data
def load_and_clean_data(file_name):
    """Parses the specific layout of the Satimo passive trend CSV."""
    # Load raw data without headers[cite: 1]
    df_raw = pd.read_csv(file_name, header=None)
    
    # Extract columns 9, 10, 11[cite: 1]
    data_cols = df_raw.iloc[:, 9:12].copy()
    data_cols.columns = ['Col9', 'Col10', 'Col11']

    dipole_data = []
    current_dipole = None
    current_date = None

    for index, row in data_cols.iterrows():
        col9 = str(row['Col9']).strip()
        col10 = str(row['Col10']).strip()
        col11 = str(row['Col11']).strip()
        
        # Identify both SD and WD dipoles to separate their data[cite: 1]
        is_new_dipole = (col9.startswith('SD') or col9.startswith('WD')) and len(col9) > 2 and col9[2].isdigit()
        
        if is_new_dipole:
            current_dipole = col9
            current_date = col11 if col11 != 'nan' else 'Current Date'
            continue
                
        if current_dipole:
            try:
                freq = float(col9)
                ref_eff = float(col10)
                date_eff = float(col11)
                
                dipole_data.append({
                    'Dipole': current_dipole,
                    'Date_Label': current_date,
                    'Frequency (MHz)': freq,
                    'Reference Efficiency (dB)': ref_eff,
                    'Date Efficiency (dB)': date_eff
                })
            except ValueError:
                pass

    return pd.DataFrame(dipole_data)

# 1. Load the data using the verbatim filename[cite: 1]
file_name = 'Satimo 1 Chamber - Passive Trend Charts - Satimo 1- Dipoles Yearly (4).csv'

try:
    df = load_and_clean_data(file_name)
    
    # 2. Sidebar for User Interaction[cite: 1]
    st.sidebar.header("Dashboard Controls")
    dipoles = df['Dipole'].unique()
    selected_dipole = st.sidebar.selectbox("Select a Dipole to View:", dipoles)
    
    subset = df[df['Dipole'] == selected_dipole].copy()
    date_label = subset["Date_Label"].iloc[0]

    # --- CALCULATIONS ---
    # Metric 1: Max Absolute Difference From Reference NIST[cite: 1]
    subset['Abs_Diff'] = (subset['Reference Efficiency (dB)'] - subset['Date Efficiency (dB)']).abs()
    max_diff_idx = subset['Abs_Diff'].idxmax()
    max_val = subset.loc[max_diff_idx, 'Abs_Diff']
    max_freq = subset.loc[max_diff_idx, 'Frequency (MHz)']

    # Metric 2: Maximum Overshoot Above 0 dB[cite: 1]
    above_0_subset = subset[subset['Date Efficiency (dB)'] > 0]
    
    # Frequency Span for Title[cite: 1]
    min_f = int(subset['Frequency (MHz)'].min())
    max_f = int(subset['Frequency (MHz)'].max())

    # Display Metrics with conditional coloring[cite: 1]
    st.write(f"**Maximum Difference From Reference NIST:** {max_val:.2f} dB at {max_freq} MHz")
    
    if not above_0_subset.empty:
        max_above_idx = above_0_subset['Date Efficiency (dB)'].idxmax()
        max_above_val = above_0_subset.loc[max_above_idx, 'Date Efficiency (dB)']
        max_above_freq = above_0_subset.loc[max_above_idx, 'Frequency (MHz)']
        # Red text for overshoot values[cite: 1]
        st.markdown(f'**Maximum Overshoot Above 0 dB:** <span style="color:red;">{max_above_val:.2f} dB at {max_above_freq} MHz</span>', unsafe_allow_html=True)
    else:
        # Green text for "None"[cite: 1]
        st.markdown('**Maximum Overshoot Above 0 dB:** <span style="color:green;">None</span>', unsafe_allow_html=True)
    
    # 3. Build Interactive Plotly Graph[cite: 1]
    fig = go.Figure()
    
    # Reference Data - NIST Line (Red/Dashed, Bold Legend)[cite: 1]
    fig.add_trace(go.Scatter(
        x=subset['Frequency (MHz)'], 
        y=subset['Reference Efficiency (dB)'],
        mode='lines+markers',
        name='<b>Reference Data - NIST</b>',
        line=dict(color='red', width=3, dash='dash')
    ))
    
    # Date Data Line (Bold Legend Label)[cite: 1]
    fig.add_trace(go.Scatter(
        x=subset['Frequency (MHz)'], 
        y=subset['Date Efficiency (dB)'],
        mode='lines+markers',
        name=f'<b>{date_label}</b>',
        line=dict(color='#ff7f0e', width=3)
    ))
    
    fig.update_layout(
        # Dipole ID is bold and size 30; Frequency span is size 20 and not bold[cite: 1]
        title=dict(
            text=f"<b>Dipole {selected_dipole}</b> <span style='font-size: 20px;'>({min_f}-{max_f} MHz)</span>",
            font=dict(size=30)
        ),
        xaxis_title="<b>Frequency (MHz)</b>",
        yaxis_title="<b>Efficiency (dB)</b>",
        hovermode="x unified",
        template="plotly_white",
        # Height reduced by 20% (700 -> 560)[cite: 1]
        height=560,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.12,
            xanchor="center",
            x=0.5,
            font=dict(size=18)
        ),
        margin=dict(t=130, b=50, l=50, r=50),
        xaxis=dict(
            title_font=dict(color='black', size=20),
            tickfont=dict(color='black', size=14),
            showgrid=True,
            gridcolor='silver',
            gridwidth=1,
            showline=True,
            linewidth=1,
            linecolor='black',
            mirror=True
        ),
        yaxis=dict(
            title_font=dict(color='black', size=20),
            tickfont=dict(color='black', size=14),
            showgrid=True,
            gridcolor='silver',
            gridwidth=1,
            showline=True,
            linewidth=1,
            linecolor='black',
            mirror=True
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

except FileNotFoundError:
    st.error(f"Could not find `{file_name}`. Please ensure it is in the same directory as this script.")
