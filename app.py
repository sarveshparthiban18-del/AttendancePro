from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, Student, Subject, Attendance
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///attendance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.secret_key = "attendancepro-secret-key"

db.init_app(app)


# ================= DATABASE SETUP =================

with app.app_context():

    db.create_all()

    # Create demo student
    student = Student.query.filter_by(
        student_id="student123"
    ).first()

    if not student:

        student = Student(
            student_id="student123",
            name="Sarvesh",
            password="1234"
        )

        db.session.add(student)


    # Default subjects
    default_subjects = [
        "Python",
        "Computer Networks",
        "Digital Electronics",
        "Microprocessors",
        "Communication Systems"
    ]

    for subject_name in default_subjects:

        existing_subject = Subject.query.filter_by(
            name=subject_name
        ).first()

        if not existing_subject:

            db.session.add(
                Subject(name=subject_name)
            )


    db.session.commit()


# ================= STUDENT LOGIN =================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        student_id = request.form.get("student_id")
        password = request.form.get("password")

        student = Student.query.filter_by(
            student_id=student_id
        ).first()

        if student and check_password_hash(student.password, password):

            session["student_id"] = student.student_id

            return redirect("/dashboard")

        return render_template(
            "login.html",
            error="Invalid Student ID or Password"
        )

    return render_template("login.html")


# ================= REGISTER =================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name")
        student_id = request.form.get("student_id")
        password = request.form.get("password")

        existing_student = Student.query.filter_by(
            student_id=student_id
        ).first()

        if existing_student:

            return render_template(
                "register.html",
                error="Student ID already exists"
            )

        new_student = Student(
            name=name,
            student_id=student_id,
            password=generate_password_hash(password)
        )

        db.session.add(new_student)
        db.session.commit()

        return redirect("/")

    return render_template("register.html")


# ================= STUDENT DASHBOARD =================

@app.route("/dashboard")
def dashboard():

    if "student_id" not in session:

        return redirect("/")

    student_id = session["student_id"]

    student = Student.query.filter_by(
        student_id=student_id
    ).first()

    attendance = Attendance.query.filter_by(
        student_id=student_id
    ).order_by(
        Attendance.date.desc()
    ).all()


    # Overall attendance

    total_classes = len(attendance)

    total_present = sum(
        1
        for record in attendance
        if record.status.lower() == "present"
    )


    if total_classes > 0:

        overall_percentage = round(
            (total_present / total_classes) * 100,
            2
        )

    else:

        overall_percentage = 0


    # Subject-wise attendance

    subject_data = {}


    for record in attendance:

        subject = record.subject

        if subject not in subject_data:

            subject_data[subject] = {
                "total": 0,
                "present": 0
            }


        subject_data[subject]["total"] += 1


        if record.status.lower() == "present":

            subject_data[subject]["present"] += 1


    # Calculate percentage for each subject

    for subject in subject_data:

        total = subject_data[subject]["total"]

        present = subject_data[subject]["present"]


        if total > 0:

            subject_data[subject]["percentage"] = round(
                (present / total) * 100,
                2
            )

        else:

            subject_data[subject]["percentage"] = 0


    return render_template(
        "dashboard.html",
        student=student,
        attendance=attendance,
        total_classes=total_classes,
        total_present=total_present,
        overall_percentage=overall_percentage,
        subject_data=subject_data
    )


# ================= STUDENT LOGOUT =================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ================= ADMIN LOGIN =================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == admin_username and password == admin_password:

            session["admin"] = True

            return redirect("/admin")

        return render_template(
            "admin_login.html",
            error="Invalid admin username or password"
        )

    return render_template("admin_login.html")

# ================= ADMIN DASHBOARD =================

@app.route("/admin")
def admin():

    # Check admin login
    if not session.get("admin"):
        return redirect("/admin/login")

    # Get all students and subjects
    students = Student.query.all()
    subjects = Subject.query.all()

    # ================= STATISTICS =================

    total_students = Student.query.count()

    total_subjects = Subject.query.count()

    total_attendance = Attendance.query.count()

    total_present = Attendance.query.filter_by(
        status="Present"
    ).count()

    total_absent = Attendance.query.filter_by(
        status="Absent"
    ).count()

    # ================= FILTERS =================

    student_filter = request.args.get(
        "student_id",
        ""
    )

    subject_filter = request.args.get(
        "subject",
        ""
    )

    date_filter = request.args.get(
        "date",
        ""
    )

    # Start with all attendance records
    query = Attendance.query

    # Student filter
    if student_filter:

        query = query.filter_by(
            student_id=student_filter
        )

    # Subject filter
    if subject_filter:

        query = query.filter_by(
            subject=subject_filter
        )

    # Date filter
    if date_filter:

        query = query.filter_by(
            date=date_filter
        )

    # Get filtered records
    attendance_records = query.order_by(
        Attendance.date.desc()
    ).all()

    # ================= SEND DATA TO HTML =================

    return render_template(
        "admin.html",

        # Students
        students=students,

        # Subjects
        subjects=subjects,

        # Attendance records
        attendance_records=attendance_records,

        # Filters
        student_filter=student_filter,
        subject_filter=subject_filter,
        date_filter=date_filter,

        # Statistics
        total_students=total_students,
        total_subjects=total_subjects,
        total_attendance=total_attendance,
        total_present=total_present,
        total_absent=total_absent
    )

# ================= ADD SUBJECT =================

