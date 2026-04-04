import os
import io
import hmac
import base64
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
st.set_page_config(
    page_title="Salary Prediction App",
    page_icon="",
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
from security import rate_limit, reset_rate_limit, validate_login_input, validate_username, validate_email, validate_password
from reviews import create_reviews_table
from password_reset import (
    create_reset_tables, create_reset_token, verify_reset_token,
    mark_token_used, get_user_email, save_user_email, send_reset_email,
)


#CONSTANTS 
MODEL_MAE_USD  = 10_000
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

#UI STYLING 
def _get_image_base64(image_path: str) -> str | None:
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None


def apply_styles() -> None:
    image4_base64   = _get_image_base64("Images/image4.jpeg")
import os
import io
import hmac
import base64
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
st.set_page_config(
    page_title="Salary Prediction App",
    page_icon="",
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
from security import rate_limit, reset_rate_limit, validate_login_input, validate_username, validate_email, validate_password
from reviews import create_reviews_table
from password_reset import (
    create_reset_tables, create_reset_token, verify_reset_token,
    mark_token_used, get_user_email, save_user_email, send_reset_email,
)


#CONSTANTS 
MODEL_MAE_USD  = 10_000
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

#UI STYLING 
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

.stApp {{
    background: #f0f2f4;
    color: #3a5570;
}}

section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #f4f7f9 0%, #e3ebf3 100%);
    color: #1a2e42;
    border-right: 1px solid rgba(0, 0, 0, 0.05);
    box-shadow: 2px 0 15px rgba(0,0,0,0.02);
}}

section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] .stTextInput label {{
    color: #1a2e42 !important;
    font-weight: 600;
}}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {{
    color: #1a2e42 !important;
}}

