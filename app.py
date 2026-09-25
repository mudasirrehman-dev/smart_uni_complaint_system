# ============================================================
# IMPORTS
# ============================================================

# Flask modules
from flask import Flask, render_template, request, redirect, url_for, session

# Database object
from extensions import db

# Database models
from models import (
    User,
    Complaint,
    ComplaintComment,
    ComplaintHistory,
    Notification
)

# Password verification
from werkzeug.security import check_password_hash

# Used for creating custom decorators
from functools import wraps

# Used for date and monthly complaint quota
from datetime import datetime

# Used for custom complaint sorting and filtering
from sqlalchemy import case, or_


# ============================================================
# FLASK APPLICATION CONFIGURATION
# ============================================================

# Create the Flask application
app = Flask(__name__)

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///complaints.db"

# Disable unnecessary SQLAlchemy tracking
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Secret key used for Flask sessions
app.secret_key = "dev-secret-key"

# Connect SQLAlchemy database with Flask application
db.init_app(app)

# ============================================================
# COMPLAINT HISTORY HELPER
# ============================================================

def add_complaint_history(
    complaint,
    user_id,
    action,
    old_status=None,
    new_status=None,
    description=None
):
    """
    Complaint ki history mein ek new record create karta hai.
    """

    history = ComplaintHistory(
        complaint_id=complaint.id,
        user_id=user_id,
        action=action,
        old_status=old_status,
        new_status=new_status,
        description=description
    )

    db.session.add(history)

# ============================================================
# HOME ROUTE
# ============================================================

@app.route("/")
def home():
    # Redirect the user to the login page
    return redirect(url_for("login"))


# ============================================================
# ROLE-BASED ACCESS CONTROL DECORATOR
# ============================================================

def role_required(required_role):
    """
    Restrict a route so that only users with the required role
    can access it.

    Example:
        @role_required("student")
    """

    def decorator(function):

        @wraps(function)
        def wrapper(*args, **kwargs):

            # Check whether the user is logged in
            if "user_id" not in session:
                return redirect(url_for("login"))

            # Check whether the logged-in user has the required role
            if session.get("role") != required_role:
                return "Access Denied", 403

            # Allow access to the original route
            return function(*args, **kwargs)

        return wrapper

    return decorator


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    # Run this code when the login form is submitted
    if request.method == "POST":

        # Get username and password from the form
        username = request.form.get("username")
        password = request.form.get("password")

        # Find the user in the database using the username
        user = User.query.filter_by(username=username).first()

        # Check:
        # 1. User exists
        # 2. Entered password matches the stored hashed password
        if user and check_password_hash(
            user.password_hash,
            password
        ):

            # Store logged-in user information in the session
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role

            # Redirect the user according to their role
            if user.role == "student":
                return redirect(url_for("student_dashboard"))

            elif user.role == "admin":
                return redirect(url_for("admin_dashboard"))

            elif user.role == "hod":
                return redirect(url_for("hod_dashboard"))

        # Show an error if login credentials are incorrect
        return "Invalid username or password"

    # Show the login page for GET requests
    return render_template("login.html")


# ============================================================
# STUDENT DASHBOARD
# ============================================================

