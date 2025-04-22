import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Enrollment Dashboard", layout="wide")
st.title("📊 Enrollment Data Dashboard")

# Use tabs to split functionality
tab1, tab2, tab3, tab4 = st.tabs(["Upload Data", "Search Open Sections", "Section-Level View", "DLC Course Data"])

with tab1:
    st.header("Upload Enrollment Data")
    uploaded_file = st.file_uploader("Upload a CSV or Excel File", type=["csv", "xlsx"])

    if uploaded_file is not None:
        try:
            # Check the file extension and read accordingly
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)

            required_cols = {'SOC Class Nbr', 'Name'}
            if not required_cols.issubset(df.columns):
                st.error("File must include 'SOC Class Nbr' and 'Name' columns.")
            else:
                unwanted_descrs = {
                    "SHORT TERM/DURATION INTERNSHIP",
                    "Engr Internship",
                    "Engr Intern",
                    "Engr Intl Intern",
                    "Engr Coop",
                    "Engr Intl Coop",
                    "Research Projects",
                    "Master's Research",
                    "Thesis Research",
                    "D.Eng. Praxis Research",
                    "Engineering Research Methods"
                }

                if "Descr" in df.columns:
                    df = df[~df['Descr'].isin(unwanted_descrs)]

                # Combine names for duplicate SOC Class Nbr values
                merged_names = df.groupby('SOC Class Nbr')['Name'].apply(
                    lambda names: ', '.join(str(name) for name in names if pd.notna(name))
                ).reset_index()

                # Keep the first of each duplicated SOC Class Nbr and drop old Name
                deduped_df = df.drop_duplicates(subset='SOC Class Nbr', keep='first').copy()
                final_df = pd.merge(deduped_df.drop(columns=['Name']), merged_names, on='SOC Class Nbr')

                st.subheader("Preview of Cleaned Data")
                st.dataframe(final_df, use_container_width=True)

                # Make CSV downloadable
                csv = final_df.to_csv(index=False).encode('utf-8')
                st.download_button("Download Cleaned CSV", data=csv, file_name="cleaned_schedule.csv", mime="text/csv")

                # Store cleaned data in session state
                st.session_state['cleaned_df'] = final_df

        except Exception as e:
            st.error(f"Error processing the file: {e}")
            
with tab2:
    st.header("Select a Course")

    final_df = st.session_state.get('cleaned_df')

    if final_df is None:
        st.warning("Please upload a file in the first tab.")
    else:
        required_search_cols = {'Subject', 'Num', 'Tot Enrl', 'Enr Cpcty', 'Descr', 'Begin Time', 'End Time'}
        if not required_search_cols.issubset(final_df.columns):
            st.error(f"Uploaded file must include these columns: {', '.join(required_search_cols)}")
        else:
            subject_options = sorted(final_df['Subject'].dropna().unique())
            subject_options_with_placeholder = ["Select a subject"] + subject_options
            selected_subject = st.selectbox("Select Subject", subject_options_with_placeholder)

            if selected_subject != "Select a subject":
                course_nums = sorted(
                    final_df[final_df['Subject'] == selected_subject]['Num'].dropna().unique()
                )
                course_nums_with_placeholder = ["Select a course number"] + course_nums
                selected_num = st.selectbox("Select Course Number", course_nums_with_placeholder)

                if selected_num != "Select a course number":
                    course_df = final_df[
                        (final_df['Subject'] == selected_subject) &
                        (final_df['Num'] == selected_num)
                    ]

                    # Open sections = where enrolled < capacity
                    open_sections = course_df[
                        pd.to_numeric(course_df['Tot Enrl'], errors='coerce') <
                        pd.to_numeric(course_df['Enr Cpcty'], errors='coerce')
                    ]

                    if not open_sections.empty:
                        st.markdown("### Open Sections")

                        for idx, row in open_sections.iterrows():
                            with st.expander(f"{row['Descr']} — {row['Begin Time']} to {row['End Time']}"):
                                col1, col2 = st.columns(2)

                                with col1:
                                    st.markdown(f"**Course Description:** {row.get('Descr', 'N/A')}")
                                    st.markdown(f"**Start Time:** {row.get('Begin Time', 'N/A')}")
                                    st.markdown(f"**End Time:** {row.get('End Time', 'N/A')}")
                                    st.markdown(f"**Location:** {row.get('Location', 'N/A')}")

                                with col2:
                                    st.markdown(f"**Instructors:** {row.get('Name', 'N/A')}")
                                    st.markdown(f"**Total Enrolled:** {row.get('Tot Enrl', 'N/A')}")
                                    st.markdown(f"**Enrollment Capacity:** {row.get('Enr Cpcty', 'N/A')}")
                    else:
                        st.warning("No open sections found for this course.")

                    # ----------- Enrollment by Campus Section ------------
                                        
                    if 'Location' in course_df.columns:
                        st.markdown("### Enrollment by Campus")

                        # Clean numeric enrollment values
                        course_df['Tot Enrl'] = pd.to_numeric(course_df['Tot Enrl'], errors='coerce')

                        enrollment_by_location = (
                            course_df.groupby('Location')['Tot Enrl']
                            .sum()
                            .sort_values(ascending=False)
                            .reset_index()
                        )

                        # Display table
                        st.dataframe(enrollment_by_location, use_container_width=True)

                    else:
                        st.info("No 'Location' column found in your data to show campus-wise enrollment.")


