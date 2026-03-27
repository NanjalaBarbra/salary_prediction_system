import streamlit as st
import base64
from reviews import get_approved_reviews, submit_review, user_already_reviewed


def _get_img_b64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None


def show_home_page():

    st.html("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;0,9..40,800&display=swap');

        .main .block-container { padding-top: 1.5rem !important; max-width: 100% !important; }

        /* ── tokens ── */
        :root {
            --bg:      #f8f7f4;
            --ink:     #0f172a;
            --ink2:    #475569;
            --ink3:    #94a3b8;
            --indigo:  #5B9BD5;
            --emerald: #10b981;
            --pink:    #f472b6;
            --orange:  #fb923c;
            --border:  #e2e8f0;
            --dark:    #080810;
        }

        /* ── typography helpers ── */
        .hp-eyebrow {
            font-family: 'DM Sans', sans-serif;
            font-size: 0.68rem; font-weight: 600;
            letter-spacing: 0.18em; text-transform: uppercase;
            color: var(--indigo); margin-bottom: 0.35rem;
        }
        .hp-h1 {
            font-family: 'DM Sans', sans-serif;
            font-size: clamp(2.4rem, 4vw, 4rem);
            font-weight: 800; color: var(--ink);
            line-height: 1.08; letter-spacing: -0.03em;
            margin: 0 0 1.2rem;
        }
        .hp-g { background: linear-gradient(120deg,#5B9BD5,#7EB3E0); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
        .hp-p { background: linear-gradient(120deg,#f472b6,#fb923c); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
        .hp-sub {
            font-family: 'DM Sans', sans-serif;
            font-size: 1rem; font-weight: 400;
            color: var(--ink2); line-height: 1.75; margin: 0 0 2rem;
        }
        .hp-h2 {
            font-family: 'DM Sans', sans-serif;
            font-size: clamp(1.8rem, 3vw, 2.4rem);
            font-weight: 800;
            color: var(--ink);
            letter-spacing: -0.03em;
            line-height: 1.1;
            margin-bottom: 0.4rem;
            -webkit-font-smoothing: antialiased;
        }
        .hp-lead {
            font-family: 'DM Sans', sans-serif;
            font-size: 0.9rem; color: var(--ink3);
            line-height: 1.7; max-width: 480px;
        }

        /* ── feature cards ── */
        .hp-fcard {
            background: #fff;
            border-radius: 18px; padding: 1.8rem;
            border: 1px solid var(--border);
            position: relative; overflow: hidden;
            height: 100%;
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }
        .hp-fcard:hover { transform: translateY(-3px); box-shadow: 0 16px 48px rgba(0,0,0,0.07); }
        .hp-fcard::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; }
        .c-green::before { background: linear-gradient(90deg,#10b981,#34d399); }
        .c-blue::before  { background: linear-gradient(90deg,#3b82f6,#6366f1); }
        .c-pink::before  { background: linear-gradient(90deg,#f472b6,#fb923c); }
        .hp-fcard-icon { width: 42px; height: 42px; border-radius: 10px; margin-bottom: 1rem; display: flex; align-items: center; justify-content: center; }
        .c-green .hp-fcard-icon { background: rgba(16,185,129,0.1); }
        .c-blue  .hp-fcard-icon { background: rgba(99,102,241,0.1); }
        .c-pink  .hp-fcard-icon { background: rgba(244,114,182,0.1); }
        .hp-fcard-icon svg { width: 20px; height: 20px; }
        .hp-fcard-title { font-family: 'Syne', sans-serif; font-size: 1rem; font-weight: 700; color: var(--ink); margin-bottom: 0.45rem; }
        .hp-fcard-text  { font-family: 'DM Sans', sans-serif; font-size: 0.85rem; color: var(--ink3); line-height: 1.7; }



        /* ── steps panel ── */
        .hp-steps-panel {
            background: #080810; border-radius: 24px;
            padding: 3rem 2.5rem; position: relative; overflow: hidden;
        }
        .hp-steps-panel::before {
            content: ''; position: absolute; inset: 0;
            background:
                radial-gradient(ellipse 50% 80% at 0% 50%, rgba(91,155,213,0.2) 0%, transparent 60%),
                radial-gradient(ellipse 50% 80% at 100% 50%, rgba(126,179,224,0.15) 0%, transparent 60%);
        }
        .hp-steps-hdr  { position: relative; z-index: 2; text-align: center; margin-bottom: 2.5rem; }
        .hp-steps-grid { position: relative; z-index: 2; display: grid; grid-template-columns: repeat(3,1fr); gap: 1.5rem; }
        .hp-scard {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 18px; padding: 2rem 1.5rem; text-align: center;
            transition: background 0.25s ease, border-color 0.25s ease;
        }
        .hp-scard:hover { background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.18); }
        .hp-snum   { font-family: 'DM Sans', sans-serif; font-size: 2.6rem; font-weight: 800; line-height: 1; margin-bottom: 0.6rem; }
        .hp-stitle { font-family: 'DM Sans', sans-serif; font-size: 1rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem; }
        .hp-stext  { font-family: 'DM Sans', sans-serif; font-size: 0.83rem; color: rgba(255,255,255,0.55); line-height: 1.7; }

        /* ── marquee testimonials ── */

        /* track + fade edges */
        .mq-outer {
            position: relative;
            overflow: hidden;
            width: 100%;
            padding: 0.5rem 0;
        }
        .mq-outer::before, .mq-outer::after {
            content: '';
            position: absolute; top: 0; bottom: 0;
            width: 120px; z-index: 2; pointer-events: none;
        }
        .mq-outer::before { left: 0;  background: linear-gradient(to right, var(--bg), transparent); }
        .mq-outer::after  { right: 0; background: linear-gradient(to left,  var(--bg), transparent); }

        /* scrolling row */
        .mq-track {
            display: flex;
            gap: 1.2rem;
            width: max-content;
            animation: mq-scroll 38s linear infinite;
        }
        .mq-track:hover { animation-play-state: paused; }
        @keyframes mq-scroll {
            from { transform: translateX(0); }
            to   { transform: translateX(calc(-50% - 0.6rem)); }
        }

        /* individual card */
        .mq-card {
            flex-shrink: 0;
            width: 300px;
            background: #fff;
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 1.4rem 1.5rem 1.3rem;
            position: relative;
        }
        /* top gradient line */
        .mq-card::before {
            content: '';
            position: absolute; top: 0; left: 0; right: 0;
            height: 2px; border-radius: 18px 18px 0 0;
        }
        .mq-c0::before { background: linear-gradient(90deg,#10b981,#34d399); }
        .mq-c1::before { background: linear-gradient(90deg,#5B9BD5,#7EB3E0); }
        .mq-c2::before { background: linear-gradient(90deg,#f472b6,#fb923c); }
        .mq-c3::before { background: linear-gradient(90deg,#3b82f6,#06b6d4); }
        .mq-c4::before { background: linear-gradient(90deg,#f59e0b,#ef4444); }

        .mq-text {
            font-family: 'DM Sans', sans-serif;
            font-size: 0.86rem; line-height: 1.75;
            color: var(--ink2);
            margin-bottom: 1.1rem;
            display: -webkit-box;
            -webkit-line-clamp: 4;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        .mq-footer {
            display: flex; align-items: center; gap: 0.7rem;
            border-top: 1px solid var(--border); padding-top: 0.9rem;
        }
        .mq-avatar {
            width: 34px; height: 34px; border-radius: 50%;
            display: inline-flex; align-items: center; justify-content: center;
            font-family: 'Syne', sans-serif; font-size: 0.75rem; font-weight: 800;
            color: #fff; flex-shrink: 0;
        }
        .mq-av0 { background: linear-gradient(135deg,#10b981,#059669); }
        .mq-av1 { background: linear-gradient(135deg,#5B9BD5,#CCDFF5); }
        .mq-av2 { background: linear-gradient(135deg,#f472b6,#db2777); }
        .mq-av3 { background: linear-gradient(135deg,#3b82f6,#0284c7); }
        .mq-av4 { background: linear-gradient(135deg,#f59e0b,#d97706); }
        .mq-name { font-family:'DM Sans',sans-serif; font-size:0.83rem; font-weight:700; color:var(--ink); display:block; }
        .mq-role { font-family:'DM Sans',sans-serif; font-size:0.72rem; color:var(--ink3); display:block; margin-top:0.05rem; }
        .mq-stars { display:inline-flex; gap:2px; margin-top:0.25rem; }
        .mq-star  { width:8px; height:8px; border-radius:1px; background:#fbbf24; display:inline-block; }
        .mq-star-empty { background:#e2e8f0; }

        /* ── review submission form panel ── */
        .rv-panel {
            background: #080810;
            border-radius: 24px;
            padding: 2.8rem 2.5rem;
            position: relative; overflow: hidden;
        }
        .rv-panel::before {
            content: ''; position: absolute; inset: 0;
            background:
                radial-gradient(ellipse 60% 70% at 0% 50%, rgba(91,155,213,0.18) 0%, transparent 60%),
                radial-gradient(ellipse 50% 60% at 100% 50%, rgba(126,179,224,0.12) 0%, transparent 60%);
            pointer-events: none;
        }
        .rv-inner { position: relative; z-index: 2; }
        .rv-hdr-eye { font-family:'DM Sans',sans-serif; font-size:0.68rem; font-weight:600; letter-spacing:0.18em; text-transform:uppercase; color:#5B9BD5; margin-bottom:0.4rem; }
        .rv-hdr-title { font-family:'DM Sans',sans-serif; font-size:clamp(1.8rem,3vw,2.4rem); font-weight:800; color:#fff; letter-spacing:-0.03em; line-height:1.1; margin-bottom:0.4rem; -webkit-font-smoothing:antialiased; }
        .rv-hdr-sub { font-family:'DM Sans',sans-serif; font-size:0.88rem; color:rgba(255,255,255,0.5); line-height:1.6; margin-bottom:2rem; }

        /* ── CTA banner ── */
        .hp-cta-banner {
            background: linear-gradient(135deg, #1e2d6b 0%, #1e4799 40%, #2158b8 70%, #2b6fd4 100%);
            border-radius: 20px; padding: 3rem 2rem; text-align: center;
        }
        .hp-cta-title { font-family: 'DM Sans', sans-serif; font-size: 1.8rem; font-weight: 800; color: #ffffff; margin-bottom: 0.6rem; }
        .hp-cta-sub   { font-family: 'DM Sans', sans-serif; font-size: 0.95rem; color: rgba(255,255,255,0.6); }

        /* ── footer ── */
        .hp-footer { text-align: center; padding: 1.8rem 0; font-family: 'DM Sans', sans-serif; font-size: 0.78rem; color: #94a3b8; }
        .hp-footer b { color: #5B9BD5; }
        </style>
    """)

    # ══ HERO ══
    left_col, right_col = st.columns([1.2, 1], gap="large")

    with left_col:
        st.html('<div class="hp-eyebrow">Powered by Stack Overflow Survey Data</div>')
        st.html('<h1 class="hp-h1">Predict Your<br><span class="hp-g">Developer</span> <span class="hp-p">Salary</span><br>Instantly</h1>')
        st.html('<p class="hp-sub">Stop guessing what you are worth. Get data-driven salary predictions tailored to your skills, experience, and location — in seconds.</p>')


    with right_col:
        _img = _get_img_b64("Images/image4.jpeg")
        _img_uri = f"data:image/jpeg;base64,{_img}" if _img else ""
        _bg = f"url('{_img_uri}') center/cover no-repeat" if _img else "linear-gradient(135deg,#0f0c29,#302b63)"
        st.html(f"""
            <div style="background:{_bg};border-radius:24px;padding:2.5rem 2rem;text-align:center;position:relative;overflow:hidden;min-height:380px;display:flex;align-items:flex-end;justify-content:center;">
                <div style="position:absolute;inset:0;border-radius:24px;background:linear-gradient(to top,rgba(8,8,16,0.85) 0%,rgba(8,8,16,0.3) 50%,rgba(8,8,16,0.1) 100%);"></div>
                <div style="position:absolute;inset:0;border-radius:24px;background:linear-gradient(135deg,rgba(99,102,241,0.25) 0%,rgba(236,72,153,0.2) 100%);"></div>
                <div style="position:relative;z-index:2;padding-bottom:1.5rem;">
                    <div style="font-family:'Syne',sans-serif;font-size:1.7rem;font-weight:800;color:#fff;line-height:1.2;margin-bottom:0.6rem;text-shadow:0 4px 20px rgba(0,0,0,0.5);">Know Your<br>True Worth</div>
                    <div style="font-family:'DM Sans',sans-serif;font-size:0.85rem;color:rgba(255,255,255,0.75);line-height:1.6;text-shadow:0 2px 8px rgba(0,0,0,0.4);">Real data. Real predictions.<br>Real career decisions.</div>
                </div>
            </div>
        """)

    st.html("<br>")

    # ══ FEATURES ══
    st.html('<div class="hp-eyebrow">Why use us</div>')
    st.html('<div class="hp-h2">Everything you need</div>')
    st.html('<div class="hp-lead">From raw survey data to precision predictions — we do the heavy lifting so you can focus on your career.</div>')
    st.html("<br>")

    f1, f2, f3 = st.columns(3, gap="large")
    with f1:
        st.html("""
            <div class="hp-fcard c-green">
                <div class="hp-fcard-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                    </svg>
                </div>
                <div class="hp-fcard-title">Data-Driven Insights</div>
                <div class="hp-fcard-text">Built on tens of thousands of real developer responses from the Stack Overflow annual salary survey.</div>
            </div>
        """)
    with f2:
        st.html("""
            <div class="hp-fcard c-blue">
                <div class="hp-fcard-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>
                    </svg>
                </div>
                <div class="hp-fcard-title">ML-Powered Accuracy</div>
                <div class="hp-fcard-text">Gradient-boosted model trained on real salaries, delivering predictions you can use in your next negotiation.</div>
            </div>
        """)
    with f3:
        st.html("""
            <div class="hp-fcard c-pink">
                <div class="hp-fcard-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#f472b6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                    </svg>
                </div>
                <div class="hp-fcard-title">Instant and Personalised</div>
                <div class="hp-fcard-text">Enter your profile once, get your number in milliseconds. Adjust any variable in real time.</div>
            </div>
        """)

    st.html("<br><br>")

    # ══ TESTIMONIALS MARQUEE ══
    st.html('<div class="hp-eyebrow">What developers say</div>')
    st.html('<div class="hp-h2">Trusted by developers worldwide</div>')
    st.html('<div class="hp-lead">From junior engineers negotiating their first offer to senior leads benchmarking against the market — every testimonial you see here has been approved by an admin.</div>')
    st.html("<br>")

    # Fetch only admin-approved reviews from the database
    all_reviews = get_approved_reviews()

    if not all_reviews:
        st.info("No testimonials have been approved yet. Be the first to leave a review after trying the salary predictor!")
        st.html("<br>")

    # Colour palette cycles across cards
    COLOURS = ["mq-c0", "mq-c1", "mq-c2", "mq-c3", "mq-c4"]
    AV_COLS  = ["mq-av0","mq-av1","mq-av2","mq-av3","mq-av4"]

    def _initials(name: str) -> str:
        parts = name.split()
        return (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else name[:2].upper()

    def _stars_html(rating: int) -> str:
        return "".join(
            '<span class="mq-star"></span>' if i < rating else '<span class="mq-star mq-star-empty"></span>'
            for i in range(5)
        )

    def _card_html(r: dict, idx: int) -> str:
        ci   = idx % len(COLOURS)
        av   = AV_COLS[ci]
        col  = COLOURS[ci]
        init = _initials(r["username"])
        stars = _stars_html(r["rating"])
        # Truncate to 220 chars for visual consistency
        text = r["review_text"][:220] + ("..." if len(r["review_text"]) > 220 else "")
        return f"""<div class="mq-card {col}">
  <p class="mq-text">{text}</p>
  <div class="mq-footer">
    <span class="mq-avatar {av}">{init}</span>
    <span>
      <span class="mq-name">{r["username"]}</span>
      <span class="mq-role">{r["role_title"]}</span>
      <span class="mq-stars">{stars}</span>
    </span>
  </div>
</div>"""

    # Build doubled card list for seamless loop
    cards_html = "".join(_card_html(r, i) for i, r in enumerate(all_reviews))
    cards_html_doubled = cards_html + cards_html   # duplicate for infinite loop

    st.html(f"""
        <div class="mq-outer">
            <div class="mq-track">
                {cards_html_doubled}
            </div>
        </div>
    """)

    st.html("<br><br>")

    # ══ REVIEW SUBMISSION FORM ══
    st.html("""
        <div class="rv-panel">
            <div class="rv-inner">
                <div class="rv-hdr-eye">Share your experience</div>
                <div class="rv-hdr-title">Leave a review</div>
                <div class="rv-hdr-sub">Tried the salary predictor? Tell other developers what you found. Reviews are approved within 24 hours.</div>
            </div>
        </div>
    """)

    # Form rendered outside the dark panel (Streamlit widgets can't live inside HTML)
    username  = st.session_state.get("username", "")
    is_logged = bool(username) and st.session_state.get("logged_in", False)

    if not is_logged:
        st.info("Log in to leave a review.")
    elif user_already_reviewed(username):
        st.success("You have already submitted a review — thank you.")
    else:
        with st.form("review_form", clear_on_submit=True):
            rv_role   = st.text_input("Your role / title",
                                       placeholder="e.g. Senior Frontend Engineer, London",
                                       max_chars=120)
            rv_text   = st.text_area("Your review",
                                      placeholder="Tell developers what you found useful...",
                                      max_chars=500, height=110)
            rv_rating = st.select_slider("Rating", options=[1, 2, 3, 4, 5], value=5,
                                          format_func=lambda x: "★" * x)
            submitted = st.form_submit_button("Submit Review", use_container_width=True,
                                               type="primary")
            if submitted:
                ok, msg = submit_review(username, rv_role, rv_text, rv_rating)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    st.html("<br><br>")

    # ══ CTA BANNER ══
    st.html('<div class="hp-cta-banner"><div class="hp-cta-title">Ready to discover your worth?</div><div class="hp-cta-sub">Join thousands of developers who have already discovered their market value.</div></div>')

    st.html("<br>")
    _, fc, _ = st.columns([2, 1.5, 2])
    with fc:
        if st.button("Get My Salary Estimate Now", use_container_width=True, type="primary"):
            st.session_state._force_nav = "Predict"
            st.rerun()

    st.html('<div class="hp-footer">Built with love using <b>Streamlit</b> &nbsp;·&nbsp; Data from <b>Stack Overflow Developer Survey</b> &nbsp;·&nbsp; <b>Free forever</b></div>')
