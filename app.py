    # -------------------- TAB 4 --------------------
    with tab4:
        st.subheader("📊 Predictive Manpower Allocation")

        # Sidebar only appears in tab4
        with st.sidebar:
            st.header("Prediction Parameters")
            current_output = st.number_input("Current Monthly Output (buses)", min_value=1, value=7)
            target_output = st.number_input("Target Monthly Output (buses)", min_value=1, value=10)
            STU = st.number_input("Standard Time per Unit (minutes)", min_value=1, value=51840)
            working_days = st.number_input("Working Days per Month", min_value=1, value=21)
            hours_per_day = st.number_input("Work Hours per Day", min_value=1, value=8)
            absenteeism_rate = st.slider("Absenteeism Rate (%)", min_value=0, max_value=20, value=5) / 100
            indirect_ratio = st.slider("Indirect Manpower Ratio (%)", min_value=0, max_value=50, value=10) / 100

        # Calculations
        AWH = working_days * hours_per_day
        efficiency_factor = current_output / target_output
        EHE = AWH * efficiency_factor * (1 - absenteeism_rate)
        current_direct_staff = df["Number of people"].sum()
        required_direct_manpower = (target_output * STU / 60) / EHE
        required_indirect_manpower = required_direct_manpower * indirect_ratio
        total_required_manpower = required_direct_manpower + required_indirect_manpower

        # Predicted staffing per process
        pred_staffing_summary = df.groupby(['Station', 'Process'])['Number of people'].sum().reset_index()
        pred_staffing_summary["Current_Proportion"] = pred_staffing_summary["Number of people"] / pred_staffing_summary["Number of people"].sum()
        pred_staffing_summary["Predicted_Number_of_People"] = pred_staffing_summary["Current_Proportion"] * required_direct_manpower
        pred_staffing_summary["Predicted_Number_of_People"] = pred_staffing_summary["Predicted_Number_of_People"].round(2)

        st.subheader("📐 Summary of Prediction")
        st.markdown(f"""
        - Current Direct Staff: **{int(current_direct_staff)}**  
        - Target Output: **{target_output} buses**  
        - Required Direct Manpower: **{required_direct_manpower:.2f}**  
        - Required Indirect Manpower: **{required_indirect_manpower:.2f}**  
        - **Total Required Manpower: {total_required_manpower:.2f}**
        """)

        st.subheader("🔮 Predicted Staffing by Station and Process")
        st.dataframe(pred_staffing_summary[["Station", "Process", "Number of people", "Predicted_Number_of_People"]],
                     use_container_width=True)
