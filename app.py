import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from predict_page import show_predict_page
from explore_page import show_explore_page
from auth_page import login_user, register_user, login_admin
from database import get_connection

ADMIN_PASSWORD = "admin@123"   


# ================= UI STYLING =================
st.markdown("""
<style>
/* --- FONTS --- */
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
}

/* --- MAIN BACKGROUND --- */
.stApp {
    background: radial-gradient(circle at 10% 20%, rgb(0, 0, 0) 0%, rgb(20, 20, 30) 40%, rgb(30, 35, 60) 90.2%);
    color: #f0f2f6;
}

/* --- SIDEBAR --- */
section[data-testid="stSidebar"] {
    background: rgba(15, 15, 20, 0.95);
    border-right: 1px solid rgba(255, 255, 255, 0.1);
}

/* --- HEADERS --- */
h1, h2, h3, h4, h5, h6 {
    color: #ffffff;
    font-weight: 700;
    letter-spacing: 0.5px;
}
h1 {
    background: -webkit-linear-gradient(45deg, #00d2ff, #3a7bd5);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* --- CARDS & CONTAINERS --- */
div.stMarkdown > div > div > div.auth-box { /* Targeted custom class */
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 40px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}

div.css-card { /* Custom wrapper if used */
    background: rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 24px;
    border: 1px solid rgba(255, 255, 255, 0.08);
}

/* --- BUTTONS --- */
.stButton > button {
    background: linear-gradient(92.88deg, #455EB5 9.16%, #5643CC 43.89%, #673FD7 64.72%);
    border-radius: 12px;
    color: white;
    font-weight: 600;
    border: none;
    padding: 0.6rem 1.2rem;
    transition: all 0.3s ease;
    box-shadow: 0 4px 14px 0 rgba(100, 100, 255, 0.39);
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(100, 100, 255, 0.23);
    background: linear-gradient(92.88deg, #5643CC 9.16%, #673FD7 43.89%, #455EB5 64.72%);
}

/* --- INPUTS --- */
.stTextInput > div > div > input, .stSelectbox > div > div > div, .stNumberInput > div > div > input {
    background-color: rgba(255, 255, 255, 0.07);
    color: white;
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}
.stTextInput > div > div > input:focus {
    border-color: #4c51bf;
    box-shadow: 0 0 0 1px #4c51bf;
}

/* --- EXPANDERS --- */
.streamlit-expanderHeader {
    background-color: rgba(255, 255, 255, 0.03);
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.05);
}

/* --- METRICS --- */
[data-testid="stMetricValue"] {
    font-size: 2rem;
    color: #4fd1c5;
}
[data-testid="stMetricLabel"] {
    color: #a0aec0;
}

/* --- DATAFRAME --- */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Session State
# -------------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = None   # guest by default
if "auth_page" not in st.session_state:
    st.session_state.auth_page = "User Login"   # default landing page
if "nav_version" not in st.session_state:
    st.session_state.nav_version = 0


st.markdown("""
<div style="text-align: center; margin-bottom: 30px;">
    <h1 style="font-size: 3.5rem; background: -webkit-linear-gradient(45deg, #FFD700, #FF8C00);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        🚀 Salary Prediction App
    </h1>
    <h3 style="color: #cbd5e0; font-weight: 300;">
        Unlock your true market value with precision.
    </h3>
</div>
""", unsafe_allow_html=True)

# -------------------------------
# ================= SIDEBAR =================
st.sidebar.title("🔐 Authentication")

if not st.session_state.logged_in:
    options = ["User Login", "User Registration", "Admin Login"]

    try:
        idx = options.index(st.session_state.auth_page)
    except ValueError:
        idx = 0

    nav_key = f"nav_{st.session_state.nav_version}"

    auth_choice = st.sidebar.radio(
        "Select Option",
        options,
        index=idx,
        key=nav_key
    )

    if auth_choice != st.session_state.auth_page:
        st.session_state.auth_page = auth_choice
        st.rerun()
else:
    if st.session_state.role == "admin":
        st.sidebar.success(f"🛡 Logged in as Admin {st.session_state.username}")
    else:
        st.sidebar.success(f"👋 Logged in as {st.session_state.username}")

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()


# Authentication Pages

if not st.session_state.logged_in:
    if st.session_state.auth_page == "User Login":
        st.subheader("🔑 User Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            success, msg = login_user(username, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = "user"
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    elif st.session_state.auth_page == "User Registration":
         st.subheader("📝 User Registration")
         username = st.text_input("Choose a Username")
         password = st.text_input("Choose a Password", type="password")
         if st.button("Register"):
            success, msg = register_user(username, password)
            if success:
                st.success(msg)
            else:
                st.error(msg)


    elif st.session_state.auth_page == "Admin Login":
        st.subheader("🛡️ Admin Login")
        username = st.text_input("Admin Username")
        password = st.text_input("Admin Password", type="password")
        if st.button("Login as Admin"):
            success, msg = login_admin(username, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = "admin"
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
    


# -------------------------------
# User Pages
# -------------------------------
elif menu == "Predict":
    if st.session_state.logged_in and st.session_state.role == "user":
        show_predict_page()
    else:
        st.warning("Please log in as a user to access this page.")

elif menu == "Explore":
    if st.session_state.logged_in and st.session_state.role == "user":
        show_explore_page()
    else:
        st.warning("Please log in as a user to access this page.")

elif menu == "My Predictions":
    if st.session_state.logged_in and st.session_state.role == "user":
        st.title("My Past Predictions")
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT country, education, employment, experience, webframework, undergradmajor, predicted_salary, predicted_at
                FROM predictions WHERE username = %s
            """, (st.session_state.username,))
            rows = cur.fetchall()
            cur.close()
            conn.close()

            if rows:
                for row in rows:
                    st.write(f"""
                    **Country:** {row[0]}  
                    **Education:** {row[1]}  
                    **Employment:** {row[2]}  
                    **Experience:** {row[3]} years  
                    **Web Framework:** {row[4]}  
                    **Undergrad Major:** {row[5]}  
                    **Predicted Salary:** ${row[6]:.2f}  
                    **Date:** {row[7]}  
                    """)
            else:
                st.info("No predictions found yet.")
        except Exception as e:
            st.error(f"Database error: {str(e)}")
    else:
        st.warning("Please log in to view your predictions.")

