import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from predict_page import show_predict_page
from explore_page import show_explore_page
from auth_page import login_user, register_user, login_admin
from database import get_connection


# ================= UI STYLING =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
}

.stApp {
    background: radial-gradient(circle at 10% 20%, rgb(0, 0, 0) 0%, rgb(20, 20, 30) 40%, rgb(30, 35, 60) 90.2%);
    color: #f0f2f6;
}

section[data-testid="stSidebar"] {
    background: rgba(15, 15, 20, 0.95);
}

h1, h2, h3 {
    color: #ffffff;
    font-weight: 700;
}

.stButton > button {
    background: linear-gradient(92.88deg, #455EB5, #673FD7);
    border-radius: 12px;
    color: white;
    font-weight: 600;
    border: none;
    padding: 0.6rem 1.2rem;
}
</style>
""", unsafe_allow_html=True)


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
            st.success(msg) if success else st.error(msg)

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
        else ["Home", "Predict", "Explore", "My Predictions", "Logout"]
    )

    menu = st.sidebar.selectbox("Navigation", menu_items)

    # ================= HOME =================
    if menu == "Home":
        st.title("🏠 Home")

    # ================= USER PAGES =================
    elif menu == "Predict":
        show_predict_page()

    elif menu == "Explore":
        show_explore_page()

    elif menu == "My Predictions":
        st.title("My Past Predictions")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT country, education, employment, experience,
                   webframework, undergradmajor,
                   predicted_salary, predicted_at
            FROM predictions
            WHERE username = %s
        """, (st.session_state.username,))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if rows:
            for r in rows:
                st.markdown(f"""
                **Country:** {r[0]}  
                **Education:** {r[1]}  
                **Employment:** {r[2]}  
                **Experience:** {r[3]} years  
                **Web Framework:** {r[4]}  
                **Undergrad Major:** {r[5]}  
                **Predicted Salary:** **${r[6]:,.2f}**  
                **Date:** {r[7]}
                """)
        else:
            st.info("No predictions yet.")

    # ================= ADMIN DASHBOARD =================
    elif menu == "Admin Dashboard":
     if st.session_state.logged_in and st.session_state.role == "admin":
        st.title("🛡 Admin Dashboard")

        # Fetch predictions
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, country, experience,education, undergradmajor, employment, webframework, predicted_salary, predicted_at FROM predictions")
        rows = cur.fetchall()
        cur.close()
        conn.close()

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
                "predicted_at": row[9].strftime("%d-%m-%Y %I:%M %p") if row[9] else ""
            }
            for row in rows
        ]
        df = pd.DataFrame(data)

        # ================= Modify Record =================
        st.subheader("✏ Modify Record")
        search_term = st.text_input("Search user by username")

        if search_term:
            filtered_df = df[df["username"].str.contains(search_term, case=False, na=False)]
        else:
            filtered_df = pd.DataFrame()

        if search_term and not filtered_df.empty:
            selected_mod = st.selectbox(
                "Select Record",
                filtered_df.index,
                format_func=lambda i: (
                    f"{filtered_df.loc[i, 'username']} | "
                    f"${filtered_df.loc[i, 'predicted_salary']:,.0f} | "
                    f"{filtered_df.loc[i, 'predicted_at']}"
                )
            )
            record_id = int(filtered_df.loc[selected_mod, "id"])
            current_salary = float(filtered_df.loc[selected_mod, "predicted_salary"])

            st.info(f"Current Salary: **${current_salary:,.2f}**")

            new_salary = st.number_input(
                "New Salary (USD)",
                min_value=0.0,
                value=current_salary,
                step=1000.0
            )

            col1, col2 = st.columns(2)

            if col1.button("Update Salary"):
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE predictions SET predicted_salary = %s WHERE id = %s",
                    (new_salary, record_id)
                )
                conn.commit()
                cur.close()
                conn.close()
                st.success("Salary updated successfully.")
                st.rerun()

            if col2.button("Delete Record"):
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    "DELETE FROM predictions WHERE id = %s",
                    (record_id,)
                )
                conn.commit()
                cur.close()
                conn.close()
                st.warning("Record deleted successfully.")
                st.rerun()
        elif search_term and filtered_df.empty:
            st.warning("No user found with that name.")

        st.subheader("📋 Salary Records")
        st.dataframe(df.drop(columns=["id"]), use_container_width=True)

        st.subheader("📊 Salary Analytics")
        if not df.empty and "country" in df.columns:
            with st.expander("View Country Distribution"):
                fig, ax = plt.subplots()
                df["country"].value_counts().plot.pie(
                    autopct="%1.1f%%",
                    ax=ax
                )
                ax.set_ylabel("")
                st.pyplot(fig)
                plt.close(fig)

        # Exporting the data
        st.subheader("📥 Export Data")
        csv = df.drop(columns=["id"]).to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV",
            csv,
            "salary_predictions.csv",
            "text/csv"
        )  