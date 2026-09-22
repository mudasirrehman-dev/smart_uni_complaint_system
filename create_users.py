from app import app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash


with app.app_context():

    # Check if student5 already exists
    existing_user = User.query.filter_by(
        username="student5"
    ).first()

    if existing_user:
        print("student5 already exists")

    else:

        student5 = User(
            username="student5",
            password_hash=generate_password_hash("student123"),
            role="student"
        )

        db.session.add(student5)
        db.session.commit()

        print("student5 created successfully!")
