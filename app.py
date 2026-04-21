import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# App Title: Satimo 1 Chamber - Interactive Dashboard
st.title("Satimo 1 Chamber - Interactive Dashboard")

# Sub-title: Color #022af2, bold/large
st.markdown('<h3 style="color:#022af2;"><b>Yearly Dipole Validation Measurements</b></h3>', unsafe_allow_html=True)

@st.cache_data
def load_and_clean_data(file_name):
    """Parses the specific layout of the Satimo passive trend CSV."""
    # Load raw data without headers to navigate the multi-level layout
    df_raw = pd.read_csv(file_name, header=None)
    
    # Extract columns 9, 10, 11 which contain Dipole, Reference, and Date data
    data_cols = df_raw.iloc[:, 9:12].copy()
    data_cols.columns = ['Col9', 'Col10', 'Col11']

    dipole_data = []
    current_dipole = None
    current_date = None

    # Loop through rows to associate frequencies and efficiencies with the correct Dipole
    for index, row in data_cols.iterrows():
        col9 = str(row['Col9']).strip()
        col10 = str(row['Col10']).strip()
        col11 = str(row['Col11']).strip()
        
        # Identify the start of a new dipole section (e.g., "SD665")
        if col9.startswith('SD') and len(col9) > 2 and col9[2].isdigit():
            current_dipole = col9
            current_date = col11 if col11 != 'nan' else 'Current Date'
            continue
                
        # If we are under a dipole, attempt to parse the numerical values
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
                # Skip header rows like "Frequency", "(Mhz)", or empty rows
                pass

    return pd.DataFrame(dipole_data)

# 1. Load the data using the verbatim filename
file_name = 'Satimo 1 Chamber - Passive Trend Charts - Satimo 1- Dipoles Yearly (4).csv'

try:
    df = load_and_clean_data(file_name)
    
    # 2. Sidebar for User Interaction
    st.sidebar.header("Dashboard Controls")
    dipoles = df['Dipole'].unique()
    selected_dipole = st.sidebar.selectbox("Select a Dipole to View:", dipoles)
    
    # Filter dataset based on selection
    subset = df[df['Dipole'] == selected_dipole]
    date_label = subset["Date_Label"].iloc[0]
    
    # 3. Build Interactive Plotly Graph
    fig = go.Figure()
    
    # Add Reference Data - NIST Line (Updated: Name is now bold)
    fig.add_trace(go.Scatter(
        x=subset['Frequency (MHz)'], 
        y=subset['Reference Efficiency (dB)'],
        mode='lines+markers',
        name='<b>Reference Data - NIST</b>',
        line=dict(color='red', width=3, dash='dash')
    ))
    
    # Add Date Data Line (Updated: Name is now bold)
    fig.add_trace(go.Scatter(
        x=subset['Frequency (MHz)'], 
        y=subset['Date Efficiency (dB)'],
        mode='lines+markers',
        name=f'<b>{date_label}</b>',
        line=dict(color='#ff7f0e', width=3)
    ))
    
    fig.update_layout(
        # Graph title size 30
        title=dict(
            text=f"Dipole {selected_dipole}",
            font=dict(size=30)
        ),
        # Bold Titles (size 20)
        xaxis_title="<b>Frequency (MHz)</b>",
        yaxis_title="<b>Efficiency (dB)</b>",
        hovermode="x unified",
        template="plotly_white",
        # Legend positioned further above (y=1.12) and centered (size 18)
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.12,
            xanchor="center",
            x=0.5,
            font=dict(size=18)
        ),
        # Top margin adjusted for legend
        margin=dict(t=120),
        # Axis labels (Titles) and Tick Labels with outside border (mirror)
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
    
    # Render the plot in the dashboard
    st.plotly_chart(fig, use_container_width=True)

    # 4. Show Raw Data Table (Optional)
    if st.checkbox("Show Raw Data for this Dipole"):
        st.dataframe(subset)

except FileNotFoundError:
    st.error(f"Could not find `{file_name}`. Please ensure it is in the same directory as this script.")
