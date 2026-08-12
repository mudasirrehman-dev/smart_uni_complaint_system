from app import app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash


with app.app_context():

    student = User(
        username="student1",
        password_hash=generate_password_hash("student123"),
        role="student"
    )

    admin = User(
        username="admin1",
        password_hash=generate_password_hash("admin123"),
        role="admin"
    )

    hod = User(
        username="hod1",
        password_hash=generate_password_hash("hod123"),
        role="hod"
    )

    db.session.add_all([student, admin, hod])
    db.session.commit()

    print("3 test users created successfully!")