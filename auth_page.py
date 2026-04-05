import streamlit as st
import re
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_connection
from password_reset import (
    create_reset_token, verify_reset_token, mark_token_used,
    get_user_email, save_user_email, send_reset_email,
)


# ------------------------------------------------------------------ #
# PASSWORD STRENGTH
# ------------------------------------------------------------------ #

def validate_password_strength(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, "Valid"


# ------------------------------------------------------------------ #
# REGISTRATION
# ------------------------------------------------------------------ #

def register_user(username, password, email=None):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT username FROM users WHERE username = %s", (username,))
                if cur.fetchone():
                    return False, "Username already exists."

                valid, msg = validate_password_strength(password)
                if not valid:
                    return False, msg

                hashed_pw = generate_password_hash(password)

                cur.execute(
                    "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
                    (username, hashed_pw, email)
                )
                conn.commit()
        return True, "User registered successfully."
    except Exception as e:
        return False, f"Error: {str(e)}"


# ------------------------------------------------------------------ #
# LOGIN
# ------------------------------------------------------------------ #

def login_user(username, password):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT password FROM users WHERE username = %s", (username,))
                user = cur.fetchone()

        if not user:
            return False, "User not found."
        if check_password_hash(user[0], password):
            return True, "Login successful."
        else:
            return False, "Invalid credentials."
    except Exception as e:
        return False, f"Error: {str(e)}"


# ------------------------------------------------------------------ #
# CHANGE PASSWORD (logged-in user)
# ------------------------------------------------------------------ #

def change_password(username, current_password, new_password):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT password FROM users WHERE username = %s", (username,))
                row = cur.fetchone()

                if not row:
                    return False, "User not found."

                if not check_password_hash(row[0], current_password):
                    return False, "Current password is incorrect."

                valid, msg = validate_password_strength(new_password)
                if not valid:
                    return False, msg

                new_hash = generate_password_hash(new_password)
                cur.execute(
                    "UPDATE users SET password = %s WHERE username = %s",
                    (new_hash, username),
                )
                conn.commit()
        return True, "Password updated successfully."
    except Exception as e:
        return False, f"Error updating password: {str(e)}"


# ------------------------------------------------------------------ #
# DELETE ACCOUNT
# ------------------------------------------------------------------ #

def delete_user_account(username):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM predictions WHERE username = %s", (username,))
                cur.execute("DELETE FROM users WHERE username = %s", (username,))
                conn.commit()
        return True, "Account and all predictions deleted."
    except Exception as e:
        return False, f"Error deleting account: {str(e)}"


# ------------------------------------------------------------------ #
# ADMIN LOGIN  — now fully database-backed
# Passwords are stored as werkzeug hashes in the admins table.
# Use create_admin.py to create or reset admin accounts.
# ------------------------------------------------------------------ #

def login_admin(username, password):
    """
    Verify admin credentials against the admins table in the database.
    Returns (True, "Admin login successful.") on success,
    or (False, "Invalid admin credentials.") on failure.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT password FROM admins WHERE username = %s",
                    (username,)
                )
                row = cur.fetchone()

        if not row:
            return False, "Invalid admin credentials."

        if check_password_hash(row[0], password):
            return True, "Admin login successful."
        else:
            return False, "Invalid admin credentials."

    except Exception as e:
        return False, f"Error: {str(e)}"


# ------------------------------------------------------------------ #
# ADMIN REGISTRATION (internal use — called by create_admin.py)
# ------------------------------------------------------------------ #

def register_admin(username, password):
    """
    Create a new admin account in the admins table.
    Password is hashed before storage — never stored in plaintext.
    Call this from create_admin.py, not from the UI.
    """
    try:
        valid, msg = validate_password_strength(password)
        if not valid:
            return False, msg

        hashed_pw = generate_password_hash(password)

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT username FROM admins WHERE username = %s", (username,)
                )
                if cur.fetchone():
                    # Admin exists — update password instead
                    cur.execute(
                        "UPDATE admins SET password = %s WHERE username = %s",
                        (hashed_pw, username)
                    )
                    conn.commit()
                    return True, f"Admin '{username}' password updated successfully."
                else:
                    cur.execute(
                        "INSERT INTO admins (username, password) VALUES (%s, %s)",
                        (username, hashed_pw)
                    )
                    conn.commit()
                    return True, f"Admin '{username}' created successfully."

    except Exception as e:
        return False, f"Error: {str(e)}"


# ------------------------------------------------------------------ #
# AUTH PAGE UI
# ------------------------------------------------------------------ #

def show_auth_page():

    # ---- Shared CSS ----
    st.markdown(
        """
        <style>
        .auth-main-title {
            text-align: center;
            font-size: 4.5rem;
            font-weight: 800;
            background: linear-gradient(120deg, #1a2e42, #2d4a6b, #4a6b8a);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-top: 2rem;
            margin-bottom: 0.5rem;
        }
        .auth-subtitle {
            text-align: center;
            font-size: 1.5rem;
            color: #1a2e42;
            margin-bottom: 3rem;
            font-weight: 700;
            background: #ffffff;
            padding: 0.75rem 2rem;
            border-radius: 50px;
            display: inline-block;
            box-shadow: 0 4px 20px rgba(45, 74, 107, 0.14);
            border: 2px solid #4a6b8a;
        }
        .auth-form-title {
            text-align: center;
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(120deg, #2d4a6b, #4a6b8a);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1.5rem;
            margin-top: 1rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .auth-form-container {
            max-width: 400px;
            margin: 0 auto;
            background: rgba(255,255,255,0.95);
            border-radius: 24px;
            padding: 2.5rem;
            box-shadow: 0 20px 60px rgba(45,74,107,0.18);
            border: 2px solid rgba(74,107,138,0.22);
            backdrop-filter: blur(10px);
        }
        .reset-code-box {
            background: #f0f2f4;
            border: 2px dashed #4a6b8a;
            border-radius: 12px;
            padding: 14px;
            text-align: center;
            font-size: 0.82rem;
            color: #3a5570;
            margin: 0.8rem 0;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.title("🔐 Authentication")
    option = st.sidebar.radio(
        "Select Option",
        ["User Login", "User Register", "Forgot Password", "Admin Login"],
    )

    # ---- Title ----
    st.markdown('<h1 class="auth-main-title">🚀 Salary Prediction App</h1>', unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align:center;"><p class="auth-subtitle">'
        'Unlock your true market value with precision.</p></div>',
        unsafe_allow_html=True,
    )

    _, form_col, _ = st.columns([1, 1.2, 1])

    with form_col:

        # ============================================================
        # USER LOGIN
        # ============================================================
        if option == "User Login":
            st.markdown('<div class="auth-form-title">🔑 User Login</div>', unsafe_allow_html=True)

            username = st.text_input("Username", key="login_username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", key="login_password",
                                     placeholder="Enter your password")

            if st.button("Login", key="login_btn", use_container_width=True):
                success, msg = login_user(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = "user"
                    st.rerun()
                else:
                    st.error(msg)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔑 Forgot Password?", key="goto_forgot", use_container_width=True):
                st.session_state["auth_page"] = "Forgot Password"
                st.rerun()

        # ============================================================
        # USER REGISTRATION
        # ============================================================
        elif option == "User Register":
            st.markdown('<div class="auth-form-title">📝 Create Account</div>', unsafe_allow_html=True)

            reg_username = st.text_input("Username", key="reg_username",
                                         placeholder="Choose a username")
            reg_email = st.text_input("Email Address", key="reg_email",
                                      placeholder="you@example.com")
            reg_password = st.text_input("Password", type="password", key="reg_password",
                                         placeholder="Min 8 chars, 1 number, 1 special char")
            reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm",
                                        placeholder="Re-enter your password")

            if st.button("Create Account", key="reg_btn", use_container_width=True):
                if not reg_username or not reg_email or not reg_password:
                    st.error("Please fill in all fields.")
                elif "@" not in reg_email:
                    st.error("Please enter a valid email address.")
                elif reg_password != reg_confirm:
                    st.error("Passwords do not match.")
                else:
                    success, msg = register_user(reg_username, reg_password, reg_email)
                    if success:
                        save_user_email(reg_username, reg_email)
                        st.success("✅ Account created! You can now log in.")
                    else:
                        st.error(msg)

        # ============================================================
        # FORGOT PASSWORD
        # ============================================================
        elif option == "Forgot Password":
            reset_step = st.session_state.get("reset_step", 1)

            if reset_step == 1:
                st.markdown('<div class="auth-form-title">🔒 Reset Password</div>',
                            unsafe_allow_html=True)
                st.markdown(
                    """
                    <p style="font-size:0.85rem; color:#6b7c8d; text-align:center; margin-bottom:1rem;">
                        Enter your username and registered email.<br>
                        We'll send you a reset code.
                    </p>
                    """,
                    unsafe_allow_html=True,
                )

                fp_username = st.text_input("Username", key="fp_username",
                                            placeholder="Your username")
                fp_email = st.text_input("Registered Email", key="fp_email",
                                         placeholder="you@example.com")

                if st.button("Send Reset Code", key="fp_send", use_container_width=True,
                             type="primary"):
                    if not fp_username or not fp_email or "@" not in fp_email:
                        st.error("Please enter your username and email.")
                    else:
                        stored = get_user_email(fp_username)
                        if stored is None:
                            st.error("Username not found.")
                        elif stored.lower() != fp_email.lower():
                            st.error("Email does not match our records for that username.")
                        else:
                            token = create_reset_token(fp_username)
                            if token:
                                ok, msg = send_reset_email(fp_email, fp_username, token)
                                if ok:
                                    st.session_state.reset_username = fp_username
                                    st.session_state.reset_step = 2
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                            else:
                                st.error("Could not generate reset token. Try again.")

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("← Back to Login", key="fp_back", use_container_width=True):
                    st.session_state.reset_step = 1
                    st.session_state.auth_page = "User Login"
                    st.rerun()

            elif reset_step == 2:
                st.markdown('<div class="auth-form-title">📬 Enter Reset Code</div>',
                            unsafe_allow_html=True)
                st.markdown(
                    """
                    <div class="reset-code-box">
                        Check your email for an 8-character reset code
                        and enter it below. It expires in 1 hour.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                rst_code = st.text_input("Reset Code", key="rst_code",
                                         placeholder="e.g. A1B2C3D4").strip().upper()
                new_pass = st.text_input("New Password", type="password", key="rst_new",
                                         placeholder="Min 8 chars, 1 number, 1 special char")
                confirm_pass = st.text_input("Confirm New Password", type="password",
                                             key="rst_confirm", placeholder="Re-enter new password")

                if st.button("Reset Password", key="rst_submit", use_container_width=True,
                             type="primary"):
                    if not rst_code or not new_pass or not confirm_pass:
                        st.error("Please fill in all fields.")
                    elif new_pass != confirm_pass:
                        st.error("Passwords do not match.")
                    else:
                        try:
                            with get_connection() as conn:
                                with conn.cursor() as cur:
                                    cur.execute(
                                        """
                                        SELECT token FROM password_reset_tokens
                                        WHERE username = %s AND used = FALSE
                                        AND expires_at > NOW()
                                        ORDER BY created_at DESC LIMIT 1
                                        """,
                                        (st.session_state.get("reset_username", ""),)
                                    )
                                    row = cur.fetchone()

                            if not row:
                                st.error("Reset code expired or already used. Request a new one.")
                                st.session_state.reset_step = 1
                            elif row[0][:8].upper() != rst_code:
                                st.error("Incorrect reset code. Please check your email.")
                            else:
                                full_token = row[0]
                                valid, result = verify_reset_token(full_token)
                                if not valid:
                                    st.error(result)
                                else:
                                    pw_ok, pw_msg = validate_password_strength(new_pass)
                                    if not pw_ok:
                                        st.error(pw_msg)
                                    else:
                                        new_hash = generate_password_hash(new_pass)
                                        with get_connection() as conn:
                                            with conn.cursor() as cur:
                                                cur.execute(
                                                    "UPDATE users SET password = %s WHERE username = %s",
                                                    (new_hash, result)
                                                )
                                                conn.commit()
                                        mark_token_used(full_token)
                                        st.success("✅ Password reset! You can now log in.")
                                        st.session_state.reset_step = 1
                                        st.session_state.reset_username = ""
                        except Exception as e:
                            st.error(f"Error: {str(e)}")

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("← Request New Code", key="rst_back", use_container_width=True):
                    st.session_state.reset_step = 1
                    st.rerun()

        # ============================================================
        # ADMIN LOGIN
        # ============================================================
        elif option == "Admin Login":
            st.markdown('<div class="auth-form-title">🛡️ Admin Login</div>', unsafe_allow_html=True)

            admin_user = st.text_input("Admin Username", key="admin_username",
                                       placeholder="Enter admin username")
            admin_pass = st.text_input("Admin Password", type="password", key="admin_password",
                                       placeholder="Enter admin password")

            if st.button("Login as Admin", key="admin_login_btn", use_container_width=True):
                success, msg = login_admin(admin_user, admin_pass)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = admin_user
                    st.session_state.role = "admin"
                    st.rerun()
                else:
                    st.error(msg)
