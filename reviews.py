"""
reviews.py
──────────
Database helpers for the user review / testimonial system.

Schema:
    reviews(id, username, role_title, review_text, rating, approved, created_at)

    - approved: admin must flip this to TRUE before review appears in marquee
    - rating:   1–5 integer
"""

import os
from database import get_connection


# ── table creation (called from database.py init) ─────────────────────────────

def create_reviews_table() -> None:
    """Create the reviews table if it does not exist."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    id          INT AUTO_INCREMENT PRIMARY KEY,
                    username    VARCHAR(80)  NOT NULL,
                    role_title  VARCHAR(120) NOT NULL,
                    review_text TEXT         NOT NULL,
                    rating      TINYINT      NOT NULL DEFAULT 5,
                    approved    BOOLEAN      NOT NULL DEFAULT FALSE,
                    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_approved (approved),
                    INDEX idx_username (username)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            conn.commit()


# ── reads ──────────────────────────────────────────────────────────────────────

def get_approved_reviews() -> list[dict]:
    """Return all admin-approved reviews ordered by newest first."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT username, role_title, review_text, rating, created_at
                    FROM   reviews
                    WHERE  approved = TRUE
                    ORDER  BY created_at DESC
                """)
                rows = cur.fetchall()
        return [
            {
                "username":    r[0],
                "role_title":  r[1],
                "review_text": r[2],
                "rating":      r[3],
            }
            for r in rows
        ]
    except Exception:
        return []


def get_all_reviews_admin() -> list[dict]:
    """Return all reviews (approved + pending) for the admin dashboard."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, username, role_title, review_text,
                           rating, approved, created_at
                    FROM   reviews
                    ORDER  BY created_at DESC
                """)
                rows = cur.fetchall()
        return [
            {
                "id":          r[0],
                "username":    r[1],
                "role_title":  r[2],
                "review_text": r[3],
                "rating":      r[4],
                "approved":    bool(r[5]),
                "created_at":  r[6],
            }
            for r in rows
        ]
    except Exception:
        return []


def user_already_reviewed(username: str) -> bool:
    """Return True if this user already has a submitted review."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM reviews WHERE username = %s LIMIT 1",
                    (username,)
                )
                return cur.fetchone() is not None
    except Exception:
        return False


# ── writes ─────────────────────────────────────────────────────────────────────

def submit_review(username: str, role_title: str,
                  review_text: str, rating: int) -> tuple[bool, str]:
    """Insert a new review (pending approval)."""
    if not (1 <= rating <= 5):
        return False, "Rating must be between 1 and 5."
    if len(review_text.strip()) < 20:
        return False, "Review must be at least 20 characters."
    if len(review_text) > 500:
        return False, "Review must be 500 characters or fewer."
    if len(role_title.strip()) < 2:
        return False, "Please enter your role or title."
    if user_already_reviewed(username):
        return False, "You have already submitted a review."
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO reviews (username, role_title, review_text, rating)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (username, role_title.strip()[:120],
                     review_text.strip()[:500], int(rating))
                )
                conn.commit()
        return True, "Your review has been submitted and is pending approval."
    except Exception as e:
        return False, f"Could not save review: {e}"


def approve_review(review_id: int) -> bool:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE reviews SET approved = TRUE WHERE id = %s",
                    (review_id,)
                )
                conn.commit()
        return True
    except Exception:
        return False


def delete_review(review_id: int) -> bool:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM reviews WHERE id = %s", (review_id,))
                conn.commit()
        return True
    except Exception:
        return False
