import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Manpower Planning Dashboard", layout="wide")
st.title("🚀 Predictive Manpower Allocation Tool")

# Upload Excel file
uploaded_file = st.file_uploader("📂 Upload the Weekly Plan Excel file", type=["xlsx"])
if uploaded_file:
    xl = pd.ExcelFile(uploaded_file)
    st.sidebar.success(f"Available sheets: {xl.sheet_names}")

    # Load 'Manhours' sheet
    df = xl.parse("Manhours")
    df.columns = df.columns.str.strip()
    df = df.dropna(how='all')
    df = df.dropna(subset=["Station", "Process", "Number of people"])

    # Filters
    st.sidebar.header("📊 Filter Options")
    selected_station = st.sidebar.multiselect("Select Station(s)", options=df["Station"].unique(), default=df["Station"].unique())
    selected_process = st.sidebar.multiselect("Select Process(es)", options=df["Process"].unique(), default=df["Process"].unique())

    filtered_df = df[df["Station"].isin(selected_station) & df["Process"].isin(selected_process)]

    # Group by Station and Process
    staffing_summary = filtered_df.groupby(['Station', 'Process'])['Number of people'].sum().reset_index()
    station_totals = staffing_summary.groupby("Station")["Number of people"].sum().reset_index()

    # Staffing Chart
    st.subheader("📈 Staffing Distribution by Process and Station")
    fig1 = px.bar(
        staffing_summary.sort_values(by="Number of people", ascending=False),
        x="Process", y="Number of people", color="Station",
        title="Staffing by Process and Station", text="Number of people"
    )
    fig1.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig1, use_container_width=True)

    # Predictive Inputs
    st.subheader("🧮 Manpower Prediction Inputs")
    with st.form("manpower_form"):
        STU = st.number_input("⏱ Standard Time per Unit (minutes)", min_value=1, value=51840)
        working_days = st.number_input("📆 Working Days per Month", min_value=1, value=21)
        hours_per_day = st.number_input("⏰ Work Hours per Day", min_value=1, value=8)
        absenteeism_rate = st.slider("🚫 Absenteeism Rate (%)", min_value=0, max_value=20, value=5) / 100
        indirect_ratio = st.slider("👥 Indirect Manpower Ratio (%)", min_value=0, max_value=50, value=10) / 100
        actual_output = st.number_input("📦 Current Output (Number of Buses)", min_value=1, value=7)
        target_output = st.number_input("🎯 Target Output (Number of Buses)", min_value=1, value=10)
        submitted = st.form_submit_button("🔍 Calculate")

    if submitted:
        # Calculations
        AWH = working_days * hours_per_day
        efficiency_factor = actual_output / target_output
        EHE = AWH * efficiency_factor * (1 - absenteeism_rate)

        current_direct_staff = filtered_df["Number of people"].sum()
        required_direct_manpower = (target_output * STU / 60) / (AWH * efficiency_factor * (1 - absenteeism_rate))
        required_indirect_manpower = required_direct_manpower * indirect_ratio
        total_required_manpower = required_direct_manpower + required_indirect_manpower

        # Predictive Distribution
        staffing_summary["Current_Proportion"] = staffing_summary["Number of people"] / staffing_summary["Number of people"].sum()
        staffing_summary["Predicted_Number_of_People"] = staffing_summary["Current_Proportion"] * required_direct_manpower
        staffing_summary["Predicted_Number_of_People"] = staffing_summary["Predicted_Number_of_People"].round(2)

        # Summary Metrics
        st.subheader("📌 Summary Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Target Output", target_output)
        col2.metric("Current Direct Staff", int(current_direct_staff))
        col3.metric("Available Working Hours", AWH)

        col4, col5, col6 = st.columns(3)
        col4.metric("Efficiency Factor", f"{efficiency_factor:.2f}")
        col5.metric("Effective Hours/Employee", f"{EHE:.2f}")
        col6.metric("Required Direct Staff", f"{required_direct_manpower:.2f}")

        col7, col8 = st.columns(2)
        col7.metric("Required Indirect Staff", f"{required_indirect_manpower:.2f}")
        col8.metric("Total Required Staff", f"{total_required_manpower:.2f}")

        # Predicted Staffing Table
        st.subheader("📋 Predicted Staffing by Process and Station")
        st.dataframe(
            staffing_summary[["Station", "Process", "Number of people", "Predicted_Number_of_People"]],
            use_container_width=True
        )

        # Download Button
        csv = staffing_summary.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Predicted Staffing", data=csv, file_name="predicted_staffing.csv", mime="text/csv")

        # Comparison Chart
        fig3 = px.bar(
            staffing_summary,
            x="Process",
            y=["Number of people", "Predicted_Number_of_People"],
            barmode="group",
            color="Station",
            title="Predicted vs Current Staffing"
        )
        fig3.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig3, use_container_width=True)

else:
    st.info("📁 Please upload a valid Excel file to begin.")