@app.route("/student/dashboard")
@role_required("student")
def student_dashboard():

    # Get the currently logged-in student's ID
    student_id = session.get("user_id")

    # Get all complaints submitted by this student
    # Newest complaints are shown first
    complaints = Complaint.query.filter_by(
        student_id=student_id
    ).order_by(
        Complaint.date_submitted.desc()
    ).all()

    # --------------------------------------------------------
    # MONTHLY COMPLAINT DISPLAY
    # --------------------------------------------------------

    # Total complaints currently fetched for the student
    complaints_used = len(complaints)

    # Remaining complaints from the limit of 5
    complaints_remaining = 5 - complaints_used

    # --------------------------------------------------------
    # EMERGENCY COMPLAINT COUNTER
    # --------------------------------------------------------

    # Count Emergency complaints submitted by this student
    emergency_count = sum(
        1
        for complaint in complaints
        if complaint.urgency_level == "Emergency"
    )

    # Emergency complaint limit is 2 per month
    emergency_remaining = 2 - emergency_count

    # Prevent negative value
    if emergency_remaining < 0:
        emergency_remaining = 0

    # --------------------------------------------------------
    # COMPLAINT STATUS COUNTS
    # --------------------------------------------------------

    # Count Pending complaints
    pending_count = sum(
        1
        for complaint in complaints
        if complaint.status == "Pending"
    )

    # Count Forwarded complaints
    forwarded_count = sum(
        1
        for complaint in complaints
        if complaint.status == "Forwarded"
    )

    # Count Solved complaints
    solved_count = sum(
        1
        for complaint in complaints
        if complaint.status == "Solved"
    )

    # Send all required data to the student dashboard
    return render_template(
        "student_dashboard.html",
        username=session.get("username"),
        complaints=complaints,
        complaints_used=complaints_used,
        complaints_remaining=complaints_remaining,
        emergency_count=emergency_count,
        emergency_remaining=emergency_remaining,
        pending_count=pending_count,
        forwarded_count=forwarded_count,
        solved_count=solved_count
    )




# ============================================================
# STUDENT COMPLAINT SUBMISSION
# ============================================================

@app.route("/complaint/new", methods=["GET", "POST"])
@role_required("student")
def submit_complaint():

    # Get the currently logged-in student's ID
    student_id = session["user_id"]

    # ========================================================
    # GET CURRENT MONTH
    # ========================================================

    # Get the current date and time
    now = datetime.now()

    # Create the first date of the current month
    month_start = datetime(
        now.year,
        now.month,
        1
    )

    # ========================================================
    # POST - SUBMIT COMPLAINT
    # ========================================================

    if request.method == "POST":

        # Get complaint information from the form
        category = request.form.get("category")
        directed_against = request.form.get("directed_against")
        description = request.form.get("description")

        # Get custom target when "Other" is selected
        custom_target = request.form.get("custom_target")

        # Get emergency checkbox value
        is_emergency = request.form.get("is_emergency")

        # ====================================================
        # BASIC BACKEND VALIDATION
        # ====================================================

        # Check category
        if not category or not category.strip():
            return "Complaint category is required."

        # Check directed against
        if not directed_against or not directed_against.strip():
            return "Directed Against is required."

        # Check description
        if not description or not description.strip():
            return "Complaint description is required."

        # ====================================================
        # CUSTOM TARGET VALIDATION
        # ====================================================

        # If "Other" is selected, custom target is required
        if directed_against == "Other":

            if not custom_target or not custom_target.strip():
                return "Please specify the person or department."

            # Remove unnecessary spaces
            custom_target = custom_target.strip()

        else:

            # No custom target for predefined options
            custom_target = None

        # ====================================================
        # MONTHLY COMPLAINT LIMIT
        # ====================================================

        # Count all complaints submitted by this student
        # during the current month
        monthly_count = Complaint.query.filter(
            Complaint.student_id == student_id,
            Complaint.date_submitted >= month_start
        ).count()

        # Maximum 5 complaints per month
        if monthly_count >= 5:
            return "Monthly complaint limit reached (5/5)."

        # ====================================================
        # EMERGENCY COMPLAINT LIMIT
        # ====================================================

        # Default urgency
        urgency_level = "Medium"

        # If student selected Emergency
        if is_emergency == "1":

            # Count Emergency complaints submitted by this
            # student during the current month
            emergency_count = Complaint.query.filter(
                Complaint.student_id == student_id,
                Complaint.urgency_level == "Emergency",
                Complaint.date_submitted >= month_start
            ).count()

            # Maximum 2 Emergency complaints per month
            if emergency_count >= 2:
                return "Emergency complaint limit reached."

            # Set urgency as Emergency
            urgency_level = "Emergency"

        # ====================================================
        # CREATE NEW COMPLAINT
        # ====================================================

        complaint = Complaint(
            student_id=student_id,
            category=category.strip(),
            directed_against=directed_against.strip(),
            custom_target=custom_target,
            description=description.strip(),
            urgency_level=urgency_level,
            status="Pending"
        )

        # ========================================================
        # SAVE COMPLAINT
        # ========================================================

        db.session.add(complaint)

        # Commit first so complaint gets its database ID
        db.session.commit()


        # ========================================================
        # CREATE COMPLAINT HISTORY
        # ========================================================

        add_complaint_history(
            complaint=complaint,
            user_id=student_id,
            action="Complaint Submitted",
            old_status=None,
            new_status="Pending",
            description="Complaint submitted by student."
        )

        # Save history record
        db.session.commit()


        # ========================================================
        # RETURN TO STUDENT DASHBOARD
        # ========================================================

        return redirect(
            url_for("student_dashboard")
        )