@app.route("/admin/add-subject", methods=["POST"])
def add_subject():

    if not session.get("admin"):
        return redirect("/admin/login")

    subject_name = request.form.get(
        "subject",
        ""
    ).strip()

    # Don't allow empty subject
    if not subject_name:
        return redirect("/admin")

    existing_subject = Subject.query.filter(
        db.func.lower(Subject.name) == subject_name.lower()
    ).first()

    # Don't allow duplicate subject
    if existing_subject:
        return redirect("/admin")

    new_subject = Subject(
        name=subject_name
    )

    db.session.add(new_subject)
    db.session.commit()

    return redirect("/admin")

# ================= DELETE SUBJECT =================

@app.route("/admin/delete-subject/<int:subject_id>", methods=["POST"])
def delete_subject(subject_id):

    if not session.get("admin"):
        return redirect("/admin/login")

    subject = Subject.query.get(subject_id)

    if subject:

        # Delete attendance records for this subject
        Attendance.query.filter_by(
            subject=subject.name
        ).delete()

        db.session.delete(subject)
        db.session.commit()

    return redirect("/admin")

# ================= MARK ATTENDANCE =================

@app.route("/admin/attendance", methods=["POST"])
def admin_attendance():

    if not session.get("admin"):
        return redirect("/admin/login")

    student_id = request.form.get(
        "student_id",
        ""
    ).strip()

    subject = request.form.get(
        "subject",
        ""
    ).strip()

    date = request.form.get(
        "date",
        ""
    ).strip()

    status = request.form.get(
        "status",
        ""
    ).strip()

    # Check required fields
    if not student_id or not subject or not date or not status:
        return redirect("/admin")

    # Only allow valid attendance status
    if status not in ["Present", "Absent"]:
        return redirect("/admin")

    # Check whether student exists
    student = Student.query.filter_by(
        student_id=student_id
    ).first()

    if not student:
        return redirect("/admin")

    # Check whether subject exists
    subject_record = Subject.query.filter_by(
        name=subject
    ).first()

    if not subject_record:
        return redirect("/admin")

    # Check existing attendance
    existing = Attendance.query.filter_by(
        student_id=student_id,
        subject=subject,
        date=date
    ).first()

    if existing:

        existing.status = status

    else:

        record = Attendance(
            student_id=student_id,
            subject=subject,
            date=date,
            status=status
        )

        db.session.add(record)

    db.session.commit()

    return redirect("/admin")

# ================= ADD STUDENT =================

@app.route("/admin/add-student", methods=["POST"])
def add_student():

    if not session.get("admin"):
        return redirect("/admin/login")

    name = request.form.get("name", "").strip()
    student_id = request.form.get("student_id", "").strip()
    password = request.form.get("password", "").strip()

    # Check empty fields
    if not name or not student_id or not password:
        return redirect("/admin")

    # Check duplicate student ID
    existing_student = Student.query.filter_by(
        student_id=student_id
    ).first()

    if existing_student:
        return redirect("/admin")

    # Create student
    new_student = Student(
        name=name,
        student_id=student_id,
        password=generate_password_hash(password)
    )

    db.session.add(new_student)
    db.session.commit()

    return redirect("/admin")

# ================= DELETE STUDENT =================

@app.route("/admin/delete-student/<int:student_db_id>", methods=["POST"])
def delete_student(student_db_id):

    if not session.get("admin"):
        return redirect("/admin/login")

    student = Student.query.get(student_db_id)

    if student:

        # Delete student's attendance records first
        Attendance.query.filter_by(
            student_id=student.student_id
        ).delete()

        db.session.delete(student)

        db.session.commit()

    return redirect("/admin")

# ================= VIEW ATTENDANCE =================

@app.route("/admin/attendance-records")
def attendance_records():

    if not session.get("admin"):
        return redirect("/admin/login")

    records = Attendance.query.order_by(
        Attendance.date.desc()
    ).all()

    students = Student.query.all()
    subjects = Subject.query.all()

    return render_template(
        "attendance_records.html",
        records=records,
        students=students,
        subjects=subjects
    )


# ================= DELETE ATTENDANCE =================

@app.route(
    "/admin/delete-attendance/<int:attendance_id>",
    methods=["POST"]
)
def delete_attendance(attendance_id):

    if not session.get("admin"):
        return redirect("/admin/login")

    record = Attendance.query.get(attendance_id)

    if record:

        db.session.delete(record)
        db.session.commit()

    return redirect("/admin")
#================= EDIT ATTENDANCE =================

@app.route("/admin/edit-attendance/<int:attendance_id>", methods=["POST"])
def edit_attendance(attendance_id):

    if not session.get("admin"):
        return redirect("/admin/login")

    record = Attendance.query.get(attendance_id)

    if record:

        record.student_id = request.form.get("student_id")
        record.subject = request.form.get("subject")
        record.date = request.form.get("date")
        record.status = request.form.get("status")

        db.session.commit()

    return redirect("/admin")
# ================= ADMIN LOGOUT =================

@app.route("/admin/logout")
def admin_logout():

    session.pop("admin", None)

    return redirect("/admin/login")

# ================= 404 ERROR =================

@app.errorhandler(404)
def page_not_found(error):

    return render_template("404.html"), 404

# ================= 500 ERROR =================

@app.errorhandler(500)
def internal_server_error(error):

    db.session.rollback()

    return render_template("500.html"), 500

# ================= RUN APP =================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )