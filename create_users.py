from app import app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash


with app.app_context():

    # Check if student2 already exists
    existing_user = User.query.filter_by(
        username="student2"
    ).first()

    if existing_user:
        print("student2 already exists")

    else:

        student2 = User(
            username="student2",
            password_hash=generate_password_hash("student123"),
            role="student"
        )

        db.session.add(student2)
        db.session.commit()

        print("student2 created successfully!")
