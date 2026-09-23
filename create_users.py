from app import app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash


with app.app_context():

    # Check if student6 already exists
    existing_user = User.query.filter_by(
        username="student6"
    ).first()

    if existing_user:
        print("student6 already exists")

    else:

        student6 = User(
            username="student6",
            password_hash=generate_password_hash("student123"),
            role="student"
        )

        db.session.add(student6)
        db.session.commit()

        print("student6 created successfully!")
