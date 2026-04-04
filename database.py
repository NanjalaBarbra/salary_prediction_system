"""
database.py — Database connection and schema management.

SECURITY HARDENING (OWASP):
  - All credentials loaded from environment variables only — never hardcoded.
  - Connection uses a dedicated low-privilege DB user (not root).
  - Parameterised queries enforced everywhere — no string interpolation.
  - Connection timeout prevents slow-loris style hangs.
  - .env file must never be committed to version control (.gitignore it).

Required environment variables (put these in a .env file locally,
and in your hosting platform's secret manager in production):

    DB_HOST=localhost
    DB_USER=salary_app_user        ← create a dedicated MySQL user, NOT root
    DB_PASSWORD=<strong-password>
    DB_NAME=salary_prediction_app
    DB_PORT=3306                   ← optional, defaults to 3306
"""

import os
import mysql.connector
from dotenv import load_dotenv

# Load .env file when running locally.
# In production, environment variables should be injected by the platform.
load_dotenv()


# ── Connection config ──────────────────────────────────────────────────────────

def _db_config() -> dict:
    """
    Build the MySQL connection config from environment variables.
    Raises a clear RuntimeError if any required variable is missing,
    so the problem is caught at startup rather than at query time.
    """
    host     = os.environ.get("DB_HOST", "localhost")
    user     = os.environ.get("DB_USER", "")
    password = os.environ.get("DB_PASSWORD", "")
    database = os.environ.get("DB_NAME", "salary_prediction_app")
    port     = int(os.environ.get("DB_PORT", 3306))

    # SECURITY: fail loudly if credentials are not configured
    if not user or not password:
        raise RuntimeError(
            "DB_USER and DB_PASSWORD must be set as environment variables. "
            "Never hardcode database credentials in source code."
        )

    return {
        "host":               host,
        "user":               user,
        "password":           password,
        "database":           database,
        "port":               port,
        "connection_timeout": 10,      # seconds — prevent hanging connections
        "autocommit":         False,   # explicit commit required
    }


def get_connection():
    """
    Return a new MySQL connection using environment-variable credentials.
    Callers should use this as a context manager:

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(...)
                conn.commit()
    """
    return mysql.connector.connect(**_db_config())


# ── Schema initialisation ──────────────────────────────────────────────────────

def init_db() -> None:
    """
    Create the database and tables if they do not already exist.
    Safe to run on every startup.
    """
    # Step 1: connect without specifying the database to create it if needed
    cfg = _db_config()
    cfg.pop("database")      # connect to server root, not a specific DB
    init_conn = mysql.connector.connect(**cfg)
    init_cur  = init_conn.cursor()
    # SECURITY: database name is a constant — no user input interpolated here
    init_cur.execute(
        "CREATE DATABASE IF NOT EXISTS salary_prediction_app "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    init_cur.close()
    init_conn.close()

    # Step 2: connect to the app database and create tables
    with get_connection() as conn:
        with conn.cursor() as cur:

            # users table — passwords stored as bcrypt/werkzeug hashes, NEVER plaintext
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id         INT AUTO_INCREMENT PRIMARY KEY,
                    username   VARCHAR(80)  UNIQUE NOT NULL,
                    email      VARCHAR(255),
                    password   VARCHAR(255) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            # predictions table — all salary/profile data per user
            cur.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id               INT AUTO_INCREMENT PRIMARY KEY,
                    username         VARCHAR(80)  NOT NULL,
                    country          VARCHAR(100),
                    education        VARCHAR(100),
                    employment       VARCHAR(50),
                    experience       TINYINT UNSIGNED,
                    devtype          VARCHAR(100),
                    frameworks       TEXT,
                    languages        TEXT,
                    predicted_salary DECIMAL(12,2),
                    predicted_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_username (username)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            conn.commit()

    print("✅ Database and tables initialised successfully")

    # Reviews table (user testimonials)
    try:
        from reviews import create_reviews_table
        create_reviews_table()
    except Exception as e:
        print(f"  ⚠️  reviews table: {e}")


def migrate_db() -> None:
    """
    Idempotent migration — adds columns that may be missing from an older schema.
    Safe to run repeatedly; silently skips columns that already exist.
    """
    migrations = [
        # (human label,  ALTER TABLE SQL)
        ("devtype",    "ALTER TABLE predictions ADD COLUMN devtype       VARCHAR(100) AFTER experience"),
        ("frameworks", "ALTER TABLE predictions ADD COLUMN frameworks    TEXT         AFTER devtype"),
        ("languages",  "ALTER TABLE predictions ADD COLUMN languages     TEXT         AFTER frameworks"),
        ("created_at", "ALTER TABLE users       ADD COLUMN created_at   DATETIME DEFAULT CURRENT_TIMESTAMP"),
        ("email",      "ALTER TABLE users       ADD COLUMN email        VARCHAR(255) AFTER username"),
        ("idx_username","ALTER TABLE predictions ADD INDEX idx_username (username)"),
    ]

    with get_connection() as conn:
        with conn.cursor() as cur:
            for label, sql in migrations:
                try:
                    cur.execute(sql)
                    print(f"  ✅ Migration applied : {label}")
                except mysql.connector.Error as e:
                    # 1060 = duplicate column, 1061 = duplicate key — both safe to ignore
                    if e.errno in (1060, 1061):
                        print(f"  ➖ Already exists   : {label}")
                    else:
                        raise
            conn.commit()

    print("✅ Migration complete")


if __name__ == "__main__":
    init_db()
    migrate_db()
