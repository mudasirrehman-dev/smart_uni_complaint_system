from app import app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash


with app.app_context():

    # Check if student7 already exists
    existing_user = User.query.filter_by(
        username="student7"
    ).first()

    if existing_user:
        print("student7 already exists")

    else:

        student7 = User(
            username="student7",
            password_hash=generate_password_hash("student123"),
            role="student"
        )

        db.session.add(student7)
        db.session.commit()

        print("student7 created successfully!")
