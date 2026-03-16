from flask import Flask, render_template, request, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import date
import pandas as pd
import io

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employee.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# DATABASE TABLE
class EmployeeAttendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    status = db.Column(db.String(20))
    reason = db.Column(db.String(200))
    date = db.Column(db.String(50))


# HOME PAGE
@app.route('/', methods=['GET','POST'])
def index():

    if request.method == 'POST':

        name = request.form['name']
        status = request.form['status']
        reason = request.form['reason']
        today = str(date.today())

        # PREVENT DUPLICATE
        existing = EmployeeAttendance.query.filter_by(name=name, date=today).first()

        if existing:
            return """
            <h2 style='color:red;text-align:center;margin-top:100px'>
            Attendance already marked today
            </h2>
            """

        record = EmployeeAttendance(
            name=name,
            status=status,
            reason=reason,
            date=today
        )

        db.session.add(record)
        db.session.commit()

        return redirect('/')

    records = EmployeeAttendance.query.all()

    return render_template("index.html", records=records)


# DELETE ATTENDANCE
@app.route("/delete/<int:id>")
def delete(id):

    record = EmployeeAttendance.query.get_or_404(id)

    db.session.delete(record)
    db.session.commit()

    return redirect('/')


# DAILY REPORT PAGE
@app.route("/daily-report")
def daily_report():

    today = str(date.today())

    records = EmployeeAttendance.query.filter_by(date=today).all()

    return render_template("daily_report.html", records=records)


# MONTHLY REPORT PAGE
@app.route("/monthly-report")
def monthly_report():

    month = str(date.today())[:7]

    records = EmployeeAttendance.query.filter(
        EmployeeAttendance.date.startswith(month)
    ).all()

    summary = {}

    for r in records:

        if r.name not in summary:
            summary[r.name] = {"present":0, "absent":0}

        if r.status == "Present":
            summary[r.name]["present"] += 1
        else:
            summary[r.name]["absent"] += 1

    return render_template(
        "monthly_report.html",
        records=records,
        summary=summary
    )


# DOWNLOAD DAILY EXCEL
@app.route("/download-daily-excel")
def download_daily_excel():

    today = str(date.today())
    records = EmployeeAttendance.query.filter_by(date=today).all()

    data = []

    for r in records:
        data.append({
            "Name": r.name,
            "Status": r.status,
            "Reason": r.reason,
            "Date": r.date
        })

    df = pd.DataFrame(data)

    output = io.BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    return send_file(
        output,
        download_name="daily_attendance.xlsx",
        as_attachment=True
    )


# DOWNLOAD MONTHLY EXCEL
@app.route("/download-monthly-excel")
def download_monthly_excel():

    month = str(date.today())[:7]

    records = EmployeeAttendance.query.filter(
        EmployeeAttendance.date.startswith(month)
    ).all()

    data = []
    summary = {}

    for r in records:

        data.append({
            "Name": r.name,
            "Status": r.status,
            "Reason": r.reason,
            "Date": r.date
        })

        if r.name not in summary:
            summary[r.name] = {"Present":0, "Absent":0}

        if r.status == "Present":
            summary[r.name]["Present"] += 1
        else:
            summary[r.name]["Absent"] += 1


    df_records = pd.DataFrame(data)

    summary_data = []
    for name, value in summary.items():
        summary_data.append({
            "Employee": name,
            "Present": value["Present"],
            "Absent": value["Absent"]
        })

    df_summary = pd.DataFrame(summary_data)


    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_records.to_excel(writer, sheet_name="Attendance", index=False)
        df_summary.to_excel(writer, sheet_name="Monthly Summary", index=False)

    output.seek(0)

    return send_file(
        output,
        download_name="monthly_attendance.xlsx",
        as_attachment=True
    )
    # CREATE DATABASE TABLES WHEN APP STARTS
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
    
   