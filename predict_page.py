import streamlit as st
import numpy as np
import pandas as pd
import joblib
from database import get_connection   # use helper function instead of global connection/cursor


@st.cache_resource
def load_model():
    # Load the end-to-end pipeline trained in train_models.py
    model = joblib.load("best_salary_model.pkl")
    return model


regressor_loaded = load_model()

def show_predict_page():
    
    # Track which step of the form the user is on
    if "predict_step" not in st.session_state:
        st.session_state.predict_step = 1

    # Step 1: Background Info
    if st.session_state.predict_step == 1:
        st.markdown(
            """
            <h3 style="text-align: center; font-weight: 700; margin-bottom: 2.5rem; font-size: 1.8rem; background: linear-gradient(120deg, #10b981, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                💰 We need some information to Estimate the salary
            </h3>
            """,
            unsafe_allow_html=True
        )
        Countries = (
            "United States", "India", "United Kingdom", "Germany", "Canada",
            "France", "Brazil", "Spain", "Australia", "Netherlands", "Poland", "other"
        )

        undergradmajor = (
            "CS/Software Eng", "Math/Stats", "IT/Systems", "Natural Sciences", "Arts",
            "Other Engineering", "Humanities", "Health Sciences", "Social Sciences",
            "Web Dev/Design", "Business", "Other", "Unknown", "Undeclared"
        )

        education_levels = (
            "less than a Bachelor's",
            "Bachelor's degree",
            "Master's degree",
            "Post grad",
        )

        # Add custom styling
        st.markdown(
            """
            <style>
            .predict-image-wrapper {
                position: relative;
            }
            .predict-image-wrapper img {
                border-radius: 20px;
                box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
                border: 4px solid rgba(251, 191, 36, 0.6);
            }
            .predict-form-container {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 24px;
                padding: 2rem 1.5rem;
                box-shadow: 0 20px 50px rgba(139, 92, 246, 0.3);
                border: 3px solid rgba(251, 191, 36, 0.4);
                backdrop-filter: blur(10px);
            }
            .form-header {
                font-size: 1.5rem;
                font-weight: 700;
                background: linear-gradient(120deg, #10b981, #3b82f6);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 1.5rem;
                padding-bottom: 0.75rem;
                border-bottom: 3px solid #fbbf24;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        # Create two-column layout
        col1, col2 = st.columns([1, 1], gap="large")
        
        # Left column: Image only
        with col1:
            st.markdown('<div class="predict-image-wrapper">', unsafe_allow_html=True)
            st.image("Images/image1.jpeg", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Right column: Form fields with header inside the container
        with col2:
            st.markdown('<div class="predict-form-container">', unsafe_allow_html=True)
            st.markdown('<div class="form-header">📋 Background Information</div>', unsafe_allow_html=True)
            
            st.session_state.country = st.selectbox("🌍 Country", Countries)
            st.session_state.education = st.selectbox("🎓 Education Level", education_levels)
            st.session_state.undergradmajor = st.selectbox("📚 Your Undergraduate Major", undergradmajor)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Next button below the columns
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("Next ➡️", on_click=lambda: st.session_state.update({"predict_step": 2}), use_container_width=True)

    # Step 2: Work Info
    elif st.session_state.predict_step == 2:
        employment = ("full-time", "part-time")
        webframeworkedwith = ("React.js", "J Query", "Spring", "Flask", "other")

        # Add custom styling
        st.markdown(
            """
            <style>
            .predict-image-wrapper-right {
                position: relative;
            }
            .predict-image-wrapper-right img {
                border-radius: 20px;
                box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
                border: 4px solid rgba(251, 191, 36, 0.6);
            }
            .predict-work-form-container {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 24px;
                padding: 2rem 1.5rem;
                box-shadow: 0 20px 50px rgba(139, 92, 246, 0.3);
                border: 3px solid rgba(251, 191, 36, 0.4);
                backdrop-filter: blur(10px);
            }
            .work-form-header {
                font-size: 1.5rem;
                font-weight: 700;
                background: linear-gradient(120deg, #8b5cf6, #3b82f6);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 1.5rem;
                padding-bottom: 0.75rem;
                border-bottom: 3px solid #fbbf24;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        # Create two-column layout (reversed: form left, image right)
        col1, col2 = st.columns([1, 1], gap="large")
        
        # Left column: Form fields with header inside the container
        with col1:
            st.markdown('<div class="predict-work-form-container">', unsafe_allow_html=True)
            st.markdown('<div class="work-form-header">💼 Work Information</div>', unsafe_allow_html=True)
            
            st.session_state.employment = st.selectbox("💻 Employment Status", employment)
            st.session_state.Experience = st.slider("📅 Years of Experience", 0, 50, 1)
            st.session_state.webframeworkedwith = st.selectbox("🔧 Web Framework conversant With", webframeworkedwith)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Right column: Image only
        with col2:
            st.markdown('<div class="predict-image-wrapper-right">', unsafe_allow_html=True)
            st.image("Images/image2.jpeg", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Buttons below the columns
        st.markdown("<br>", unsafe_allow_html=True)
        col_back, col_calc = st.columns([1, 1], gap="medium")
        
        with col_back:
            st.button("⬅️ Back", on_click=lambda: st.session_state.update({"predict_step": 1}), use_container_width=True)
        
        with col_calc:
            calculate_clicked = st.button("💰 Calculate Salary", use_container_width=True, type="primary")
        
        if calculate_clicked:
            # Build a DataFrame with the exact feature names used in train_models.py
            X = pd.DataFrame(
                [
                    {
                        "Country": st.session_state.country,
                        "EdLevel": st.session_state.education,
                        "Employment": st.session_state.employment,
                        "Experience": float(st.session_state.Experience),
                        "WebframeWorkedWith": st.session_state.webframeworkedwith,
                        "UndergradMajor": st.session_state.undergradmajor,
                    }
                ]
            )

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
                