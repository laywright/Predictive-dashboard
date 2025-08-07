import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy import stats

# --- Page Configuration ---
st.set_page_config(page_title="Unified Manpower Dashboard", page_icon="🚌", layout="wide")
st.title("🚌 Unified Manpower Dashboard")

# --- File Upload ---
uploaded_file = st.file_uploader("Upload the Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name='Manhours')
    df.columns = df.columns.str.strip()
    df = df.dropna(how='all')
    df = df.dropna(subset=["Station", "Process", "Number of people"])
    df['Number of people'] = pd.to_numeric(df['Number of people'], errors='coerce')

    # Extract bus columns excluding Bus 21–24
    bus_columns = [col for col in df.columns if str(col).startswith('Bus') and col not in ['Bus 21', 'Bus 22', 'Bus 23', 'Bus 24']]
    df['Avg_Time_Per_Process'] = df[bus_columns].mean(axis=1)
    df['Variance'] = df[bus_columns].var(axis=1)
    df['Avg_Manhours'] = df[bus_columns].mean(axis=1)
    df['Manhours per person'] = df['Avg_Manhours'] / df['Number of people'].replace(0, pd.NA)

    # --- Sidebar Inputs for Prediction ---
    st.sidebar.header("🧮 Prediction Parameters")
    current_output = st.sidebar.number_input("Current Monthly Output (buses)", min_value=1, value=7)
    target_output = st.sidebar.number_input("Target Monthly Output (buses)", min_value=1, value=10)
    STU = st.sidebar.number_input("Standard Time per Unit (minutes)", min_value=1, value=51840)
    working_days = st.sidebar.number_input("Working Days per Month", min_value=1, value=21)
    hours_per_day = st.sidebar.number_input("Work Hours per Day", min_value=1, value=8)
    absenteeism_rate = st.sidebar.slider("Absenteeism Rate (%)", 0, 20, 5) / 100
    indirect_ratio = st.sidebar.slider("Indirect Manpower Ratio (%)", 0, 50, 10) / 100

    # --- Prediction Calculation ---
    AWH = working_days * hours_per_day
    efficiency_factor = current_output / target_output
    EHE = AWH * efficiency_factor * (1 - absenteeism_rate)
    current_direct_staff = df["Number of people"].sum()
    required_direct_manpower = (target_output * STU / 60) / EHE
    required_indirect_manpower = required_direct_manpower * indirect_ratio
    total_required_manpower = required_direct_manpower + required_indirect_manpower

    # --- Predictive Distribution ---
    staffing_summary = df.groupby(['Station', 'Process'])['Number of people'].sum().reset_index()
    staffing_summary["Current_Proportion"] = staffing_summary["Number of people"] / staffing_summary["Number of people"].sum()
    staffing_summary["Predicted_Number_of_People"] = staffing_summary["Current_Proportion"] * required_direct_manpower
    staffing_summary["Predicted_Number_of_People"] = staffing_summary["Predicted_Number_of_People"].round(2)

    # --- Add Prediction Column to Main DataFrame ---
    df = df.merge(staffing_summary[['Station', 'Process', 'Predicted_Number_of_People']], on=['Station', 'Process'], how='left')

    # --- TABS ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary", "⏱ Process Time", "🧠 HR Gaps", "🔮 Predictions"])

    # --- TAB 1: Summary ---
    with tab1:
        st.subheader("Total Manhours Summary")
        total_hours = df[bus_columns].multiply(df['Number of people'], axis=0).sum()
        total_df = pd.DataFrame({'Bus': bus_columns, 'Manhours': total_hours.values})
        avg_manhours = total_df['Manhours'].mean()

        st.metric("Average total manhours per bus", f"{avg_manhours:.1f} hrs")

        selected_bus = st.selectbox("View Manhours for specific bus", bus_columns)
        st.write(f"**{selected_bus} Manhours:** {total_hours[selected_bus]:.1f} hrs")

        fig1 = px.bar(total_df, x='Bus', y='Manhours', title="Total manhours per bus",
                      labels={'Bus': 'Bus', 'Manhours': 'Total Manhours'},
                      color_discrete_sequence=['green'], text='Manhours')
        fig1.update_layout(hovermode="x unified")
        st.plotly_chart(fig1, use_container_width=True)

    # --- TAB 2: Process Time Analysis ---
    with tab2:
        st.subheader("Average time per process")
        process_avg_df = df[['Process', 'Avg_Time_Per_Process']].dropna().sort_values(by='Avg_Time_Per_Process', ascending=False)

        fig2 = px.bar(process_avg_df, x='Process', y='Avg_Time_Per_Process',
                      title='Average Time per Process Across All Buses',
                      labels={'Avg_Time_Per_Process': 'Avg Time (hrs)'}, text='Avg_Time_Per_Process')
        fig2.update_layout(yaxis_range=[0, 30], xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)

    # --- TAB 3: HR Allocation Gaps ---
    with tab3:
        st.subheader("Human Resource Allocation Gaps")
        gap_df = df[['Station', 'Process', 'Avg_Manhours', 'Number of people', 'Manhours per person', 'Predicted_Number_of_People']].dropna()
        gap_df = gap_df.sort_values(by='Manhours per person', ascending=False)

        fig3 = px.bar(gap_df, x='Process', y='Manhours per person', color='Station',
                      title='HR Allocation Gaps by Process',
                      labels={'Manhours per person': 'Manhours/Person'}, text='Manhours per person')
        fig3.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig3, use_container_width=True)

    # --- TAB 4: Predictions ---
    with tab4:
        st.subheader("Predicted Staffing by Station and Process")

        st.dataframe(df[['Station', 'Process', 'Number of people', 'Predicted_Number_of_People']],
                     use_container_width=True)

        st.markdown(f"""
        ### 📐 Manpower Calculation Summary

        - Current Direct Staff: **{int(current_direct_staff)}**
        - Target Output: **{target_output} buses**
        - Required Direct Manpower: **{required_direct_manpower:.2f}**
        - Required Indirect Manpower: **{required_indirect_manpower:.2f}**
        - Total Required Manpower: **{total_required_manpower:.2f}**
        """)

else:
    st.info("📂 Please upload a valid Excel file to begin.")
