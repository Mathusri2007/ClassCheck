# Student Attendance Management System

Track daily student attendance, calculate attendance percentages and export reports.

**Tech:** HTML, CSS, JavaScript (frontend) · Python + Flask (backend) · SQLite (database)

## Features
- Add / delete students
- Mark daily attendance (Present / Absent), edit any date later
- Attendance percentage per student, with optional date range
- Students below 75% highlighted; CSV report download

## Run locally
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000. The SQLite database (`attendance.db`) is created automatically.

## Structure
```
app.py            Flask API + SQLite
static/index.html UI
static/style.css  Styles
static/app.js     Frontend logic
```
