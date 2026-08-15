from flask import Flask, render_template, request, redirect, url_for, session
from extensions import db
from models import User, Complaint
from werkzeug.security import check_password_hash
from functools import wraps
from datetime import datetime
from sqlalchemy import case, or_


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

    student_id = session.get("user_id")

    complaints = Complaint.query.filter_by(
        student_id=student_id
    ).order_by(
        Complaint.date_submitted.desc()
    ).all()

    complaints_used = len(complaints)

    complaints_remaining = 5 - complaints_used

    pending_count = sum(
        1 for complaint in complaints
        if complaint.status == "Pending"
    )

    forwarded_count = sum(
        1 for complaint in complaints
        if complaint.status == "Forwarded"
    )

    solved_count = sum(
        1 for complaint in complaints
        if complaint.status == "Solved"
    )

    return render_template(
        "student_dashboard.html",
        username=session.get("username"),
        complaints=complaints,
        complaints_used=complaints_used,
        complaints_remaining=complaints_remaining,
        pending_count=pending_count,
        forwarded_count=forwarded_count,
        solved_count=solved_count
    )

@app.route("/admin/dashboard")
@role_required("admin")
def admin_dashboard():

    # ==============================
    # NORMAL COMPLAINT QUEUE
    # ==============================

    complaints = Complaint.query.filter(
    Complaint.group_id == None,
    Complaint.directed_against != "Admin"
).order_by(
    case(
        # Emergency only when Pending
        (
            (Complaint.urgency_level == "Emergency") &
            (Complaint.status == "Pending"),
            1
        ),

        # Normal Pending complaints
        (Complaint.status == "Pending", 2),

        # Forwarded complaints
        (Complaint.status == "Forwarded", 3),

        # Solved complaints
        (Complaint.status == "Solved", 4),

        else_=5
    ),
    Complaint.date_submitted.desc()
    ).all()
    

    # ==============================
    # GROUPED COMPLAINTS
    # ==============================

    grouped_complaints = Complaint.query.filter(
        Complaint.group_id != None
    ).all()

    groups = {}

    for complaint in grouped_complaints:

        if complaint.group_id not in groups:
            groups[complaint.group_id] = []

        groups[complaint.group_id].append(complaint)

    # ==============================
    # SEND DATA TO HTML
    # ==============================

    return render_template(
        "admin_dashboard.html",
        username=session.get("username"),
        complaints=complaints,
        groups=groups
    )
@app.route("/complaint/<int:complaint_id>/solve", methods=["POST"])
@role_required("admin")
def solve_complaint(complaint_id):

    complaint = Complaint.query.get_or_404(complaint_id)

    # Security:
    # Admin cannot solve a complaint against Admin
    if complaint.directed_against == "Admin":
        return "Access Denied", 403

    # If complaint belongs to a group
    if complaint.group_id is not None:

        grouped_complaints = Complaint.query.filter_by(
            group_id=complaint.group_id
        ).all()

        # Solve every complaint in this group
        for grouped_complaint in grouped_complaints:
            grouped_complaint.status = "Solved"

    else:

        # Normal single complaint
        complaint.status = "Solved"

    db.session.commit()

    return redirect(url_for("admin_dashboard"))

@app.route("/complaint/<int:complaint_id>/forward", methods=["POST"])
@role_required("admin")
def forward_to_hod(complaint_id):

    complaint = Complaint.query.get_or_404(complaint_id)

    # Admin cannot forward a complaint against Admin
    # because it already belongs to HOD
    if complaint.directed_against == "Admin":
        return "Access Denied", 403

    complaint.status = "Forwarded"

    db.session.commit()

    return redirect(url_for("admin_dashboard"))

