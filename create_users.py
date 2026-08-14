from app import app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash


with app.app_context():

    # Check if student3 already exists
    existing_user = User.query.filter_by(
        username="student3"
    ).first()

    if existing_user:
        print("student3 already exists")

    else:

        student3 = User(
            username="student3",
            password_hash=generate_password_hash("student123"),
            role="student"
        )

        db.session.add(student3)
        db.session.commit()

        print("student3 created successfully!")
