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
    required_direct_manpower = (target_output * STU / 60) / (AWH * efficiency_factor * (1 - absenteeism_rate))
    required_indirect_manpower = required_direct_manpower * indirect_ratio
    total_required_manpower = required_direct_manpower + required_indirect_manpower

    # Predictive Distribution
    staffing_summary["Current_Proportion"] = staffing_summary["Number of people"] / staffing_summary["Number of people"].sum()
    staffing_summary["Predicted_Number_of_People"] = staffing_summary["Current_Proportion"] * required_direct_manpower
    staffing_summary["Predicted_Number_of_People"] = staffing_summary["Predicted_Number_of_People"].round(2)

    # Display Equations and Results
    st.subheader("Manpower Calculation Summary")

    st.markdown(f"""
    **Equations Used:**

    - Available Working Hours (AWH) = Working Days × Hours per Day  
    - Efficiency Factor = Current Output / Target Output  
    - Effective Hours per Employee (EHE) = AWH × Efficiency Factor × (1 - Absenteeism Rate)  
    - Required Direct Manpower = (Target Output × STU / 60) / EHE  
    - Required Indirect Manpower = Direct × Indirect Ratio  
    - Total Required Manpower = Direct + Indirect

    **Results:**

    - Current Direct Staff: {int(current_direct_staff)}  
    - Target Output: {target_output} buses  
    - Standard Time per Unit: {STU} minutes  
    - Working Days: {working_days}  
    - Work Hours/Day: {hours_per_day}  
    - Absenteeism Rate: {absenteeism_rate * 100:.1f}%  
    - Efficiency Factor: {efficiency_factor:.2f}  
    - Effective Hours per Employee: {EHE:.2f}  
    - Required Direct Manpower: {required_direct_manpower:.2f}  
    - Required Indirect Manpower: {required_indirect_manpower:.2f}  
    - Total Required Manpower: {total_required_manpower:.2f}
    """)

    # Display Prediction Table
    st.subheader("Predicted Staffing by Station and Process")
    st.dataframe(staffing_summary[["Station", "Process", "Number of people", "Predicted_Number_of_People"]],
                 use_container_width=True)

    # Bar Chart: Predicted vs Current
    fig = px.bar(staffing_summary,
                 x="Process",
                 y=["Number of people", "Predicted_Number_of_People"],
                 barmode="group",
                 color="Station",
                 title="Predicted vs Current Staffing by Process")
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Please upload a valid Excel file to begin.")
