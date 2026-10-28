import csv
import io
import sqlite3

from flask import Flask, Response, g, jsonify, request

app = Flask(__name__, static_folder="static", static_url_path="")
DB = "attendance.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_no TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    class_name TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('Present', 'Absent')),
    UNIQUE (student_id, date)
);
"""


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_):
    conn = g.pop("db", None)
    if conn:
        conn.close()


def init_db():
    with sqlite3.connect(DB) as conn:
        conn.executescript(SCHEMA)


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/api/students")
def list_students():
    rows = db().execute("SELECT * FROM students ORDER BY roll_no").fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/api/students")
def add_student():
    d = request.get_json(force=True)
    roll, name = (d.get("roll_no") or "").strip(), (d.get("name") or "").strip()
    if not roll or not name:
        return jsonify(error="Roll number and name are required"), 400
    try:
        db().execute(
            "INSERT INTO students (roll_no, name, class_name) VALUES (?, ?, ?)",
            (roll, name, (d.get("class_name") or "").strip()),
        )
        db().commit()
    except sqlite3.IntegrityError:
        return jsonify(error="Roll number already exists"), 409
    return jsonify(ok=True), 201


@app.delete("/api/students/<int:sid>")
def delete_student(sid):
    db().execute("DELETE FROM students WHERE id = ?", (sid,))
    db().commit()
    return jsonify(ok=True)


@app.get("/api/attendance")
def get_attendance():
    date = request.args.get("date", "")
    rows = db().execute(
        "SELECT student_id, status FROM attendance WHERE date = ?", (date,)
    ).fetchall()
    return jsonify({r["student_id"]: r["status"] for r in rows})


@app.post("/api/attendance")
def save_attendance():
    d = request.get_json(force=True)
    date, records = d.get("date"), d.get("records", [])
    if not date:
        return jsonify(error="Date is required"), 400
    db().executemany(
        """INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)
           ON CONFLICT(student_id, date) DO UPDATE SET status = excluded.status""",
        [(r["student_id"], date, r["status"]) for r in records],
    )
    db().commit()
    return jsonify(ok=True)


def report_rows(start, end):
    rows = db().execute(
        """SELECT s.roll_no, s.name, s.class_name,
                  COUNT(a.id) AS total,
                  COALESCE(SUM(a.status = 'Present'), 0) AS present
           FROM students s
           LEFT JOIN attendance a ON a.student_id = s.id
                AND a.date >= ? AND a.date <= ?
           GROUP BY s.id ORDER BY s.roll_no""",
        (start or "0000-01-01", end or "9999-12-31"),
    ).fetchall()
    out = []
    for r in rows:
        r = dict(r)
        r["absent"] = r["total"] - r["present"]
        r["percentage"] = round(100 * r["present"] / r["total"], 2) if r["total"] else 0
        out.append(r)
    return out


@app.get("/api/report")
def report():
    return jsonify(report_rows(request.args.get("start"), request.args.get("end")))


@app.get("/api/report.csv")
def report_csv():
    rows = report_rows(request.args.get("start"), request.args.get("end"))
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Roll No", "Name", "Class", "Total Days", "Present", "Absent", "Attendance %"])
    for r in rows:
        w.writerow([r["roll_no"], r["name"], r["class_name"], r["total"],
                    r["present"], r["absent"], r["percentage"]])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=attendance_report.csv"})


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
