from extensions import db
from datetime import datetime, timedelta


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


# Pakistan / Lahore Time = UTC + 5
def pakistan_time():
    return datetime.utcnow() + timedelta(hours=5)


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

    group_id = db.Column(
        db.Integer,
        nullable=True
    )