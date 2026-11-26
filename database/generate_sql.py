"""Regenerates schema.sql (MySQL DDL from the SQLAlchemy models) and seed.sql (dev seed data).
Run from repo root:  python database/generate_sql.py
"""
import os, sys, tempfile, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "backend"))
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/gen.db"
os.environ.setdefault("SECRET_KEY", "generator")
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import mysql
from app.database.session import Base, engine, SessionLocal
import app.models  # noqa
from app.utils.seed import seed

def q(v):
    if v is None: return "NULL"
    if isinstance(v, bool): return "1" if v else "0"
    if isinstance(v, (int, float)): return repr(v)
    if isinstance(v, datetime.datetime): return "'" + v.strftime("%Y-%m-%d %H:%M:%S") + "'"
    return "'" + str(v).replace("\\", "\\\\").replace("'", "''") + "'"

ddl = ["-- MySQL 8 schema generated from backend/app/models/models.py (python database/generate_sql.py)",
       "CREATE DATABASE IF NOT EXISTS timetable_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;", "USE timetable_db;",
       "SET FOREIGN_KEY_CHECKS = 0;"]
for t in Base.metadata.sorted_tables:
    ddl.append(f"DROP TABLE IF EXISTS `{t.name}`;")
for t in Base.metadata.sorted_tables:
    ddl.append(str(CreateTable(t).compile(dialect=mysql.dialect())).strip().rstrip(";") + " ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;")
    for ix in sorted(t.indexes, key=lambda i: i.name or ""):
        ddl.append(str(CreateIndex(ix).compile(dialect=mysql.dialect())).strip() + ";")
ddl.append("SET FOREIGN_KEY_CHECKS = 1;")
open(os.path.join(HERE, "schema.sql"), "w").write("\n\n".join(ddl) + "\n")

Base.metadata.create_all(engine); db = SessionLocal(); seed(db)
out = ["-- DEVELOPMENT-ONLY seed data. Passwords are bcrypt hashes of the demo credentials in README.md.",
       "USE timetable_db;", "SET FOREIGN_KEY_CHECKS = 0;"]
for t in Base.metadata.sorted_tables:
    rows = db.execute(t.select()).fetchall()
    if not rows: continue
    cols = ", ".join(f"`{c.name}`" for c in t.columns)
    vals = ",\n  ".join("(" + ", ".join(q(v) for v in r) + ")" for r in rows)
    out.append(f"INSERT INTO `{t.name}` ({cols}) VALUES\n  {vals};")
out.append("SET FOREIGN_KEY_CHECKS = 1;")
open(os.path.join(HERE, "seed.sql"), "w").write("\n\n".join(out) + "\n")
print("schema.sql / seed.sql written")
