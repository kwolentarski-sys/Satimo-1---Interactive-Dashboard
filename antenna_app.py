import streamlit as st
import pandas as pd
import plotly.express as px

# UI Config
st.set_page_config(page_title="Antenna Efficiency Dashboard", layout="wide")

st.title("📡 Antenna Lab: Efficiency Analyzer")
st.markdown("---")

# 1. File Upload
uploaded_file = st.sidebar.file_uploader("Upload your antenna CSV", type="csv")

if uploaded_file:
    # Attempt to read the file
    try:
        # Sneaky check for delimiter (commas vs semicolons)
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
        
        st.sidebar.success("File loaded successfully!")
        
        # 2. Column Selection
        cols = df.columns.tolist()
        freq_col = st.sidebar.selectbox("Which column is Frequency?", cols)
        eff_col = st.sidebar.selectbox("Which column is Efficiency?", cols)
        
        # 3. Efficiency Unit Correction
        st.sidebar.markdown("---")
        unit = st.sidebar.radio("Data format:", ["Decimal (0.0-1.0)", "Percentage (0-100%)", "dB"])

        if unit == "Decimal (0.0-1.0)":
            df['Plot_Eff'] = df[eff_col] * 100
        elif unit == "dB":
            df['Plot_Eff'] = (10**(df[eff_col]/10)) * 100
        else:
            df['Plot_Eff'] = df[eff_col]

        # 4. The Visuals
        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader("Efficiency Sweep")
            fig = px.line(df, x=freq_col, y='Plot_Eff', 
                         labels={'Plot_Eff': 'Efficiency (%)', freq_col: 'Frequency'},
                         template="plotly_dark")
            
            # Add 'Success' markers
            fig.add_hrect(y0=70, y1=100, fillcolor="green", opacity=0.1, annotation_text="High Perf")
            fig.update_traces(line_color='#00d1b2', line_width=3)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Summary Metrics")
            peak_val = df['Plot_Eff'].max()
            peak_freq = df.loc[df['Plot_Eff'].idxmax(), freq_col]
            avg_val = df['Plot_Eff'].mean()

            st.metric("Peak Efficiency", f"{peak_val:.2f}%")
            st.metric("at Frequency", f"{peak_freq}")
            st.metric("Average", f"{avg_val:.2f}%")

        # 5. Data Preview
        with st.expander("View Raw Data Table"):
            st.dataframe(df)

    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.info("Tip: Make sure the file isn't currently open in Excel!")

else:
    st.info("👈 Please upload your .csv file in the sidebar to begin.")