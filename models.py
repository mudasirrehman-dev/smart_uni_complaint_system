from extensions import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

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

from datetime import datetime

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)

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

    date_submitted = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    group_id = db.Column(
        db.Integer,
        nullable=True
    )