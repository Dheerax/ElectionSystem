import os
import logging
import sqlite3

logger = logging.getLogger(__name__)

# Try to import psycopg2 for PostgreSQL, but don't fail locally if missing
try:
    import psycopg2
    from psycopg2.extras import DictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.info("psycopg2 not available. Only SQLite can be used.")

DB_PATH = os.path.join(os.path.dirname(__file__), 'election.db')
DATABASE_URL = os.environ.get('DATABASE_URL')

# Internal config variable
USE_POSTGRES = DATABASE_URL and ('postgres://' in DATABASE_URL or 'postgresql://' in DATABASE_URL)

class PostgresCursorWrapper:
    """Wraps psycopg2 cursor to mimic sqlite3 behavior."""
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, query, parameters=()):
        # Convert SQLite ? placeholders to PostgreSQL %s
        new_query = query.replace('?', '%s')
        self._cursor.execute(new_query, parameters)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def executescript(self, script):
        self._cursor.execute(script)
        return self

    def close(self):
        self._cursor.close()

class PostgresConnectionWrapper:
    """Wraps psycopg2 connection to mimic sqlite3 connection."""
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return PostgresCursorWrapper(self._conn.cursor())

    def execute(self, query, parameters=()):
        cur = self.cursor()
        return cur.execute(query, parameters)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()

def get_db():
    if USE_POSTGRES and PSYCOPG2_AVAILABLE:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)
        return PostgresConnectionWrapper(conn)
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

def get_last_insert_id(cursor):
    """Abstraction to get the last inserted row ID for the cursor's connection."""
    if USE_POSTGRES and PSYCOPG2_AVAILABLE:
        try:
            cursor._cursor.execute("SELECT LASTVAL()")
            return cursor._cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to get LASTVAL: {e}")
            cursor._cursor.execute("ROLLBACK")
            return None
    else:
        return cursor.lastrowid

def init_db():
    conn = get_db()
    cur = conn.cursor()

    if USE_POSTGRES and PSYCOPG2_AVAILABLE:
        # PostgreSQL Schema
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS voters (
                voter_id      SERIAL PRIMARY KEY,
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
                election_id    SERIAL PRIMARY KEY,
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
                id           SERIAL PRIMARY KEY,
                election_id  INTEGER NOT NULL REFERENCES elections(election_id) ON DELETE CASCADE,
                department   TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS election_eligible_rolls (
                id           SERIAL PRIMARY KEY,
                election_id  INTEGER NOT NULL REFERENCES elections(election_id) ON DELETE CASCADE,
                roll_number  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS candidates (
                candidate_id   SERIAL PRIMARY KEY,
                election_id    INTEGER NOT NULL REFERENCES elections(election_id),
                candidate_name TEXT NOT NULL,
                description    TEXT DEFAULT '',
                position       TEXT NOT NULL,
                party_name     TEXT,
                symbol_path    TEXT
            );

            CREATE TABLE IF NOT EXISTS votes (
                vote_id      SERIAL PRIMARY KEY,
                voter_id     INTEGER NOT NULL REFERENCES voters(voter_id),
                candidate_id INTEGER NOT NULL REFERENCES candidates(candidate_id),
                election_id  INTEGER NOT NULL REFERENCES elections(election_id),
                ip_address   TEXT,
                location     TEXT,
                timestamp    TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS complaints (
                complaint_id   SERIAL PRIMARY KEY,
                name           TEXT NOT NULL,
                email          TEXT,
                roll_number    TEXT NOT NULL,
                description    TEXT NOT NULL,
                id_card_path   TEXT,
                admin_response TEXT,
                status         TEXT DEFAULT 'pending'
            );

            CREATE TABLE IF NOT EXISTS admin_log (
                log_id     SERIAL PRIMARY KEY,
                action     TEXT NOT NULL,
                target     TEXT,
                timestamp  TEXT NOT NULL
            );
        """)
    else:
        # SQLite Schema
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

    # Safe migrations
    _safe_add_column(conn, cur, 'voters', 'face_encoding', 'TEXT')
    _safe_add_column(conn, cur, 'voters', 'password_hash', 'TEXT')
    _safe_add_column(conn, cur, 'voters', 'department', "TEXT NOT NULL DEFAULT ''")
    _safe_add_column(conn, cur, 'elections', 'description', "TEXT DEFAULT ''")
    _safe_add_column(conn, cur, 'elections', 'position_role', "TEXT DEFAULT ''")
    _safe_add_column(conn, cur, 'elections', 'eligible_type', "TEXT DEFAULT 'department'")
    _safe_add_column(conn, cur, 'elections', 'results_published', 'INTEGER DEFAULT 0')
    _safe_add_column(conn, cur, 'elections', 'roll_start', "TEXT DEFAULT ''")
    _safe_add_column(conn, cur, 'elections', 'roll_end', "TEXT DEFAULT ''")
    _safe_add_column(conn, cur, 'candidates', 'description', "TEXT DEFAULT ''")

    conn.commit()
    conn.close()


def _safe_add_column(conn, cur, table, column, col_def):
    """Add column only if it doesn't already exist."""
    try:
        if USE_POSTGRES and PSYCOPG2_AVAILABLE:
            cur.execute("SAVEPOINT sp_opt")
        
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
        
        if USE_POSTGRES and PSYCOPG2_AVAILABLE:
            cur.execute("RELEASE SAVEPOINT sp_opt")
    except Exception:
        if USE_POSTGRES and PSYCOPG2_AVAILABLE:
            cur._cursor.execute("ROLLBACK TO SAVEPOINT sp_opt")
        pass


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
