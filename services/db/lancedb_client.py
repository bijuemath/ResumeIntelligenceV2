import lancedb
from pathlib import Path
from uuid import uuid4
import pyarrow as pa

# ---------- DB PATH ----------
DB_PATH = Path("data/lancedb")
DB_PATH.mkdir(parents=True, exist_ok=True)

db = lancedb.connect(DB_PATH)

# ---------- SCHEMA ----------
resume_schema = pa.schema([
    pa.field("id", pa.string()),
    pa.field("filename", pa.string()),
    pa.field("text", pa.string()),
])

# ---------- TABLE HANDLER ----------
def get_or_create_table():
    if "resumes" in db.table_names():
        return db.open_table("resumes")

    return db.create_table(
        name="resumes",
        schema=resume_schema,   # Required
        mode="create"
    )

# ---------- STORE ----------
def store_resume(filename: str, text: str):
    table = get_or_create_table()

    table.add([{
        "id": str(uuid4()),
        "filename": filename,
        "text": text
    }])
