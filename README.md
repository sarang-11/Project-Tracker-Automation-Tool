Project Tracker Automation Tool

A lightweight internal project tracking tool built using Streamlit and Google Sheets. It allows you to manage project statuses, deadlines, and visualize progress through charts and summaries.

---

Features:

- Add and update project records
- Sync with Google Sheets
- Filter projects by status
- Progress bars for status tracking
- Gantt-style project timeline
- Download reports (CSV and TXT)
- AI-generated status summaries
- Calendar view for planning

---

Setup Instructions:

1. Clone the repository
   git clone https://github.com/sarang-11/Project-Tracker-Automation-Tool.git
   cd Project-Tracker-Automation-Tool

2. Install the dependencies
   pip install -r requirements.txt

3. Add your Google Sheets credentials
   - Place your credentials.json file in the project root

4. Run the application
   streamlit run app.py

---

Tech Stack:

- Streamlit for UI
- Python (pandas, gspread, plotly)
- Google Sheets for data storage

---
