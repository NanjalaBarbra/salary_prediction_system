import streamlit as st
import re
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_connection

# -------------------------------
# Password Strength Validation
# -------------------------------
def validate_password_strength(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, "Valid"

# -------------------------------
# User Registration
# -------------------------------
def register_user(username, password):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT username FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return False, "Username already exists."

        valid, msg = validate_password_strength(password)
        if not valid:
            cur.close()
            conn.close()
            return False, msg

        hashed_pw = generate_password_hash(password)
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_pw))
        conn.commit()
        cur.close()
        conn.close()
        return True, "User registered successfully."
    except Exception as e:
        return False, f"Error: {str(e)}"

# -------------------------------
# User Login
# -------------------------------
def login_user(username, password):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user:
            return False, "User not found."
        if check_password_hash(user[0], password):
            return True, "Login successful."
        else:
            return False, "Invalid credentials."
    except Exception as e:
        return False, f"Error: {str(e)}"


# -------------------------------
# Change Password
# -------------------------------
def change_password(username, current_password, new_password):
    """
    Verify the current password, then update to the new hashed password.
    Returns (success: bool, message: str).
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE username = %s", (username,))
        row = cur.fetchone()

        if not row:
            cur.close()
            conn.close()
            return False, "User not found."

        stored_hash = row[0]
        if not check_password_hash(stored_hash, current_password):
            cur.close()
            conn.close()
            return False, "Current password is incorrect."

        # Validate new password strength
        valid, msg = validate_password_strength(new_password)
        if not valid:
            cur.close()
            conn.close()
            return False, msg

        new_hash = generate_password_hash(new_password)
        cur.execute(
            "UPDATE users SET password = %s WHERE username = %s",
            (new_hash, username),
        )
        conn.commit()
        cur.close()
        conn.close()
        return True, "Password updated successfully."
    except Exception as e:
        return False, f"Error updating password: {str(e)}"


# -------------------------------
# Delete User Account (+ Predictions)
# -------------------------------
def delete_user_account(username):
    """
    Delete a user and all of their predictions.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Delete predictions first to avoid FK issues
        cur.execute("DELETE FROM predictions WHERE username = %s", (username,))
        cur.execute("DELETE FROM users WHERE username = %s", (username,))

        conn.commit()
        cur.close()
        conn.close()
        return True, "Account and all predictions deleted."
    except Exception as e:
        return False, f"Error deleting account: {str(e)}"

# -------------------------------
# Admin Login (Hardcoded)
# -------------------------------
def login_admin(username, password):
    if username == "admin" and password == "admin@123":
        return True, "Admin login successful."
    else:
        return False, "Invalid admin credentials."

