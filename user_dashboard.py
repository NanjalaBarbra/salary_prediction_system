import io
import base64
from datetime import datetime

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from database import get_connection
from email_report import generate_pdf, send_salary_report
from security import rate_limit, reset_rate_limit
from auth_page import validate_password_strength, change_password, delete_user_account

MODEL_MAE_USD = 10_000


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
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)

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
