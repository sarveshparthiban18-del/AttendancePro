# AttendancePro 📊

AttendancePro is a web-based college attendance management system built using Python Flask.

It allows students to view their attendance and provides administrators with tools to manage students, subjects, and attendance records.

## 🚀 Features

### Student
- Student registration
- Secure student login
- Overall attendance percentage
- Subject-wise attendance
- Present/Absent statistics
- Attendance history
- Responsive dashboard

### Admin
- Secure admin login
- Dashboard statistics
- Add students
- Delete students
- Add subjects
- Delete subjects
- Mark attendance
- Edit attendance
- Delete attendance
- Filter attendance records

## 🛠️ Technologies Used

- Python
- Flask
- Flask-SQLAlchemy
- SQLite
- HTML
- CSS
- Jinja2
- Docker
- Git & GitHub
- GitHub Actions

## 📁 Project Structure

```text
AttendancePro/
│
├── app.py
├── database.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
├── .env
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── admin.html
│   ├── admin_login.html
│   ├── 404.html
│   └── 500.html
│
└── .github/
    └── workflows/
        └── ci.yml