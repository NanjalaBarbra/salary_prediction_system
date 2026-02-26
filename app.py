import os
import io
import base64
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
st.set_page_config(
    page_title="Salary Prediction App",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

import pandas as pd
import matplotlib.pyplot as plt

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
    change_password,
    delete_user_account,
)
from database import get_connection
from email_report import generate_pdf, send_salary_report
from password_reset import (
    create_reset_tables, create_reset_token, verify_reset_token,
    mark_token_used, get_user_email, save_user_email, send_reset_email,
)


# ================= CONSTANTS =================
# Approximate model MAE from validation set (re-evaluate if model is retrained)
MODEL_MAE_USD = 10_000

# Admin password loaded from environment variable — never hardcode secrets in source
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
if not ADMIN_PASSWORD:
    # Warn in the UI if the env var isn't set (dev convenience, remove before prod)
    pass  # handled gracefully in the danger-zone check below


# ================= UI STYLING =================
def _get_image_base64(image_path: str) -> str | None:
    """Return base64-encoded image or None if file not found."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None


def apply_styles() -> None:
    """Inject all custom CSS into the Streamlit page."""
    image4_base64 = _get_image_base64("Images/image4.jpeg")
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

/* ---- Text inputs, textareas, selectboxes ---- */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input,
.stSelectbox > div > div > div {{
    background-color: #ffffff !important;
    color: #1a202c !important;
    border: 1px solid #d1d5db !important;
    border-radius: 8px !important;
}}

.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {{
    color: #9ca3af !important;
}}

/* Keep sidebar inputs readable on the purple background */
section[data-testid="stSidebar"] .stTextInput > div > div > input {{
    background-color: rgba(255,255,255,0.15) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.3) !important;
}}
</style>
""",
        unsafe_allow_html=True,
    )


# ================= SESSION STATE =================
def init_session_state() -> None:
    """Initialise all session state keys with safe defaults."""
    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("username", "")
    st.session_state.setdefault("role", None)
    st.session_state.setdefault("auth_page", "User Login")