# ========================================================
    # GET - SHOW COMPLAINT FORM
    # ========================================================

    # Count Emergency complaints for this student
    # during the current month
    emergency_count = Complaint.query.filter(
        Complaint.student_id == student_id,
        Complaint.urgency_level == "Emergency",
        Complaint.date_submitted >= month_start
    ).count()

    # Show complaint form
    return render_template(
        "submit_complaint.html",
        emergency_count=emergency_count
    )


# ============================================================
# COMPLAINT DETAILS
# ============================================================

@app.route("/complaint/<int:complaint_id>/details")
@role_required("student")
def complaint_details(complaint_id):

    # --------------------------------------------------------
    # Get complaint
    # --------------------------------------------------------

    complaint = Complaint.query.get_or_404(complaint_id)

    # --------------------------------------------------------
    # Security Check
    # --------------------------------------------------------
    # Student can only view their own complaint.
    # --------------------------------------------------------

    if complaint.student_id != session["user_id"]:
        return "Access Denied", 403

    # --------------------------------------------------------
    # Get comments
    # --------------------------------------------------------

    comments = ComplaintComment.query.filter_by(
        complaint_id=complaint.id
    ).order_by(
        ComplaintComment.created_at.asc()
    ).all()

    # --------------------------------------------------------
    # Get complaint history
    # --------------------------------------------------------

    history = ComplaintHistory.query.filter_by(
        complaint_id=complaint.id
    ).order_by(
        ComplaintHistory.created_at.asc()
    ).all()

    # --------------------------------------------------------
    # Display complaint details
    # --------------------------------------------------------

    return render_template(
        "complaint_details.html",
        complaint=complaint,
        comments=comments,
        history=history
    )

# ============================================================
# ADD COMPLAINT COMMENT
# ============================================================

@app.route(
    "/complaint/<int:complaint_id>/comment",
    methods=["POST"]
)
@role_required("student")
def add_complaint_comment(complaint_id):

    # --------------------------------------------------------
    # Get complaint
    # --------------------------------------------------------

    complaint = Complaint.query.get_or_404(complaint_id)

    # --------------------------------------------------------
    # Security Check
    # --------------------------------------------------------
    # Student can only comment on their own complaint.
    # --------------------------------------------------------

    if complaint.student_id != session["user_id"]:
        return "Access Denied", 403

    # --------------------------------------------------------
    # Get comment
    # --------------------------------------------------------

    comment_text = request.form.get("comment")

    if comment_text:
        comment_text = comment_text.strip()

    # --------------------------------------------------------
    # Validate comment
    # --------------------------------------------------------

    if not comment_text:
        return """
        <h3>Comment Required</h3>
        <p>Please enter a comment or feedback.</p>
        <a href="/complaint/{}/details">
            Back to Complaint
        </a>
        """.format(complaint.id), 400

    # --------------------------------------------------------
    # Create comment
    # --------------------------------------------------------

    comment = ComplaintComment(
        complaint_id=complaint.id,
        user_id=session["user_id"],
        comment=comment_text
    )

    db.session.add(comment)

    # --------------------------------------------------------
    # Save comment
    # --------------------------------------------------------

    db.session.commit()

    # --------------------------------------------------------
    # Return to complaint details
    # --------------------------------------------------------

    return redirect(
        url_for(
            "complaint_details",
            complaint_id=complaint.id
        )
    )






# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin/dashboard")
@role_required("admin")
def admin_dashboard():

    # ========================================================
    # NORMAL COMPLAINT QUEUE
    # ========================================================
    # Show complaints that:
    # 1. Are not part of any group
    # 2. Are not directed against Admin
    #
    # Complaints directed against Admin are handled by HOD.
    # ========================================================

    complaints = Complaint.query.filter(
        Complaint.group_id == None,
        Complaint.directed_against != "Admin"
    ).order_by(

        # ----------------------------------------------------
        # PRIORITY SORTING
        # ----------------------------------------------------
        # Priority order:
        # 1. Emergency + Pending
        # 2. Normal Pending
        # 3. Forwarded
        # 4. Solved
        # 5. Anything else
        # ----------------------------------------------------

        case(
            # Priority 1:
            # Emergency complaints that are still Pending
            (
                (Complaint.urgency_level == "Emergency") &
                (Complaint.status == "Pending"),
                1
            ),

            # Priority 2:
            # All normal Pending complaints
            (
                Complaint.status == "Pending",
                2
            ),

            # Priority 3:
            # Complaints forwarded to HOD
            (
                Complaint.status == "Forwarded",
                3
            ),

            # Priority 4:
            # Solved complaints
            (
                Complaint.status == "Solved",
                4
            ),
            # Priority 5:
            # Rejected complaints
            (
                Complaint.status == "Rejected",
                5
            ),

            # Priority 6:
            # Any other status
            else_=6
        ),

        # Within the same priority,
        # show the newest complaints first
        Complaint.date_submitted.desc()

    ).all()


    # ========================================================
    # GROUPED COMPLAINTS
    # ========================================================
    # Get all complaints that belong to a group.
    # ========================================================

    grouped_complaints = Complaint.query.filter(
        Complaint.group_id != None
    ).all()


    # Dictionary to store complaints according to their Group ID
    #
    # Example:
    # {
    #     5: [complaint1, complaint2],
    #     10: [complaint3, complaint4]
    # }
    groups = {}


    # Organize grouped complaints by their group_id
    for complaint in grouped_complaints:

        # Create a new list if this Group ID does not exist
        if complaint.group_id not in groups:
            groups[complaint.group_id] = []

        # Add the complaint to its corresponding group
        groups[complaint.group_id].append(complaint)


    # ========================================================
    # SEND DATA TO ADMIN DASHBOARD
    # ========================================================

    return render_template(
        "admin_dashboard.html",
        username=session.get("username"),
        complaints=complaints,
        groups=groups
    )


# ============================================================
# SOLVE SINGLE COMPLAINT
# ============================================================

@app.route(
    "/complaint/<int:complaint_id>/solve",
    methods=["POST"]
)
@role_required("admin")
def solve_complaint(complaint_id):

    # ========================================================
    # GET COMPLAINT
    # ========================================================

    complaint = Complaint.query.get_or_404(complaint_id)


    # ========================================================
    # SECURITY CHECK
    # ========================================================
    # Admin cannot solve complaints directed against Admin.
    # These complaints are handled by HOD.

    if complaint.directed_against == "Admin":
        return "Access Denied", 403


    # ========================================================
    # GET SOLUTION / FEEDBACK
    # ========================================================

    solution = request.form.get(
        f"solution_{complaint_id}"
    )


    # Remove unnecessary spaces
    if solution:
        solution = solution.strip()


    # ========================================================
    # SOLUTION IS REQUIRED
    # ========================================================

    if not solution:

        return """
        <h3>Solution / Feedback Required</h3>

        <p>
            Please enter a solution or feedback before solving
            the complaint.
        </p>

        <a href="/admin/dashboard">
            Back to Admin Dashboard
        </a>
        """, 400


    # ========================================================
    # CHECK IF COMPLAINT BELONGS TO A GROUP
    # ========================================================

    if complaint.group_id is not None:

        # Get all complaints in this group
        grouped_complaints = Complaint.query.filter_by(
            group_id=complaint.group_id
        ).all()


        # ====================================================
        # SOLVE ALL GROUP COMPLAINTS
        # ====================================================

        for grouped_complaint in grouped_complaints:

            old_status = grouped_complaint.status

            grouped_complaint.status = "Solved"


            # Add history for every complaint
            add_complaint_history(
                complaint=grouped_complaint,
                user_id=session["user_id"],
                action="Complaint Solved",
                old_status=old_status,
                new_status="Solved",
                description=solution
            )


    else:

        # ====================================================
        # SINGLE COMPLAINT
        # ====================================================

        old_status = complaint.status

        complaint.status = "Solved"


        # ====================================================
        # ADD HISTORY
        # ====================================================

        add_complaint_history(
            complaint=complaint,
            user_id=session["user_id"],
            action="Complaint Solved",
            old_status=old_status,
            new_status="Solved",
            description=solution
        )


    # ========================================================
    # SAVE CHANGES
    # ========================================================

    db.session.commit()


    # ========================================================
    # RETURN TO ADMIN DASHBOARD
    # ========================================================

    return redirect(
        url_for("admin_dashboard")
    )

