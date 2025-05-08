import streamlit as st
import pandas as pd
import io
from collections import defaultdict

st.set_page_config(page_title="Duplicate Checker with Root Cause Grouping", layout="wide")
st.title("🔍 Duplicate Analyzer + Root Cause Group Summary")

uploaded_file = st.file_uploader("Upload your CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("✅ File uploaded successfully!")

        df.columns = df.columns.astype(str)
        column_to_check = st.selectbox("Select a column to check for duplicates", df.columns)

        show_root_cause = st.checkbox("🔍 Show root cause columns and value breakdown")
        show_conflict_group_summary = st.checkbox("📊 Show grouped summary of conflicting column sets")

        if st.button("Analyze"):
            col_data = df[column_to_check]

            total_values = len(col_data)
            unique_values = col_data.nunique()
            duplicated_values_count = col_data.duplicated().sum()
            null_count = col_data.isna().sum()

            duplicate_summary = col_data.value_counts()[col_data.value_counts() > 1]
            duplicate_df = duplicate_summary.reset_index()
            duplicate_df.columns = [column_to_check, 'Count']

            st.subheader("📊 Summary")
            st.markdown(f"🔹 Total values in column: `{total_values}`")
            st.markdown(f"🔹 Unique values: `{unique_values}`")
            st.markdown(f"🔹 Duplicated values (occurred more than once): `{len(duplicate_summary)}`")
            st.markdown(f"🔹 Null values: `{null_count}`")

            if not duplicate_df.empty:
                st.subheader("📄 Duplicated Value Details")
                st.dataframe(duplicate_df, use_container_width=True)

                # Download
                csv_buffer = io.StringIO()
                duplicate_df.to_csv(csv_buffer, index=False)
                st.download_button("📥 Download Duplicates as CSV", csv_buffer.getvalue(), file_name="duplicate_values.csv", mime="text/csv")

                # --- Root Cause Analysis ---
                duplicated_groups = df[df.duplicated(column_to_check, keep=False)]
                grouped = duplicated_groups.groupby(column_to_check)

                root_cause_list = []
                grouped_summary = defaultdict(lambda: {'groups': 0, 'rows': 0})

                for val, group in grouped:
                    diff_cols = group.nunique(dropna=False)
                    varied_cols = diff_cols[diff_cols > 1].index.tolist()

                    if column_to_check in varied_cols:
                        varied_cols.remove(column_to_check)

                    # Store value-level root cause (if enabled)
                    if show_root_cause:
                        conflicting_values = {
                            col: group[col].dropna().unique().tolist()
                            for col in varied_cols
                        }
                        root_cause_list.append({
                            column_to_check: val,
                            'Conflicting_Columns': ", ".join(varied_cols) if varied_cols else "None",
                            'Conflicting_Values': conflicting_values if conflicting_values else "None"
                        })

                    # Update grouped summary
                    if show_conflict_group_summary:
                        key = frozenset(varied_cols)
                        grouped_summary[key]['groups'] += 1
                        grouped_summary[key]['rows'] += group.shape[0]

                # Root Cause Value Display
                if show_root_cause and root_cause_list:
                    st.subheader("🧪 Root Cause with Actual Values")
                    root_df = pd.DataFrame(root_cause_list)
                    st.dataframe(root_df, use_container_width=True)

                    # Download
                    root_csv = io.StringIO()
                    root_df.to_csv(root_csv, index=False)
                    st.download_button("📥 Download Root Cause Report", root_csv.getvalue(), file_name="root_cause_report.csv", mime="text/csv")

                # Grouped Conflict Set Summary
                if show_conflict_group_summary and grouped_summary:
                    st.subheader("📊 Grouped Conflicting Columns Summary")

                    summary_data = []
                    for key, stats in grouped_summary.items():
                        summary_data.append({
                            'Conflicting_Columns': ", ".join(sorted(key)) if key else 'None',
                            'Affected_Duplicate_Groups': stats['groups'],
                            'Affected_Rows': stats['rows']
                        })

                    summary_df = pd.DataFrame(summary_data)
                    st.dataframe(summary_df.sort_values(by='Affected_Rows', ascending=False), use_container_width=True)

                    # Download
                    summary_csv = io.StringIO()
                    summary_df.to_csv(summary_csv, index=False)
                    st.download_button("📥 Download Grouped Conflict Summary", summary_csv.getvalue(), file_name="conflict_group_summary.csv", mime="text/csv")

            else:
                st.info("✅ No duplicate values found in the selected column.")

    except Exception as e:
        st.error(f"❌ Error while processing file: {str(e)}")
