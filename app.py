import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Manpower Planning Tool", layout="wide")
st.title("Predictive Manpower Allocation")

# Upload Excel file
uploaded_file = st.file_uploader("Upload the Weekly Plan Excel file", type=["xlsx"])
if uploaded_file:
    xl = pd.ExcelFile(uploaded_file)
    df = xl.parse("Manhours")
    df.columns = df.columns.str.strip()
    df = df.dropna(how='all')
    df = df.dropna(subset=["Station", "Process", "Number of people"])

    # Group by Station and Process
    staffing_summary = df.groupby(['Station', 'Process'])['Number of people'].sum().reset_index()

    # User Inputs
    st.sidebar.header("Input Parameters")
    current_output = st.sidebar.number_input("Current Monthly Output (buses)", min_value=1, value=7)
    target_output = st.sidebar.number_input("Target Monthly Output (buses)", min_value=1, value=10)
    STU = st.sidebar.number_input("Standard Time per Unit (minutes)", min_value=1, value=51840)
    working_days = st.sidebar.number_input("Working Days per Month", min_value=1, value=21)
    hours_per_day = st.sidebar.number_input("Work Hours per Day", min_value=1, value=8)
    absenteeism_rate = st.sidebar.slider("Absenteeism Rate (%)", min_value=0, max_value=20, value=5) / 100
    indirect_ratio = st.sidebar.slider("Indirect Manpower Ratio (%)", min_value=0, max_value=50, value=10) / 100

    # Calculations
    AWH = working_days * hours_per_day
    efficiency_factor = current_output / target_output
    EHE = AWH * efficiency_factor * (1 - absenteeism_rate)

    current_direct_staff = df["Number of people"].sum()
    required_direct_manpower = (target_output * STU / 60) / EHE
    required_indirect_manpower = required_direct_manpower * indirect_ratio
    total_required_manpower = required_direct_manpower + required_indirect_manpower

    # Predictive Distribution
    staffing_summary["Current_Proportion"] = staffing_summary["Number of people"] / staffing_summary["Number of people"].sum()
    staffing_summary["Predicted_Number_of_People"] = staffing_summary["Current_Proportion"] * required_direct_manpower
    staffing_summary["Predicted_Number_of_People"] = staffing_summary["Predicted_Number_of_People"].round(2)

    # 📈 Staffing Distribution Chart
    st.subheader("📈 Staffing Distribution by Process and Station")
    fig1 = px.bar(
        staffing_summary.sort_values(by="Number of people", ascending=False),
        x="Process", y="Number of people", color="Station",
        title="Staffing by Process and Station", text="Number of people"
    )
    fig1.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig1, use_container_width=True)

    # 📐 Equation-Based Summary
    st.subheader("📊 Manpower Calculation Summary")
    st.markdown(f"""
    **Equations Used:**

    - AWH = Working Days × Hours per Day  
    - Efficiency Factor = Current Output / Target Output  
    - EHE = AWH × Efficiency × (1 - Absenteeism Rate)  
    - Required Direct = (Target × STU / 60) / EHE  
    - Required Indirect = Direct × Indirect Ratio  
    - Total Required = Direct + Indirect

    **Results:**

    - Current Direct Staff: {int(current_direct_staff)}  
    - Target Output: {target_output} buses  
    - Efficiency Factor: {efficiency_factor:.2f}  
    - Effective Hours per Employee: {EHE:.2f}  
    - Required Direct Manpower: {required_direct_manpower:.2f}  
    - Required Indirect Manpower: {required_indirect_manpower:.2f}  
    - Total Required Manpower: {total_required_manpower:.2f}
    """)

    # 📊 Prediction Table
    st.subheader("🔮 Predicted Staffing by Station and Process")
    st.dataframe(staffing_summary[["Station", "Process", "Number of people", "Predicted_Number_of_People"]],
                 use_container_width=True)

    # 📈 Predicted vs Current Chart
    fig2 = px.bar(
        staffing_summary,
        x="Process",
        y=["Number of people", "Predicted_Number_of_People"],
        barmode="group",
        color="Station",
        title="Predicted vs Current Staffing by Process"
    )
    fig2.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("Please upload a valid Excel file to begin.")
