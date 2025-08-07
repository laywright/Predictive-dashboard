import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Page setup
st.set_page_config(page_title="🚌 BasiGo Manpower Dashboard", layout="wide")
st.title("🚌 BasiGo Manpower Dashboard")

# Upload Excel file
uploaded_file = st.file_uploader("📤 Upload your workforce Excel file", type=["xlsx"])

# If a file is uploaded
if uploaded_file is not None:
    # Load data
    df = pd.read_excel(uploaded_file)

    # Preprocess data
    df['Start'] = pd.to_datetime(df['Start'])
    df['End'] = pd.to_datetime(df['End'])
    df['Duration (Hrs)'] = (df['End'] - df['Start']).dt.total_seconds() / 3600
    df['Date'] = df['Start'].dt.date

    # Define four tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📥 Upload & Preview",
        "⏱️ Process Time Analysis",
        "📉 Human Resource Gaps",
        "📊 Predictive Allocation"
    ])

    # ──────────── Tab 1 ────────────
    with tab1:
        st.subheader("📥 Uploaded Data Preview")
        st.dataframe(df, use_container_width=True)

    # ──────────── Tab 2 ────────────
    with tab2:
        st.subheader("⏱️ Average Time per Station")
        avg_time = df.groupby('Station')['Duration (Hrs)'].mean().reset_index()
        st.dataframe(avg_time, use_container_width=True)
        fig = px.bar(avg_time, x='Station', y='Duration (Hrs)', title='Average Duration per Station')
        st.plotly_chart(fig, use_container_width=True)

    # ──────────── Tab 3 ────────────
    with tab3:
        st.subheader("📉 Manhours by Station")
        manhours = df.groupby('Station')['Duration (Hrs)'].sum().reset_index()
        st.dataframe(manhours, use_container_width=True)
        pie = px.pie(manhours, values='Duration (Hrs)', names='Station', title='Total Manhours Distribution')
        st.plotly_chart(pie, use_container_width=True)

    # ──────────── Tab 4 ────────────
    with tab4:
        st.subheader("📊 Predictive Manpower Allocation")

        with st.sidebar:
            st.header("🔧 Prediction Inputs")
            current_output = st.number_input("Current Monthly Output (buses)", min_value=1, value=7)
            target_output = st.number_input("Target Monthly Output (buses)", min_value=1, value=10)
            STU = st.number_input("Standard Time per Unit (minutes)", min_value=1, value=51840)
            working_days = st.number_input("Working Days per Month", min_value=1, value=21)
            hours_per_day = st.number_input("Work Hours per Day", min_value=1, value=8)
            absenteeism = st.slider("Absenteeism Rate (%)", min_value=0, max_value=20, value=5) / 100
            indirect_ratio = st.slider("Indirect Manpower Ratio (%)", min_value=0, max_value=50, value=10) / 100

        # Predictive calculations
        total_minutes = STU * target_output
        minutes_per_person = working_days * hours_per_day * 60
        required_direct = total_minutes / minutes_per_person
        adjusted_total = required_direct / ((1 - absenteeism) * (1 - indirect_ratio))

        prediction_df = pd.DataFrame({
            'Metric': [
                'Current Output (buses)',
                'Target Output (buses)',
                'Required Direct Manpower',
                'Adjusted Total Manpower'
            ],
            'Value': [
                current_output,
                target_output,
                round(required_direct, 2),
                round(adjusted_total, 2)
            ]
        })

        st.dataframe(prediction_df, use_container_width=True)
        st.success(f"✅ Estimated Required Manpower: **{round(adjusted_total)}** people for {target_output} buses/month.")

# Show info when no file is uploaded
else:
    st.info("📤 Please upload your workforce Excel file to start analysis.")
