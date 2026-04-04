import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'election.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    # ─── Core tables (CREATE IF NOT EXISTS — safe for existing data) ─────────
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS voters (
            voter_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_number   TEXT NOT NULL UNIQUE,
            name          TEXT NOT NULL,
            department    TEXT NOT NULL DEFAULT '',
            email         TEXT,
            phone         TEXT,
            photo         TEXT,
            face_encoding TEXT,
            password_hash TEXT,
            has_voted     INTEGER DEFAULT 0,
            is_registered INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS elections (
            election_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            election_title TEXT NOT NULL,
            description    TEXT DEFAULT '',
            position_role  TEXT DEFAULT '',
            eligible_type  TEXT DEFAULT 'department',
            start_date     TEXT NOT NULL,
            end_date       TEXT NOT NULL,
            results_published INTEGER DEFAULT 0,
            roll_start     TEXT DEFAULT '',
            roll_end       TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS election_eligible_depts (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            election_id  INTEGER NOT NULL REFERENCES elections(election_id) ON DELETE CASCADE,
            department   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS election_eligible_rolls (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            election_id  INTEGER NOT NULL REFERENCES elections(election_id) ON DELETE CASCADE,
            roll_number  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS candidates (
            candidate_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            election_id    INTEGER NOT NULL REFERENCES elections(election_id),
            candidate_name TEXT NOT NULL,
            description    TEXT DEFAULT '',
            position       TEXT NOT NULL,
            party_name     TEXT,
            symbol_path    TEXT
        );

        CREATE TABLE IF NOT EXISTS votes (
            vote_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            voter_id     INTEGER NOT NULL REFERENCES voters(voter_id),
            candidate_id INTEGER NOT NULL REFERENCES candidates(candidate_id),
            election_id  INTEGER NOT NULL REFERENCES elections(election_id),
            ip_address   TEXT,
            location     TEXT,
            timestamp    TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name           TEXT NOT NULL,
            email          TEXT,
            roll_number    TEXT NOT NULL,
            description    TEXT NOT NULL,
            id_card_path   TEXT,
            admin_response TEXT,
            status         TEXT DEFAULT 'pending'
        );

        CREATE TABLE IF NOT EXISTS admin_log (
            log_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            action     TEXT NOT NULL,
            target     TEXT,
            timestamp  TEXT NOT NULL
        );
    """)

    # ─── Safe column migrations (ALTER TABLE IF column missing) ──────────────
    _safe_add_column(cur, 'voters', 'face_encoding', 'TEXT')
    _safe_add_column(cur, 'voters', 'password_hash', 'TEXT')
    _safe_add_column(cur, 'voters', 'department', "TEXT NOT NULL DEFAULT ''")
    _safe_add_column(cur, 'elections', 'description', "TEXT DEFAULT ''")
    _safe_add_column(cur, 'elections', 'position_role', "TEXT DEFAULT ''")
    _safe_add_column(cur, 'elections', 'eligible_type', "TEXT DEFAULT 'department'")
    _safe_add_column(cur, 'elections', 'results_published', 'INTEGER DEFAULT 0')
    _safe_add_column(cur, 'elections', 'roll_start', "TEXT DEFAULT ''")
    _safe_add_column(cur, 'elections', 'roll_end', "TEXT DEFAULT ''")
    _safe_add_column(cur, 'candidates', 'description', "TEXT DEFAULT ''")

    conn.commit()
    conn.close()


def _safe_add_column(cur, table, column, col_def):
    """Add column only if it doesn't already exist (SQLite migration helper)."""
    try:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
    except Exception:
        pass  # Column already exists


# ── Department constants for SVPCET ──────────────────────────────────────────
SVPCET_DEPARTMENTS = [
    ("CE",   "Civil Engineering"),
    ("EEE",  "Electrical & Electronics Engineering"),
    ("ECE",  "Electronics & Communication Engineering"),
    ("ME",   "Mechanical Engineering"),
    ("CSE",  "Computer Science & Engineering"),
    ("CSE-AI",  "CSE (Artificial Intelligence)"),
    ("CSE-AIML", "CSE (AI & Machine Learning)"),
    ("MCA",  "Master of Computer Applications"),
    ("MBA",  "Master of Business Administration"),
    ("MTECH-CSE", "M.Tech - CSE"),
    ("MTECH-EPS", "M.Tech - Electrical Power Systems"),
    ("MTECH-ES",  "M.Tech - Embedded Systems"),
]
