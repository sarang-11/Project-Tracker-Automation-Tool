import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
from io import StringIO
import plotly.express as px
from st_aggrid import GridOptionsBuilder, AgGrid, JsCode

# ---- Google Sheets Setup ----
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPE
)

client = gspread.authorize(creds)
sheet = client.open("Project Tracker").sheet1

# ---- Auto Initialize Sheet Header if Empty ----
if len(sheet.get_all_values()) == 0:
    sheet.append_row(['Project Name', 'Description', 'Status', 'Start Date', 'Due Date'])

# ---- Read Data ----
data = sheet.get_all_records()
df = pd.DataFrame(data)

# ---- Status & Progress Mapping ----
progress_map = {
    "Not Started": 0,
    "In Progress": 50,
    "On Hold": 25,
    "Completed": 100
}

# ---- Convert Dates & Calculate ----
if not df.empty:
    df["Start Date"] = pd.to_datetime(df["Start Date"])
    df["Due Date"] = pd.to_datetime(df["Due Date"])
    df["Status"] = df["Status"].str.strip().str.title()
    df["Days Left"] = (df["Due Date"] - pd.Timestamp.today()).dt.days
    df["Progress"] = df["Status"].map(progress_map)

# ---- Streamlit Config ----
st.set_page_config(page_title="📌 Project Tracker", layout="wide")

st.markdown("""
    <style>
        body { background-color: #0e1117; color: white; }
        .stApp { background-color: #0e1117; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: white;'>📌 Internal Project Tracker</h1>", unsafe_allow_html=True)

# ---- Add New Project ----
with st.expander("➕ Add New Project"):
    with st.form("project_form"):
        pname = st.text_input("Project Name")
        desc = st.text_area("Description")
        status_options = list(progress_map.keys())
        status = st.selectbox("Status", status_options)
        sdate = st.date_input("Start Date", date.today())
        ddate = st.date_input("Due Date", date.today())
        submitted = st.form_submit_button("Add Project")
        if submitted and pname:
            sheet.append_row([pname, desc, status, str(sdate), str(ddate)])
            st.success(f"✅ Project '{pname}' added!")

# ---- Filter Projects ----
st.sidebar.markdown("### 🔍 Filter Projects")
status_filter = st.sidebar.multiselect("Filter by Status", list(progress_map.keys()), default=list(progress_map.keys()))

filtered_df = df[df['Status'].isin(status_filter)] if not df.empty else pd.DataFrame()

# ---- Display Projects ----
if filtered_df.empty:
    st.info("No projects to display.")
else:
    for i, row in filtered_df.iterrows():
        with st.expander(f"📁 {row['Project Name']}"):
            st.write(f"📝 **Description**: {row['Description']}")
            st.write(f"📌 **Status**: {row['Status']}")
            st.progress(int(row["Progress"]))
            st.write(f"⏰ **Start Date**: {row['Start Date'].date()}")
            st.write(f"📅 **Due Date**: {row['Due Date'].date()}")

            with st.form(f"edit_form_{i}"):
                new_status = st.selectbox("Update Status", list(progress_map.keys()), index=list(progress_map.keys()).index(row["Status"]))
                if st.form_submit_button("Update Status"):
                    sheet.update_cell(i + 2, 3, new_status)
                    st.success(f"✅ Status updated to '{new_status}'")

# ---- AI Summary ----
if not df.empty:
    st.subheader("🪄 Project Summary")
    total_projects = len(df)
    in_progress = df[df["Status"] == "In Progress"].shape[0]
    due_this_week = df[(df["Due Date"] >= pd.Timestamp.today()) & (df["Due Date"] <= pd.Timestamp.today() + pd.Timedelta(days=7))].shape[0]
    on_track = df[df["Status"].isin(["In Progress", "Completed"])].shape[0]

    summary = f"You have {in_progress} project(s) in progress, {due_this_week} due this week. {int((on_track/total_projects)*100)}% of your projects are on track."
    st.success(summary)

# ---- Calendar View ----
if not df.empty:
    st.subheader("📅 Calendar View")
    cal_df = df[["Project Name", "Start Date", "Due Date", "Status"]].copy()
    cal_df["Start Date"] = cal_df["Start Date"].dt.strftime('%Y-%m-%d')
    cal_df["Due Date"] = cal_df["Due Date"].dt.strftime('%Y-%m-%d')

    gb = GridOptionsBuilder.from_dataframe(cal_df)
    gb.configure_default_column(editable=False, groupable=True)
    gb.configure_column("Start Date", type=["dateColumnFilter","customDateTimeFormat"], custom_format_string='yyyy-MM-dd', pivot=True)
    gb.configure_column("Due Date", type=["dateColumnFilter","customDateTimeFormat"], custom_format_string='yyyy-MM-dd', pivot=True)
    gb.configure_grid_options(domLayout='normal')
    AgGrid(cal_df, gridOptions=gb.build(), theme="streamlit", enable_enterprise_modules=False, fit_columns_on_grid_load=True)

# ---- Visuals ----
if not df.empty:
    st.subheader("📊 Visual Overview")

    status_colors = {
        "Not Started": "#636E72",
        "In Progress": "#0984E3",
        "On Hold": "#FD9644",
        "Completed": "#00B894"
    }

    # Pie Chart
    status_chart = df["Status"].value_counts().reset_index()
    status_chart.columns = ["Status", "Count"]
    fig1 = px.pie(
        status_chart,
        names="Status",
        values="Count",
        title="📌 Project Status Distribution",
        color="Status",
        color_discrete_map=status_colors
    )
    st.plotly_chart(fig1, use_container_width=True)

    # Gantt Chart
    fig2 = px.timeline(
        df.sort_values("Start Date"),
        x_start="Start Date", x_end="Due Date",
        y="Project Name", color="Status",
        title="📅 Project Timeline",
        color_discrete_map=status_colors
    )
    fig2.update_yaxes(autorange="reversed")
    st.plotly_chart(fig2, use_container_width=True)

# ---- Export ----
st.subheader("📤 Export Project Data")
col1, col2 = st.columns(2)

with col1:
    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download CSV", csv_data, file_name="project_tracker.csv", mime="text/csv")

with col2:
    txt_buffer = StringIO()
    filtered_df.to_string(buf=txt_buffer)
    txt_bytes = txt_buffer.getvalue().encode("utf-8")
    st.download_button("⬇️ Download TXT", txt_bytes, file_name="project_tracker.txt", mime="text/plain")
