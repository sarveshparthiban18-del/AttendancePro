from flask import Flask, render_template, request, redirect, session
from database import db, Student, Subject, Attendance

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///attendance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.secret_key = "attendancepro-secret-key"

db.init_app(app)


# --------------------------------
# CREATE DATABASE
# --------------------------------

with app.app_context():

    db.create_all()

    # -----------------------------
    # CREATE DEMO STUDENT
    # -----------------------------

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

        db.session.commit()


    # -----------------------------
    # CREATE DEMO SUBJECTS
    # -----------------------------

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

            new_subject = Subject(
                name=subject_name
            )

            db.session.add(new_subject)

    db.session.commit()


    # -----------------------------
    # CREATE DEMO ATTENDANCE
    # -----------------------------

    demo_data = [
        ("Python", 30, 27),
        ("Computer Networks", 35, 28),
        ("Digital Electronics", 32, 25),
        ("Microprocessors", 28, 23),
        ("Communication Systems", 25, 20)
    ]

    for subject_name, total, present in demo_data:

        existing_record = Attendance.query.filter_by(
            student_id="student123",
            subject=subject_name
        ).first()

        if not existing_record:

            record = Attendance(
                student_id="student123",
                subject=subject_name,
                total_classes=total,
                present_classes=present
            )

            db.session.add(record)

    db.session.commit()


# --------------------------------
# STUDENT LOGIN
# --------------------------------

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        student_id = request.form.get("student_id")
        password = request.form.get("password")

        student = Student.query.filter_by(
            student_id=student_id
        ).first()

        if student and student.password == password:

            session["student_id"] = student.student_id

            return redirect("/dashboard")

        return render_template(
            "login.html",
            error="Invalid Student ID or Password"
        )

    return render_template("login.html")


# --------------------------------
# STUDENT REGISTER
# --------------------------------

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
            password=password
        )

        db.session.add(new_student)
        db.session.commit()

        return redirect("/")

    return render_template("register.html")


# --------------------------------
# STUDENT DASHBOARD
# --------------------------------

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
    ).all()

    total_classes = sum(
        item.total_classes
        for item in attendance
    )

    total_present = sum(
        item.present_classes
        for item in attendance
    )

    if total_classes > 0:

        overall_percentage = round(
            (total_present / total_classes) * 100,
            2
        )

    else:

        overall_percentage = 0

    return render_template(
        "dashboard.html",
        student=student,
        attendance=attendance,
        total_classes=total_classes,
        total_present=total_present,
        overall_percentage=overall_percentage
    )


# --------------------------------
# STUDENT LOGOUT
# --------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =================================
# ADMIN LOGIN
# =================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "admin123":

            session["admin"] = True

            return redirect("/admin")

        return render_template(
            "admin_login.html",
            error="Invalid admin username or password"
        )

    return render_template("admin_login.html")


# =================================
# ADMIN DASHBOARD
# =================================

@app.route("/admin")
def admin():

    if not session.get("admin"):

        return redirect("/admin/login")

    students = Student.query.all()

    subjects = Subject.query.all()

    return render_template(
        "admin.html",
        students=students,
        subjects=subjects
    )


# =================================
# ADD SUBJECT
# =================================

@app.route("/admin/add-subject", methods=["POST"])
def add_subject():

    if not session.get("admin"):

        return redirect("/admin/login")

    subject_name = request.form.get("subject")

    if subject_name:

        subject_name = subject_name.strip()

        existing_subject = Subject.query.filter_by(
            name=subject_name
        ).first()

        if not existing_subject:

            new_subject = Subject(
                name=subject_name
            )

            db.session.add(new_subject)

            db.session.commit()

    return redirect("/admin")


# =================================
# MARK ATTENDANCE
# =================================

@app.route("/admin/attendance", methods=["POST"])
def admin_attendance():

    if not session.get("admin"):

        return redirect("/admin/login")

    student_id = request.form.get("student_id")
    subject = request.form.get("subject")
    status = request.form.get("status")

    record = Attendance.query.filter_by(
        student_id=student_id,
        subject=subject
    ).first()

    if not record:

        record = Attendance(
            student_id=student_id,
            subject=subject,
            total_classes=0,
            present_classes=0
        )

        db.session.add(record)

    record.total_classes += 1

    if status == "present":

        record.present_classes += 1

    db.session.commit()

    return redirect("/admin")


# =================================
# ADMIN LOGOUT
# =================================

@app.route("/admin/logout")
def admin_logout():

    session.pop("admin", None)

    return redirect("/admin/login")


# =================================
# RUN APPLICATION
# =================================

if __name__ == "__main__":

    app.run(debug=True)