with tab3:
    st.header("Section-Level Enrollment View")

    final_df = st.session_state.get('cleaned_df')

    if final_df is None:
        st.warning("Please upload a CSV file in the first tab.")
    elif not {'SOC Class Nbr', 'Subject', 'Num', 'Section', 'Descr', 'Campus', 'Location',
              'Tot Enrl', 'Enr Cpcty', 'Wait Tot', 'Wait Cap', 'Name'}.issubset(final_df.columns):
        st.error("Uploaded CSV must include all required columns.")
    else:
        subject_options_sec = sorted(final_df['Subject'].dropna().unique())
        selected_subject_sec = st.selectbox("Select Subject", subject_options_sec, key="subject_sec")

        if selected_subject_sec:
            course_nums_sec = sorted(final_df[final_df['Subject'] == selected_subject_sec]['Num'].dropna().unique())
            selected_num_sec = st.selectbox("Select Course Number", course_nums_sec, key="num_sec")

            if selected_num_sec:
                course_df = final_df[
                    (final_df['Subject'] == selected_subject_sec) &
                    (final_df['Num'] == selected_num_sec)
                ]

                section_ids = sorted(course_df['SOC Class Nbr'].dropna().unique())
                selected_section = st.selectbox("Select Section (Class Nbr)", section_ids, key="class_nbr_sec")

                if selected_section:
                    section_info = course_df[course_df['SOC Class Nbr'] == selected_section]

                    st.subheader(f"Enrollment Details for Section {selected_section}")

                    for idx, row in section_info.iterrows():
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Course:** {row.get('Subject')} {row.get('Num')} - {row.get('Section')}")
                            st.markdown(f"**Course Title:** {row.get('Descr')}")
                            st.markdown(f"**Campus:** {row.get('Campus')}")
                            st.markdown(f"**Location:** {row.get('Location')}")
                            st.markdown(f"**Instructor:** {row.get('Name')}")
                        with col2:
                            st.markdown(f"**Total Enrolled:** {row.get('Tot Enrl')}")
                            st.markdown(f"**Enrollment Capacity:** {row.get('Enr Cpcty')}")
                            st.markdown(f"**Waitlist Total:** {row.get('Wait Tot')}")
                            st.markdown(f"**Waitlist Capacity:** {row.get('Wait Cap')}")

                    # 📊 Breakdown by Campus for the course (all sections)
                    st.markdown("#### Campus Breakdown Across All Sections of This Course")

                    campus_breakdown = (
                        course_df.groupby(['Campus', 'Location'])[['Tot Enrl', 'Enr Cpcty', 'Wait Tot', 'Wait Cap']]
                        .sum()
                        .sort_values(by='Tot Enrl', ascending=False)
                        .reset_index()
                    )

                    st.dataframe(campus_breakdown, use_container_width=True)
