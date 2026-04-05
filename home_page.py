import streamlit as st
from reviews import get_approved_reviews, submit_review, user_already_reviewed


def show_home_page():

    st.html("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

    .main .block-container { padding-top: 0 !important; max-width: 100% !important; }
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body, .stApp {
        font-family: 'DM Sans', sans-serif;
        background: #f0f2f4;
        color: #6b7c8d;
    }

    /* ══════════════════════════════════════════
       HERO
    ══════════════════════════════════════════ */
    .hero-shell {
        padding: 1.4rem 1.4rem 0;
        max-width: 1280px;
        margin: 0 auto;
    }
    .hero {
        display: none;
    }
    .hero-rich {
        position: relative;
        overflow: hidden;
        padding: 4.4rem 3rem 4.8rem;
        background:
            radial-gradient(circle at top left, rgba(240,242,244,0.22) 0%, transparent 26%),
            radial-gradient(circle at bottom right, rgba(217,228,238,0.16) 0%, transparent 30%),
            linear-gradient(135deg, #4a6b8a 0%, #3e5f7d 52%, #2d4a6b 100%);
        border-radius: 32px;
        color: #ffffff;
        box-shadow: 0 28px 70px rgba(45, 74, 107, 0.22);
    }
    .hero-rich::before {
        content: "";
        position: absolute;
        width: 360px;
        height: 360px;
        right: -120px;
        top: -120px;
        border-radius: 50%;
        background: rgba(255,255,255,0.08);
        filter: blur(6px);
    }
    .hero-rich::after {
        content: "";
        position: absolute;
        inset: auto auto -70px -90px;
        width: 280px;
        height: 280px;
        border-radius: 50%;
        background: rgba(255,255,255,0.06);
    }
    .hero-grid {
        position: relative;
        z-index: 2;
        display: grid;
        grid-template-columns: minmax(0, 1.15fr) minmax(300px, 0.85fr);
        gap: 2.4rem;
        align-items: flex-start;
    }
    .hero-copy {
        text-align: left;
        max-width: 640px;
    }
    .hero-badge {
        display: inline-flex; align-items: flex-start; gap: 6px;
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 9999px;
        padding: 6px 15px;
        font-size: 0.72rem; font-weight: 600;
        color: #f0f2f4; background: rgba(255,255,255,0.08);
        margin-bottom: 1.3rem;
        letter-spacing: 0.04em;
        backdrop-filter: blur(10px);
    }
    .hero-dot {
        width: 7px; height: 7px; border-radius: 50%;
        background: #f0f2f4;
        display: inline-block;
    }
    .hero-h1 {
        font-size: clamp(2.2rem, 4vw, 3.6rem);
        font-weight: 800;
        color: #ffffff;
        line-height: 1.1;
        letter-spacing: -0.04em;
        max-width: 680px;
        margin: 0 0 1.1rem;
    }
    .hero-h1 span { color: #d9e4ee; }
    .hero-sub {
        font-size: 1.04rem;
        color: rgba(240,242,244,0.88);
        line-height: 1.8;
        max-width: 520px;
        margin: 0;
    }
    .hero-actions {
        display: flex;
        gap: 0.9rem;
        flex-wrap: wrap;
        margin-top: 1.8rem;
    }
    .hero-chip {
        display: inline-flex;
        align-items: flex-start;
        gap: 0.5rem;
        padding: 0.8rem 1rem;
        border-radius: 16px;
        background: rgba(255,255,255,0.10);
        border: 1px solid rgba(255,255,255,0.14);
        color: #f0f2f4;
        font-size: 0.82rem;
        font-weight: 600;
        backdrop-filter: blur(10px);
    }
    .hero-chip strong {
        font-size: 0.98rem;
        color: #ffffff;
    }
    .hero-learn-more {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-top: 0.9rem;
        padding: 0.42rem 0.95rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #12354d 0%, #0b2436 100%);
        border: 1px solid rgba(255,255,255,0.10);
        color: #ffffff !important;
        font-size: 0.68rem;
        font-weight: 700;
        text-decoration: none !important;
        letter-spacing: 0.01em;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 20px rgba(5,16,26,0.28);
        transition: transform 0.18s ease, background 0.18s ease, border-color 0.18s ease;
    }
    .hero-learn-more:hover {
        transform: translateY(-1px);
        background: linear-gradient(135deg, #184663 0%, #102d42 100%);
        border-color: rgba(255,255,255,0.16);
    }
    .hero-visual {
        position: relative;
        min-height: 580px !important;
    }
    
    .hero-card-main {
        overflow: hidden !important;
        position: absolute !important;
        right: 0 !important;
        top: 0px !important;
        width: min(100%, 480px) !important; min-height: 480px !important;
        padding: 1.4rem !important;
        box-shadow: 0 24px 55px rgba(14, 30, 46, 0.26) !important;
        color: #1a2e42 !important;
        z-index: 10 !important;
        background: transparent !important; /* Move background to ::before */
        border: 1px solid rgba(255,255,255,0.42) !important;
        border-radius: 28px !important;
    }

    .hero-card-top {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        margin-bottom: 1rem;
    }
    .hero-card-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #6b7c8d;
        font-weight: 700;
    }
    .hero-card-pill {
        font-size: 0.72rem;
        font-weight: 700;
        color: #2d4a6b;
        background: #eaf0f5;
        padding: 0.42rem 0.7rem;
        border-radius: 999px;
    }
    .hero-salary-box {
        background: linear-gradient(135deg, #1a2e42 0%, #2d4a6b 100%);
        color: #ffffff;
        border-radius: 22px;
        padding: 1.3rem 1.2rem;
        margin-bottom: 1rem;
    }
    .hero-salary-caption {
        color: rgba(240,242,244,0.76);
        font-size: 0.76rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.35rem;
    }
    .hero-salary-value {
        font-size: clamp(1.9rem, 3vw, 2.7rem);
        font-weight: 800;
        line-height: 1;
        letter-spacing: -0.04em;
    }
    .hero-salary-range {
        margin-top: 0.55rem;
        font-size: 0.83rem;
        color: rgba(240,242,244,0.7);
    }
    .hero-mini-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.8rem;
        margin-bottom: 1rem;
    }
    .hero-mini-card {
        background: #f6f9fb;
        border: 1px solid #e0e7ed;
        border-radius: 18px;
        padding: 0.95rem;
    }
    .hero-mini-title {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #6b7c8d;
        margin-bottom: 0.4rem;
    }
    .hero-mini-value {
        font-size: 1.1rem;
        font-weight: 800;
        color: #1a2e42;
    }
    .hero-mini-sub {
        font-size: 0.78rem;
        color: #6b7c8d;
        margin-top: 0.2rem;
        line-height: 1.45;
    }
    .hero-bars {
        display: flex;
        align-items: flex-end;
        gap: 0.45rem;
        height: 70px;
        margin-top: 0.7rem;
    }
    .hero-bar {
        flex: 1;
        border-radius: 12px 12px 4px 4px;
        background: linear-gradient(180deg, #7c98b3 0%, #4a6b8a 100%);
    }
    .hero-float {
        position: absolute;
        display: flex;
        flex-direction: column;
        gap: 0.2rem;
        padding: 0.95rem 1rem;
        border-radius: 18px;
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(255,255,255,0.18);
        box-shadow: 0 16px 35px rgba(17, 33, 48, 0.18);
        backdrop-filter: blur(10px);
        color: #ffffff;
    }
    .hero-float-top {
        right: 260px;
        top: 0;
    }
    .hero-float-bottom {
        left: 10px;
        bottom: 18px;
    }
    .hero-float-label {
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: rgba(240,242,244,0.7);
    }
    .hero-float-value {
        font-size: 1.15rem;
        font-weight: 800;
        line-height: 1;
    }
    .hero-float-sub {
        font-size: 0.78rem;
        color: rgba(240,242,244,0.82);
    }
    .hero-stats {
        max-width: 1180px;
        margin: -2rem auto 2.8rem;
        padding: 0 1.6rem;
        position: relative;
        z-index: 4;
    }
    .hero-stats-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 1rem;
    }
    .hero-stat-card {
        background: rgba(255,255,255,0.92);
        border: 1px solid rgba(74, 107, 138, 0.14);
        border-radius: 22px;
        padding: 1.1rem 1.15rem;
        box-shadow: 0 20px 50px rgba(45, 74, 107, 0.10);
    }
    .hero-stat-value {
        font-size: 1.5rem;
        font-weight: 800;
        color: #1a2e42;
        line-height: 1;
        margin-bottom: 0.35rem;
    }
    .hero-stat-label {
        font-size: 0.8rem;
        color: #6b7c8d;
        line-height: 1.5;
    }
    .section-intro {
        max-width: 1200px;
        margin: 0 auto 1.35rem;
        padding: 0 2rem;
        display: flex;
        align-items: end;
        justify-content: space-between;
        gap: 1.2rem;
    }
    .section-intro-copy {
        max-width: 620px;
    }
    .section-eyebrow {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        color: #4a6b8a;
        margin-bottom: 0.45rem;
    }
    .section-title {
        font-size: clamp(1.55rem, 2.3vw, 2.2rem);
        font-weight: 800;
        color: #1a2e42;
        letter-spacing: -0.03em;
        line-height: 1.1;
        margin-bottom: 0.45rem;
    }
    .section-sub {
        font-size: 0.95rem;
        line-height: 1.75;
        color: #6b7c8d;
    }
    .section-badge {
        background: #ffffff;
        border: 1px solid #dce5ec;
        border-radius: 18px;
        padding: 0.9rem 1rem;
        min-width: 220px;
        box-shadow: 0 14px 34px rgba(45, 74, 107, 0.08);
    }
    .section-badge-title {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.11em;
        color: #6b7c8d;
        margin-bottom: 0.35rem;
    }
    .section-badge-text {
        font-size: 0.9rem;
        color: #1a2e42;
        line-height: 1.55;
    }

    /* ══════════════════════════════════════════
       GRID CONTAINER
    ══════════════════════════════════════════ */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.5rem;
        padding: 0 2rem 3rem;
        max-width: 1200px;
        margin: 2.5rem auto 0;
    }
    @media (max-width: 900px) {
        .grid-container { grid-template-columns: 1fr; padding: 0 1rem 2rem; }
    }

    /* ══════════════════════════════════════════
       FEATURE CARD
    ══════════════════════════════════════════ */
    .feature-card {
        background: #ffffff;
        border: 1px solid rgba(74, 107, 138, 0.18);
        border-radius: 16px;
        overflow: hidden;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        cursor: pointer;
    }
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 48px rgba(45, 74, 107, 0.14);
    }

    /* ── IMAGE CONTAINER ── */
    .image-container {
        width: 100%;
        aspect-ratio: 4/3;
        position: relative;
        overflow: hidden;
    }
    .placeholder-image {
        width: 100%; height: 100%;
        display: flex; align-items: flex-start; justify-content: center;
        flex-direction: column;
        gap: 0.8rem;
        position: relative;
    }
    .placeholder-image svg {
        width: 48px; height: 48px; opacity: 0.9;
    }
    .placeholder-image-label {
        font-size: 0.8rem; font-weight: 600;
        color: rgba(255,255,255,0.6);
        text-transform: uppercase; letter-spacing: 0.1em;
    }

    /* card colour themes */
    .card-predict  .placeholder-image { background: linear-gradient(135deg, #1a2e42 0%, #2d4a6b 55%, #4a6b8a 100%); }
    .card-skillgap .placeholder-image { background: linear-gradient(135deg, #23384f 0%, #3a5570 55%, #4a6b8a 100%); }
    .card-explore  .placeholder-image { background: linear-gradient(135deg, #2d425d 0%, #3a5570 55%, #5a7a98 100%); }

    /* salary preview inside predict card */
    .prev-salary {
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 10px;
        padding: 1rem 1.2rem;
        text-align: center;
        min-width: 180px;
    }
    .prev-salary-amt {
        font-size: 1.9rem; font-weight: 800;
        color: #fff; letter-spacing: -0.04em; line-height: 1;
    }
    .prev-salary-lbl {
        font-size: 0.68rem; color: rgba(255,255,255,0.45);
        margin-top: 3px; text-transform: uppercase; letter-spacing: 0.08em;
    }
    .prev-bar-wrap { display:flex; gap:3px; margin-top:0.7rem; }
    .prev-bar { height: 3px; border-radius: 2px; }

    /* skill bars inside skillgap card */
    .prev-skill-list { display:flex; flex-direction:column; gap:0.5rem; width:100%; padding:0 1.5rem; }
    .prev-skill-row  { display:flex; align-items:center; justify-content:space-between; }
    .prev-skill-name { font-size:0.75rem; color:#fff; font-weight:500; }
    .prev-skill-pct  { font-size:0.75rem; color:#d9e4ee; font-weight:700; }
    .prev-skill-bg   { height:3px; border-radius:2px; background:rgba(255,255,255,0.1); margin-top:3px; }
    .prev-skill-fill { height:3px; border-radius:2px; background:#d9e4ee; }

    /* chart bars inside explore card */
    .prev-chart { display:flex; align-items:flex-end; gap:5px; height:80px; padding:0 1.5rem; width:100%; }
    .prev-chart-bar { flex:1; border-radius:3px 3px 0 0; background:rgba(255,255,255,0.2); }
    .prev-chart-bar.hi { background:#d9e4ee; }

    /* ── INFO SECTION ── */
    .info-section {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        padding: 1rem 1.2rem;
        border-top: 1px solid #e0e6eb;
        gap: 0.8rem;
    }

    /* Avatar */
    .avatar {
        width: 36px; height: 36px;
        border-radius: 50%;
        display: flex; align-items: flex-start; justify-content: center;
        font-size: 0.78rem; font-weight: 700;
        color: #fff; flex-shrink: 0;
    }
    .av-predict  { background: #2d4a6b; }
    .av-skillgap { background: #3a5570; }
    .av-explore  { background: #4a6b8a; }

    /* Title Text */
    .title-text {
        flex: 1;
        min-width: 0;
    }
    .title-text-main {
        font-size: 0.9rem; font-weight: 700;
        color: #1a2e42;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .title-text-sub {
        font-size: 0.72rem; color: #6b7c8d;
        margin-top: 2px;
    }

    /* Bookmark Button */
    .bookmark-btn {
        display: flex; align-items: flex-start; gap: 4px;
        flex-shrink: 0;
        background: #f0f2f4;
        border-radius: 8px;
        padding: 5px 10px;
        cursor: pointer;
        transition: background 0.15s;
    }
    .bookmark-btn:hover { background: #e1e7ec; }
    .bookmark-btn svg { width: 14px; height: 14px; color: #4a6b8a; }
    .bookmark-count {
        font-size: 0.75rem; font-weight: 600;
        color: #3a5570;
    }


    /* ══════════════════════════════════════════
       TESTIMONIALS
    ══════════════════════════════════════════ */
    .mq-section { padding: 0 2rem 3rem; max-width: 1200px; margin: 0 auto; }
    .mq-top { text-align:center; margin-bottom:1.5rem; }
    .mq-eyebrow { font-size:0.7rem; font-weight:600; letter-spacing:0.16em; text-transform:uppercase; color:#4a6b8a; margin-bottom:0.3rem; }
    .mq-h2 { font-size:clamp(1.4rem,2.2vw,1.9rem); font-weight:800; color:#1a2e42; letter-spacing:-0.03em; }
    .mq-outer { position:relative; overflow:hidden; width:100%; padding:0.4rem 0; }
    .mq-outer::before,.mq-outer::after { content:''; position:absolute; top:0; bottom:0; width:80px; z-index:2; pointer-events:none; }
    .mq-outer::before { left:0; background:linear-gradient(to right,#f0f2f4,transparent); }
    .mq-outer::after  { right:0; background:linear-gradient(to left,#f0f2f4,transparent); }
    .mq-track { display:flex; gap:0.9rem; width:max-content; animation:mq-scroll 38s linear infinite; }
    .mq-track:hover { animation-play-state:paused; }
    @keyframes mq-scroll { from{transform:translateX(0);} to{transform:translateX(calc(-50% - 0.45rem));} }
    .mq-card { flex-shrink:0; width:280px; background:#fff; border:1px solid #d7e0e8; border-radius:13px; padding:1.2rem 1.3rem; position:relative; }
    .mq-card::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; border-radius:13px 13px 0 0; }
    .mq-c0::before{background:linear-gradient(90deg,#2d4a6b,#4a6b8a);}
    .mq-c1::before{background:linear-gradient(90deg,#3a5570,#5a7a98);}
    .mq-c2::before{background:linear-gradient(90deg,#1a2e42,#4a6b8a);}
    .mq-c3::before{background:linear-gradient(90deg,#2d4a6b,#6b8aa7);}
    .mq-c4::before{background:linear-gradient(90deg,#3a5570,#7d96ad);}
    .mq-text { font-size:0.83rem; line-height:1.75; color:#6b7c8d; margin-bottom:0.9rem; display:-webkit-box; -webkit-line-clamp:4; -webkit-box-orient:vertical; overflow:hidden; }
    .mq-footer { display:flex; align-items:center; gap:0.6rem; border-top:1px solid #e1e7ec; padding-top:0.8rem; }
    .mq-avatar { width:30px; height:30px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; font-size:0.7rem; font-weight:700; color:#fff; flex-shrink:0; }
    .mq-av0{background:#2d4a6b;}
    .mq-av1{background:#3a5570;}
    .mq-av2{background:#4a6b8a;}
    .mq-av3{background:#1a2e42;}
    .mq-av4{background:#5a7a98;}
    .mq-name { font-size:0.81rem; font-weight:700; color:#1a2e42; display:block; }
    .mq-role { font-size:0.71rem; color:#6b7c8d; display:block; margin-top:1px; }
    .mq-stars { display:inline-flex; gap:2px; margin-top:3px; }
    .mq-star { width:7px; height:7px; border-radius:1px; background:#4a6b8a; display:inline-block; }
    .mq-star-empty { background:#e4e4e7; }

    /* ══════════════════════════════════════════
       REVIEW FORM
    ══════════════════════════════════════════ */
    .rv-panel {
        background: linear-gradient(135deg, #1a2e42 0%, #2d4a6b 100%); border-radius: 16px;
        padding: 2.2rem 2rem; position: relative; overflow: hidden;
        margin: 0 2rem 3rem; max-width: 1200px;
    }
    .rv-panel::before {
        content:''; position:absolute; inset:0;
        background:radial-gradient(ellipse 60% 80% at 0% 50%,rgba(240,242,244,0.10) 0%,transparent 60%);
        pointer-events:none;
    }
    .rv-inner { position:relative; z-index:2; }
    .rv-eye   { font-size:0.7rem; font-weight:600; letter-spacing:0.16em; text-transform:uppercase; color:#d9e4ee; margin-bottom:0.3rem; }
    .rv-title { font-size:clamp(1.4rem,2.2vw,1.9rem); font-weight:800; color:#fff; letter-spacing:-0.03em; line-height:1.15; margin-bottom:0.3rem; }
    .rv-sub   { font-size:0.83rem; color:rgba(240,242,244,0.72); line-height:1.6; }

    /* ══════════════════════════════════════════
       CTA
    ══════════════════════════════════════════ */
    .cta-panel {
        background: linear-gradient(135deg, #2d4a6b 0%, #3a5570 45%, #4a6b8a 100%);
        border-radius: 16px; padding: 2.5rem 2rem;
        text-align: center; margin: 0 2rem 2rem;
        max-width: 1200px;
    }
    .cta-title { font-size:clamp(1.4rem,2.2vw,1.9rem); font-weight:800; color:#fff; letter-spacing:-0.03em; margin-bottom:0.5rem; }
    .cta-sub   { font-size:0.86rem; color:rgba(240,242,244,0.82); line-height:1.65; }

    .home-footer {
        margin: 2.5rem 2rem 1rem;
        max-width: 1200px;
        background: #ffffff;
        border: 1px solid #d7e0e8;
        border-radius: 20px;
        padding: 3.6rem 2.2rem 2.8rem;
        box-shadow: 0 20px 45px rgba(45, 74, 107, 0.10);
    }
    .home-footer-main {
        display: grid;
        grid-template-columns: 1.35fr 1.7fr 0.9fr;
        gap: 2rem;
        align-items: start;
    }
    .home-footer-brand {
        display: flex;
        flex-direction: column;
        gap: 0.9rem;
    }
    .home-footer-logo {
        width: 46px;
        height: 46px;
        border-radius: 14px;
        display: inline-flex;
        align-items: flex-start;
        justify-content: center;
        background: linear-gradient(135deg, #2d4a6b 0%, #4a6b8a 100%);
        color: #ffffff;
        font-size: 1rem;
        font-weight: 800;
        box-shadow: 0 14px 28px rgba(45, 74, 107, 0.22);
    }
    .home-footer-title {
        font-size: 1.05rem;
        font-weight: 800;
        color: #1a2e42;
        letter-spacing: -0.02em;
    }
    .home-footer-desc {
        max-width: 320px;
        font-size: 0.82rem;
        line-height: 1.75;
        color: #6b7c8d;
    }
    .home-footer-links {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 1.2rem;
    }
    .home-footer-group-title {
        margin-bottom: 0.85rem;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #4a6b8a;
    }
    .home-footer-link-list {
        display: flex;
        flex-direction: column;
        gap: 0.62rem;
    }
    .home-footer-link {
        font-size: 0.82rem;
        color: #3a5570;
        text-decoration: none;
        transition: color 0.2s ease, transform 0.2s ease;
    }
    .home-footer-link:hover {
        color: #1a2e42;
        transform: translateX(2px);
    }
    .home-footer-socials {
        display: flex;
        flex-direction: column;
        gap: 0.85rem;
    }
    .home-footer-social-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.75rem;
    }
    .home-footer-social {
        display: inline-flex;
        align-items: flex-start;
        justify-content: center;
        min-height: 42px;
        border-radius: 12px;
        border: 1px solid #d7e0e8;
        background: #f0f2f4;
        color: #3a5570;
        text-decoration: none;
        font-size: 0.8rem;
        font-weight: 700;
        transition: transform 0.2s ease, border-color 0.2s ease, background 0.2s ease, color 0.2s ease;
    }
    .home-footer-social:hover {
        transform: translateY(-2px);
        border-color: #4a6b8a;
        background: #e6edf3;
        color: #1a2e42;
    }
    .home-footer-bottom {
        margin-top: 1.5rem;
        padding-top: 1rem;
        border-top: 1px solid #d7e0e8;
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 1rem;
        flex-wrap: wrap;
    }
    .home-footer-copy {
        font-size: 0.78rem;
        color: #6b7c8d;
    }
    .home-footer-legal {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        flex-wrap: wrap;
    }
    .home-footer-legal a {
        font-size: 0.78rem;
        color: #3a5570;
        text-decoration: none;
    }
    .home-footer-legal a:hover {
        color: #1a2e42;
    }
    @media (max-width: 920px) {
        .hero-rich {
            padding: 3.4rem 1.4rem 4.2rem;
        }
        .hero-grid {
            grid-template-columns: 1fr;
        }
        .hero-copy {
            text-align: center;
            max-width: none;
        }
        .hero-h1,
        .hero-sub {
            margin-left: auto;
            margin-right: auto;
        }
        .hero-actions {
            justify-content: center;
        }
        .hero-visual {
            min-height: 320px;
            margin-top: 0.6rem;
        }
        
    .hero-card-main {
        overflow: hidden !important;
        position: absolute !important;
        right: 0 !important;
        top: 0px !important;
        width: min(100%, 480px) !important; min-height: 480px !important;
        padding: 1.4rem !important;
        box-shadow: 0 24px 55px rgba(14, 30, 46, 0.26) !important;
        color: #1a2e42 !important;
        z-index: 10 !important;
        background: transparent !important; /* Move background to ::before */
        border: 1px solid rgba(255,255,255,0.42) !important;
        border-radius: 28px !important;
    }

        .hero-float-top {
            right: 14px;
            top: -10px;
        }
        .hero-float-bottom {
            left: 14px;
            bottom: -8px;
        }
        .hero-stats {
            margin-top: -1.7rem;
        }
        .hero-stats-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .section-intro {
            flex-direction: column;
            align-items: flex-start;
        }
        .home-footer-main {
            grid-template-columns: 1fr;
        }
        .home-footer-links {
            grid-template-columns: 1fr;
        }
        .home-footer-social-grid {
            grid-template-columns: repeat(4, minmax(0, 1fr));
        }
    }
    @media (max-width: 640px) {
        .hero-shell {
            padding: 0.9rem 0.9rem 0;
        }
        .hero-rich {
            border-radius: 24px;
            padding: 2.9rem 1.1rem 4.2rem;
        }
        .hero-visual {
            min-height: 290px;
        }
        .hero-mini-grid,
        .hero-stats-grid {
            grid-template-columns: 1fr;
        }
        .hero-float {
            position: relative;
            margin-top: 0.75rem;
        }
        .hero-float-top,
        .hero-float-bottom {
            inset: auto;
        }
        .hero-stats {
            padding: 0 1rem;
        }
        .section-intro {
            padding: 0 1rem;
        }
        .home-footer {
            margin: 2rem 1rem 1rem;
            padding: 2.8rem 1.2rem 2.1rem;
        }
        .home-footer-social-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .home-footer-bottom {
            align-items: flex-start;
            flex-direction: column;
        }
    }

    

    
    /* Stacking layers for transparency + image */
    .hero-card-main::before {
        content: "" !important;
        position: absolute !important;
        top: 0 !important; left: 0 !important; right: 0 !important; bottom: 0 !important;
        background: rgba(255,255,255,0.96) !important;
        z-index: -2 !important;
    }
    .hero-card-main::after {
        content: "" !important;
        position: absolute !important;
        top: 0 !important; right: 0 !important; bottom: 0 !important; left: 0 !important;
        background-image: url("data:image/jpeg;base64,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") !important;
        background-size: contain !important;
        background-position: right center !important;
        background-repeat: no-repeat !important;
        opacity: 0.35 !important; /* Increased for visibility */
        z-index: -1 !important;
        pointer-events: none !important;
    }


    
    .hero-market-section {
        margin-top: 1.8rem !important;
        border-top: 1px solid rgba(0,0,0,0.06) !important;
        padding-top: 1.5rem !important;
    }

    .hero-market-bars {
        display: flex !important;
        align-items: flex-end !important;
        justify-content: space-between !important;
        height: 110px !important;
        margin-top: 1.5rem !important;
        padding: 0 15px !important;
    }
    .hero-market-bar {
        width: 60px !important;
        background: linear-gradient(180deg, #185FA5 0%, #0D47A1 100%) !important;
        border-radius: 8px 8px 4px 4px !important;
        position: relative !important;
        transition: height 0.6s ease !important;
    }
    .hero-market-bar::after {
        content: attr(data-label) !important;
        position: absolute !important;
        bottom: -24px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        font-size: 0.7rem !important;
        color: #4a5568 !important;
        font-weight: 600 !important;
        white-space: nowrap !important;
    }

    </style>
    """)

    # ══ HERO ══════════════════════════════════════════════════════════════════
    st.html("""
        <div class="hero">
            <div class="hero-badge">
                <span class="hero-dot"></span>
                Stack Overflow Developer Survey 2025
            </div>
            <h1 class="hero-h1">
                Predict Your <span>Developer Salary</span><br>with Real Data
            </h1>
            <p class="hero-sub">
                Stop guessing what you are worth. Get data-driven salary predictions
                tailored to your skills, experience, and location — in seconds.
            </p>
        </div>
    """)

    # ══ GRID CONTAINER — 3 Feature Cards ══════════════════════════════════════
    st.html("""
        <div class="hero-shell">
            <div class="hero-rich">
                <div class="hero-grid">
                    <div class="hero-copy">
                        <div class="hero-badge">
                            <span class="hero-dot"></span>
                            Stack Overflow Developer Survey 2025
                        </div>
                        <h1 class="hero-h1">
                            Understand Your <span>Market Value</span><br>Before Your Next Move
                        </h1>
                        <p class="hero-sub">
                            Turn your skills, experience, location, and stack into a confident salary benchmark.
                            Explore what you could earn now, and what to learn next to grow faster.
                        </p>
                        <div class="hero-actions">
                            <div class="hero-chip"><strong>49K+</strong> salary data points</div>
                            <div class="hero-chip"><strong>180+</strong> countries compared</div>
                            <div class="hero-chip"><strong>ML</strong> prediction engine</div>
                        </div>
                        <a class="hero-learn-more" href="https://stackoverflow.blog/2017/05/09/introducing-stack-overflow-trends/" target="_blank" rel="noopener noreferrer">Learn more</a>
                    </div>
                    <div class="hero-visual">
                        <div class="hero-float hero-float-top">
                            <span class="hero-float-label">Top Uplift</span>
                            <span class="hero-float-value">+18.4%</span>
                            <span class="hero-float-sub">Rust + cloud infra</span>
                        </div>
                        <div class="hero-card-main">
                            <div class="hero-card-top">
                                <span class="hero-card-label">Salary Snapshot</span>
                                <span class="hero-card-pill">Live estimate</span>
                            </div>
        """)


    st.html("""
                            
                        <div class="hero-market-section">
                            <div class="hero-card-label">Market Landscape</div>
                            <div class="hero-market-bars">
                                <div class="hero-market-bar" style="height: 35%;" data-label="Junior" data-value="$52K"></div>
                                <div class="hero-market-bar" style="height: 58%;" data-label="Mid" data-value="$89K"></div>
                                <div class="hero-market-bar" style="height: 82%;" data-label="Senior" data-value="$124K"></div>
                                <div class="hero-market-bar" style="height: 100%;" data-label="Lead" data-value="$168K"></div>
                            </div>
                        </div>


                        </div>
                    </div>
                </div>
            </div>
    """)

    st.html("""
        <div class="hero-stats">
            <div class="hero-stats-grid">
                <div class="hero-stat-card">
                    <div class="hero-stat-value">10K+</div>
                    <div class="hero-stat-label">Survey-backed salary records used to train the model and benchmark roles.</div>
                </div>
                <div class="hero-stat-card">
                    <div class="hero-stat-value">3 Views</div>
                    <div class="hero-stat-label">Prediction, market exploration, and skill-gap guidance in one workflow.</div>
                </div>
                <div class="hero-stat-card">
                    <div class="hero-stat-value">Fast</div>
                    <div class="hero-stat-label">Get a salary estimate in seconds without digging through fragmented salary sites.</div>
                </div>
                <div class="hero-stat-card">
                    <div class="hero-stat-value">Actionable</div>
                    <div class="hero-stat-label">See how your stack, location, and next skills can shift your earning potential.</div>
                </div>
            </div>
        </div>
    """)

    st.html("""
        <div class="section-intro">
            <div class="section-intro-copy">
                <div class="section-eyebrow">Everything in one place</div>
                <div class="section-title">Explore salary intelligence, not just a single number</div>
                <div class="section-sub">
                    The homepage now leads with clearer value, stronger visuals, and a quicker sense
                    of what each part of the app helps users do next.
                </div>
            </div>
            <div class="section-badge">
                <div class="section-badge-title">Why it matters</div>
                <div class="section-badge-text">Users can benchmark today, discover opportunities, and plan their next learning move from the same screen.</div>
            </div>
        </div>
    """)

    st.html(f"""
        <div class="grid-container">

            <!-- ─── CARD 1: Predict Salary ─── -->
            <div class="feature-card card-predict">

                <!-- Image Container -->
                <div class="image-container">
                    <div class="placeholder-image">
                        <div class="prev-salary">
                            <div class="prev-salary-amt">{f"${st.session_state.prediction:,.0f}" if "prediction" in st.session_state else "---"}</div>
                            <div class="prev-salary-lbl">Estimated salary</div>
                            <div class="prev-bar-wrap">
                                <div class="prev-bar" style="flex:1;background:rgba(255,255,255,0.12);"></div>
                                <div class="prev-bar" style="flex:2.4;background:#60a5fa;"></div>
                                <div class="prev-bar" style="flex:0.8;background:rgba(255,255,255,0.12);"></div>
                            </div>
                        </div>
                        <div style="display:flex;gap:5px;margin-top:0.5rem;">
                            <span style="background:rgba(255,255,255,0.1);border-radius:5px;padding:3px 8px;font-size:0.65rem;color:rgba(255,255,255,0.6);">Python</span>
                            <span style="background:rgba(255,255,255,0.1);border-radius:5px;padding:3px 8px;font-size:0.65rem;color:rgba(255,255,255,0.6);">5 yrs</span>
                            <span style="background:rgba(255,255,255,0.1);border-radius:5px;padding:3px 8px;font-size:0.65rem;color:rgba(255,255,255,0.6);">Kenya</span>
                        </div>
                    </div>
                </div>

                <!-- Info Section -->
                <div class="info-section">
                    <!-- Avatar -->
                    <div class="avatar av-predict">SP</div>
                    <!-- Title Text -->
                    <div class="title-text">
                        <div class="title-text-main">Predict Salary</div>
                        <div class="title-text-sub">ML-powered · XGBoost · R² 0.63</div>
                    </div>
                    <!-- Bookmark Button -->
                    <div class="bookmark-btn">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
                        </svg>
                        <span class="bookmark-count">49K</span>
                    </div>
                </div>
            </div>

            <!-- ─── CARD 2: Skill Gap ─── -->
            <div class="feature-card card-skillgap">

                <!-- Image Container -->
                <div class="image-container">
                    <div class="placeholder-image">
                        <div style="width:100%;padding:0 1.5rem;">
                            <div style="font-size:0.65rem;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.7rem;text-align:center;">Salary uplift by skill</div>
                        </div>
                        <div class="prev-skill-list">
                            <div>
                                <div class="prev-skill-row">
                                    <span class="prev-skill-name">Rust</span>
                                    <span class="prev-skill-pct">+18.4%</span>
                                </div>
                                <div class="prev-skill-bg"><div class="prev-skill-fill" style="width:82%;"></div></div>
                            </div>
                            <div>
                                <div class="prev-skill-row">
                                    <span class="prev-skill-name">Kubernetes</span>
                                    <span class="prev-skill-pct">+14.2%</span>
                                </div>
                                <div class="prev-skill-bg"><div class="prev-skill-fill" style="width:65%;"></div></div>
                            </div>
                            <div>
                                <div class="prev-skill-row">
                                    <span class="prev-skill-name">TypeScript</span>
                                    <span class="prev-skill-pct">+11.7%</span>
                                </div>
                                <div class="prev-skill-bg"><div class="prev-skill-fill" style="width:52%;"></div></div>
                            </div>
                            <div>
                                <div class="prev-skill-row">
                                    <span class="prev-skill-name">Go</span>
                                    <span class="prev-skill-pct">+9.3%</span>
                                </div>
                                <div class="prev-skill-bg"><div class="prev-skill-fill" style="width:40%;"></div></div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Info Section -->
                <div class="info-section">
                    <div class="avatar av-skillgap">SG</div>
                    <div class="title-text">
                        <div class="title-text-main">Skill Gap Analysis</div>
                        <div class="title-text-sub">Career growth · Uplift calculator</div>
                    </div>
                    <div class="bookmark-btn">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
                        </svg>
                        <span class="bookmark-count">180+</span>
                    </div>
                </div>
            </div>

            <!-- ─── CARD 3: Explore Data ─── -->
            <div class="feature-card card-explore">

                <!-- Image Container -->
                <div class="image-container">
                    <div class="placeholder-image">
                        <div style="width:100%;padding:0 1.5rem;">
                            <div style="font-size:0.65rem;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.7rem;text-align:center;">Median salary by country</div>
                        </div>
                        <div class="prev-chart">
                            <div class="prev-chart-bar" style="height:38%;"></div>
                            <div class="prev-chart-bar hi" style="height:100%;"></div>
                            <div class="prev-chart-bar" style="height:75%;"></div>
                            <div class="prev-chart-bar" style="height:88%;"></div>
                            <div class="prev-chart-bar" style="height:55%;"></div>
                            <div class="prev-chart-bar" style="height:42%;"></div>
                            <div class="prev-chart-bar" style="height:65%;"></div>
                            <div class="prev-chart-bar" style="height:30%;"></div>
                        </div>
                        <div style="display:flex;gap:5px;margin-top:0.8rem;padding:0 1.5rem;flex-wrap:wrap;justify-content:center;">
                            <span style="background:rgba(255,255,255,0.08);border-radius:5px;padding:3px 8px;font-size:0.65rem;color:rgba(255,255,255,0.5);">49K+ responses</span>
                            <span style="background:rgba(255,255,255,0.08);border-radius:5px;padding:3px 8px;font-size:0.65rem;color:rgba(255,255,255,0.5);">180+ countries</span>
                        </div>
                    </div>
                </div>

                <!-- Info Section -->
                <div class="info-section">
                    <div class="avatar av-explore">EX</div>
                    <div class="title-text">
                        <div class="title-text-main">Explore Data</div>
                        <div class="title-text-sub">Market insights · SO Survey 2025</div>
                    </div>
                    <div class="bookmark-btn">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
                        </svg>
                        <span class="bookmark-count">49K</span>
                    </div>
                </div>
            </div>

        </div>
    """)

    # ══ TESTIMONIALS ══════════════════════════════════════════════════════════
    SEED_REVIEWS = [
        {"username": "Arjun Kapoor",  "role_title": "Senior Backend Engineer, Berlin",  "review_text": "I had no idea I was being underpaid by nearly $18,000 a year until I ran my profile through this tool. Walked into my next review with the data and came out with a significant raise.", "rating": 5},
        {"username": "Sofia Mendes",  "role_title": "Full Stack Developer, Lisbon",      "review_text": "The what-if simulator is genuinely useful. I tested adding Python to my stack and immediately saw the projected salary impact. It helped me prioritise exactly what to learn next.",    "rating": 5},
        {"username": "Thomas Walsh",  "role_title": "Engineering Manager, Toronto",      "review_text": "As a hiring manager I recommended this to every candidate who pushed back on our offers. It gave both sides an objective reference point and made negotiations much smoother.",          "rating": 5},
        {"username": "Lena Fischer",  "role_title": "DevOps Engineer, Munich",           "review_text": "Accurate, fast, and free. I compared the prediction against three job offers I had at the time and it was spot on for two of them. This is now my first stop before any interview.",   "rating": 5},
        {"username": "Marcus Osei",   "role_title": "Android Developer, Accra",          "review_text": "Finally a tool that accounts for country and tech stack together. Most salary calculators only consider one or the other. The breakdown by region is incredibly useful.",               "rating": 4},
        {"username": "Priya Sharma",  "role_title": "Data Scientist, Bangalore",         "review_text": "Used this before negotiating a remote role with a US company. The country comparison feature alone was worth it — helped me understand the gap and make a confident counter-offer.",    "rating": 5},
    ]
    all_reviews = get_approved_reviews()
    COLOURS = ["mq-c0","mq-c1","mq-c2","mq-c3","mq-c4"]
    AV_COLS  = ["mq-av0","mq-av1","mq-av2","mq-av3","mq-av4"]

    def _initials(name):
        parts = name.split()
        return (parts[0][0]+parts[-1][0]).upper() if len(parts) >= 2 else name[:2].upper()

    def _stars(r):
        return "".join('<span class="mq-star"></span>' if i < r else '<span class="mq-star mq-star-empty"></span>' for i in range(5))

    def _card(r, idx):
        ci   = idx % 5
        text = r["review_text"][:220]+("..." if len(r["review_text"])>220 else "")
        return f"""<div class="mq-card {COLOURS[ci]}">
  <p class="mq-text">{text}</p>
  <div class="mq-footer">
    <span class="mq-avatar {AV_COLS[ci]}">{_initials(r["username"])}</span>
    <span><span class="mq-name">{r["username"]}</span>
    <span class="mq-role">{r["role_title"]}</span>
    <span class="mq-stars">{_stars(r["rating"])}</span></span>
  </div>
</div>"""

    cards = "".join(_card(r, i) for i, r in enumerate(all_reviews))

    st.html(f"""
        <div class="mq-section">
            <div class="mq-top">
                <div class="mq-eyebrow">What developers say</div>
                <div class="mq-h2">Trusted by developers worldwide</div>
            </div>
            <div class="mq-outer">
                <div class="mq-track">{cards}{cards}</div>
            </div>
        </div>
    """)

    # ══ REVIEW FORM ═══════════════════════════════════════════════════════════
    st.html("""
        <div class="rv-panel">
            <div class="rv-inner">
                <div class="rv-eye">Share your experience</div>
                <div class="rv-title">Leave a review</div>
                <div class="rv-sub">Tried the salary predictor? Tell other developers what you found. Reviews are approved within 24 hours.</div>
            </div>
        </div>
    """)

    username  = st.session_state.get("username", "")
    is_logged = bool(username) and st.session_state.get("logged_in", False)

    if not is_logged:
        st.info("Log in to leave a review.")
    elif user_already_reviewed(username):
        st.success("You have already submitted a review — thank you.")
    else:
        with st.form("review_form", clear_on_submit=True):
            rv_role   = st.text_input("Your role / title", placeholder="e.g. Senior Frontend Engineer, London", max_chars=120)
            rv_text   = st.text_area("Your review", placeholder="Tell developers what you found useful...", max_chars=500, height=110)
            rv_rating = st.select_slider("Rating", options=[1,2,3,4,5], value=5, format_func=lambda x:"★"*x)
            submitted = st.form_submit_button("Submit Review", use_container_width=True, type="primary")
            if submitted:
                ok, msg = submit_review(username, rv_role, rv_text, rv_rating)
                st.success(msg) if ok else st.error(msg)

    # ══ CTA ═══════════════════════════════════════════════════════════════════
    st.html("""
        <div class="cta-panel">
            <div class="cta-title">Ready to discover your worth?</div>
            <div class="cta-sub">Join thousands of developers who have already discovered their market value.</div>
        </div>
    """)

    st.html("""
        <div class="home-footer">
            <div class="home-footer-main">
                <div class="home-footer-brand">
                    <div class="home-footer-logo">SP</div>
                    <div class="home-footer-title">Salary Predictor</div>
                    <div class="home-footer-desc">
                        Data-driven salary insights for developers, powered by survey data,
                        machine learning, and practical career planning tools.
                    </div>
                </div>
                <div class="home-footer-links">
                    <div>
                        <div class="home-footer-group-title">Product</div>
                        <div class="home-footer-link-list">
                            <a class="home-footer-link" href="#">Overview</a>
                            <a class="home-footer-link" href="#">Pricing</a>
                            <a class="home-footer-link" href="#">Marketplace</a>
                            <a class="home-footer-link" href="#">Features</a>
                        </div>
                    </div>
                    <div>
                        <div class="home-footer-group-title">Company</div>
                        <div class="home-footer-link-list">
                            <a class="home-footer-link" href="#">About</a>
                            <a class="home-footer-link" href="#">Team</a>
                            <a class="home-footer-link" href="#">Blog</a>
                            <a class="home-footer-link" href="#">Careers</a>
                        </div>
                    </div>
                    <div>
                        <div class="home-footer-group-title">Resources</div>
                        <div class="home-footer-link-list">
                            <a class="home-footer-link" href="#">Help Center</a>
                            <a class="home-footer-link" href="#">Sales</a>
                            <a class="home-footer-link" href="#">Advertise</a>
                            <a class="home-footer-link" href="#">Privacy</a>
                        </div>
                    </div>
                </div>
                <div class="home-footer-socials">
                    <div class="home-footer-group-title">Social Links</div>
                    <div class="home-footer-social-grid">
                        <a class="home-footer-social" href="#" aria-label="Instagram">Instagram</a>
                        <a class="home-footer-social" href="#" aria-label="Facebook">Facebook</a>
                        <a class="home-footer-social" href="#" aria-label="Twitter">Twitter</a>
                        <a class="home-footer-social" href="#" aria-label="LinkedIn">LinkedIn</a>
                    </div>
                </div>
            </div>
            <div class="home-footer-bottom">
                <div class="home-footer-copy">Copyright 2026 Salary Predictor. All rights reserved.</div>
                <div class="home-footer-legal">
                    <a href="#">Terms &amp; Conditions</a>
                    <a href="#">Privacy Policy</a>
                </div>
            </div>
        </div>
    """)
