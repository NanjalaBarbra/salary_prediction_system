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
    option = st.sidebar.radio("Select Option", ["User Register", "User Login", "Admin Login"])

    st.markdown("""
    <div class="auth-box">
        <h1>🚀 Salary Prediction App</h1>
        <p>Unlock your true market value with precision.</p>
    </div>
    """, unsafe_allow_html=True)

    if option == "User Register":
        st.subheader("📝 User Registration")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Register"):
            success, msg = register_user(username, password)
            st.success(msg) if success else st.error(msg)

    elif option == "User Login":
        st.subheader("🔑 User Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            success, msg = login_user(username, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(msg)
            else:
                st.error(msg)

    elif option == "Admin Login":
        st.subheader("🛡️ Admin Login")
        username = st.text_input("Admin Username")
        password = st.text_input("Admin Password", type="password")
        if st.button("Login as Admin"):
            success, msg = login_admin(username, password)
            if success:
                st.session_state.admin_logged_in = True
                st.success(msg)
            else:
                st.error(msg)