# ================= PAGE: MY PROFILE =================
def show_profile_section() -> None:
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
        col_logout, col_delete = st.columns(2)

        with col_logout:
            if st.button("🚪 Logout All Sessions", use_container_width=True):
                st.session_state.clear()
                st.rerun()

        with col_delete:
            st.session_state.setdefault("confirm_delete", False)

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
                col_confirm, col_cancel = st.columns(2)
                if col_confirm.button("Yes, Delete", type="primary"):
                    success, msg = delete_user_account(username)
                    if success:
                        st.success(msg)
                        st.session_state.clear()
                        st.rerun()
                    else:
                        st.error(msg)
                if col_cancel.button("Cancel"):
                    st.session_state.confirm_delete = False
                    st.rerun()

    st.divider()

    # --- USER METRICS ---
    # Use context manager to ensure the connection is always closed
    with get_connection() as conn:
        with conn.cursor() as cur:
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
                "country", "education", "employment", "experience",
                "webframework", "undergradmajor", "predicted_salary", "predicted_at",
            ]
        )
        avg_sal = "No predictions yet"
        max_sal = "—"
        min_sal = "—"
        total_preds = 0

    col_user, col_total, col_avg, col_high, col_low = st.columns(5)
    col_user.metric("Username", username)
    col_total.metric("Total Predictions", total_preds)
    col_avg.metric("Avg Pred. Salary", avg_sal)
    col_high.metric("Highest Salary", max_sal)
    col_low.metric("Lowest Salary", min_sal)

    st.divider()

    # --- SALARY GROWTH TREND ---
    st.subheader("📈 Salary Growth Trend")

    chart_buf = None
    latest_pred = None

    if not df_hist.empty:
        df_hist["date_obj"] = pd.to_datetime(df_hist["predicted_at"], errors="coerce")
        df_hist = df_hist.dropna(subset=["date_obj"]).sort_values("date_obj")

        if not df_hist.empty:
            st.line_chart(
                df_hist.set_index("date_obj")["predicted_salary"],
                height=240,
            )

            # Build chart for report export
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
            plt.close(fig_rep)  # prevent memory accumulation on reruns

            latest_pred = df_hist.iloc[-1]
        else:
            st.info("No valid dated predictions to plot yet.")
    else:
        st.info("Make some predictions to see your salary growth trend.")

    # --- DOWNLOAD REPORT ---
    if not df_hist.empty and chart_buf and latest_pred is not None:
        st.write("### 📄 Export My Salary Report")

        rep_date = datetime.now().strftime("%d %B %Y")
        rep_sal = f"${int(latest_pred['predicted_salary']):,}"
        rep_min = f"${int(max(0, latest_pred['predicted_salary'] - MODEL_MAE_USD)):,}"
        rep_max = f"${int(latest_pred['predicted_salary'] + MODEL_MAE_USD):,}"

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
                <div class="subtitle">Generated for {username} on {rep_date}</div>
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

        col_dl, col_email = st.columns(2)

        with col_dl:
            st.download_button(
                label="📥 Download Report (HTML)",
                data=html_content,
                file_name=f"Salary_Report_{username}.html",
                mime="text/html",
                use_container_width=True,
            )

        with col_email:
            with st.expander("📧 Email Report as PDF", expanded=False):
                recipient = st.text_input(
                    "Enter your email address",
                    key="profile_report_email",
                    placeholder="you@example.com",
                )
                if st.button("Send PDF Report", key="profile_send_email", use_container_width=True, type="primary"):
                    if not recipient or "@" not in recipient:
                        st.error("Please enter a valid email address.")
                    else:
                        with st.spinner("Generating PDF and sending email..."):
                            pdf_buf = generate_pdf(
                                username=username,
                                df_hist=df_hist,
                                latest_salary=float(latest_pred["predicted_salary"]),
                                avg_sal=avg_sal,
                                max_sal=max_sal,
                                min_sal=min_sal,
                                total_preds=total_preds,
                                mae=MODEL_MAE_USD,
                            )
                            ok, msg = send_salary_report(recipient, username, pdf_buf)
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)


