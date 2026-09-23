from extensions import db
from datetime import datetime, timedelta


# ============================================================
# USER MODEL
# ============================================================

class User(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(200),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False
    )


# ============================================================
# PAKISTAN / LAHORE TIME
# UTC + 5
# ============================================================

def pakistan_time():
    return datetime.utcnow() + timedelta(hours=5)


# ============================================================
# COMPLAINT MODEL
# ============================================================

class Complaint(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    category = db.Column(
        db.String(100),
        nullable=False
    )

    directed_against = db.Column(
        db.String(100),
        nullable=False
    )

    # Used when student selects "Other"
    custom_target = db.Column(
        db.String(200),
        nullable=True
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    urgency_level = db.Column(
        db.String(20),
        nullable=False,
        default="Medium"
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Pending"
    )

    # Pakistan / Lahore Date and Time
    date_submitted = db.Column(
        db.DateTime,
        default=pakistan_time
    )

    # Existing grouping field
    group_id = db.Column(
        db.Integer,
        nullable=True
    )


# ============================================================
# COMPLAINT COMMENT MODEL
# ============================================================

class ComplaintComment(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # Complaint to which this comment belongs
    complaint_id = db.Column(
        db.Integer,
        db.ForeignKey("complaint.id"),
        nullable=False
    )

    # User who wrote the comment
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    # Comment / feedback / solution
    comment = db.Column(
        db.Text,
        nullable=False
    )

    # Date and time of comment
    created_at = db.Column(
        db.DateTime,
        default=pakistan_time
    )


# ============================================================
# COMPLAINT HISTORY MODEL
# ============================================================

class ComplaintHistory(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # Complaint whose history is being recorded
    complaint_id = db.Column(
        db.Integer,
        db.ForeignKey("complaint.id"),
        nullable=False
    )

    # User who performed the action
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    # Example:
    # Submitted
    # Forwarded
    # Solved
    # Rejected
    # Comment Added
    action = db.Column(
        db.String(100),
        nullable=False
    )

    # Status before the action
    old_status = db.Column(
        db.String(20),
        nullable=True
    )

    # Status after the action
    new_status = db.Column(
        db.String(20),
        nullable=True
    )

    # Additional information about the action
    description = db.Column(
        db.Text,
        nullable=True
    )

    # Date and time of action
    created_at = db.Column(
        db.DateTime,
        default=pakistan_time
    )


# ============================================================
# NOTIFICATION MODEL
# ============================================================

class Notification(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # User who will receive the notification
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    # Related complaint
    complaint_id = db.Column(
        db.Integer,
        db.ForeignKey("complaint.id"),
        nullable=True
    )

    # Notification message
    message = db.Column(
        db.String(300),
        nullable=False
    )

    # False = unread
    # True = read
    is_read = db.Column(
        db.Boolean,
        default=False
    )

    # Date and time of notification
    created_at = db.Column(
        db.DateTime,
        default=pakistan_time
    )