import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Antenna Lab: GitHub Integrated", layout="wide")

# --- CONFIGURATION ---
# REPLACE THIS URL with the "Raw" link you copied in Step 1
GITHUB_CSV_URL = "https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/your_file.csv"

st.title("📡 Live Antenna Efficiency Dashboard")

# --- DATA LOADING LOGIC ---
@st.cache_data # This keeps the app fast by not re-downloading every second
def load_github_data(url):
    try:
        return pd.read_csv(url)
    except Exception as e:
        st.error(f"Could not fetch data from GitHub: {e}")
        return None

# Sidebar option to switch between GitHub and Manual Upload
data_source = st.sidebar.radio("Data Source", ["GitHub (Auto)", "Manual Upload"])

if data_source == "GitHub (Auto)":
    df = load_github_data(GITHUB_CSV_URL)
else:
    uploaded_file = st.sidebar.file_uploader("Upload local CSV", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
    else:
        df = None

# --- VISUALIZATION ---
if df is not None:
    # Auto-mapping columns (Assuming common names, otherwise use sidebar selectbox)
    cols = df.columns.tolist()
    freq_col = st.sidebar.selectbox("Frequency Column", cols, index=0)
    eff_col = st.sidebar.selectbox("Efficiency Column", cols, index=1)

    # Simple Graph
    fig = px.line(df, x=freq_col, y=eff_col, title="Total Efficiency vs. Frequency")
    fig.update_traces(line_color='#00d1b2')
    st.plotly_chart(fig, use_container_width=True)
    
    st.success(f"Viewing data from: {data_source}")
else:
    st.info("Awaiting data...")