# ================= PAGE: ADMIN DASHBOARD =================
def show_admin_section() -> None:
    st.title("🛡 Admin Dashboard")

    # Use context manager to ensure connection is always closed
    with get_connection() as conn:
        with conn.cursor() as cur:

            # ------------- Fetch predictions -------------
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
                    "predicted_at": row[9].strftime("%d-%m-%Y %I:%M %p") if row[9] else "",
                }
                for row in rows
            ]

            if data:
                df = pd.DataFrame(data)
                df["id"] = df["id"].astype(str)
            else:
                df = pd.DataFrame(
                    columns=[
                        "id", "username", "country", "experience", "education",
                        "undergradmajor", "employment", "webframework",
                        "predicted_salary", "predicted_at",
                    ]
                )

            # ------------- KPI CARDS -------------
            cur.execute("SELECT COUNT(*) FROM users")
            total_users_count = cur.fetchone()[0]

            col_users, col_preds, col_high, col_low = st.columns(4)
            col_users.metric("Total Users", total_users_count)
            col_preds.metric("Total Predictions", len(df))

            if not df.empty and "predicted_salary" in df.columns:
                col_high.metric("Highest Salary (USD)", f"${int(df['predicted_salary'].max()):,}")
                col_low.metric("Lowest Salary (USD)", f"${int(df['predicted_salary'].min()):,}")
            else:
                col_high.metric("Highest Salary (USD)", "$0")
                col_low.metric("Lowest Salary (USD)", "$0")

            st.divider()

            # ------------- UPDATE / DELETE SINGLE RECORD -------------
            st.subheader("✏ Modify Record")
            search_term = st.text_input("Search user by username")

            filtered_df = (
                df[df["username"].str.contains(search_term, case=False, na=False)]
                if search_term
                else pd.DataFrame()
            )

            if search_term and not filtered_df.empty:
                selected_mod = st.selectbox(
                    "Select Record",
                    filtered_df.index,
                    format_func=lambda i: (
                        f"{filtered_df.loc[i, 'username']} ({filtered_df.loc[i, 'predicted_at']})"
                    ),
                )

                curr_sal = float(filtered_df.loc[selected_mod, "predicted_salary"])
                st.info(f"Current Salary: ${int(curr_sal):,}")

                new_salary = st.number_input("New Salary (USD)", value=int(curr_sal), step=1000)

                col_update, col_delete_rec = st.columns(2)
                record_id = int(filtered_df.loc[selected_mod, "id"])

                if col_update.button("Update", key="admin_update_record"):
                    cur.execute(
                        "UPDATE predictions SET predicted_salary = %s WHERE id = %s",
                        (new_salary, record_id),
                    )
                    conn.commit()
                    st.success("Record updated successfully.")
                    st.rerun()

                if col_delete_rec.button("Delete", key="admin_delete_record"):
                    cur.execute("DELETE FROM predictions WHERE id = %s", (record_id,))
                    conn.commit()
                    st.warning("Record deleted successfully.")
                    st.rerun()

            elif search_term and filtered_df.empty:
                st.warning("No user found with that name.")

            st.divider()

            # ------------- DANGER ZONE -------------
            with st.expander("🚨 Danger Zone: Delete All Data"):
                st.warning(
                    "This action will permanently delete all users and predictions. Proceed with caution."
                )
                del_pass = st.text_input("Enter Admin Password to Confirm", type="password")

                if st.button("🗑 Delete ALL Records and Users"):
                    if not ADMIN_PASSWORD:
                        st.error("ADMIN_PASSWORD environment variable is not set. Cannot verify.")
                    elif del_pass == ADMIN_PASSWORD:
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

            cur.execute(
                """
                SELECT u.username, COUNT(p.id) AS prediction_count
                FROM users u
                LEFT JOIN predictions p ON p.username = u.username
                GROUP BY u.username
                """
            )
            user_rows = cur.fetchall()
            all_users = [{"username": r[0], "prediction_count": r[1]} for r in user_rows]

            if all_users:
                df_users = pd.DataFrame(all_users)
                st.dataframe(df_users, use_container_width=True)

                st.markdown("#### 🛠 Manage User")
                selected_username = st.selectbox("Select User to Manage", df_users["username"])

                if selected_username:
                    with st.expander(f"Manage {selected_username}"):
                        st.write("You can remove this user and all of their stored predictions.")
                        col_del_user, _ = st.columns([1, 4])
                        if col_del_user.button(
                            "❌ Delete User and Predictions",
                            type="primary",
                            key="delete_user_button",
                        ):
                            cur.execute(
                                "DELETE FROM predictions WHERE username = %s", (selected_username,)
                            )
                            cur.execute(
                                "DELETE FROM users WHERE username = %s", (selected_username,)
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
                        plt.close(fig_country)  # prevent memory accumulation

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
                        plt.close(fig_exp)  # prevent memory accumulation

                if "employment" in df.columns:
                    with st.expander("💼 Employment Type vs Average Salary (Bar Chart)"):
                        emp_salary = (
                            df.groupby("employment")["predicted_salary"].mean().reset_index()
                        )
                        fig_emp, ax_emp = plt.subplots()
                        ax_emp.bar(emp_salary["employment"], emp_salary["predicted_salary"])
                        ax_emp.set_xlabel("Employment Type")
                        ax_emp.set_ylabel("Average Predicted Salary (USD)")
                        ax_emp.set_title("Average Salary by Employment Type")
                        st.pyplot(fig_emp)
                        plt.close(fig_emp)  # prevent memory accumulation

            st.divider()

            # ------------- CSV DOWNLOAD -------------
            st.subheader("📥 Export Data")
            csv = df.drop(columns=["id"], errors="ignore").to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "salary_predictions.csv", "text/csv")


# ================= MAIN =================
apply_styles()
init_session_state()
create_reset_tables()

# ================= SIDEBAR AUTH =================
st.sidebar.title("🔐 Authentication")