# -------------------------------
# Authentication UI
# -------------------------------
def show_auth_page():
    st.sidebar.title("🔐 Authentication")
    option = st.sidebar.radio("Select Option", ["User Register", "User Login", "Forgot Password", "Admin Login"])

    # Add custom styling for centered layout
    st.markdown("""
        <style>
        .auth-main-title {
            text-align: center;
            font-size: 4.5rem;
            font-weight: 800;
            background: linear-gradient(120deg, #10b981, #3b82f6, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-top: 2rem;
            margin-bottom: 0.5rem;
            text-shadow: 0 4px 20px rgba(59, 130, 246, 0.3);
        }
        .auth-subtitle {
            text-align: center;
            font-size: 1.5rem;
            color: #1e40af;
            margin-bottom: 3rem;
            font-weight: 700;
            background: #ffffff;
            padding: 0.75rem 2rem;
            border-radius: 50px;
            display: inline-block;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
            border: 2px solid #3b82f6;
        }
        .auth-form-container {
            max-width: 400px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 24px;
            padding: 2.5rem 2.5rem;
            box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4);
            border: 3px solid rgba(251, 191, 36, 0.4);
            backdrop-filter: blur(10px);
        }
        .auth-form-title {
            text-align: center;
            font-size: 1.8rem;
            font-weight: 700;
            background: linear-gradient(120deg, #8b5cf6, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2rem;
            margin-top: 1rem;
        }
        .auth-footer {
            text-align: center;
            margin-top: 3rem;
            font-size: 1.2rem;
            color: #1f2937;
            font-weight: 600;
            background: linear-gradient(120deg, #fbbf24, #f59e0b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        /* Center text input labels */
        .auth-form-container label {
            text-align: center;
            display: block;
            font-weight: 600;
            color: #1f2937;
            font-size: 1rem;
        }
        /* Center and style text inputs */
        .auth-form-container input {
            text-align: center;
            border-radius: 12px;
            border: 2px solid #e5e7eb;
            padding: 0.75rem;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        .auth-form-container input:focus {
            border-color: #8b5cf6;
            box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2);
        }
        /* Center button */
        div[data-testid="stButton"] button {
            width: 100%;
            background: linear-gradient(120deg, #10b981, #3b82f6);
            color: white;
            border: none;
            padding: 0.85rem 1.5rem;
            border-radius: 12px;
            font-weight: 700;
            font-size: 1.1rem;
            margin-top: 1.5rem;
            box-shadow: 0 10px 30px rgba(16, 185, 129, 0.3);
            transition: all 0.3s ease;
        }
        div[data-testid="stButton"] button:hover {
            background: linear-gradient(120deg, #059669, #2563eb);
            transform: translateY(-2px);
            box-shadow: 0 15px 40px rgba(16, 185, 129, 0.4);
        }
        /* Style success and error messages */
        .stSuccess {
            background: linear-gradient(120deg, #10b981, #059669);
            color: white;
            border-radius: 12px;
            padding: 1rem;
            font-weight: 600;
        }
        .stError {
            background: linear-gradient(120deg, #ef4444, #dc2626);
            color: white;
            border-radius: 12px;
            padding: 1rem;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)

    # Main title and subtitle
    st.markdown('<h1 class="auth-main-title">🚀 Salary Prediction App</h1>', unsafe_allow_html=True)
    st.markdown('<div style="text-align: center;"><p class="auth-subtitle">Unlock your true market value with precision.</p></div>', unsafe_allow_html=True)

    # Centered form container
    if option == "User Register":
        st.markdown('<div class="auth-form-title">📝 User Registration</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-form-container">', unsafe_allow_html=True)
        
        username = st.text_input("Username", key="register_username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", key="register_password", placeholder="Enter your password")
        
        if st.button("Register", key="register_btn"):
            success, msg = register_user(username, password)
            if success:
                st.success(msg)
            else:
                st.error(msg)
        
        st.markdown('</div>', unsafe_allow_html=True)

    elif option == "User Login":
        st.markdown('<div class="auth-form-title">🔑 User Login</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-form-container">', unsafe_allow_html=True)
        
        username = st.text_input("Username", key="login_username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
        
        if st.button("Login", key="login_btn"):
            success, msg = login_user(username, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(msg)
            else:
                st.error(msg)
        
        st.markdown('</div>', unsafe_allow_html=True)

    elif option == "Forgot Password":
        st.markdown('<div class="auth-form-title">🔄 Reset Password</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-form-container">', unsafe_allow_html=True)
        
        username = st.text_input("Username", key="forgot_username", placeholder="Enter your username")
        current_password = st.text_input("Current Password", type="password", key="current_password", placeholder="Enter current password")
        new_password = st.text_input("New Password", type="password", key="new_password", placeholder="Enter new password")
        
        if st.button("Change Password", key="change_password_btn"):
            success, msg = change_password(username, current_password, new_password)
            if success:
                st.success(msg)
            else:
                st.error(msg)
        
        st.markdown('</div>', unsafe_allow_html=True)

    elif option == "Admin Login":
        st.markdown('<div class="auth-form-title">🛡️ Admin Login</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-form-container">', unsafe_allow_html=True)
        
        username = st.text_input("Admin Username", key="admin_username", placeholder="Enter admin username")
        password = st.text_input("Admin Password", type="password", key="admin_password", placeholder="Enter admin password")
        
        if st.button("Login as Admin", key="admin_login_btn"):
            success, msg = login_admin(username, password)
            if success:
                st.session_state.admin_logged_in = True
                st.success(msg)
            else:
                st.error(msg)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Footer message
    st.markdown('<p class="auth-footer">👈 Use sidebar to login or register</p>', unsafe_allow_html=True)