@app.route(
    "/complaint/<int:complaint_id>/reject",
    methods=["POST"]
)
@role_required("admin")
def reject_complaint(complaint_id):

    complaint = Complaint.query.get_or_404(complaint_id)

    # Admin cannot reject complaints directed against Admin
    if complaint.directed_against == "Admin":
        return "Access Denied", 403

    # Get feedback/rejection reason from the same textarea
    feedback = request.form.get(
        f"solution_{complaint_id}"
    )

    if feedback:
        feedback = feedback.strip()

    # Feedback is required before rejecting
    if not feedback:
        return """
        <h3>Rejection Feedback Required</h3>

        <p>
            Please enter a rejection reason or feedback
            before rejecting the complaint.
        </p>

        <a href="/admin/dashboard">
            Back to Admin Dashboard
        </a>
        """, 400

    # Save old status for history
    old_status = complaint.status

    # Change complaint status
    complaint.status = "Rejected"

    # Add complaint history
    add_complaint_history(
        complaint=complaint,
        user_id=session["user_id"],
        action="Complaint Rejected",
        old_status=old_status,
        new_status="Rejected",
        description=feedback
    )

    db.session.commit()

    return redirect(url_for("admin_dashboard"))


# ============================================================
# FORWARD SINGLE COMPLAINT TO HOD
# ============================================================

@app.route(
    "/complaint/<int:complaint_id>/forward",
    methods=["POST"]
)
@role_required("admin")
def forward_to_hod(complaint_id):

    # ========================================================
    # GET COMPLAINT
    # ========================================================

    complaint = Complaint.query.get_or_404(complaint_id)

    # ========================================================
    # SECURITY CHECK
    # ========================================================
    # Admin cannot forward complaints directed against Admin.
    # Those complaints are handled directly by HOD.

    if complaint.directed_against == "Admin":
        return "Access Denied", 403

    # ========================================================
    # SAVE OLD STATUS
    # ========================================================

    old_status = complaint.status

    # ========================================================
    # CHANGE STATUS
    # ========================================================

    complaint.status = "Forwarded"

    # ========================================================
    # CREATE HISTORY RECORD
    # ========================================================

    add_complaint_history(
        complaint=complaint,
        user_id=session["user_id"],
        action="Forwarded to HOD",
        old_status=old_status,
        new_status="Forwarded",
        description="Complaint forwarded to HOD by Admin."
    )

    # ========================================================
    # SAVE CHANGES
    # ========================================================

    db.session.commit()

    # ========================================================
    # RETURN TO ADMIN DASHBOARD
    # ========================================================

    return redirect(
        url_for("admin_dashboard")
    )


# ============================================================
# COMPLAINT GROUPING
# ============================================================

