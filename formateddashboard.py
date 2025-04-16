import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


st.set_page_config(page_title="Enrollment Dashboard", layout="wide")
st.title("📊 Enrollment Data Dashboard")

# Use tabs to split functionality
tab1, tab2, tab3 = st.tabs(["Upload Data", "Search Open Sections", "Section-Level View"])

with tab1:
    st.header("Upload Enrollment Data")
    uploaded_file = st.file_uploader("Upload a CSV File", type=["csv"])

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)

            required_cols = {'SOC Class Nbr', 'Name'}
            if not required_cols.issubset(df.columns):
                st.error("CSV must include 'SOC Class Nbr' and 'Name' columns.")
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
        st.warning("Please upload a CSV file in the first tab.")
    else:
        required_search_cols = {'Subject', 'Num', 'Tot Enrl', 'Enr Cpcty', 'Descr', 'Begin Time', 'End Time'}
        if not required_search_cols.issubset(final_df.columns):
            st.error(f"Uploaded CSV must include these columns: {', '.join(required_search_cols)}")
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
    st.header("🔍 Section-Level Enrollment View")

    final_df = st.session_state.get('cleaned_df')

    if final_df is None:
        st.warning("Please upload a CSV file in the first tab.")
    elif not {'SOC Class Nbr', 'Subject', 'Num', 'Tot Enrl', 'Enr Cpcty', 'Wait Tot Enrl', 'Wait Cap', 'Location'}.issubset(final_df.columns):
        st.error("Uploaded CSV must include 'SOC Class Nbr', 'Subject', 'Num', 'Tot Enrl', 'Enr Cpcty', 'Wait Tot Enrl', 'Wait Cap', and 'Location'.")
    else:
        subject_options_sec = sorted(final_df['Subject'].dropna().unique())
        selected_subject_sec = st.selectbox("Select Subject", subject_options_sec, key="subject_sec")

        if selected_subject_sec:
            course_nums_sec = sorted(final_df[final_df['Subject'] == selected_subject_sec]['Num'].dropna().unique())
            selected_num_sec = st.selectbox("Select Course Number", course_nums_sec, key="num_sec")

            if selected_num_sec:
                section_df = final_df[
                    (final_df['Subject'] == selected_subject_sec) &
                    (final_df['Num'] == selected_num_sec)
                ]

                section_ids = sorted(section_df['SOC Class Nbr'].dropna().unique())
                selected_section = st.selectbox("Select Section (Class Nbr)", section_ids, key="class_nbr_sec")

                if selected_section:
                    section_info = section_df[section_df['SOC Class Nbr'] == selected_section]

                    st.subheader(f"📘 Enrollment Details for Section {selected_section}")

                    for idx, row in section_info.iterrows():
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Course Description:** {row.get('Descr', 'N/A')}")
                            st.markdown(f"**Location (Campus):** {row.get('Location', 'N/A')}")
                            st.markdown(f"**Total Enrolled:** {row.get('Tot Enrl', 'N/A')}")
                            st.markdown(f"**Enrollment Capacity:** {row.get('Enr Cpcty', 'N/A')}")

                        with col2:
                            st.markdown(f"**Waitlist Total Enrolled:** {row.get('Wait Tot Enrl', 'N/A')}")
                            st.markdown(f"**Waitlist Capacity:** {row.get('Wait Cap', 'N/A')}")
                            st.markdown(f"**Instructor(s):** {row.get('Name', 'N/A')}")

                    # Breakdown of enrollments by campus for this course (across all sections)
                    st.markdown("#### 🏫 Campus Breakdown for This Course")

                    campus_breakdown = (
                        section_df.groupby('Location')[['Tot Enrl', 'Enr Cpcty', 'Wait Tot Enrl', 'Wait Cap']]
                        .sum()
                        .sort_values(by='Tot Enrl', ascending=False)
                        .reset_index()
                    )

                    st.dataframe(campus_breakdown, use_container_width=True)
