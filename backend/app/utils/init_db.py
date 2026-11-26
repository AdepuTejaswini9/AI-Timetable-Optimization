"""python -m app.utils.init_db [--seed]  -> create tables (and optionally load dev seed data)."""
import sys
from app.database.session import Base, engine, SessionLocal
import app.models  # noqa
from app.utils.seed import seed

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    if "--seed" in sys.argv:
        db = SessionLocal(); seed(db); db.close()
    print("Database ready.")
