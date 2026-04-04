import streamlit as st


def show_about_page():
    """
    About Us page with information about the app
    """
    
    st.markdown(
        """
        <div style="text-align: center; margin-top: 2rem; margin-bottom: 3rem;">
            <h1 style="font-size: 3rem; font-weight: 800; background: linear-gradient(120deg, #1a2e42, #2d4a6b, #4a6b8a); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 1rem;">
                About Us
            </h1>
            <p style="font-size: 1.2rem; color: #6b7c8d; font-weight: 500; max-width: 700px; margin: 0 auto;">
                Learn more about our mission and the technology behind our salary predictions
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Mission Section
    st.markdown(
        """
        <div style="background: rgba(255, 255, 255, 0.98); border-radius: 24px; padding: 2.5rem; box-shadow: 0 20px 50px rgba(45, 74, 107, 0.14); border: 1px solid rgba(74, 107, 138, 0.18); margin-bottom: 2rem;">
            <h2 style="font-size: 1.8rem; font-weight: 700; color: #1a2e42; margin-bottom: 1.5rem;">
                🎯 Our Mission
            </h2>
            <p style="color: #6b7c8d; font-size: 1.1rem; line-height: 1.8;">
                We believe that every developer deserves to know their true market value. Our mission is to empower 
                software developers worldwide with data-driven salary insights, helping them make informed career 
                decisions and negotiate fair compensation.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Technology Section
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown(
            """
            <div style="background: rgba(255, 255, 255, 0.98); border-radius: 20px; padding: 2rem; box-shadow: 0 15px 40px rgba(45, 74, 107, 0.10); border: 1px solid rgba(74, 107, 138, 0.18); height: 100%;">
                <h3 style="font-size: 1.5rem; font-weight: 700; color: #2d4a6b; margin-bottom: 1.5rem;">
                    🤖 Our Technology
                </h3>
                <ul style="color: #6b7c8d; font-size: 1rem; line-height: 1.8; list-style-position: inside;">
                    <li><strong>Machine Learning Models:</strong> Advanced regression algorithms trained on real-world data</li>
                    <li><strong>Data Source:</strong> Stack Overflow Developer Survey with 10,000+ responses</li>
                    <li><strong>Features:</strong> Country, experience, education, tech stack, and more</li>
                    <li><strong>Accuracy:</strong> Continuously improved through data validation and model tuning</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div style="background: rgba(255, 255, 255, 0.98); border-radius: 20px; padding: 2rem; box-shadow: 0 15px 40px rgba(45, 74, 107, 0.10); border: 1px solid rgba(74, 107, 138, 0.18); height: 100%;">
                <h3 style="font-size: 1.5rem; font-weight: 700; color: #4a6b8a; margin-bottom: 1.5rem;">
                    🔐 Privacy & Security
                </h3>
                <ul style="color: #6b7c8d; font-size: 1rem; line-height: 1.8; list-style-position: inside;">
                    <li><strong>Secure Authentication:</strong> Password hashing and secure session management</li>
                    <li><strong>Data Protection:</strong> Your personal information is encrypted and protected</li>
                    <li><strong>No Data Selling:</strong> We never sell or share your data with third parties</li>
                    <li><strong>Full Control:</strong> Delete your account and data anytime</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Team Section
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #2d4a6b 0%, #3a5570 100%); border-radius: 24px; padding: 2.5rem; text-align: center; box-shadow: 0 20px 50px rgba(45, 74, 107, 0.20); margin-bottom: 2rem; margin-top: 2rem;">
            <h2 style="color: #ffffff; font-size: 2rem; font-weight: 700; margin-bottom: 1rem;">
                Built by Developers, for Developers
            </h2>
            <p style="color: #f0f2f4; font-size: 1.1rem; max-width: 600px; margin: 0 auto;">
                Our team consists of experienced data scientists and software engineers passionate about 
                making salary transparency accessible to everyone.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Features Highlight
    st.markdown(
        """
        <div style="margin-top: 3rem; margin-bottom: 2rem;">
            <h2 style="text-align: center; font-size: 2rem; font-weight: 700; color: #1a2e42; margin-bottom: 2.5rem;">
                What You Get
            </h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    feat1, feat2, feat3 = st.columns(3, gap="large")

    with feat1:
        st.markdown(
            """
            <div style="text-align: center; padding: 1.5rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">💰</div>
                <h4 style="color: #1a2e42; font-weight: 600; margin-bottom: 0.5rem;">Salary Predictions</h4>
                <p style="color: #6b7c8d; font-size: 0.95rem;">Instant, personalized salary estimates based on your profile</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with feat2:
        st.markdown(
            """
            <div style="text-align: center; padding: 1.5rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
                <h4 style="color: #1a2e42; font-weight: 600; margin-bottom: 0.5rem;">Data Exploration</h4>
                <p style="color: #6b7c8d; font-size: 0.95rem;">Explore salary trends across countries and experience levels</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with feat3:
        st.markdown(
            """
            <div style="text-align: center; padding: 1.5rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📈</div>
                <h4 style="color: #1a2e42; font-weight: 600; margin-bottom: 0.5rem;">Track History</h4>
                <p style="color: #6b7c8d; font-size: 0.95rem;">Monitor your salary predictions and career growth over time</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Contact/CTA Section
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.markdown(
            """
            <div style="background: rgba(255, 255, 255, 0.98); border-radius: 20px; padding: 2rem; text-align: center; box-shadow: 0 15px 40px rgba(45, 74, 107, 0.10); border: 1px solid rgba(74, 107, 138, 0.18);">
                <h3 style="color: #1a2e42; font-weight: 700; margin-bottom: 1rem;">Ready to get started?</h3>
                <p style="color: #6b7c8d; margin-bottom: 1.5rem;">Join us today and discover your true market value</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        
        btn_col1, btn_col2 = st.columns(2, gap="medium")
        with btn_col1:
            if st.button("🔑 Login", use_container_width=True, type="primary"):
                st.session_state.current_page = "login"
                st.rerun()
        with btn_col2:
            if st.button("📝 Register", use_container_width=True):
                st.session_state.current_page = "register"
                st.rerun()
