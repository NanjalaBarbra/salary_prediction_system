import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime

from predict_page import show_predict_page
from explore_page import show_explore_page
from auth_page import (
    login_user,
    register_user,
    login_admin,
    validate_password_strength,
    change_password,
    delete_user_account,
)
from database import get_connection


# ================= UI STYLING =================
# Load image4 and encode as base64 for CSS background
def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None

image4_base64 = get_image_base64("Images/image4.jpeg")
image4_data_uri = f"data:image/jpeg;base64,{image4_base64}" if image4_base64 else ""

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Poppins', sans-serif;
}}

.stApp {{
    background: linear-gradient(135deg, #f0f9ff 0%, #e0e7ff 50%, #fce7f3 100%);
    color: #1a202c;
}}

section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    color: #ffffff;
    border-right: 3px solid #fbbf24;
}}

section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] .stTextInput label {{
    color: #ffffff !important;
    font-weight: 600;
}}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {{
    color: #fbbf24 !important;
}}

h1, h2, h3 {{
    color: #1a202c;
    font-weight: 700;
}}

.hero-title {{
    font-size: 2.4rem;
    font-weight: 700;
    background: linear-gradient(120deg, #10b981, #3b82f6, #8b5cf6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}

.hero-subtitle {{
    color: #1f2937;
    font-size: 1rem;
    font-weight: 500;
}}

.metric-pill {{
    background: linear-gradient(120deg, #fbbf24, #f59e0b);
    border-radius: 999px;
    padding: 0.35rem 0.9rem;
    font-size: 0.8rem;
    color: #ffffff;
    font-weight: 600;
}}

.feature-card {{
    background: rgba(255, 255, 255, 0.95);
    border-radius: 20px;
    padding: 1.5rem 1.5rem;
    box-shadow: 0 20px 50px rgba(102, 126, 234, 0.3);
    border: 2px solid rgba(251, 191, 36, 0.3);
    transition: all 0.3s ease;
}}

.feature-card:hover {{
    transform: translateY(-5px);
    box-shadow: 0 25px 60px rgba(102, 126, 234, 0.4);
}}

.feature-title {{
    font-weight: 600;
    font-size: 1rem;
    background: linear-gradient(120deg, #8b5cf6, #3b82f6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}

.feature-text {{
    font-size: 0.9rem;
    color: #4b5563;
}}

.calc-card {{
    background: #ffffff url('{image4_data_uri}') center/cover no-repeat;
    border-radius: 20px;
    padding: 1.4rem 1.5rem;
    box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12);
    border: 1px solid rgba(148, 163, 184, 0.45);
    position: relative;
}}

.calc-card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.85);
    border-radius: 20px;
    z-index: 0;
}}

.calc-card > * {{
    position: relative;
    z-index: 1;
}}

.calc-label {{
    font-size: 0.8rem;
    font-weight: 500;
    color: #4b5563;
    margin-bottom: 0.2rem;
}}

.calc-input {{
    width: 100%;
    border-radius: 999px;
    border: 1px solid #d1d5db;
    padding: 0.45rem 0.9rem;
    font-size: 0.85rem;
    color: #111827;
    background: #f9fafb;
}}

.calc-input::placeholder {{
    color: #9ca3af;
}}

.stButton > button {{
    background: linear-gradient(120deg, #2563eb, #4f46e5);
    border-radius: 999px;
    color: white;
    font-weight: 600;
    border: none;
    padding: 0.55rem 1.4rem;
    box-shadow: 0 10px 25px rgba(37, 99, 235, 0.35);
}}

.stButton > button:hover {{
    background: linear-gradient(120deg, #1d4ed8, #4338ca);
    transform: translateY(-1px);
}}
</style>
""",
    unsafe_allow_html=True,
)


# ================= SESSION STATE =================
st.session_state.setdefault("logged_in", False)
st.session_state.setdefault("username", "")
st.session_state.setdefault("role", None)
st.session_state.setdefault("auth_page", "User Login")


# ================= HEADER =================


# ================= SIDEBAR AUTH =================
st.sidebar.title("🔐 Authentication")

if not st.session_state.logged_in:
    st.markdown("""
    <div style="text-align:center; margin-bottom:30px;">
        <h1>🚀 Salary Prediction App</h1>
        <h3 style="color:#cbd5e0; font-weight:300;">
            Unlock your true market value with precision.
        </h3>
    </div>
    """, unsafe_allow_html=True)
    auth_choice = st.sidebar.radio(
        "Select Option",
        ["User Login", "User Registration", "Admin Login"],
        index=["User Login", "User Registration", "Admin Login"]
        .index(st.session_state.auth_page)
    )
    st.session_state.auth_page = auth_choice
else:
    label = "🛡 Admin" if st.session_state.role == "admin" else "👋 User"
    st.sidebar.success(f"{label}: {st.session_state.username}")

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()


# ================= AUTH PAGES =================
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
                # After successful registration, send the user to the login page
                st.session_state.auth_page = "User Login"
                st.rerun()
            else:
                st.error(msg)

    elif st.session_state.auth_page == "Admin Login":
        st.subheader("🛡 Admin Login")
        username = st.text_input("Admin Username")
        password = st.text_input("Admin Password", type="password")

        if st.button("Login as Admin"):
            success, msg = login_admin(username, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = "admin"
                st.rerun()
            else:
                st.error(msg)


# ================= MAIN APP =================
if st.session_state.logged_in:

    menu_items = (
        ["Admin Dashboard"]
        if st.session_state.role == "admin"
        else ["Home", "Predict", "Explore", "My Profile", "Logout"]
    )

    # Allow Home buttons to force navigation
    if "_force_nav" in st.session_state and st.session_state._force_nav in menu_items:
        default_index = menu_items.index(st.session_state._force_nav)
        del st.session_state._force_nav
    else:
        default_index = 0

    menu = st.sidebar.selectbox("Navigation", menu_items, index=default_index)

    # ================= HOME =================
    if menu == "Home":
        left, right = st.columns([3, 2])

        with left:
            st.markdown(
                """
                <div style="margin-top: 1.0rem; margin-bottom: 1.6rem;">
                    <h1 class="hero-title" style="margin-bottom: 0.6rem;">
                        Know your true market salary as a developer.
                    </h1>
                    <p class="hero-subtitle" style="max-width: 540px;">
                        Benchmark your pay against thousands of real-world developer salaries.
                        Get a personalized estimate based on your role, experience,
                        education, and tech stack.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-bottom: 0.8rem;">
                    <span class="metric-pill">✔ Built on global survey data</span>
                    <span class="metric-pill">✔ ML model tuned for real-world use</span>
                    <span class="metric-pill">✔ Results in just a few clicks</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with right:
            st.markdown(
                """
                <div class="calc-card">
                    <p style="font-size:0.85rem; font-weight:600; color:#4b5563; margin-bottom:0.5rem;">
                        START YOUR ESTIMATE
                    </p>
                    <h3 style="font-size:1.15rem; font-weight:600; margin-bottom:0.9rem; color:#111827;">
                        What could you be earning?
                    </h3>
                    <div style="display:flex; flex-direction:column; gap:0.6rem; margin-bottom:0.9rem;">
                        <div>
                            <div class="calc-label">Job title</div>
                            <input class="calc-input" placeholder="e.g. Backend Developer" disabled />
                        </div>
                        <div>
                            <div class="calc-label">Location</div>
                            <input class="calc-input" placeholder="e.g. Germany, India, United States" disabled />
                        </div>
                        <div>
                            <div class="calc-label">Years of experience</div>
                            <input class="calc-input" placeholder="Drag the slider on the next step" disabled />
                        </div>
                    </div>
                    <p style="font-size:0.78rem; color:#6b7280; margin-bottom:0.8rem;">
                        We’ll ask a few quick questions about your background and stack,
                        then generate a tailored salary estimate.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("")
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Start my salary estimate"):
                st.session_state._force_nav = "Predict"
                st.rerun()
        with c2:
            if st.button("Browse salary trends"):
                st.session_state._force_nav = "Explore"
                st.rerun()

    # ================= USER PAGES =================
    elif menu == "Predict":
        show_predict_page()

    elif menu == "Explore":
        show_explore_page()

    elif menu == "My Profile":
        st.title("👤 My Profile & Dashboard")

        username = st.session_state.username

        # --- ACCOUNT SETTINGS ---
        with st.expander("⚙️ Account Settings", expanded=False):
            st.markdown("### 🔐 Security")

            with st.form("change_pass_form"):
                cur_pass = st.text_input("Current Password", type="password")
                new_pass = st.text_input(
                    "New Password",
                    type="password",
                    help="Min 8 chars, 1 number, 1 special character",
                )
                confirm_pass = st.text_input("Confirm New Password", type="password")

                if st.form_submit_button("Update Password"):
                    if new_pass != confirm_pass:
                        st.error("New passwords do not match.")
                    else:
                        success, resp = change_password(username, cur_pass, new_pass)
                        if success:
                            st.success(resp)
                        else:
                            st.error(resp)

            st.markdown("### 🚨 Danger Zone")
            c_d1, c_d2 = st.columns(2)

            with c_d1:
                if st.button("🚪 Logout All Sessions", use_container_width=True):
                    st.session_state.clear()
                    st.rerun()

            with c_d2:
                if "confirm_delete" not in st.session_state:
                    st.session_state.confirm_delete = False

                if not st.session_state.confirm_delete:
                    if st.button(
                        "🗑 Delete Account",
                        type="primary",
                        use_container_width=True,
                        key="delete_account_btn",
                    ):
                        st.session_state.confirm_delete = True
                        st.rerun()
                else:
                    st.warning("Are you sure? This cannot be undone.")
                    col_del1, col_del2 = st.columns(2)
                    if col_del1.button("Yes, Delete", type="primary"):
                        success, msg = delete_user_account(username)
                        if success:
                            st.success(msg)
                            st.session_state.clear()
                            st.rerun()
                        else:
                            st.error(msg)
                    if col_del2.button("Cancel"):
                        st.session_state.confirm_delete = False
                        st.rerun()

        st.divider()

        # --- USER METRICS / SUMMARY ---
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT country, education, employment, experience,
                   webframework, undergradmajor,
                   predicted_salary, predicted_at
            FROM predictions
            WHERE username = %s
            """,
            (username,),
        )
        rows = cur.fetchall()

        user_preds = [
            {
                "country": r[0],
                "education": r[1],
                "employment": r[2],
                "experience": r[3],
                "webframework": r[4],
                "undergradmajor": r[5],
                "predicted_salary": r[6],
                "predicted_at": r[7],
            }
            for r in rows
        ]

        if user_preds:
            df_hist = pd.DataFrame(user_preds)
            avg_sal = f"${int(df_hist['predicted_salary'].mean()):,}"
            max_sal = f"${int(df_hist['predicted_salary'].max()):,}"
            min_sal = f"${int(df_hist['predicted_salary'].min()):,}"
            total_preds = len(df_hist)
        else:
            df_hist = pd.DataFrame(
                columns=[
                    "country",
                    "education",
                    "employment",
                    "experience",
                    "webframework",
                    "undergradmajor",
                    "predicted_salary",
                    "predicted_at",
                ]
            )
            avg_sal = "No predictions yet"
            max_sal = "—"
            min_sal = "—"
            total_preds = 0

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Username", username)
        col2.metric("Total Predictions", total_preds)
        col3.metric("Avg Pred. Salary", avg_sal)
        col4.metric("Highest Salary", max_sal)
        col5.metric("Lowest Salary", min_sal)

        st.divider()

        # --- Salary Growth Trend ---
        st.subheader("📈 Salary Growth Trend")

        chart_buf = None
        latest_pred = None

        if not df_hist.empty:
            # Ensure we have a datetime column for ordering and plotting
            df_hist["date_obj"] = pd.to_datetime(df_hist["predicted_at"], errors="coerce")
            df_hist = df_hist.dropna(subset=["date_obj"]).sort_values("date_obj")

            if not df_hist.empty:
                st.line_chart(
                    df_hist.set_index("date_obj")["predicted_salary"],
                    height=240,
                )

                # Prepare figure for report export
                fig_rep, ax_rep = plt.subplots(figsize=(8, 4))
                ax_rep.plot(
                    df_hist["date_obj"],
                    df_hist["predicted_salary"],
                    marker="o",
                    linestyle="-",
                    color="#4c51bf",
                )
                ax_rep.set_title("Salary Growth Trend")
                ax_rep.set_xlabel("Date")
                ax_rep.set_ylabel("Predicted Salary (USD)")
                plt.xticks(rotation=45)
                plt.tight_layout()

                chart_buf = io.BytesIO()
                fig_rep.savefig(chart_buf, format="png")
                chart_buf.seek(0)
                chart_b64 = base64.b64encode(chart_buf.read()).decode()

                latest_pred = df_hist.iloc[-1]
            else:
                st.info("No valid dated predictions to plot yet.")
        else:
            st.info("Make some predictions to see your salary growth trend.")

        # --- Download Simple HTML Report ---
        if not df_hist.empty and chart_buf and latest_pred is not None:
            st.write("### 📄 Export My Salary Report")

            rep_name = username
            rep_date = datetime.now().strftime("%d %B %Y")
            rep_sal = f"${int(latest_pred['predicted_salary']):,}"

            # Simple +/- range around latest prediction
            mae_estimate = 10000
            rep_min = f"${int(max(0, latest_pred['predicted_salary'] - mae_estimate)):,}"
            rep_max = f"${int(latest_pred['predicted_salary'] + mae_estimate):,}"

            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 40px; color: #333; }}
                    .header {{ text-align: center; margin-bottom: 40px; }}
                    .title {{ font-size: 28px; color: #4c51bf; font-weight: bold; }}
                    .subtitle {{ font-size: 16px; color: #666; }}
                    .card {{ background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #ddd; }}
                    .metric-row {{ display: flex; justify-content: space-between; margin-bottom: 10px; }}
                    .metric-label {{ font-weight: bold; color: #555; }}
                    .metric-val {{ font-size: 18px; color: #2d3748; }}
                    .highlight {{ color: #2b6cb0; font-size: 24px; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <div class="title">Salary Prediction Report</div>
                    <div class="subtitle">Generated for {rep_name} on {rep_date}</div>
                </div>

                <div class="card">
                    <h3>👤 User Summary</h3>
                    <div class="metric-row"><span class="metric-label">Total Predictions:</span> <span class="metric-val">{total_preds}</span></div>
                    <div class="metric-row"><span class="metric-label">Average Predicted Salary:</span> <span class="metric-val">{avg_sal}</span></div>
                    <div class="metric-row"><span class="metric-label">Highest Salary:</span> <span class="metric-val">{max_sal}</span></div>
                    <div class="metric-row"><span class="metric-label">Lowest Salary:</span> <span class="metric-val">{min_sal}</span></div>
                </div>

                <div class="card">
                    <h3>🚀 Latest Prediction</h3>
                    <div class="metric-row"><span class="metric-label">Predicted Salary:</span> <span class="highlight">{rep_sal}</span></div>
                    <div class="metric-row"><span class="metric-label">Estimated Range:</span> <span class="metric-val">{rep_min} - {rep_max}</span></div>
                </div>

                <h3>📈 Growth Trajectory</h3>
                <div style="text-align: center;">
                    <img src="data:image/png;base64,{chart_b64}" width="100%" />
                </div>

                <p style="text-align: center; margin-top: 50px; font-size: 12px; color: #aaa;">
                    Generated by the Salary Prediction System
                </p>
            </body>
            </html>
            """

            st.download_button(
                label="📥 Download My Salary Report (HTML)",
                data=html_content,
                file_name=f"Salary_Report_{username}.html",
                mime="text/html",
            )

        # Close DB handles for this section
        cur.close()
        conn.close()

    # ================= ADMIN DASHBOARD =================
    elif menu == "Admin Dashboard":
     if st.session_state.logged_in and st.session_state.role == "admin":
        st.title("🛡 Admin Dashboard")

        # Use a local admin password for destructive actions (should match auth logic)
        ADMIN_PASSWORD = "admin@123"

        # ------------- Fetch predictions (with id) -------------
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, username, country, experience, education, undergradmajor,
                   employment, webframework, predicted_salary, predicted_at
            FROM predictions
            """
        )
        rows = cur.fetchall()

        data = [
            {
                "id": row[0],
                "username": row[1],
                "country": row[2],
                "experience": row[3],
                "education": row[4],
                "undergradmajor": row[5],
                "employment": row[6],
                "webframework": row[7],
                "predicted_salary": row[8],
                "predicted_at": row[9].strftime("%d-%m-%Y %I:%M %p")
                if row[9]
                else "",
            }
            for row in rows
        ]

        if data:
            df = pd.DataFrame(data)
            if "id" in df.columns:
                df["id"] = df["id"].astype(str)
        else:
            df = pd.DataFrame(
                columns=[
                    "id",
                    "username",
                    "country",
                    "experience",
                    "education",
                    "undergradmajor",
                    "employment",
                    "webframework",
                    "predicted_salary",
                    "predicted_at",
                ]
            )

        # ------------- KPI CARDS -------------
        c1, c2, c3, c4 = st.columns(4)

        # Total users from users table
        cur.execute("SELECT COUNT(*) FROM users")
        total_users_count = cur.fetchone()[0]

        c1.metric("Total Users", total_users_count)
        c2.metric("Total Predictions", len(df))

        if not df.empty and "predicted_salary" in df.columns:
            c3.metric("Highest Salary (USD)", f"${int(df['predicted_salary'].max()):,}")
            c4.metric("Lowest Salary (USD)", f"${int(df['predicted_salary'].min()):,}")
        else:
            c3.metric("Highest Salary (USD)", "$0")
            c4.metric("Lowest Salary (USD)", "$0")

        st.divider()

        # ------------- UPDATE / DELETE SINGLE RECORD -------------
        st.subheader("✏ Modify Record")

        search_term = st.text_input("Search user by username")

        if search_term:
            filtered_df = df[
                df["username"].str.contains(search_term, case=False, na=False)
            ]
        else:
            filtered_df = pd.DataFrame()

        if search_term and not filtered_df.empty:
            selected_mod = st.selectbox(
                "Select Record",
                filtered_df.index,
                format_func=lambda i: f"{filtered_df.loc[i, 'username']} ({filtered_df.loc[i, 'predicted_at']})",
            )

            curr_sal = float(filtered_df.loc[selected_mod, "predicted_salary"])
            st.info(f"Current Salary: ${int(curr_sal):,}")

            new_salary = st.number_input(
                "New Salary (USD)",
                value=int(curr_sal),
                step=1000,
            )

            c_mod1, c_mod2 = st.columns(2)
            record_id = int(filtered_df.loc[selected_mod, "id"])

            if c_mod1.button("Update", key="admin_update_record"):
                cur.execute(
                    "UPDATE predictions SET predicted_salary = %s WHERE id = %s",
                    (new_salary, record_id),
                )
                conn.commit()
                st.success("Record updated successfully.")
                st.rerun()

            if c_mod2.button("Delete", key="admin_delete_record"):
                cur.execute("DELETE FROM predictions WHERE id = %s", (record_id,))
                conn.commit()
                st.warning("Record deleted successfully.")
                st.rerun()

        elif search_term and filtered_df.empty:
            st.warning("No user found with that name.")

        st.divider()

        # ------------- DELETE ALL DATA (Danger Zone) -------------
        with st.expander("🚨 Danger Zone: Delete All Data"):
            st.warning(
                "This action will permanently delete all users and predictions. Proceed with caution."
            )
            del_pass = st.text_input(
                "Enter Admin Password to Confirm", type="password"
            )

            if st.button("🗑 Delete ALL Records and Users"):
                if del_pass == ADMIN_PASSWORD:
                    # Delete predictions first due to FK constraints (if any)
                    cur.execute("DELETE FROM predictions")
                    cur.execute("DELETE FROM users")
                    conn.commit()
                    st.success("All user accounts and predictions have been deleted.")
                    st.rerun()
                else:
                    st.error("Incorrect Admin Password.")

        st.divider()

        # ------------- USER MANAGEMENT -------------
        st.subheader("👥 User Management")

        # For this project, users table only has username/password.
        # We still show each user and how many predictions they have.
        cur.execute(
            """
            SELECT u.username, COUNT(p.id) AS prediction_count
            FROM users u
            LEFT JOIN predictions p ON p.username = u.username
            GROUP BY u.username
            """
        )
        user_rows = cur.fetchall()

        all_users = [
            {"username": row[0], "prediction_count": row[1]} for row in user_rows
        ]

        if all_users:
            df_users = pd.DataFrame(all_users)
            st.dataframe(df_users, use_container_width=True)

            st.markdown("#### 🛠 Manage User")
            selected_username = st.selectbox(
                "Select User to Manage", df_users["username"]
            )

            if selected_username:
                with st.expander(f"Manage {selected_username}"):
                    st.write(
                        "You can remove this user and all of their stored predictions."
                    )

                    col_u1, _ = st.columns([1, 4])
                    if col_u1.button(
                        "❌ Delete User and Predictions",
                        type="primary",
                        key="delete_user_button",
                    ):
                        cur.execute(
                            "DELETE FROM predictions WHERE username = %s",
                            (selected_username,),
                        )
                        cur.execute(
                            "DELETE FROM users WHERE username = %s",
                            (selected_username,),
                        )
                        conn.commit()
                        st.warning(
                            f"User {selected_username} and all related predictions have been deleted."
                        )
                        st.rerun()
        else:
            st.info("No registered users found.")

        st.divider()

        # ------------- TABLE OF PREDICTIONS -------------
        st.subheader("📋 Salary Records")
        if not df.empty:
            st.dataframe(df.drop(columns=["id"], errors="ignore"), use_container_width=True)
        else:
            st.info("No prediction records available.")

        st.divider()

        # ------------- ANALYTICS -------------
        st.subheader("📊 Salary Analytics")

        if not df.empty:
            # Country distribution (Pie)
            if "country" in df.columns:
                with st.expander("🌍 Country Distribution (Pie Chart)"):
                    country_counts = df["country"].value_counts()
                    fig_country, ax_country = plt.subplots()
                    ax_country.pie(
                        country_counts,
                        labels=country_counts.index,
                        autopct="%1.1f%%",
                        startangle=90,
                    )
                    ax_country.axis("equal")
                    st.pyplot(fig_country)

            # Experience vs Average Salary (Line)
            if "experience" in df.columns:
                with st.expander("📈 Experience vs Average Salary (Line Chart)"):
                    exp_salary = (
                        df.groupby("experience")["predicted_salary"]
                        .mean()
                        .reset_index()
                        .sort_values("experience")
                    )
                    fig_exp, ax_exp = plt.subplots()
                    ax_exp.plot(
                        exp_salary["experience"],
                        exp_salary["predicted_salary"],
                        marker="o",
                    )
                    ax_exp.set_xlabel("Experience (Years)")
                    ax_exp.set_ylabel("Average Predicted Salary (USD)")
                    ax_exp.set_title("Salary Trend by Experience")
                    st.pyplot(fig_exp)

            # Employment type vs Average Salary (Bar)
            if "employment" in df.columns:
                with st.expander(
                    "💼 Employment Type vs Average Salary (Bar Chart)"
                ):
                    emp_salary = (
                        df.groupby("employment")["predicted_salary"]
                        .mean()
                        .reset_index()
                    )
                    fig_emp, ax_emp = plt.subplots()
                    ax_emp.bar(
                        emp_salary["employment"],
                        emp_salary["predicted_salary"],
                    )
                    ax_emp.set_xlabel("Employment Type")
                    ax_emp.set_ylabel("Average Predicted Salary (USD)")
                    ax_emp.set_title("Average Salary by Employment Type")
                    st.pyplot(fig_emp)

        st.divider()

        # ------------- CSV DOWNLOAD -------------
        st.subheader("📥 Export Data")
        csv = df.drop(columns=["id"], errors="ignore").to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download CSV",
            csv,
            "salary_predictions.csv",
            "text/csv",
        )

        # Close connection used for admin dashboard
        cur.close()
        conn.close()