import streamlit as st
import pickle
import numpy as np
from database import get_connection   # use helper function instead of global connection/cursor

def load_model():
    with open("notebooks/saved_steps.pkl", "rb") as file:
        data = pickle.load(file)
    return data

data = load_model()

regressor_loaded = data["model"]
le_country = data["le_country"]
le_education = data["le_education"]
le_employment = data["le_employment"]
le_undergradmajor = data["le_undergradmajor"]
le_webfameworkedwith = data["le_webfameworkedwith"]

def show_predict_page():
    #st.title("Salary Prediction App")
    st.write("""### We need some information to predict the salary""")

    # Track which step of the form the user is on
    if "predict_step" not in st.session_state:
        st.session_state.predict_step = 1

    # Step 1: Background Info
    if st.session_state.predict_step == 1:
        Countries = (
            "United States", "India", "United Kingdom", "Germany", "Canada",
            "France", "Brazil", "Spain", "Australia", "Netherlands", "Poland", "other"
        )

        undergradmajor = (
            "CS/Software Eng", "Math/Stats", "IT/Systems ", "Natural Sciences", "Arts",
            "Other Engineering", "Humanities", "Health Sciences", "Social Sciences",
            "Web Dev/Design", "Business"
        )

        st.session_state.country = st.selectbox("Country", Countries)
        st.session_state.education = st.selectbox("Education Level", tuple(le_education.classes_))
        st.session_state.undergradmajor = st.selectbox("Your Undergraduate Major", undergradmajor)

        st.button("Next", on_click=lambda: st.session_state.update({"predict_step": 2}))

    # Step 2: Work Info
    elif st.session_state.predict_step == 2:
        employment = ("full-time", "part-time")
        webframeworkedwith = ("React.js", "J Query", "Spring", "Flask", "other")

        st.session_state.employment = st.selectbox("Employment Status", employment)
        st.session_state.Experience = st.slider("Years of Experience", 0, 50, 1)
        st.session_state.webframeworkedwith = st.selectbox("Web Framework conversant With", webframeworkedwith)

        st.button("Back", on_click=lambda: st.session_state.update({"predict_step": 1}))

        if st.button("Calculate Salary"):
            X = np.array([[
                st.session_state.country,
                st.session_state.education,
                st.session_state.employment,
                st.session_state.Experience,
                st.session_state.webframeworkedwith,
                st.session_state.undergradmajor
            ]])

            # Apply label encoders
            X[:, 0] = le_country.transform(X[:, 0])
            X[:, 1] = le_education.transform(X[:, 1])
            X[:, 2] = le_employment.transform(X[:, 2])
            X[:, 4] = le_webfameworkedwith.transform(X[:, 4])
            X[:, 5] = le_undergradmajor.transform(X[:, 5])
            X = X.astype(float)

            salary = regressor_loaded.predict(X)
            st.subheader(f"The estimated salary is ${salary[0]:.2f}")

            # -------------------------------
            # Save prediction to database
            # -------------------------------
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO predictions (username, country, education, employment, experience, webframework, undergradmajor, predicted_salary)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    st.session_state.username if "username" in st.session_state else "guest",
                    st.session_state.country,
                    st.session_state.education,
                    st.session_state.employment,
                    st.session_state.Experience,
                    st.session_state.webframeworkedwith,
                    st.session_state.undergradmajor,
                    float(salary[0])
                ))
                conn.commit()
                cur.close()
                conn.close()
                st.success("✅ Prediction saved to database")
            except Exception as e:
                st.error(f"Database error: {str(e)}")
                