@app.route("/complaints/group", methods=["POST"])
@role_required("admin")
def group_complaints():

    # Get selected complaint IDs
    complaint_ids = request.form.getlist("complaint_ids")

    print("Selected Complaint IDs:", complaint_ids)

    # Minimum 2 complaints required
    if len(complaint_ids) < 2:
        return "Please select at least 2 complaints to create a group."

    # Convert IDs from string to integer
    complaint_ids = [
        int(complaint_id)
        for complaint_id in complaint_ids
    ]

    # Get valid complaints
    complaints = Complaint.query.filter(
        Complaint.id.in_(complaint_ids),
        Complaint.status == "Pending",
        Complaint.directed_against != "Admin",
        Complaint.group_id == None
    ).all()

    print(
        "Found Complaints:",
        [
            (
                complaint.id,
                complaint.category,
                complaint.directed_against
            )
            for complaint in complaints
        ]
    )

    # Make sure all selected complaints are valid
    if len(complaints) != len(complaint_ids):
        return (
            "Some selected complaints are invalid, already grouped, "
            "not pending, or cannot be grouped."
        )

    # Minimum 2 valid complaints
    if len(complaints) < 2:
        return "Please select at least 2 valid complaints."

    # First complaint for comparison
    first_complaint = complaints[0]

    # Check ONLY Directed Against
    for complaint in complaints:

        if (
            complaint.directed_against
            != first_complaint.directed_against
        ):
            return f"""
                <h3>Complaints cannot be grouped!</h3>

                <p>
                    All selected complaints must have the same
                    Directed Against value.
                </p>

                <p>
                    Selected first value:
                    {first_complaint.directed_against}
                </p>

                <a href="/admin/dashboard">
                    Back to Admin Dashboard
                </a>
            """

    # Use first complaint ID as Group ID
    group_id = first_complaint.id

    # Assign same Group ID to all selected complaints
    for complaint in complaints:
        complaint.group_id = group_id

    db.session.commit()

    return f"""
        <h2>Complaints Grouped Successfully!</h2>

        <p>Selected Complaints: {complaint_ids}</p>

        <p>Group ID: {group_id}</p>

        <p>
            Directed Against:
            {first_complaint.directed_against}
        </p>

        <p>
            Total Complaints in Group:
            {len(complaints)}
        </p>

        <a href="/admin/dashboard">
            Back to Admin Dashboard
        </a>
    """

@app.route("/group/<int:group_id>/solve", methods=["POST"])
@role_required("admin")
def solve_group(group_id):

    complaints = Complaint.query.filter_by(
        group_id=group_id
    ).all()

    if not complaints:
        return "Group not found", 404

    # Solve all complaints in the group
    for complaint in complaints:
        complaint.status = "Solved"

        # Remove from group
        complaint.group_id = None

    db.session.commit()

    return redirect(url_for("admin_dashboard"))

@app.route("/group/<int:group_id>/forward", methods=["POST"])
@role_required("admin")
def forward_group_to_hod(group_id):

    complaints = Complaint.query.filter_by(
        group_id=group_id
    ).all()

    if not complaints:
        return "Group not found", 404

    # Forward all complaints in the group
    for complaint in complaints:
        complaint.status = "Forwarded"

        # Remove from group
        complaint.group_id = None

    db.session.commit()

    return redirect(url_for("admin_dashboard"))

@app.route("/group/<int:group_id>/undo", methods=["POST"])
@role_required("admin")
def undo_group(group_id):

    print("Undo requested for Group ID:", group_id)

    complaints = Complaint.query.filter(
        Complaint.group_id == group_id
    ).all()

    print("Complaints found:", [
        (complaint.id, complaint.group_id)
        for complaint in complaints
    ])

    if len(complaints) == 0:
        return f"Group {group_id} not found", 404

    # Only Pending groups can be undone
    for complaint in complaints:
        if complaint.status != "Pending":
            return "Only Pending groups can be undone."

    # Remove group_id from all complaints
    for complaint in complaints:
        complaint.group_id = None

    db.session.commit()

    print("Group undone successfully:", group_id)

    return redirect(url_for("admin_dashboard"))

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

        # Redirect to student dashboard
        return redirect(
            url_for("student_dashboard")
        )

    return render_template("submit_complaint.html")

@app.route("/hod/dashboard")
@role_required("hod")
def hod_dashboard():

    complaints = Complaint.query.filter(
        or_(
            Complaint.directed_against == "Admin",
            Complaint.status == "Forwarded"
        )
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