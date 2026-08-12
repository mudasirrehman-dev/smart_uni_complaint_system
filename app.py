from flask import Flask, render_template, request, redirect, url_for, session
from extensions import db
from models import User, Complaint
from werkzeug.security import check_password_hash
from functools import wraps


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

    return render_template(
        "student_dashboard.html",
        username=session.get("username")
    )


@app.route("/admin/dashboard")
@role_required("admin")
def admin_dashboard():

    return render_template(
        "admin_dashboard.html",
        username=session.get("username")
    )

@app.route("/complaint/new", methods=["GET", "POST"])
@role_required("student")
def submit_complaint():

    if request.method == "POST":

        category = request.form.get("category")
        directed_against = request.form.get("directed_against")
        description = request.form.get("description")
        is_emergency = request.form.get("is_emergency")

        print("Category:", category)
        print("Directed Against:", directed_against)
        print("Description:", description)
        print("Emergency:", is_emergency)

        return "Complaint form submitted successfully!"

    return render_template("submit_complaint.html")

@app.route("/hod/dashboard")
@role_required("hod")
def hod_dashboard():

    return render_template(
        "hod_dashboard.html",
        username=session.get("username")
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)