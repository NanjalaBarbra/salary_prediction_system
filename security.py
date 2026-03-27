"""
security.py — Centralised rate limiting and input validation.

OWASP Top 10 mitigations implemented here:
  A01 - Broken Access Control   : rate limiting blocks brute-force login attempts
  A03 - Injection               : input sanitisation strips dangerous characters
  A04 - Insecure Design         : schema-based validation rejects unexpected fields
  A07 - Identification/Auth     : lockout after repeated failed login attempts

Usage:
    from security import rate_limit, validate_login_input, validate_prediction_input

    # In a Streamlit page:
    allowed, msg = rate_limit("login", key=username)
    if not allowed:
        st.error(msg)
        st.stop()
"""

import re
import time
import streamlit as st


# ══════════════════════════════════════════════════════════════════════════════
# RATE LIMITING
# ══════════════════════════════════════════════════════════════════════════════
#
# Streamlit has no built-in rate limiting. We use session_state as an in-process
# store keyed by (endpoint, identifier). This protects a single-server deployment.
# For multi-process/cloud deployments, replace the store with Redis.
#
# Limits (sensible defaults — adjust to your traffic):
#   login       : 5 attempts per 60 s per username
#   register    : 5 attempts per 60 s per IP (approximated by session)
#   predict     : 30 attempts per 60 s per username
#   password    : 3 attempts per 300 s per username

_RATE_LIMITS = {
    # endpoint_name: (max_calls, window_seconds)
    # OWASP A07: limit auth-related endpoints to prevent brute-force & enumeration
    "login":           (5,  60),    # 5 attempts per 60 s per username
    "register":        (5,  60),    # 5 registrations per 60 s per session
    "predict":         (30, 60),    # 30 predictions per 60 s per user
    "password_reset":  (3,  300),   # 3 reset requests per 5 min per username
    "change_password": (3,  300),   # 3 change attempts per 5 min per username
    "admin_action":    (10, 60),    # 10 admin writes per 60 s — prevents bulk abuse
}

_STORE_KEY = "_rl_store"   # key inside st.session_state


def _get_store() -> dict:
    """Return (or create) the rate-limit store in session state."""
    if _STORE_KEY not in st.session_state:
        st.session_state[_STORE_KEY] = {}
    return st.session_state[_STORE_KEY]


def rate_limit(endpoint: str, key: str = "global") -> tuple[bool, str]:
    """
    Check whether the caller is within the allowed rate for `endpoint`.

    Args:
        endpoint : one of the keys in _RATE_LIMITS
        key      : discriminator — use username for auth, "global" otherwise

    Returns:
        (True, "")          → request is allowed
        (False, message)    → request is blocked; show `message` to the user
    """
    if endpoint not in _RATE_LIMITS:
        return True, ""   # unknown endpoint — allow by default (fail open)

    max_calls, window = _RATE_LIMITS[endpoint]
    store    = _get_store()
    store_key = f"{endpoint}:{key}"
    now       = time.time()

    calls: list[float] = store.get(store_key, [])

    # Discard timestamps outside the current window
    calls = [t for t in calls if now - t < window]

    if len(calls) >= max_calls:
        wait = int(window - (now - calls[0]))
        return False, (
            f"⚠️ Too many {endpoint} attempts. "
            f"Please wait {wait} second{'s' if wait != 1 else ''} before trying again."
        )

    calls.append(now)
    store[store_key] = calls
    return True, ""


def reset_rate_limit(endpoint: str, key: str = "global") -> None:
    """Clear the rate-limit counter for a key (e.g. after a successful login)."""
    store = _get_store()
    store.pop(f"{endpoint}:{key}", None)


# ══════════════════════════════════════════════════════════════════════════════
# INPUT VALIDATION & SANITISATION
# ══════════════════════════════════════════════════════════════════════════════

# Maximum field lengths — enforced before any DB write
_MAX_LENGTHS = {
    "username":   80,
    "password":   128,
    "email":      254,   # RFC 5321 limit
    "country":    100,
    "education":  100,
    "employment": 50,
    "devtype":    100,
    "major":      100,
    "frameworks": 500,   # comma-joined list
    "languages":  500,
}

# Characters that are never valid in a username (SQL/XSS/path injection guard)
_UNSAFE_USERNAME_RE = re.compile(r"[^\w\-\.]")   # allow word chars, dash, dot only

# Simple email regex (RFC 5322 subset — good enough for UX validation)
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


def sanitise_string(value: str, max_length: int = 255) -> str:
    """
    Strip leading/trailing whitespace and truncate to max_length.
    Does NOT strip HTML — rely on parameterised queries for SQL safety.
    """
    return str(value).strip()[:max_length]


