from app import app
from extensions import db
from sqlalchemy import text

with app.app_context():
    try:
        db.session.execute(
            text("ALTER TABLE complaint ADD COLUMN hod_group_id INTEGER")
        )
        db.session.commit()
        print("SUCCESS: hod_group_id column added.")
    except Exception as e:
        db.session.rollback()
        if "duplicate column name" in str(e).lower():
            print("INFO: column already exists.")
        else:
            print("ERROR:", e)