with tab4:
    st.header("View DLC Courses")

    final_df = st.session_state.get('cleaned_df')

    if final_df is None:
        st.warning("Please upload a CSV file in the first tab.")
    elif not {'Subject', 'Num', 'Section', 'Location', 'Tot Enrl', 'Enr Cpcty', 'Wait Tot', 'Wait Cap'}.issubset(final_df.columns):
        st.error("Uploaded CSV must include all required columns for this view.")
    else:
        # Filter to sections that have a "V" in the Section
        dlc_df = final_df[final_df['Section'].astype(str).str.contains('V', na=False)]

        if dlc_df.empty:
            st.info("No courses with 'V' sections found.")
        else:
            # Get unique course numbers that have a V section
            dlc_courses = dlc_df[['Subject', 'Num']].drop_duplicates()
            dlc_courses['Course'] = dlc_courses['Subject'].astype(str).str.strip() + " " + dlc_courses['Num'].astype(str).str.strip()

            selected_course = st.selectbox("Select a DLC Course", ["Select a course"] + dlc_courses['Course'].tolist())

            if selected_course != "Select a course":
                # Instead of simple split, use the dataframe to match
                selected_subject = selected_course.split(' ')[0]
                selected_num = ' '.join(selected_course.split(' ')[1:])

                selected_course_df = dlc_df[
                    (dlc_df['Subject'].astype(str).str.strip() == selected_subject) &
                    (dlc_df['Num'].astype(str).str.strip() == selected_num)
                ]

                if selected_course_df.empty:
                    st.warning("No data available for the selected course.")
                else:
                    
                    st.subheader(f"Enrollment Summary for {selected_course}")

                    # Sum the columns across all 'V' sections
                    summary = selected_course_df[['Enr Cpcty', 'Tot Enrl', 'Wait Cap', 'Wait Tot']].apply(pd.to_numeric, errors='coerce').sum()
                    st.markdown(
                        f"""
                        <h3 style='margin-bottom: 0;'>{'Total Enrolled —'} {int(summary['Tot Enrl'])}</h3>
                        """,
                        unsafe_allow_html=True
                    )
                    #st.metric("Total Enrolled", int(summary['Tot Enrl']))
                    st.metric("Total Enrollment Capacity", int(summary['Enr Cpcty']))
                    st.metric("Total on Waitlist", int(summary['Wait Tot']))
                    st.metric("Total Waitlist Capacity", int(summary['Wait Cap']))

                    st.divider()

                    # Show available seats before detailed table
                    st.subheader("Available Seats by Location")

                    detailed_table = selected_course_df[['Section', 'Location', 'Enr Cpcty', 'Tot Enrl', 'Wait Cap', 'Wait Tot']]

                    available_seats = []
                    for idx, row in detailed_table.iterrows():
                        try:
                            tot_enrl = pd.to_numeric(row['Tot Enrl'], errors='coerce')
                            enr_cpcty = pd.to_numeric(row['Enr Cpcty'], errors='coerce')
                            location = row['Location']

                            if pd.notnull(tot_enrl) and pd.notnull(enr_cpcty) and (enr_cpcty > tot_enrl) and location != '':
                                seats_available = int(enr_cpcty - tot_enrl)
                                available_seats.append(f"{location} has {seats_available} seats available")
                        except Exception:
                            continue

                    if available_seats:
                        for seat_info in available_seats:
                            st.write(seat_info)
                    else:
                        st.write("No locations with available seats.")

                    st.divider()

                    # Section and Location Breakdown
                    st.subheader("Section and Location Breakdown")

                    # Create a total row
                    total_row = {
                        'Section': 'TOTAL',
                        'Location': '',
                        'Tot Enrl': detailed_table['Tot Enrl'].apply(pd.to_numeric, errors='coerce').sum(),
                        'Enr Cpcty': detailed_table['Enr Cpcty'].apply(pd.to_numeric, errors='coerce').sum(),
                        'Wait Tot': detailed_table['Wait Tot'].apply(pd.to_numeric, errors='coerce').sum(),
                        'Wait Cap': detailed_table['Wait Cap'].apply(pd.to_numeric, errors='coerce').sum(),
                    }

                    # Append the total row
                    detailed_table = pd.concat([detailed_table, pd.DataFrame([total_row])], ignore_index=True)

                    st.dataframe(detailed_table, use_container_width=True)