def validate_username(username: str) -> tuple[bool, str]:
    """
    Validate a username:
      - 3–80 characters
      - Only word characters, hyphens, and dots
    """
    username = sanitise_string(username, _MAX_LENGTHS["username"])
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(username) > _MAX_LENGTHS["username"]:
        return False, f"Username must be at most {_MAX_LENGTHS['username']} characters."
    if _UNSAFE_USERNAME_RE.search(username):
        return False, "Username may only contain letters, numbers, hyphens, and dots."
    return True, ""


def validate_email(email: str) -> tuple[bool, str]:
    """Basic email format validation."""
    email = sanitise_string(email, _MAX_LENGTHS["email"])
    if not _EMAIL_RE.match(email):
        return False, "Please enter a valid email address."
    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """
    Password strength rules (OWASP minimum):
      - 8–128 characters
      - At least one digit
      - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if len(password) > _MAX_LENGTHS["password"]:
        return False, f"Password must be at most {_MAX_LENGTHS['password']} characters."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?`~]", password):
        return False, "Password must contain at least one special character."
    return True, ""


# Allowed values — schema-based validation rejects anything unexpected.
# These are derived from the model's valid categories; update if retrained.
_VALID_EMPLOYMENT = {"Full-time", "Freelancer/Contractor", "Student"}

_VALID_EDUCATION = {
    "Bachelor's degree",
    "Master's degree",
    "Post grad",
    "Less than Bachelor's",
}

_VALID_EXPERIENCE_RANGE = (0, 50)   # years


def validate_prediction_input(
    country:    str,
    education:  str,
    employment: str,
    experience: float,
    devtype:    str,
    major:      str,
    frameworks: list,
    languages:  list,
    valid_countries: list,
    valid_devtypes:  list,
    valid_majors:    list,
    valid_frameworks: list,
    valid_languages:  list,
) -> tuple[bool, str]:
    """
    Schema-based validation for prediction inputs.
    Returns (True, "") if all inputs are valid, (False, message) otherwise.

    All string fields are sanitised before comparison.
    List fields are checked to ensure every element is in the allowed set.
    """
    # Country — "Other" is always valid as a fallback for unsupported countries
    country = sanitise_string(country, _MAX_LENGTHS["country"])
    if country != "Other" and country not in valid_countries:
        return False, f"Invalid country: '{country}'."

    # Education
    education = sanitise_string(education, _MAX_LENGTHS["education"])
    if education not in _VALID_EDUCATION:
        return False, f"Invalid education level: '{education}'."

    # Employment
    employment = sanitise_string(employment, _MAX_LENGTHS["employment"])
    if employment not in _VALID_EMPLOYMENT:
        return False, f"Invalid employment type: '{employment}'."

    # Experience
    try:
        experience = float(experience)
    except (ValueError, TypeError):
        return False, "Experience must be a number."
    lo, hi = _VALID_EXPERIENCE_RANGE
    if not (lo <= experience <= hi):
        return False, f"Experience must be between {lo} and {hi} years."

    # DevType
    devtype = sanitise_string(devtype, _MAX_LENGTHS["devtype"])
    if devtype not in valid_devtypes:
        return False, f"Invalid developer type: '{devtype}'."

    # Major
    # UndergradMajor removed in 2025 survey — skip major validation

    # Frameworks — each element must be in the allowed set
    if not isinstance(frameworks, list):
        return False, "Frameworks must be a list."
    valid_fw_set = set(valid_frameworks)
    for fw in frameworks:
        if sanitise_string(fw, 100) not in valid_fw_set:
            return False, f"Invalid framework: '{fw}'."

    # Languages — each element must be in the allowed set
    if not isinstance(languages, list):
        return False, "Languages must be a list."
    valid_lang_set = set(valid_languages)
    for lang in languages:
        if sanitise_string(lang, 100) not in valid_lang_set:
            return False, f"Invalid language: '{lang}'."

    return True, ""


def validate_login_input(username: str, password: str) -> tuple[bool, str]:
    """
    Light validation for login — we don't expose which field is wrong
    to avoid username enumeration (OWASP A07).
    """
    username = sanitise_string(username, _MAX_LENGTHS["username"])
    password = sanitise_string(password, _MAX_LENGTHS["password"])

    if not username or not password:
        return False, "Please enter your username and password."
    if len(username) > _MAX_LENGTHS["username"] or len(password) > _MAX_LENGTHS["password"]:
        return False, "Invalid credentials."   # deliberately vague
    return True, ""