h1, h2, h3, h4, h5, h6 {{ color: #1a2e42; font-weight: 700; }}

label,
.stTextInput label p,
.stSelectbox label p,
.stNumberInput label p,
.stTextArea label p,
.stRadio label p,
[data-testid="stWidgetLabel"] p {{
    color: #111d2e !important;
    font-weight: 600 !important;
}}

.stButton > button {{
    background: linear-gradient(120deg, #2d4a6b, #4a6b8a);
    border-radius: 999px;
    color: white;
    font-weight: 600;
    border: none;
    padding: 0.55rem 1.4rem;
    box-shadow: 0 10px 25px rgba(45, 74, 107, 0.28);
}}

.stButton > button:hover {{
    background: linear-gradient(120deg, #1a2e42, #3a5570);
    transform: translateY(-1px);
}}

section[data-testid="stSidebar"] .stButton > button {{
    background: linear-gradient(120deg, #111d2e, #1a2e42) !important;
    color: white !important;
    box-shadow: 0 8px 20px rgba(17, 29, 46, 0.35) !important;
}}

section[data-testid="stSidebar"] .stButton > button:hover {{
    background: linear-gradient(120deg, #0a121c, #111d2e) !important;
}}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input,
.stSelectbox > div > div > div {{
    background-color: #ffffff !important;
    color: #1a2e42 !important;
    border: 1px solid #c8d2db !important;
    border-radius: 8px !important;
}}

section[data-testid="stSidebar"] .stTextInput > div > div > input {{
    background-color: rgba(255,255,255,0.85) !important;
    color: #1a2e42 !important;
    border: 1px solid rgba(0,0,0,0.1) !important;
}}

.calc-card {{
    background: #ffffff url('{image4_data_uri}') center/cover no-repeat;
    border-radius: 20px; padding: 1.4rem 1.5rem;
    box-shadow: 0 18px 40px rgba(15,23,42,0.12);
    border: 1px solid rgba(74, 107, 138, 0.24); position: relative;
}}
.calc-card::before {{
    content: ''; position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(255,255,255,0.88);
    border-radius: 20px; z-index: 0;
}}
.calc-card > * {{ position: relative; z-index: 1; }}
    section[data-testid="stSidebar"] div.stButton > button[kind="secondary"] {{
        background: none !important;
        border: none !important;
        color: #185FA5 !important;
        font-size: 15px !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 8px 12px !important;
        border-radius: 8px !important;
        width: 100% !important;
        box-shadow: none !important;
        cursor: pointer !important;
    }}
    section[data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover {{
        background-color: #e8f2fb !important;
        color: #042C53 !important;
    }}
    section[data-testid="stSidebar"] div.stButton > button[kind="secondary"] * {{
        text-align: left !important;
        justify-content: flex-start !important;
        width: 100% !important;
    }}
</style>
""", unsafe_allow_html=True)


# SESSION STATE 
def init_session_state() -> None:
    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("username", "")
    st.session_state.setdefault("role", None)
    st.session_state.setdefault("auth_page", "User Login")


# PAGE: MY PROFILE 
def show_profile_section() -> None:
    st.title("My Profile & Dashboard")
    username = st.session_state.username

    # ── 1. USER METRICS ──────────────────────────────────
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT country, education, employment, experience,
                       devtype, frameworks, languages, undergradmajor,
                       predicted_salary, predicted_at
                FROM predictions
                WHERE username = %s
                """,
                (username,),
            )
            rows = cur.fetchall()

    user_preds = [
        {
            "country":          r[0],
            "education":        r[1],
            "employment":       r[2],
            "experience":       r[3],
            "devtype":          r[4],
            "frameworks":       r[5],
            "languages":        r[6],
            "undergradmajor":   r[7],
            "predicted_salary": r[8],
            "predicted_at":     r[9],
        }
        for r in rows
    ]

    if user_preds:
        df_hist     = pd.DataFrame(user_preds)
        avg_sal     = f"${int(df_hist['predicted_salary'].mean()):,}"
        max_sal     = f"${int(df_hist['predicted_salary'].max()):,}"
        min_sal     = f"${int(df_hist['predicted_salary'].min()):,}"
        total_preds = len(df_hist)
    else:
        df_hist = pd.DataFrame(columns=[
            "country", "education", "employment", "experience",
            "devtype", "frameworks", "languages", "undergradmajor",
            "predicted_salary", "predicted_at",
        ])
        avg_sal     = "No predictions yet"
        max_sal     = "—"
        min_sal     = "—"
        total_preds = 0

    col_user, col_total, col_avg, col_high, col_low = st.columns(5)
    col_user.metric("Username",           username)
    col_total.metric("Total Predictions", total_preds)
    col_avg.metric("Avg Salary",          avg_sal)
    col_high.metric("Highest Salary",     max_sal)
    col_low.metric("Lowest Salary",       min_sal)

    st.divider()

    # ── 2. SALARY GROWTH TREND ───────────────────────────
    st.subheader("Salary Growth Trend")

    chart_buf   = None
    latest_pred = None

    if not df_hist.empty:
        df_hist["date_obj"] = pd.to_datetime(df_hist["predicted_at"], errors="coerce")
        df_hist = df_hist.dropna(subset=["date_obj"]).sort_values("date_obj")

        if not df_hist.empty:
            st.line_chart(df_hist.set_index("date_obj")["predicted_salary"], height=240)

            fig_rep, ax_rep = plt.subplots(figsize=(8, 4))
            ax_rep.plot(df_hist["date_obj"], df_hist["predicted_salary"],
                        marker="o", linestyle="-", color="#4c51bf")
            ax_rep.set_title("Salary Growth Trend")
            ax_rep.set_xlabel("Date")
            ax_rep.set_ylabel("Predicted Salary (USD)")
            plt.xticks(rotation=45)
            plt.tight_layout()

            chart_buf = io.BytesIO()
            fig_rep.savefig(chart_buf, format="png")
            chart_buf.seek(0)
            chart_b64 = base64.b64encode(chart_buf.read()).decode()
            plt.close(fig_rep)

            latest_pred = df_hist.iloc[-1]
        else:
            st.info("No valid dated predictions to plot yet.")
    else:
        st.info("Make some predictions to see your salary growth trend.")

    st.divider()

    # ── 3. EXPORT REPORT ─────────────────────────────────
    if not df_hist.empty and chart_buf and latest_pred is not None:
        st.subheader("Export My Salary Report")

        rep_date = datetime.now().strftime("%d %B %Y")
        rep_sal  = f"${int(latest_pred['predicted_salary']):,}"
        rep_min  = f"${int(max(0, latest_pred['predicted_salary'] - MODEL_MAE_USD)):,}"
        rep_max  = f"${int(latest_pred['predicted_salary'] + MODEL_MAE_USD):,}"

        html_content = f"""
        <html><head><style>
            body {{ font-family: Arial, sans-serif; padding: 40px; color: #333; }}
            .title {{ font-size: 28px; color: #4c51bf; font-weight: bold; text-align:center; }}
            .subtitle {{ font-size: 16px; color: #666; text-align:center; margin-bottom:40px; }}
            .card {{ background: #f8f9fa; padding: 20px; border-radius: 10px;
                     margin-bottom: 20px; border: 1px solid #ddd; }}
            .row {{ display: flex; justify-content: space-between; margin-bottom: 10px; }}
            .label {{ font-weight: bold; color: #555; }}
            .val {{ font-size: 18px; color: #2d3748; }}
            .big {{ color: #2b6cb0; font-size: 24px; font-weight: bold; }}
        </style></head><body>
            <div class="title">Salary Prediction Report</div>
            <div class="subtitle">Generated for {username} on {rep_date}</div>
            <div class="card">
                <h3>User Summary</h3>
                <div class="row"><span class="label">Total Predictions:</span><span class="val">{total_preds}</span></div>
                <div class="row"><span class="label">Average Salary:</span><span class="val">{avg_sal}</span></div>
                <div class="row"><span class="label">Highest Salary:</span><span class="val">{max_sal}</span></div>
                <div class="row"><span class="label">Lowest Salary:</span><span class="val">{min_sal}</span></div>
            </div>
            <div class="card">
                <h3>Latest Prediction</h3>
                <div class="row"><span class="label">Predicted Salary:</span><span class="big">{rep_sal}</span></div>
                <div class="row"><span class="label">Estimated Range:</span><span class="val">{rep_min} - {rep_max}</span></div>
            </div>
            <h3>Growth Trajectory</h3>
            <img src="data:image/png;base64,{chart_b64}" width="100%" />
            <p style="text-align:center; margin-top:50px; font-size:12px; color:#aaa;">
                Generated by the Salary Prediction System</p>
        </body></html>"""

        col_dl, col_email = st.columns(2)

        with col_dl:
            st.download_button(
                label="Download Report (HTML)",
                data=html_content,
                file_name=f"Salary_Report_{username}.html",
                mime="text/html",
                use_container_width=True,
            )

        with col_email:
            with st.expander("Email Report as PDF", expanded=False):
                recipient = st.text_input("Enter your email address",
                                          key="profile_report_email",
                                          placeholder="you@example.com")
                if st.button("Send PDF Report", key="profile_send_email",
                             use_container_width=True, type="primary"):
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
                        if ok: st.success(msg)
                        else:  st.error(msg)

    st.divider()

    # ── 4. ACCOUNT SETTINGS ──────────────────────────────
    with st.expander("Account Settings", expanded=False):

        st.markdown("#### Change Password")
        with st.form("change_pass_form"):
            cur_pass     = st.text_input("Current Password", type="password")
            new_pass     = st.text_input("New Password", type="password",
                                         help="Min 8 chars, 1 number, 1 special character")
            confirm_pass = st.text_input("Confirm New Password", type="password")

            if st.form_submit_button("Update Password"):
                # SECURITY: rate-limit to prevent brute-force of current password (OWASP A07)
                _cp_ok, _cp_msg = rate_limit("change_password", key=username.lower())
                if not _cp_ok:
                    st.error(_cp_msg)
                elif new_pass != confirm_pass:
                    st.error("New passwords do not match.")
                else:
                    success, resp = change_password(username, cur_pass, new_pass)
                    if success:
                        reset_rate_limit("change_password", key=username.lower())
                        st.success(resp)
                    else:
                        st.error(resp)

        st.markdown("#### Danger Zone")
        col_logout, col_delete = st.columns(2)

        with col_logout:
            if st.button("Logout All Sessions", use_container_width=True):
                st.session_state.clear()
                st.rerun()

        with col_delete:
            st.session_state.setdefault("confirm_delete", False)
            if not st.session_state.confirm_delete:
                if st.button("Delete Account", type="primary",
                             use_container_width=True, key="delete_account_btn"):
                    st.session_state.confirm_delete = True
                    st.rerun()
            else:
                st.warning("Are you sure? This cannot be undone.")
                col_yes, col_no = st.columns(2)
                if col_yes.button("Yes, Delete", type="primary"):
                    success, msg = delete_user_account(username)
                    if success:
                        st.success(msg)
                        st.session_state.clear()
                        st.rerun()
                    else:
                        st.error(msg)
                if col_no.button("Cancel"):
                    st.session_state.confirm_delete = False
                    st.rerun()


# ================= PAGE: ADMIN DASHBOARD =================
def show_admin_section() -> None:
    st.title("Admin Dashboard")

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT id, username, country, experience, education, undergradmajor,
                       employment, devtype, frameworks, languages,
                       predicted_salary, predicted_at
                FROM predictions
            """)
            rows = cur.fetchall()

            data = [
                {
                    "id":               row[0],
                    "username":         row[1],
                    "country":          row[2],
                    "experience":       row[3],
                    "education":        row[4],
                    "undergradmajor":   row[5],
                    "employment":       row[6],
                    "devtype":          row[7],
                    "frameworks":       row[8],
                    "languages":        row[9],
                    "predicted_salary": row[10],
                    "predicted_at":     row[11].strftime("%d-%m-%Y %I:%M %p") if row[11] else "",
                }
                for row in rows
            ]

            df = pd.DataFrame(data) if data else pd.DataFrame(columns=[
                "id","username","country","experience","education","undergradmajor",
                "employment","devtype","frameworks","languages","predicted_salary","predicted_at",
            ])
            if not df.empty:
                df["id"] = df["id"].astype(str)

            # KPI cards
            cur.execute("SELECT COUNT(*) FROM users")
            total_users_count = cur.fetchone()[0]

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Users",       total_users_count)
            c2.metric("Total Predictions", len(df))
            if not df.empty:
                c3.metric("Highest Salary (USD)", f"${int(df['predicted_salary'].max()):,}")
                c4.metric("Lowest Salary (USD)",  f"${int(df['predicted_salary'].min()):,}")
            else:
                c3.metric("Highest Salary (USD)", "$0")
                c4.metric("Lowest Salary (USD)",  "$0")

            st.divider()

            # Modify record
            st.subheader("Modify Record")
            search_term = st.text_input("Search user by username")
            filtered_df = (
                df[df["username"].str.contains(search_term, case=False, na=False)]
                if search_term else pd.DataFrame()
            )

            if search_term and not filtered_df.empty:
                selected_mod = st.selectbox(
                    "Select Record", filtered_df.index,
                    format_func=lambda i: (
                        f"{filtered_df.loc[i,'username']} — "
                        f"{filtered_df.loc[i,'devtype'] or 'N/A'} — "
                        f"{filtered_df.loc[i,'predicted_at']}"
                    ),
                )
                curr_sal  = float(filtered_df.loc[selected_mod, "predicted_salary"])
                st.info(f"Current Salary: ${int(curr_sal):,}")
                new_salary = st.number_input("New Salary (USD)", value=int(curr_sal), step=1000)
                col_upd, col_del = st.columns(2)
                record_id = int(filtered_df.loc[selected_mod, "id"])

                if col_upd.button("Update", key="admin_update_record"):
                    cur.execute("UPDATE predictions SET predicted_salary = %s WHERE id = %s",
                                (new_salary, record_id))
                    conn.commit()
                    st.success("Record updated.")
                    st.rerun()

                if col_del.button("Delete", key="admin_delete_record"):
                    cur.execute("DELETE FROM predictions WHERE id = %s", (record_id,))
                    conn.commit()
                    st.warning("Record deleted.")
                    st.rerun()

            elif search_term and filtered_df.empty:
                st.warning("No user found with that name.")

            st.divider()

            # Danger zone
            with st.expander("Danger Zone: Delete All Data"):
                st.warning("This will permanently delete all users and predictions.")
                del_pass = st.text_input("Enter Admin Password to Confirm", type="password")
                if st.button("Delete ALL Records and Users"):
                    # SECURITY: rate-limit destructive admin action (OWASP A01)
                    _aa_ok, _aa_msg = rate_limit("admin_action", key="delete_all")
                    if not _aa_ok:
                        st.error(_aa_msg)
                    elif not ADMIN_PASSWORD:
                        st.error("ADMIN_PASSWORD environment variable is not set.")
                    elif hmac.compare_digest(del_pass.encode(), ADMIN_PASSWORD.encode()):
                        # SECURITY: hmac.compare_digest prevents timing attacks (OWASP A02)
                        cur.execute("DELETE FROM predictions")
                        cur.execute("DELETE FROM users")
                        conn.commit()
                        st.success("All data deleted.")
                        st.rerun()
                    else:
                        st.error("Incorrect Admin Password.")

            st.divider()

            # User management
            st.subheader("User Management")
            cur.execute("""
                SELECT u.username, COUNT(p.id) AS prediction_count
                FROM users u
                LEFT JOIN predictions p ON p.username = u.username
                GROUP BY u.username
            """)
            all_users = [{"username": r[0], "prediction_count": r[1]}
                         for r in cur.fetchall()]

            if all_users:
                df_users = pd.DataFrame(all_users)
                st.dataframe(df_users, use_container_width=True)

                st.markdown("#### Manage User")
                selected_username = st.selectbox("Select User", df_users["username"])
                if selected_username:
                    with st.expander(f"Manage {selected_username}"):
                        st.write("Remove this user and all their stored predictions.")
                        col_del_user, _ = st.columns([1, 4])
                        if col_del_user.button("Delete User and Predictions",
                                               type="primary", key="delete_user_button"):
                            cur.execute("DELETE FROM predictions WHERE username = %s",
                                        (selected_username,))
                            cur.execute("DELETE FROM users WHERE username = %s",
                                        (selected_username,))
                            conn.commit()
                            st.warning(f"User {selected_username} deleted.")
                            st.rerun()
            else:
                st.info("No registered users found.")

            st.divider()

            # Salary records table
            st.subheader("Salary Records")
            display_cols = [
                "username","country","education",
                "employment","devtype","frameworks","languages",
                "experience","predicted_salary","predicted_at",
            ]
            display_cols = [c for c in display_cols if c in df.columns]
            if not df.empty:
                st.dataframe(df[display_cols], use_container_width=True)
            else:
                st.info("No prediction records available.")

            st.divider()

            # Analytics
            st.subheader("Salary Analytics")
            if not df.empty:
                if "country" in df.columns:
                    with st.expander("Country Distribution"):
                        country_counts = df["country"].dropna().value_counts()
                        if country_counts.empty:
                            st.info("No country data yet.")
                        else:
                            fig, ax = plt.subplots()
                            ax.pie(country_counts, labels=country_counts.index,
                                   autopct="%1.1f%%", startangle=90)
                            ax.axis("equal")
                            st.pyplot(fig); plt.close(fig)

                if "experience" in df.columns:
                    with st.expander("Experience vs Average Salary"):
                        exp_sal = (df[df["experience"].notna()]
                                   .groupby("experience")["predicted_salary"]
                                   .mean().reset_index().sort_values("experience"))
                        if exp_sal.empty:
                            st.info("No experience data yet.")
                        else:
                            fig, ax = plt.subplots()
                            ax.plot(exp_sal["experience"], exp_sal["predicted_salary"], marker="o")
                            ax.set_xlabel("Experience (Years)")
                            ax.set_ylabel("Average Predicted Salary (USD)")
                            ax.set_title("Salary Trend by Experience")
                            st.pyplot(fig); plt.close(fig)

                if "devtype" in df.columns:
                    with st.expander("Developer Role vs Average Salary"):
                        role_sal = (df[df["devtype"].notna() & (df["devtype"] != "")]
                                    .groupby("devtype")["predicted_salary"]
                                    .mean().sort_values(ascending=True))
                        if role_sal.empty:
                            st.info("No developer role data yet.")
                        else:
                            fig, ax = plt.subplots(figsize=(8, 5))
                            ax.barh(role_sal.index, role_sal.values, color="#6366f1")
                            ax.set_xlabel("Average Predicted Salary (USD)")
                            ax.set_title("Average Salary by Developer Role")
                            plt.tight_layout()
                            st.pyplot(fig); plt.close(fig)

                if "languages" in df.columns:
                    with st.expander("Top Programming Languages Used"):
                        lang_series = (
                            df["languages"].dropna()
                              .loc[df["languages"].dropna() != ""]
                              .str.split(",").explode().str.strip()
                              .value_counts().head(12)
                        )
                        if lang_series.empty:
                            st.info("No language data yet.")
                        else:
                            fig, ax = plt.subplots(figsize=(8, 5))
                            lang_series.sort_values().plot(kind="barh", ax=ax, color="#4a6b8a")
                            ax.set_xlabel("Count")
                            ax.set_title("Top Languages Across All Predictions")
                            plt.tight_layout()
                            st.pyplot(fig); plt.close(fig)

                if "employment" in df.columns:
                    with st.expander("Employment Type vs Average Salary"):
                        emp_sal = (df[df["employment"].notna()]
                                   .groupby("employment")["predicted_salary"]
                                   .mean().reset_index())
                        if emp_sal.empty:
                            st.info("No employment data yet.")
                        else:
                            fig, ax = plt.subplots()
                            ax.bar(emp_sal["employment"], emp_sal["predicted_salary"],
                                   color="#f472b6")
                            ax.set_xlabel("Employment Type")
                            ax.set_ylabel("Average Predicted Salary (USD)")
                            ax.set_title("Average Salary by Employment Type")
                            st.pyplot(fig); plt.close(fig)

            st.divider()

            # CSV export
            st.subheader("Export Data")
            export_cols = [c for c in display_cols if c in df.columns] if not df.empty else []
            csv = (df[export_cols] if export_cols else df).to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "salary_predictions.csv", "text/csv")

            st.divider()

            # ── Review Moderation ──────────────────────────────────────────
            st.subheader("Review Moderation")
            st.caption("Approve reviews to display them in the homepage testimonials marquee.")

            try:
                from reviews import get_all_reviews_admin, approve_review, delete_review as del_review
                all_rv = get_all_reviews_admin()
            except Exception as e:
                st.error(f"Could not load reviews: {e}")
                all_rv = []

            if not all_rv:
                st.info("No reviews submitted yet.")
            else:
                pending   = [r for r in all_rv if not r["approved"]]
                approved  = [r for r in all_rv if r["approved"]]

                if pending:
                    st.markdown(f"**Pending approval ({len(pending)})**")
                    for r in pending:
                        with st.expander(f"{r['username']} — {r['role_title']} — {r['created_at'].strftime('%Y-%m-%d') if r['created_at'] else ''}"):
                            st.write(r["review_text"])
                            st.write(f"Rating: {'★' * r['rating']}{'☆' * (5 - r['rating'])}")
                            col_a, col_d = st.columns(2)
                            with col_a:
                                if st.button("Approve", key=f"rv_approve_{r['id']}", type="primary"):
                                    approve_review(r["id"])
                                    st.success("Approved.")
                                    st.rerun()
                            with col_d:
                                if st.button("Delete", key=f"rv_delete_{r['id']}"):
                                    del_review(r["id"])
                                    st.warning("Deleted.")
                                    st.rerun()
                else:
                    st.success("No pending reviews.")

                if approved:
                    st.markdown(f"**Live on homepage ({len(approved)})**")
                    for r in approved:
                        with st.expander(f"{r['username']} — {r['role_title']}"):
                            st.write(r["review_text"])
                            st.write(f"Rating: {'★' * r['rating']}{'☆' * (5 - r['rating'])}")
                            if st.button("Remove from homepage", key=f"rv_rm_{r['id']}"):
                                del_review(r["id"])
                                st.warning("Removed.")
                                st.rerun()


# ================= MAIN =================
apply_styles()
init_session_state()
create_reset_tables()
try:
    create_reviews_table()
except Exception:
    pass

# ================= SIDEBAR =================
st.sidebar.markdown("""
    <div style='text-align: center; padding: 10px 0;'>
        <span style='font-size: 22px; font-weight: bold; color: #185FA5;'>Salary Predictor</span>
        <br>
        <span style='font-size: 10px; color: #888; letter-spacing: 2px;'>ML-POWERED · REAL-TIME</span>
    </div>
""", unsafe_allow_html=True)
if not st.session_state.logged_in:
    _auth_options = ["User Login", "User Registration", "Forgot Password", "Admin Login"]
    _current = st.session_state.get("auth_page", "User Login")
    if _current not in _auth_options:
        _current = "User Login"
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    for auth_opt in _auth_options:
        if _current == auth_opt:
            st.sidebar.markdown(f"""
                <div style='background-color: #185FA5; color: white; 
                padding: 8px 12px; border-radius: 8px; 
                margin-bottom: 4px; font-weight: bold;'>
                    {auth_opt}
                </div>
            """, unsafe_allow_html=True)
        else:
            if st.sidebar.button(auth_opt, key=f"auth_nav_{auth_opt}", use_container_width=True):
                st.session_state.auth_page = auth_opt
                st.rerun()


#AUTH PAGES 
if not st.session_state.logged_in:

    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Playfair+Display:wght@700;800&display=swap');
        .stApp {
            background: linear-gradient(135deg, #f0f4f8 0%, #d9e4ee 35%, #2d4a6b 75%, #0f1b29 100%) !important;
        }
        .main .block-container { padding-top:2rem !important; max-width:100% !important; }
        [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(1) {
            background: rgba(255, 255, 255, 0.92);
            backdrop-filter: blur(16px);
            padding: 2.5rem;
            border-radius: 20px;
            box-shadow: 0 15px 45px rgba(10, 20, 30, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.7);
            margin-top: 1rem;
            margin-bottom: 2rem;
        }
        .auth-form-logo { font-family:'DM Sans',sans-serif; font-size:1.1rem; font-weight:700; color:#4a6b8a; margin-bottom:0.3rem; letter-spacing: 0.05em; text-transform: uppercase; }
        .auth-form-title { font-family:'Playfair Display',serif; font-size:2.4rem; font-weight:800; color:#111d2e; margin-bottom:0.3rem; white-space:nowrap; }
        .auth-form-subtitle { font-size:0.95rem; color:#4a6b8a; margin-bottom:1.5rem; }
        .auth-form-divider { border:none; border-top:1px solid #d7e0e8; margin:1rem 0 1.5rem; }
        .auth-hero-panel {
            border-radius:24px;
            background:linear-gradient(135deg,#1a2e42,#2d4a6b,#3a5570);
            background-size:400% 400%;
            animation:gradientShift 8s ease infinite;
            min-height:520px; position:relative; overflow:hidden;
            display:flex; align-items:center; justify-content:center; padding:2.5rem;
        }
        @keyframes gradientShift {
            0%   { background-position:0% 50%; }
            50%  { background-position:100% 50%; }
            100% { background-position:0% 50%; }
        }
        .auth-hero-panel::before {
            content:''; position:absolute; width:350px; height:350px;
            background:radial-gradient(circle,rgba(240,242,244,0.14) 0%,transparent 70%);
            top:-80px; right:-60px; border-radius:50%;
            animation:float1 6s ease-in-out infinite;
        }
        .auth-hero-panel::after {
            content:''; position:absolute; width:250px; height:250px;
            background:radial-gradient(circle,rgba(74,107,138,0.28) 0%,transparent 70%);
            bottom:-50px; left:5%; border-radius:50%;
            animation:float2 8s ease-in-out infinite;
        }
        @keyframes float1 { 0%,100%{transform:translateY(0) scale(1);} 50%{transform:translateY(-20px) scale(1.05);} }
        @keyframes float2 { 0%,100%{transform:translateY(0) scale(1);} 50%{transform:translateY(15px) scale(0.95);} }
        .auth-hero-inner { position:relative; z-index:2; text-align:center; }
        .auth-badge {
            display:inline-block; background:rgba(255,255,255,0.1);
            border:1px solid rgba(255,255,255,0.2); border-radius:999px;
            padding:0.35rem 1.1rem; font-size:0.7rem; color:rgba(255,255,255,0.8);
            letter-spacing:0.1em; text-transform:uppercase; margin-bottom:1.2rem;
            backdrop-filter:blur(8px);
        }
        .auth-hero-title {
            font-family:'Playfair Display',serif; font-size:2.6rem; font-weight:800;
            color:#ffffff; line-height:1.2; margin:0 0 1rem 0;
            text-shadow:0 4px 24px rgba(0,0,0,0.3);
        }
        .auth-hero-title span {
            background:linear-gradient(120deg,#d9e4ee,#f0f2f4,#9eb3c7);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent;
        }
        .auth-hero-sub { color:rgba(240,242,244,0.78); font-size:0.9rem; line-height:1.7; margin-bottom:2rem; }
        .auth-stats { display:flex; justify-content:center; gap:0.8rem; flex-wrap:wrap; }
        .auth-stat-pill {
            background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.15);
            border-radius:14px; padding:0.75rem 1.1rem; backdrop-filter:blur(12px);
            text-align:center; min-width:80px;
        }
        .auth-stat-num  { font-size:1.3rem; font-weight:700; margin-bottom:0.1rem; }
        .auth-stat-label{ font-size:0.6rem; color:rgba(255,255,255,0.6); text-transform:uppercase; letter-spacing:0.08em; }
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
                    if not _un_ok:       st.error(_un_msg)
                    elif not _em_ok:     st.error(_em_msg)
                    elif not _pw_ok:     st.error(_pw_msg)
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
                            <div class="auth-stat-num" style="color:#9eb3c7;">95%</div>
                            <div class="auth-stat-label">Accuracy</div>
                        </div>
                        <div class="auth-stat-pill">
                            <div class="auth-stat-num" style="color:#c7d5e2;">Free</div>
                            <div class="auth-stat-label">Always</div>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)


# MAIN APP 
if st.session_state.logged_in:

    pages = (
        {"Admin Dashboard": "Admin Dashboard", "Logout": "Logout"}
        if st.session_state.role == "admin"
        else {
            "Home": "Home",
            "Predict": "Predict",
            "Explore": "Explore",
            "Skill Gap": "Skill Gap",
            "My Profile": "My Profile",
            "Logout": "Logout"
        }
    )

    if "_force_nav" in st.session_state and st.session_state._force_nav in pages.values():
        st.session_state.nav_selectbox = st.session_state._force_nav
        del st.session_state._force_nav

    if "nav_selectbox" not in st.session_state or st.session_state.nav_selectbox not in pages.values():
        st.session_state.nav_selectbox = next(iter(pages.values()))

    # Sidebar nav with clickable text
    # Sidebar nav styling (moved to global apply_styles)

    role_label = "Admin" if st.session_state.role == "admin" else "User"
    st.sidebar.success(f"{role_label}: {st.session_state.username}")

    st.sidebar.markdown("### Navigation")

    for label, page_key in pages.items():
        if st.session_state.nav_selectbox == page_key:
            st.sidebar.markdown(f"""
                <div style='background-color: #185FA5; color: white; 
                padding: 8px 12px; border-radius: 8px; 
                margin-bottom: 4px; font-weight: bold;'>
                    {label}
                </div>
            """, unsafe_allow_html=True)
        else:
            if st.sidebar.button(label, key=f"nav_{page_key}", use_container_width=True):
                if page_key == "Logout":
                    st.session_state.clear()
                    st.rerun()
                else:
                    st.session_state.nav_selectbox = page_key
                    st.rerun()

    # Removed standalone logout button as it was added to the navigation menu ABOVE.

    menu = st.session_state.nav_selectbox

    if   menu == "Home":            show_home_page()
    elif menu == "Predict":         show_predict_page()
    elif menu == "Explore":         show_explore_page()
    elif menu == "Skill Gap":       show_skill_gap_page()
    elif menu == "My Profile":      show_profile_section()
    elif menu == "Admin Dashboard": show_admin_section()
