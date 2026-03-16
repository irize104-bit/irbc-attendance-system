from flask import Flask, render_template, request, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import date
import pandas as pd
import io

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Database Model
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    status = db.Column(db.String(20))
    reason = db.Column(db.String(200))
    date = db.Column(db.String(20))
 # Overtime Model
class Overtime(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    hours = db.Column(db.Float)
    date = db.Column(db.String(20))


# Home Page
@app.route('/')
def index():
    employees = ["David", "Dhanu", "Karame", "Mukilan"]
    return render_template("index.html", employees=employees)


# Save Attendance
@app.route('/save', methods=['POST'])
def save():

    names = request.form.getlist('name[]')
    reasons = request.form.getlist('reason[]')

    for i in range(len(names)):

        status = request.form.get(f'status_{i+1}')

        # If nothing selected, skip this employee
        if not status:
            continue

        new_record = Attendance(
            name=names[i],
            status=status,
            reason=reasons[i],
            date=str(date.today())
        )

        db.session.add(new_record)

    db.session.commit()

    return redirect('/daily')






 # Overtime Page
@app.route('/overtime')
def overtime():

    employees = ["David", "Dhanu", "Karame", "Mukilan"]

    return render_template("overtime.html", employees=employees)


# Save Overtime
@app.route('/save_overtime', methods=['POST'])
def save_overtime():

    names = request.form.getlist('name')
    hours = request.form.getlist('hours')

    for i in range(len(names)):

        ot = Overtime(
            name=names[i],
            hours=float(hours[i]) if hours[i] else 0,
            date=str(date.today())
        )

        db.session.add(ot)

    db.session.commit()

    return redirect('/')



# Daily Report
@app.route('/daily')
def daily():

    today = str(date.today())
    records = Attendance.query.filter_by(date=today).all()

    return render_template("daily_report.html", records=records)


# Monthly Report
@app.route('/monthly')
def monthly():
    from datetime import datetime

    month = datetime.now().strftime("%Y-%m")

    records = Attendance.query.filter(
        Attendance.status != None
    ).all()

    return render_template("monthly.html", records=records)

# Delete Attendance
@app.route('/delete/<int:id>')
def delete(id):

    record = Attendance.query.get_or_404(id)

    db.session.delete(record)
    db.session.commit()

    return redirect('/daily')


# Edit Attendance
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):

    record = Attendance.query.get_or_404(id)

    if request.method == 'POST':

        record.status = request.form.get('status')
        record.reason = request.form.get('reason')

        db.session.commit()

        return redirect('/daily')

    return render_template('edit.html', record=record)


# Excel Download
@app.route('/download')
def download():

records = Attendance.query.filter(Attendance.status != None).all()

    data = []

    for r in records:

        ot = Overtime.query.filter_by(name=r.name, date=r.date).first()

        data.append({
            "Name": r.name,
            "Status": r.status,
            "Reason": r.reason,
            "Overtime": ot.hours if ot else 0,
            "Date": r.date
        })

    df = pd.DataFrame(data)

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    output.seek(0)

    return send_file(
        output,
        download_name="attendance_report.xlsx",
        as_attachment=True
    )

# Create database tables
with app.app_context():
    db.create_all()

# Run App
if __name__ == "__main__":
    app.run(debug=True)




