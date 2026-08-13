from flask import Flask, render_template, request, redirect, url_for, session
from extensions import db
from models import User, Complaint
from werkzeug.security import check_password_hash
from functools import wraps
from datetime import datetime
from sqlalchemy import case


app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///complaints.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.secret_key = "dev-secret-key"

db.init_app(app)


@app.route("/")
def home():
    return redirect(url_for("login"))


def role_required(required_role):

    def decorator(function):

        @wraps(function)
        def wrapper(*args, **kwargs):

            if "user_id" not in session:
                return redirect(url_for("login"))

            if session.get("role") != required_role:
                return "Access Denied", 403

            return function(*args, **kwargs)

        return wrapper

    return decorator


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(
            user.password_hash,
            password
        ):

            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role

            if user.role == "student":
                return redirect(url_for("student_dashboard"))

            elif user.role == "admin":
                return redirect(url_for("admin_dashboard"))

            elif user.role == "hod":
                return redirect(url_for("hod_dashboard"))

        return "Invalid username or password"

    return render_template("login.html")


@app.route("/student/dashboard")
@role_required("student")
def student_dashboard():

    student_id = session["user_id"]

    now = datetime.now()

    month_start = datetime(now.year, now.month, 1)

    monthly_count = Complaint.query.filter(
        Complaint.student_id == student_id,
        Complaint.date_submitted >= month_start
    ).count()

    remaining = 5 - monthly_count

    # Student ki complaints
    complaints = Complaint.query.filter_by(
        student_id=student_id
    ).order_by(
        Complaint.date_submitted.desc()
    ).all()

    return render_template(
        "student_dashboard.html",
        username=session.get("username"),
        monthly_count=monthly_count,
        remaining=remaining,
        complaints=complaints
    )


@app.route("/admin/dashboard")
@role_required("admin")
def admin_dashboard():

    complaints = Complaint.query.filter(
        Complaint.directed_against != "Admin"
    ).order_by(

        case(
            (Complaint.urgency_level == "Emergency", 1),
            (Complaint.urgency_level == "High", 2),
            (Complaint.urgency_level == "Medium", 3),
            (Complaint.urgency_level == "Low", 4),
            else_=5
        ),

        Complaint.date_submitted.desc()

    ).all()

    return render_template(
        "admin_dashboard.html",
        username=session.get("username"),
        complaints=complaints
    )

@app.route("/complaint/new", methods=["GET", "POST"])
@role_required("student")
def submit_complaint():

    if request.method == "POST":

        category = request.form.get("category")
        directed_against = request.form.get("directed_against")
        description = request.form.get("description")
        is_emergency = request.form.get("is_emergency")

        # Current logged-in student
        student_id = session["user_id"]

        # Current date
        now = datetime.now()

        # Start of current month
        month_start = datetime(now.year, now.month, 1)

        # Count student's complaints this month
        monthly_count = Complaint.query.filter(
            Complaint.student_id == student_id,
            Complaint.date_submitted >= month_start
        ).count()

        # Monthly quota check
        if monthly_count >= 5:
            return "Monthly complaint limit reached (5/5)."

        # Emergency or standard complaint
        if is_emergency == "1":
            urgency_level = "Emergency"
        else:
            urgency_level = "Medium"

        # Create complaint
        complaint = Complaint(
            student_id=student_id,
            category=category,
            directed_against=directed_against,
            urgency_level=urgency_level,
            status="Pending"
        )

        # Save complaint
        db.session.add(complaint)
        db.session.commit()

        return "Complaint submitted successfully!"

    return render_template("submit_complaint.html")

@app.route("/hod/dashboard")
@role_required("hod")
def hod_dashboard():

    complaints = Complaint.query.filter(
        Complaint.directed_against == "Admin"
    ).order_by(
        Complaint.date_submitted.desc()
    ).all()

    return render_template(
        "hod_dashboard.html",
        username=session.get("username"),
        complaints=complaints
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)