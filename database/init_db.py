import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "extraction_data.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"


def init_database():

    conn = sqlite3.connect(DB_PATH)

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = f.read()

    conn.executescript(schema)

    conn.commit()
    conn.close()

    print(f"Base de dados criada em: {DB_PATH}")


if __name__ == "__main__":
    init_database()