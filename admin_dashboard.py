import hmac
import os

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from database import get_connection
from security import rate_limit

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    raise ValueError("ADMIN_PASSWORD environment variable must be set before starting the app.")


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
                "id", "username", "country", "experience", "education", "undergradmajor",
                "employment", "devtype", "frameworks", "languages", "predicted_salary", "predicted_at",
            ])
            if not df.empty:
                df["id"] = df["id"].astype(str)

            # ── KPI cards ─────────────────────────────────────────
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

            # ── Modify record ──────────────────────────────────────
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
                        f"{filtered_df.loc[i, 'username']} — "
                        f"{filtered_df.loc[i, 'devtype'] or 'N/A'} — "
                        f"{filtered_df.loc[i, 'predicted_at']}"
                    ),
                )
                curr_sal   = float(filtered_df.loc[selected_mod, "predicted_salary"])
                st.info(f"Current Salary: ${int(curr_sal):,}")
                new_salary = st.number_input("New Salary (USD)", value=int(curr_sal), step=1000)
                col_upd, col_del = st.columns(2)
                record_id  = int(filtered_df.loc[selected_mod, "id"])

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

            # ── Danger zone ────────────────────────────────────────
            with st.expander("Danger Zone: Delete All Data"):
                st.warning("This will permanently delete all users and predictions.")
                del_pass = st.text_input("Enter Admin Password to Confirm", type="password")
                if st.button("Delete ALL Records and Users"):
                    _aa_ok, _aa_msg = rate_limit("admin_action", key="delete_all")
                    if not _aa_ok:
                        st.error(_aa_msg)
                    elif hmac.compare_digest(del_pass.encode(), ADMIN_PASSWORD.encode()):
                        cur.execute("DELETE FROM predictions")
                        cur.execute("DELETE FROM users")
                        conn.commit()
                        st.success("All data deleted.")
                        st.rerun()
                    else:
                        st.error("Incorrect Admin Password.")

            st.divider()

            # ── User management ────────────────────────────────────
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

            # ── Salary records table ───────────────────────────────
            st.subheader("Salary Records")
            display_cols = [
                "username", "country", "education",
                "employment", "devtype", "frameworks", "languages",
                "experience", "predicted_salary", "predicted_at",
            ]
            display_cols = [c for c in display_cols if c in df.columns]
            if not df.empty:
                st.dataframe(df[display_cols], use_container_width=True)
            else:
                st.info("No prediction records available.")

            st.divider()

            # ── Analytics ──────────────────────────────────────────
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
                            st.pyplot(fig)
                            plt.close(fig)

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
                            st.pyplot(fig)
                            plt.close(fig)

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
                            st.pyplot(fig)
                            plt.close(fig)

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
                            st.pyplot(fig)
                            plt.close(fig)

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
                            st.pyplot(fig)
                            plt.close(fig)

            st.divider()

            # ── CSV export ─────────────────────────────────────────
            st.subheader("Export Data")
            export_cols = [c for c in display_cols if c in df.columns] if not df.empty else []
            csv = (df[export_cols] if export_cols else df).to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "salary_predictions.csv", "text/csv")

            st.divider()

            # ── Review moderation ──────────────────────────────────
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
                pending  = [r for r in all_rv if not r["approved"]]
                approved = [r for r in all_rv if r["approved"]]

                if pending:
                    st.markdown(f"**Pending approval ({len(pending)})**")
                    for r in pending:
                        with st.expander(
                            f"{r['username']} — {r['role_title']} — "
                            f"{r['created_at'].strftime('%Y-%m-%d') if r['created_at'] else ''}"
                        ):
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