if not st.session_state.logged_in:
    _auth_options = ["User Login", "User Registration", "Forgot Password", "Admin Login"]
    _current = st.session_state.get("auth_page", "User Login")
    if _current not in _auth_options:
        _current = "User Login"
    auth_choice = st.sidebar.radio(
        "Select Option",
        _auth_options,
        index=_auth_options.index(_current),
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

    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Playfair+Display:wght@700;800&display=swap');

        .main .block-container {
            padding-top: 2rem !important;
            padding-bottom: 0 !important;
            max-width: 100% !important;
        }

        /* ── Form card ── */
        .auth-form-card {
            background: rgba(255,255,255,0.97);
            border-radius: 24px;
            padding: 2.8rem 3rem;
            box-shadow: 0 24px 64px rgba(15,12,41,0.15);
            border: 1px solid rgba(102,126,234,0.12);
        }
        .auth-form-logo {
            font-family: 'DM Sans', sans-serif;
            font-size: 1rem;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 0.3rem;
        }
        .auth-form-title {
            font-family: 'Playfair Display', serif;
            font-size: 1.7rem;
            font-weight: 700;
            color: #1a202c;
            margin-bottom: 0.3rem;
            white-space: nowrap;
        }
        .auth-form-subtitle {
            font-size: 0.82rem;
            color: #9ca3af;
            margin-bottom: 1.5rem;
        }
        .auth-form-divider {
            border: none;
            border-top: 1px solid #f0f0f0;
            margin: 1rem 0 1.5rem;
        }

        /* ── Animated hero panel ── */
        .auth-hero-panel {
            border-radius: 24px;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            background-size: 400% 400%;
            animation: gradientShift 8s ease infinite;
            min-height: 520px;
            position: relative;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2.5rem;
        }
        @keyframes gradientShift {
            0%   { background-position: 0% 50%; }
            50%  { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        /* floating orbs */
        .auth-hero-panel::before {
            content: '';
            position: absolute;
            width: 350px; height: 350px;
            background: radial-gradient(circle, rgba(102,126,234,0.4) 0%, transparent 70%);
            top: -80px; right: -60px;
            border-radius: 50%;
            animation: float1 6s ease-in-out infinite;
        }
        .auth-hero-panel::after {
            content: '';
            position: absolute;
            width: 250px; height: 250px;
            background: radial-gradient(circle, rgba(236,72,153,0.3) 0%, transparent 70%);
            bottom: -50px; left: 5%;
            border-radius: 50%;
            animation: float2 8s ease-in-out infinite;
        }
        @keyframes float1 {
            0%, 100% { transform: translateY(0) scale(1); }
            50%       { transform: translateY(-20px) scale(1.05); }
        }
        @keyframes float2 {
            0%, 100% { transform: translateY(0) scale(1); }
            50%       { transform: translateY(15px) scale(0.95); }
        }
        .auth-hero-inner {
            position: relative;
            z-index: 2;
            text-align: center;
        }
        .auth-badge {
            display: inline-block;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 999px;
            padding: 0.35rem 1.1rem;
            font-size: 0.7rem;
            color: rgba(255,255,255,0.8);
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin-bottom: 1.2rem;
            backdrop-filter: blur(8px);
        }
        .auth-hero-title {
            font-family: 'Playfair Display', serif;
            font-size: 2.6rem;
            font-weight: 800;
            color: #ffffff;
            line-height: 1.2;
            margin: 0 0 1rem 0;
            text-shadow: 0 4px 24px rgba(0,0,0,0.3);
        }
        .auth-hero-title span {
            background: linear-gradient(120deg, #fbbf24, #f472b6, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .auth-hero-sub {
            color: rgba(255,255,255,0.7);
            font-size: 0.9rem;
            line-height: 1.7;
            margin-bottom: 2rem;
        }
        .auth-stats {
            display: flex;
            justify-content: center;
            gap: 0.8rem;
            flex-wrap: wrap;
        }
        .auth-stat-pill {
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 14px;
            padding: 0.75rem 1.1rem;
            backdrop-filter: blur(12px);
            text-align: center;
            min-width: 80px;
        }
        .auth-stat-num {
            font-size: 1.3rem;
            font-weight: 700;
            margin-bottom: 0.1rem;
        }
        .auth-stat-label {
            font-size: 0.6rem;
            color: rgba(255,255,255,0.6);
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        </style>
    """, unsafe_allow_html=True)

    form_col, banner_col = st.columns([1, 1], gap="large")

    # ── LEFT: Form card ──
    with form_col:
        st.markdown('<div class="auth-form-card">', unsafe_allow_html=True)
        st.markdown('<div class="auth-form-logo">🚀 Salary Prediction App</div>', unsafe_allow_html=True)

        if st.session_state.auth_page == "User Login":
            st.markdown('<div class="auth-form-title">Welcome back</div>', unsafe_allow_html=True)
            st.markdown('<div class="auth-form-subtitle">Sign in to your account to continue</div>', unsafe_allow_html=True)
            st.markdown('<hr class="auth-form-divider">', unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Sign In →", use_container_width=True, type="primary"):
                success, msg = login_user(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = "user"
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
            email = st.text_input("Email Address", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="Min 8 chars, 1 number, 1 special char")
            confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Create Account →", use_container_width=True, type="primary"):
                if not email or "@" not in email:
                    st.error("Please enter a valid email address.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                else:
                    success, msg = register_user(username, password)
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
                rst_email = st.text_input("Registered Email", key="rst_email", placeholder="you@example.com")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Send Reset Code →", use_container_width=True, type="primary"):
                    if not rst_username or not rst_email or "@" not in rst_email:
                        st.error("Please enter your username and email.")
                    else:
                        stored_email = get_user_email(rst_username)
                        if stored_email is None:
                            st.error("Username not found.")
                        elif stored_email.lower() != rst_email.lower():
                            st.error("Email does not match our records for that username.")
                        else:
                            token = create_reset_token(rst_username)
                            if token:
                                ok, msg = send_reset_email(rst_email, rst_username, token)
                                if ok:
                                    st.session_state.reset_username = rst_username
                                    st.session_state.reset_step = 2
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                            else:
                                st.error("Could not generate reset token.")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("← Back to Login", use_container_width=True):
                    st.session_state.reset_step = 1
                    st.session_state.auth_page = "User Login"
                    st.rerun()

            elif reset_step == 2:
                st.markdown('<div class="auth-form-title">Enter reset code</div>', unsafe_allow_html=True)
                st.markdown('<div class="auth-form-subtitle">Check your email for the 8-character code</div>', unsafe_allow_html=True)
                st.markdown('<hr class="auth-form-divider">', unsafe_allow_html=True)
                st.markdown("""<div style="background:#f0f4ff;border:2px dashed #667eea;border-radius:12px;
                    padding:12px;text-align:center;font-size:0.82rem;color:#4c51bf;
                    margin-bottom:1rem;font-weight:600;">Code expires in 1 hour</div>""", unsafe_allow_html=True)
                rst_code = st.text_input("Reset Code", key="rst_code", placeholder="e.g. A1B2C3D4").strip().upper()
                new_pass = st.text_input("New Password", type="password", key="rst_new_pass", placeholder="Min 8 chars, 1 number, 1 special char")
                confirm_pass = st.text_input("Confirm New Password", type="password", key="rst_confirm_pass", placeholder="Re-enter new password")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Reset Password →", use_container_width=True, type="primary"):
                    if not rst_code or not new_pass or not confirm_pass:
                        st.error("Please fill in all fields.")
                    elif new_pass != confirm_pass:
                        st.error("Passwords do not match.")
                    else:
                        try:
                            with get_connection() as conn:
                                with conn.cursor() as cur:
                                    cur.execute(
                                        "SELECT token FROM password_reset_tokens WHERE username = %s AND used = FALSE AND expires_at > NOW() ORDER BY created_at DESC LIMIT 1",
                                        (st.session_state.get("reset_username", ""),)
                                    )
                                    row = cur.fetchone()
                            if not row:
                                st.error("Code expired or already used. Request a new one.")
                                st.session_state.reset_step = 1
                            elif row[0][:8].upper() != rst_code:
                                st.error("Incorrect reset code. Please check your email.")
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
                                                cur.execute("UPDATE users SET password = %s WHERE username = %s", (hashed, result))
                                                conn.commit()
                                        mark_token_used(full_token)
                                        st.success("Password reset! You can now log in.")
                                        st.session_state.reset_step = 1
                                        st.session_state.auth_page = "User Login"
                                        st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("← Request New Code", use_container_width=True):
                    st.session_state.reset_step = 1
                    st.rerun()

        elif st.session_state.auth_page == "Admin Login":
            st.markdown('<div class="auth-form-title">Admin access</div>', unsafe_allow_html=True)
            st.markdown('<div class="auth-form-subtitle">Restricted to administrators only</div>', unsafe_allow_html=True)
            st.markdown('<hr class="auth-form-divider">', unsafe_allow_html=True)
            username = st.text_input("Admin Username", placeholder="Enter admin username")
            password = st.text_input("Admin Password", type="password", placeholder="Enter admin password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Sign In as Admin →", use_container_width=True, type="primary"):
                success, msg = login_admin(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = "admin"
                    st.rerun()
                else:
                    st.error(msg)

        st.markdown('</div>', unsafe_allow_html=True)

    # ── RIGHT: Animated hero banner ──
    with banner_col:
        st.markdown("""
            <div class="auth-hero-panel">
                <div class="auth-hero-inner">
                    <div class="auth-badge">✦ Developer Salary Intelligence</div>
                    <h2 class="auth-hero-title">
                        Know Your<br><span>True Worth</span>
                    </h2>
                    <p class="auth-hero-sub">
                        Precision salary predictions powered<br>
                        by real-world developer data.<br>
                        Make smarter career moves today.
                    </p>
                    <div class="auth-stats">
                        <div class="auth-stat-pill">
                            <div class="auth-stat-num" style="color:#fbbf24;">10K+</div>
                            <div class="auth-stat-label">Responses</div>
                        </div>
                        <div class="auth-stat-pill">
                            <div class="auth-stat-num" style="color:#34d399;">50+</div>
                            <div class="auth-stat-label">Countries</div>
                        </div>
                        <div class="auth-stat-pill">
                            <div class="auth-stat-num" style="color:#a78bfa;">95%</div>
                            <div class="auth-stat-label">Accuracy</div>
                        </div>
                        <div class="auth-stat-pill">
                            <div class="auth-stat-num" style="color:#f472b6;">Free</div>
                            <div class="auth-stat-label">Always</div>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)


# ================= MAIN APP =================
if st.session_state.logged_in:

    menu_items = (
        ["Admin Dashboard"]
        if st.session_state.role == "admin"
        else ["Home", "Predict", "Explore", "Skill Gap", "My Profile", "Logout"]
    )

    # Handle forced navigation from buttons (e.g. "Start my salary estimate")
    if "_force_nav" in st.session_state and st.session_state._force_nav in menu_items:
        st.session_state.nav_selectbox = st.session_state._force_nav
        del st.session_state._force_nav

    # Initialise selectbox state if not set
    if "nav_selectbox" not in st.session_state or st.session_state.nav_selectbox not in menu_items:
        st.session_state.nav_selectbox = menu_items[0]

    # Bind selectbox directly to session state key — Streamlit keeps them in sync
    st.sidebar.selectbox("Navigation", menu_items, key="nav_selectbox")
    menu = st.session_state.nav_selectbox

    if menu == "Home":
        show_home_page()

    elif menu == "Predict":
        show_predict_page()

    elif menu == "Explore":
        show_explore_page()

    elif menu == "Skill Gap":
        show_skill_gap_page()

    elif menu == "My Profile":
        show_profile_section()

    elif menu == "Admin Dashboard":
        show_admin_section()

    elif menu == "Logout":
        st.session_state.clear()
        st.rerun()
