import os
import base64
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
st.set_page_config(
    page_title="Salary Prediction App",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

from predict_page import show_predict_page
from explore_page import show_explore_page
from skill_gap_page import show_skill_gap_page
from home_page import show_home_page
from about_page import show_about_page
from auth_page import (
    login_user,
    register_user,
    login_admin,
    validate_password_strength,
)
from security import rate_limit, reset_rate_limit, validate_login_input, validate_username, validate_email, validate_password
from reviews import create_reviews_table
from password_reset import (
    create_reset_tables, create_reset_token, verify_reset_token,
    mark_token_used, get_user_email, save_user_email, send_reset_email,
)
from database import get_connection
from user_dashboard import show_profile_section
from admin_dashboard import show_admin_section


# ── CONSTANTS ─────────────────────────────────────────────────────────────────
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    raise ValueError("ADMIN_PASSWORD environment variable must be set before starting the app.")


# ── UI STYLING ────────────────────────────────────────────────────────────────
def _get_image_base64(image_path: str) -> str | None:
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None


def apply_styles() -> None:
    image4_base64   = _get_image_base64("Images/image4.jpeg")
    image4_data_uri = f"data:image/jpeg;base64,{image4_base64}" if image4_base64 else ""

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] {{ font-family: 'Poppins', sans-serif; }}
.stApp {{ background: #f0f2f4; color: #3a5570; }}
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #f4f7f9 0%, #e3ebf3 100%);
    color: #1a2e42; border-right: 1px solid rgba(0,0,0,0.05);
    box-shadow: 2px 0 15px rgba(0,0,0,0.02);
}}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] .stTextInput label {{ color: #1a2e42 !important; font-weight: 600; }}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {{ color: #1a2e42 !important; }}
h1, h2, h3, h4, h5, h6 {{ color: #1a2e42; font-weight: 700; }}
label, .stTextInput label p, .stSelectbox label p, .stNumberInput label p,
.stTextArea label p, .stRadio label p, [data-testid="stWidgetLabel"] p {{
    color: #111d2e !important; font-weight: 600 !important;
}}
.stButton > button {{
    background: linear-gradient(120deg, #2d4a6b, #4a6b8a);
    border-radius: 999px; color: white; font-weight: 600; border: none;
    padding: 0.55rem 1.4rem; box-shadow: 0 10px 25px rgba(45,74,107,0.28);
}}
.stButton > button:hover {{ background: linear-gradient(120deg,#1a2e42,#3a5570); transform:translateY(-1px); }}
section[data-testid="stSidebar"] .stButton > button {{
    background: linear-gradient(120deg,#111d2e,#1a2e42) !important;
    color: white !important; box-shadow: 0 8px 20px rgba(17,29,46,0.35) !important;
}}
section[data-testid="stSidebar"] .stButton > button:hover {{
    background: linear-gradient(120deg,#0a121c,#111d2e) !important;
}}
.stTextInput > div > div > input, .stTextArea > div > div > textarea,
.stNumberInput > div > div > input, .stSelectbox > div > div > div {{
    background-color: #ffffff !important; color: #1a2e42 !important;
    border: 1px solid #c8d2db !important; border-radius: 8px !important;
}}
section[data-testid="stSidebar"] .stTextInput > div > div > input {{
    background-color: rgba(255,255,255,0.85) !important; color: #1a2e42 !important;
    border: 1px solid rgba(0,0,0,0.1) !important;
}}
.calc-card {{
    background: #ffffff url('{image4_data_uri}') center/cover no-repeat;
    border-radius: 20px; padding: 1.4rem 1.5rem;
    box-shadow: 0 18px 40px rgba(15,23,42,0.12);
    border: 1px solid rgba(74,107,138,0.24); position: relative;
}}
.calc-card::before {{
    content:''; position:absolute; top:0; left:0; right:0; bottom:0;
    background: rgba(255,255,255,0.88); border-radius:20px; z-index:0;
}}
.calc-card > * {{ position:relative; z-index:1; }}
section[data-testid="stSidebar"] div.stButton > button[kind="secondary"] {{
    background:none !important; border:none !important; color:#185FA5 !important;
    font-size:15px !important; text-align:left !important;
    justify-content:flex-start !important; padding:8px 12px !important;
    border-radius:8px !important; width:100% !important;
    box-shadow:none !important; cursor:pointer !important;
}}
section[data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover {{
    background-color:#e8f2fb !important; color:#042C53 !important;
}}
</style>
""", unsafe_allow_html=True)


# ── SESSION STATE ─────────────────────────────────────────────────────────────
def init_session_state() -> None:
    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("username", "")
    st.session_state.setdefault("role", None)
    st.session_state.setdefault("auth_page", "User Login")


# ── BOOTSTRAP ─────────────────────────────────────────────────────────────────
apply_styles()
init_session_state()
create_reset_tables()
try:
    create_reviews_table()
except Exception:
    pass


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("""
    <div style='text-align:center; padding:10px 0;'>
        <span style='font-size:22px; font-weight:bold; color:#185FA5;'>Salary Predictor</span><br>
        <span style='font-size:10px; color:#888; letter-spacing:2px;'>ML-POWERED · REAL-TIME</span>
    </div>
""", unsafe_allow_html=True)

if not st.session_state.logged_in:
    # Admin Login is hidden from the public sidebar.
    # Admins access it via: your-app-url/?admin=1
    _auth_options = ["User Login", "User Registration", "Forgot Password"]
    _current = st.session_state.get("auth_page", "User Login")
    if _current not in _auth_options and _current != "Admin Login":
        _current = "User Login"
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    for auth_opt in _auth_options:
        if _current == auth_opt:
            st.sidebar.markdown(f"""
                <div style='background-color:#185FA5; color:white;
                padding:8px 12px; border-radius:8px;
                margin-bottom:4px; font-weight:bold;'>{auth_opt}</div>
            """, unsafe_allow_html=True)
        else:
            if st.sidebar.button(auth_opt, key=f"auth_nav_{auth_opt}", use_container_width=True):
                st.session_state.auth_page = auth_opt
                st.rerun()

    # ── Subtle admin access link at the bottom of the sidebar ──────────────
    # Clicking this navigates to ?admin=1 which reveals the Admin Login button
    st.sidebar.markdown("<br><br><br>", unsafe_allow_html=True)
    st.sidebar.markdown("""
        <div style='text-align:center;'>
            <a href='?admin=1' target='_self'
               style='font-size:11px; color:#aab8c5;
               text-decoration:none; letter-spacing:0.05em;
               opacity:0.6;'>
               ⚙ Admin
            </a>
        </div>
    """, unsafe_allow_html=True)

    # Show Admin Login only when ?admin=1 is in the URL
    if st.query_params.get("admin") == "1":
        if _current == "Admin Login":
            st.sidebar.markdown("""
                <div style='background-color:#185FA5; color:white;
                padding:8px 12px; border-radius:8px;
                margin-bottom:4px; font-weight:bold;'>Admin Login</div>
            """, unsafe_allow_html=True)
        else:
            if st.sidebar.button("Admin Login", key="auth_nav_Admin Login", use_container_width=True):
                st.session_state.auth_page = "Admin Login"
                st.rerun()


# ── AUTH PAGES ────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:

    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Playfair+Display:wght@700;800&display=swap');
        .stApp { background: linear-gradient(135deg,#f0f4f8 0%,#d9e4ee 35%,#2d4a6b 75%,#0f1b29 100%) !important; }
        .main .block-container { padding-top:2rem !important; max-width:100% !important; }
        [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(1) {
            background:rgba(255,255,255,0.92); backdrop-filter:blur(16px);
            padding:2.5rem; border-radius:20px;
            box-shadow:0 15px 45px rgba(10,20,30,0.2);
            border:1px solid rgba(255,255,255,0.7);
            margin-top:1rem; margin-bottom:2rem;
        }
        .auth-form-logo { font-family:'DM Sans',sans-serif; font-size:1.1rem; font-weight:700; color:#4a6b8a; margin-bottom:0.3rem; letter-spacing:0.05em; text-transform:uppercase; }
        .auth-form-title { font-family:'Playfair Display',serif; font-size:2.4rem; font-weight:800; color:#111d2e; margin-bottom:0.3rem; white-space:nowrap; }
        .auth-form-subtitle { font-size:0.95rem; color:#4a6b8a; margin-bottom:1.5rem; }
        .auth-form-divider { border:none; border-top:1px solid #d7e0e8; margin:1rem 0 1.5rem; }
        .auth-hero-panel {
            border-radius:24px; background:linear-gradient(135deg,#1a2e42,#2d4a6b,#3a5570);
            background-size:400% 400%; animation:gradientShift 8s ease infinite;
            min-height:520px; position:relative; overflow:hidden;
            display:flex; align-items:center; justify-content:center; padding:2.5rem;
        }
        @keyframes gradientShift { 0%{background-position:0% 50%;} 50%{background-position:100% 50%;} 100%{background-position:0% 50%;} }
        .auth-hero-inner { position:relative; z-index:2; text-align:center; }
        .auth-badge {
            display:inline-block; background:rgba(255,255,255,0.1);
            border:1px solid rgba(255,255,255,0.2); border-radius:999px;
            padding:0.35rem 1.1rem; font-size:0.7rem; color:rgba(255,255,255,0.8);
            letter-spacing:0.1em; text-transform:uppercase; margin-bottom:1.2rem; backdrop-filter:blur(8px);
        }
        .auth-hero-title {
            font-family:'Playfair Display',serif; font-size:2.6rem; font-weight:800;
            color:#ffffff; line-height:1.2; margin:0 0 1rem 0; text-shadow:0 4px 24px rgba(0,0,0,0.3);
        }
        .auth-hero-title span { background:linear-gradient(120deg,#d9e4ee,#f0f2f4,#9eb3c7); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
        .auth-hero-sub { color:rgba(240,242,244,0.78); font-size:0.9rem; line-height:1.7; margin-bottom:2rem; }
        .auth-stats { display:flex; justify-content:center; gap:0.8rem; flex-wrap:wrap; }
        .auth-stat-pill {
            background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.15);
            border-radius:14px; padding:0.75rem 1.1rem; backdrop-filter:blur(12px);
            text-align:center; min-width:80px;
        }
        .auth-stat-num { font-size:1.3rem; font-weight:700; margin-bottom:0.1rem; }
        .auth-stat-label { font-size:0.6rem; color:rgba(255,255,255,0.6); text-transform:uppercase; letter-spacing:0.08em; }
        </style>
    """, unsafe_allow_html=True)

    form_col, banner_col = st.columns([1, 1], gap="large")

    with form_col:
        st.markdown('<div class="auth-form-logo">Salary Prediction App</div>', unsafe_allow_html=True)

        if st.session_state.auth_page == "User Login":
            st.markdown('<div class="auth-form-title">Welcome back</div>', unsafe_allow_html=True)
            st.markdown('<div class="auth-form-subtitle">Sign in to your account to continue</div>', unsafe_allow_html=True)
            st.markdown('<hr class="auth-form-divider">', unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Sign In", use_container_width=True, type="primary"):
                _rl_ok, _rl_msg = rate_limit("login", key=username.lower().strip())
                if not _rl_ok:
                    st.error(_rl_msg)
                else:
                    _vi_ok, _vi_msg = validate_login_input(username, password)
                    if not _vi_ok:
                        st.error(_vi_msg)
                    else:
                        success, msg = login_user(username, password)
                        if success:
                            reset_rate_limit("login", key=username.lower().strip())
                            st.session_state.logged_in = True
                            st.session_state.username  = username
                            st.session_state.role      = "user"
                            st.rerun()
                        else:
                            st.error(msg)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Forgot Password?", use_container_width=True):
                st.session_state.auth_page = "Forgot Password"
                st.rerun()

        elif st.session_state.auth_page == "User Registration":
            st.markdown('<div class="auth-form-title">Create account</div>', unsafe_allow_html=True)
            st.markdown('<div class="auth-form-subtitle">Join thousands of developers today</div>', unsafe_allow_html=True)
            st.markdown('<hr class="auth-form-divider">', unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="Choose a username")
            email    = st.text_input("Email Address", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="Min 8 chars, 1 number, 1 special char")
            confirm  = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Create Account", use_container_width=True, type="primary"):
                _rl_ok, _rl_msg = rate_limit("register", key="global")
                if not _rl_ok:
                    st.error(_rl_msg)
                else:
                    _un_ok, _un_msg = validate_username(username)
                    _em_ok, _em_msg = validate_email(email)
                    _pw_ok, _pw_msg = validate_password(password)
                    if not _un_ok:           st.error(_un_msg)
                    elif not _em_ok:         st.error(_em_msg)
                    elif not _pw_ok:         st.error(_pw_msg)
                    elif password != confirm: st.error("Passwords do not match.")
                    else:
                        success, msg = register_user(username, password, email)
                        if success:
                            save_user_email(username, email)
                            st.success("Account created! You can now log in.")
                            st.session_state.auth_page = "User Login"
                            st.rerun()
                        else:
                            st.error(msg)

        elif st.session_state.auth_page == "Forgot Password":
            reset_step = st.session_state.get("reset_step", 1)
            if reset_step == 1:
                st.markdown('<div class="auth-form-title">Reset password</div>', unsafe_allow_html=True)
                st.markdown('<div class="auth-form-subtitle">We will send a reset code to your email</div>', unsafe_allow_html=True)
                st.markdown('<hr class="auth-form-divider">', unsafe_allow_html=True)
                rst_username = st.text_input("Username", key="rst_username", placeholder="Your username")
                rst_email    = st.text_input("Registered Email", key="rst_email", placeholder="you@example.com")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Send Reset Code", use_container_width=True, type="primary"):
                    _rl_ok, _rl_msg = rate_limit("password_reset", key=rst_username.lower().strip())
                    if not _rl_ok:
                        st.error(_rl_msg)
                    elif not rst_username or not rst_email or "@" not in rst_email:
                        st.error("Please enter your username and email.")
                    else:
                        stored_email = get_user_email(rst_username)
                        if stored_email is None:
                            st.error("Username not found.")
                        elif stored_email.lower() != rst_email.lower():
                            st.error("Email does not match our records.")
                        else:
                            token = create_reset_token(rst_username)
                            if token:
                                ok, msg = send_reset_email(rst_email, rst_username, token)
                                if ok:
                                    st.session_state.reset_username = rst_username
                                    st.session_state.reset_step     = 2
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                            else:
                                st.error("Could not generate reset token.")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Back to Login", use_container_width=True):
                    st.session_state.reset_step = 1
                    st.session_state.auth_page  = "User Login"
                    st.rerun()

            elif reset_step == 2:
                st.markdown('<div class="auth-form-title">Enter reset code</div>', unsafe_allow_html=True)
                st.markdown('<div class="auth-form-subtitle">Check your email for the 8-character code</div>', unsafe_allow_html=True)
                st.markdown('<hr class="auth-form-divider">', unsafe_allow_html=True)
                st.markdown("""<div style="background:#f0f2f4;border:2px dashed #4a6b8a;border-radius:12px;
                    padding:12px;text-align:center;font-size:0.82rem;color:#3a5570;
                    margin-bottom:1rem;font-weight:600;">Code expires in 1 hour</div>""",
                    unsafe_allow_html=True)
                rst_code     = st.text_input("Reset Code", key="rst_code", placeholder="e.g. A1B2C3D4").strip().upper()
                new_pass     = st.text_input("New Password", type="password", key="rst_new_pass")
                confirm_pass = st.text_input("Confirm New Password", type="password", key="rst_confirm_pass")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Reset Password", use_container_width=True, type="primary"):
                    if not rst_code or not new_pass or not confirm_pass:
                        st.error("Please fill in all fields.")
                    elif new_pass != confirm_pass:
                        st.error("Passwords do not match.")
                    else:
                        try:
                            with get_connection() as conn:
                                with conn.cursor() as cur:
                                    cur.execute(
                                        "SELECT token FROM password_reset_tokens "
                                        "WHERE username = %s AND used = FALSE "
                                        "AND expires_at > NOW() "
                                        "ORDER BY created_at DESC LIMIT 1",
                                        (st.session_state.get("reset_username", ""),)
                                    )
                                    row = cur.fetchone()
                            if not row:
                                st.error("Code expired or already used. Request a new one.")
                                st.session_state.reset_step = 1
                            elif row[0][:8].upper() != rst_code:
                                st.error("Incorrect reset code.")
                            else:
                                full_token = row[0]
                                valid, result = verify_reset_token(full_token)
                                if not valid:
                                    st.error(result)
                                else:
                                    ok, msg = validate_password_strength(new_pass)
                                    if not ok:
                                        st.error(msg)
                                    else:
                                        from werkzeug.security import generate_password_hash
                                        hashed = generate_password_hash(new_pass)
                                        with get_connection() as conn:
                                            with conn.cursor() as cur:
                                                cur.execute(
                                                    "UPDATE users SET password = %s WHERE username = %s",
                                                    (hashed, result))
                                                conn.commit()
                                        mark_token_used(full_token)
                                        st.success("Password reset! You can now log in.")
                                        st.session_state.reset_step = 1
                                        st.session_state.auth_page  = "User Login"
                                        st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Request New Code", use_container_width=True):
                    st.session_state.reset_step = 1
                    st.rerun()

        elif st.session_state.auth_page == "Admin Login":
            st.markdown('<div class="auth-form-title">Admin access</div>', unsafe_allow_html=True)
            st.markdown('<div class="auth-form-subtitle">Restricted to administrators only</div>', unsafe_allow_html=True)
            st.markdown('<hr class="auth-form-divider">', unsafe_allow_html=True)
            username = st.text_input("Admin Username", placeholder="Enter admin username")
            password = st.text_input("Admin Password", type="password", placeholder="Enter admin password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Sign In as Admin", use_container_width=True, type="primary"):
                _rl_ok, _rl_msg = rate_limit("login", key=f"admin:{username.lower().strip()}")
                if not _rl_ok:
                    st.error(_rl_msg)
                else:
                    _vi_ok, _vi_msg = validate_login_input(username, password)
                    if not _vi_ok:
                        st.error(_vi_msg)
                    else:
                        success, msg = login_admin(username, password)
                        if success:
                            reset_rate_limit("login", key=f"admin:{username.lower().strip()}")
                            st.session_state.logged_in = True
                            st.session_state.username  = username
                            st.session_state.role      = "admin"
                            st.rerun()
                        else:
                            st.error(msg)

    with banner_col:
        st.markdown("""
            <div class="auth-hero-panel">
                <div class="auth-hero-inner">
                    <div class="auth-badge">Developer Salary Intelligence</div>
                    <h2 class="auth-hero-title">Know Your<br><span>True Worth</span></h2>
                    <p class="auth-hero-sub">
                        Precision salary predictions powered<br>
                        by real-world developer data.<br>
                        Make smarter career moves today.
                    </p>
                    <div class="auth-stats">
                        <div class="auth-stat-pill">
                            <div class="auth-stat-num" style="color:#f0f2f4;">10K+</div>
                            <div class="auth-stat-label">Responses</div>
                        </div>
                        <div class="auth-stat-pill">
                            <div class="auth-stat-num" style="color:#d9e4ee;">50+</div>
                            <div class="auth-stat-label">Countries</div>
                        </div>
                        <div class="auth-stat-pill">
                            <div class="auth-stat-num" style="color:#c7d5e2;">Free</div>
                            <div class="auth-stat-label">Always</div>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)


# ── MAIN APP (logged in) ──────────────────────────────────────────────────────
if st.session_state.logged_in:

    pages = (
        {"Admin Dashboard": "Admin Dashboard", "Logout": "Logout"}
        if st.session_state.role == "admin"
        else {
            "Home":       "Home",
            "Predict":    "Predict",
            "Explore":    "Explore",
            "Skill Gap":  "Skill Gap",
            "My Profile": "My Profile",
            "Logout":     "Logout",
        }
    )

    if "_force_nav" in st.session_state and st.session_state._force_nav in pages.values():
        st.session_state.nav_selectbox = st.session_state._force_nav
        del st.session_state._force_nav

    if "nav_selectbox" not in st.session_state or st.session_state.nav_selectbox not in pages.values():
        st.session_state.nav_selectbox = next(iter(pages.values()))

    role_label = "Admin" if st.session_state.role == "admin" else "User"
    st.sidebar.success(f"{role_label}: {st.session_state.username}")
    st.sidebar.markdown("### Navigation")

    for label, page_key in pages.items():
        if st.session_state.nav_selectbox == page_key:
            st.sidebar.markdown(f"""
                <div style='background-color:#185FA5; color:white;
                padding:8px 12px; border-radius:8px;
                margin-bottom:4px; font-weight:bold;'>{label}</div>
            """, unsafe_allow_html=True)
        else:
            if st.sidebar.button(label, key=f"nav_{page_key}", use_container_width=True):
                if page_key == "Logout":
                    st.session_state.clear()
                    st.rerun()
                else:
                    st.session_state.nav_selectbox = page_key
                    st.rerun()

    menu = st.session_state.nav_selectbox

    if   menu == "Home":            show_home_page()
    elif menu == "Predict":         show_predict_page()
    elif menu == "Explore":         show_explore_page()
    elif menu == "Skill Gap":       show_skill_gap_page()
    elif menu == "My Profile":      show_profile_section()
    elif menu == "Admin Dashboard": show_admin_section()
