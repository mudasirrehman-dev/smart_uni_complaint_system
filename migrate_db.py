from app import app
from extensions import db
from sqlalchemy import text


# ============================================================
# DATABASE MIGRATION
# ============================================================

with app.app_context():

    # --------------------------------------------------------
    # 1. Add custom_target column to existing complaint table
    # --------------------------------------------------------

    try:
        db.session.execute(
            text(
                "ALTER TABLE complaint "
                "ADD COLUMN custom_target VARCHAR(200)"
            )
        )

        print("SUCCESS: custom_target column added.")

    except Exception as e:

        # Column may already exist
        if "duplicate column name" in str(e).lower():
            print("INFO: custom_target column already exists.")

        else:
            print("ERROR:", e)


    # --------------------------------------------------------
    # 2. Create new tables
    # --------------------------------------------------------

    db.create_all()

    print("SUCCESS: New database tables created.")

    # Save changes
    db.session.commit()

    print("Database migration completed successfully.")