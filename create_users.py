from app import app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash


with app.app_context():

    # Check if student4 already exists
    existing_user = User.query.filter_by(
        username="student4"
    ).first()

    if existing_user:
        print("student4 already exists")

    else:

        student4 = User(
            username="student4",
            password_hash=generate_password_hash("student123"),
            role="student"
        )

        db.session.add(student4)
        db.session.commit()

        print("student4 created successfully!")