@app.route("/complaints/group", methods=["POST"])
@role_required("admin")
def group_complaints():

    # Get selected complaint IDs from the form
    complaint_ids = request.form.getlist("complaint_ids")

    print("Selected Complaint IDs:", complaint_ids)

    # At least 2 complaints are required to create a group
    if len(complaint_ids) < 2:
        return "Please select at least 2 complaints to create a group."

    # Convert complaint IDs from strings to integers
    complaint_ids = [
        int(complaint_id)
        for complaint_id in complaint_ids
    ]

    # ========================================================
    # GET VALID COMPLAINTS
    # ========================================================
    # Selected complaints must:
    # 1. Be Pending
    # 2. Not be directed against Admin
    # 3. Not already belong to another group
    # ========================================================

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

    # Make sure every selected complaint is valid
    if len(complaints) != len(complaint_ids):
        return (
            "Some selected complaints are invalid, already grouped, "
            "not pending, or cannot be grouped."
        )

    # Double-check that at least 2 valid complaints exist
    if len(complaints) < 2:
        return "Please select at least 2 valid complaints."

    # ========================================================
    # CHECK DIRECTED AGAINST VALUE
    # ========================================================
    # All selected complaints must have the same
    # "Directed Against" value.
    # ========================================================

    first_complaint = complaints[0]

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

    # ========================================================
    # CREATE THE GROUP
    # ========================================================

    # Use the first complaint's ID as the Group ID
    group_id = first_complaint.id

    # Assign the same Group ID to every selected complaint
    for complaint in complaints:
        complaint.group_id = group_id

    # Save changes to the database
    db.session.commit()

    # Show grouping result
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


# ============================================================
# SOLVE GROUPED COMPLAINTS
# ============================================================

@app.route("/group/<int:group_id>/solve", methods=["POST"])
@role_required("admin")
def solve_group(group_id):

    # Get all complaints belonging to this group
    complaints = Complaint.query.filter_by(
        group_id=group_id
    ).all()

    # Return error if the group does not exist
    if not complaints:
        return "Group not found", 404

    # Solve every complaint in the group
    for complaint in complaints:

        # Change complaint status
        complaint.status = "Solved"

        # Remove the complaint from the group
        complaint.group_id = None

    # Save all changes
    db.session.commit()

    # Return to Admin Dashboard
    return redirect(url_for("admin_dashboard"))


# ============================================================
# FORWARD GROUPED COMPLAINTS TO HOD
# ============================================================

@app.route("/group/<int:group_id>/forward", methods=["POST"])
@role_required("admin")
def forward_group_to_hod(group_id):

    # Get all complaints belonging to this group
    complaints = Complaint.query.filter_by(
        group_id=group_id
    ).all()

    # Return error if the group does not exist
    if not complaints:
        return "Group not found", 404

    # Forward every complaint in the group
    for complaint in complaints:

        # Change complaint status
        complaint.status = "Forwarded"

        # Remove the complaint from the group
        complaint.group_id = None

    # Save all changes
    db.session.commit()

    # Return to Admin Dashboard
    return redirect(url_for("admin_dashboard"))


# ============================================================
# UNDO COMPLAINT GROUP
# ============================================================

@app.route("/group/<int:group_id>/undo", methods=["POST"])
@role_required("admin")
def undo_group(group_id):

    # Print Group ID for debugging
    print("Undo requested for Group ID:", group_id)

    # Get all complaints belonging to this group
    complaints = Complaint.query.filter(
        Complaint.group_id == group_id
    ).all()

    # Print found complaints for debugging
    print(
        "Complaints found:",
        [
            (complaint.id, complaint.group_id)
            for complaint in complaints
        ]
    )

    # Return error if the group does not exist
    if len(complaints) == 0:
        return f"Group {group_id} not found", 404

    # ========================================================
    # CHECK GROUP STATUS
    # ========================================================
    # Only groups containing Pending complaints can be undone.
    # ========================================================

    for complaint in complaints:
        if complaint.status != "Pending":
            return "Only Pending groups can be undone."

    # Remove the Group ID from every complaint
    for complaint in complaints:
        complaint.group_id = None

    # Save changes
    db.session.commit()

    print("Group undone successfully:", group_id)

    # Return to Admin Dashboard
    return redirect(url_for("admin_dashboard"))


# ============================================================
# HOD DASHBOARD
# ============================================================

