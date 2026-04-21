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

# Toggle between Yearly and Quarterly validation
validation_type = st.sidebar.selectbox(
    "Select Validation Type:",
    ["Yearly", "Quarterly"]
)

# Dynamic Sub-title based on selection
sub_title_text = f"{validation_type} - Passive Dipole Validation Measurements"
st.markdown(f'<h3 style="color:#022af2;"><b>{sub_title_text}</b></h3>', unsafe_allow_html=True)

@st.cache_data
def load_and_clean_data(file_name):
    """Dynamically finds and parses the Satimo passive trend data."""
    try:
        df_raw = pd.read_csv(file_name, header=None)
        
        # DYNAMIC COLUMN DETECTION: Search for the "Dipoles" header
        start_col = None
        for r in range(min(15, len(df_raw))):
            for c in range(len(df_raw.columns)):
                if str(df_raw.iloc[r, c]).strip() == "Dipoles":
                    start_col = c
                    break
            if start_col is not None: break
        
        if start_col is None:
            return pd.DataFrame() # No data block found

        # Extract the correct 3 columns (Dipole, Reference, Measured)
        data_cols = df_raw.iloc[:, start_col:start_col+3].copy()
        data_cols.columns = ['Col9', 'Col10', 'Col11']

        dipole_data = []
        current_dipole = None
        current_date = None

        for index, row in data_cols.iterrows():
            col9 = str(row['Col9']).strip()
            col10 = str(row['Col10']).strip()
            col11 = str(row['Col11']).strip()
            
            # Identify SD or WD dipoles
            is_new_header = (col9.startswith('SD') or col9.startswith('WD')) and len(col9) > 2 and col9[2].isdigit()
            
            if is_new_header:
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
    except FileNotFoundError:
        return None

# Mapping selections to filenames verbatim
files = {
    "Yearly": 'Satimo 1 Chamber - Passive Trend Charts - Satimo 1- Dipoles Yearly (4).csv',
    "Quarterly": 'Satimo 1 Chamber - Passive Trend Charts - Satimo 1- Dipoles Quarterly (1).csv'
}

file_name = files[validation_type]
df = load_and_clean_data(file_name)

if df is not None and not df.empty:
    dipoles = df['Dipole'].unique()
    selected_dipole = st.sidebar.selectbox("Select a Dipole to View:", dipoles)
    
    subset = df[df['Dipole'] == selected_dipole].copy()
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
    
    fig.add_trace(go.Scatter(
        x=subset['Frequency (MHz)'], y=subset['Reference Efficiency (dB)'],
        mode='lines+markers', name='<b>Reference Data - NIST</b>',
        line=dict(color='red', width=3, dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=subset['Frequency (MHz)'], y=subset['Date Efficiency (dB)'],
        mode='lines+markers', name=f'<b>{date_label}</b>',
        line=dict(color='#ff7f0e', width=3)
    ))
    
    fig.update_layout(
        title=dict(
            text=f"<b>Dipole {selected_dipole}</b> <span style='font-size: 20px;'>({min_f}-{max_f} MHz)</span>",
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
            title_font=dict(color='black', size=20), tickfont=dict(color='black', size=14),
            showgrid=True, gridcolor='silver', gridwidth=1,
            showline=True, linewidth=1, linecolor='black', mirror=True
        ),
        yaxis=dict(
            title_font=dict(color='black', size=20), tickfont=dict(color='black', size=14),
            showgrid=True, gridcolor='silver', gridwidth=1,
            showline=True, linewidth=1, linecolor='black', mirror=True
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error(f"Please ensure `{file_name}` is uploaded to the directory.")