# -------------------------------
# Admin Dashboard
# -------------------------------
elif menu == "Admin Dashboard":
    if st.session_state.logged_in and st.session_state.role == "admin":
        st.title("🛡 Admin Dashboard")

        # Fetch predictions
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, country, experience, predicted_salary, predicted_at FROM predictions")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        data = [
            {
                "id": row[0],
                "username": row[1],
                "country": row[2],
                "experience": row[3],
                "predicted_salary": row[4],
                "predicted_at": row[5].strftime("%d-%m-%Y %I:%M %p") if row[5] else ""
            }
            for row in rows
        ]
        df = pd.DataFrame(data)

        # KPIs
        c1, c2, c3, c4 = st.columns(4)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        total_users_count = cur.fetchone()[0]
        cur.close()
        conn.close()

        c1.metric("Total Users", total_users_count)
        c2.metric("Total Predictions", len(df))
        if not df.empty:
            c3.metric("Highest Salary", f"KES{int(df['predicted_salary'].max()):,}")
            c4.metric("Lowest Salary", f"KES{int(df['predicted_salary'].min()):,}")
        else:
            c3.metric("Highest Salary", "KES0")
            c4.metric("Lowest Salary", "KES0")

        st.divider()

        # Modify Record
        st.subheader("✏ Modify Record")
        search_term = st.text_input("Search User by Name")
        if search_term:
            filtered_df = df[df["username"].str.contains(search_term, case=False, na=False)]
        else:
            filtered_df = pd.DataFrame()

        if search_term and not filtered_df.empty:
            selected_mod = st.selectbox(
                "Select Record",
                filtered_df.index,
                format_func=lambda i: f"{filtered_df.loc[i, 'username']} ({filtered_df.loc[i, 'predicted_at']})"
            )
            curr_sal = filtered_df.loc[selected_mod, 'predicted_salary']
            st.info(f"Current Salary: KES{int(curr_sal):,}")
            new_salary = st.number_input("New Salary", value=int(curr_sal), step=10000)

            c_mod1, c_mod2 = st.columns(2)
            record_id = int(df.loc[selected_mod, "id"])

            if c_mod1.button("Update"):
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("UPDATE predictions SET predicted_salary = %s WHERE id = %s", (new_salary, record_id))
                conn.commit()
                cur.close()
                conn.close()
                st.success("Updated successfully")
                st.rerun()

            if c_mod2.button("Delete"):
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("DELETE FROM predictions WHERE id = %s", (record_id,))
                conn.commit()
                cur.close()
                conn.close()
                st.warning("Deleted successfully")
                st.rerun()
        elif search_term and filtered_df.empty:
            st.warning("No user found with that name.")

        st.divider()

        # Salary Records
        st.subheader("📋 Salary Records")
        st.dataframe(df.drop(columns=["id"], errors="ignore"))

        # Analytics
        st.subheader("📊 Salary Analytics")
        if "country" in df.columns:
            with st.expander("View Country Distribution"):
                country_counts = df["country"].value_counts()
                fig, ax = plt.subplots()
                ax.pie(country_counts, labels=country_counts.index, autopct='%1.1f%%')
                st.pyplot(fig)

        st.subheader("📥 Export Data")
        csv = df.drop(columns=["id"], errors="ignore").to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "salary_predictions.csv", "text/csv")

# -------------------------------
# Logout
# -------------------------------
elif menu == "Logout":
    if st.session_state.logged_in:
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = "user"
        st.success("You have been logged out successfully.")
        st.rerun()
    else:
        st.info("You are not logged in.")