@app.route("/hod/dashboard")
@role_required("hod")
def hod_dashboard():

    # ========================================================
    # GET COMPLAINTS FOR HOD
    # ========================================================
    # HOD can see:
    # 1. Complaints directed against Admin
    # 2. Complaints forwarded by Admin
    # 3. Complaints previously solved by HOD
    # ========================================================

    complaints = Complaint.query.filter(
        or_(
            Complaint.directed_against == "Admin",

            Complaint.status == "Forwarded",

            Complaint.id.in_(
                db.session.query(ComplaintHistory.complaint_id)
                .filter(
                    ComplaintHistory.user_id == session["user_id"],
                    ComplaintHistory.action == "Complaint Solved"
                )
            )
        )
    ).order_by(

        case(

            # Priority 1:
            # Active Emergency complaints
            (
                (Complaint.urgency_level == "Emergency") &
                (Complaint.status != "Solved"),
                1
            ),

            # Priority 2:
            # Pending complaints
            (
                Complaint.status == "Pending",
                2
            ),

            # Priority 3:
            # Forwarded complaints
            (
                Complaint.status == "Forwarded",
                3
            ),

            # Priority 4:
            # Solved complaints
            (
                Complaint.status == "Solved",
                4
            ),

            else_=5
        ),

        Complaint.date_submitted.desc()

    ).all()


    # ========================================================
    # COUNT ACTIVE EMERGENCY COMPLAINTS
    # ========================================================

    emergency_count = sum(
        1
        for complaint in complaints
        if (
            complaint.urgency_level == "Emergency"
            and complaint.status != "Solved"
        )
    )


    # ========================================================
    # SEND DATA TO HOD DASHBOARD
    # ========================================================

    return render_template(
        "hod_dashboard.html",
        username=session.get("username"),
        complaints=complaints,
        emergency_count=emergency_count
    )

# ============================================================
# HOD SOLVE COMPLAINT
# ============================================================

@app.route(
    "/hod/complaint/<int:complaint_id>/solve",
    methods=["POST"]
)
@role_required("hod")
def hod_solve_complaint(complaint_id):

    # ========================================================
    # GET COMPLAINT
    # ========================================================

    complaint = Complaint.query.get_or_404(complaint_id)


    # ========================================================
    # SECURITY CHECK
    # ========================================================
    # HOD can only solve:
    #
    # 1. Complaints directed against Admin
    # OR
    # 2. Complaints forwarded by Admin
    # ========================================================

    if (
        complaint.directed_against != "Admin"
        and complaint.status != "Forwarded"
    ):
        return "Access Denied", 403


    # ========================================================
    # GET SOLUTION / FEEDBACK
    # ========================================================

    solution = request.form.get("solution")


    # Remove unnecessary spaces
    if solution:
        solution = solution.strip()


    # ========================================================
    # SOLUTION IS REQUIRED
    # ========================================================

    if not solution:

        return """
        <h3>Solution / Feedback Required</h3>

        <p>
            Please enter a solution or feedback before solving
            the complaint.
        </p>

        <a href="/hod/dashboard">
            Back to HOD Dashboard
        </a>
        """, 400


    # ========================================================
    # SAVE OLD STATUS
    # ========================================================

    old_status = complaint.status


    # ========================================================
    # CHANGE STATUS
    # ========================================================

    complaint.status = "Solved"


    # ========================================================
    # CREATE HISTORY
    # ========================================================

    add_complaint_history(
        complaint=complaint,
        user_id=session["user_id"],
        action="Complaint Solved",
        old_status=old_status,
        new_status="Solved",
        description=solution
    )


    # ========================================================
    # SAVE CHANGES
    # ========================================================

    db.session.commit()


    # ========================================================
    # RETURN TO HOD DASHBOARD
    # ========================================================

    return redirect(
        url_for("hod_dashboard")
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    # Remove all logged-in user information from the session
    session.clear()

    # Redirect the user back to the login page
    return redirect(url_for("login"))


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    # Create all database tables if they do not already exist
    with app.app_context():
        db.create_all()

    # Start the Flask development server
    app.run(debug=True)