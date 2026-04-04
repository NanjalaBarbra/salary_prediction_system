"""
email_report.py
---------------
Generates a professional salary report PDF and sends it via Gmail SMTP.

Setup (one-time):
    1. Go to https://myaccount.google.com/apppasswords
    2. Generate an App Password for "Mail"
    3. Set these environment variables before running Streamlit:
         export SENDER_EMAIL="your_gmail@gmail.com"
         export SENDER_APP_PASSWORD="xxxx xxxx xxxx xxxx"
"""

import io
import os
from dotenv import load_dotenv
load_dotenv()  # loads SENDER_EMAIL and SENDER_APP_PASSWORD from .env file
import smtplib
import base64
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from dotenv import load_dotenv
load_dotenv()

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image as RLImage,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT


# ------------------------------------------------------------------ #
# PDF GENERATION
# ------------------------------------------------------------------ #

def _build_chart(df_hist: pd.DataFrame) -> io.BytesIO | None:
    """Render a salary trend chart and return it as a PNG BytesIO buffer."""
    if df_hist.empty:
        return None

    df = df_hist.copy()
    df["date_obj"] = pd.to_datetime(df["predicted_at"], errors="coerce")
    df = df.dropna(subset=["date_obj"]).sort_values("date_obj")
    if df.empty:
        return None

    fig, ax = plt.subplots(figsize=(6.5, 3))
    ax.plot(
        df["date_obj"],
        df["predicted_salary"],
        marker="o",
        linewidth=2,
        color="#5B9BD5",
        markerfacecolor="#fbbf24",
        markeredgecolor="#5B9BD5",
        markersize=6,
    )
    ax.fill_between(df["date_obj"], df["predicted_salary"], alpha=0.1, color="#5B9BD5")
    ax.set_xlabel("Date", fontsize=9, color="#6b7280")
    ax.set_ylabel("Predicted Salary (USD)", fontsize=9, color="#6b7280")
    ax.set_title("Salary Prediction Trend", fontsize=11, fontweight="bold", color="#1a202c")
    ax.tick_params(axis="x", rotation=30, labelsize=7)
    ax.tick_params(axis="y", labelsize=7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, _: f"${x:,.0f}")
    )
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    buf.seek(0)
    plt.close(fig)
    return buf


def generate_pdf(
    username: str,
    df_hist: pd.DataFrame,
    latest_salary: float,
    avg_sal: str,
    max_sal: str,
    min_sal: str,
    total_preds: int,
    mae: int = 10_000,
) -> io.BytesIO:
    """Build a polished salary report PDF and return it as a BytesIO buffer."""

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=26,
        textColor=colors.HexColor("#5B9BD5"),
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#6b7280"),
        spaceAfter=16,
        alignment=TA_CENTER,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#1a202c"),
        spaceBefore=16,
        spaceAfter=8,
        fontName="Helvetica-Bold",
        borderPad=4,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#374151"),
        spaceAfter=6,
        leading=16,
    )
    highlight_style = ParagraphStyle(
        "Highlight",
        parent=styles["Normal"],
        fontSize=22,
        textColor=colors.HexColor("#5B9BD5"),
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        spaceAfter=4,
    )

    story = []
    rep_date = datetime.now().strftime("%d %B %Y")

    # ---- Header ----
    story.append(Paragraph("Salary Prediction Report", title_style))
    story.append(Paragraph(f"Prepared for <b>{username}</b> &nbsp;|&nbsp; {rep_date}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#5B9BD5")))
    story.append(Spacer(1, 12))

    # ---- Summary metrics table ----
    story.append(Paragraph("Account Summary", section_style))

    summary_data = [
        ["Metric", "Value"],
        ["Username", username],
        ["Total Predictions Made", str(total_preds)],
        ["Average Predicted Salary", avg_sal],
        ["Highest Predicted Salary", max_sal],
        ["Lowest Predicted Salary", min_sal],
        ["Report Generated", rep_date],
    ]
    summary_table = Table(summary_data, colWidths=[2.8 * inch, 3.8 * inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5B9BD5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8faff"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 16))

    # ---- Latest prediction highlight ----
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e7eb")))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Latest Salary Estimate", section_style))

    est_min = max(0, latest_salary - mae)
    est_max = latest_salary + mae
    story.append(Paragraph(f"${latest_salary:,.2f}", highlight_style))
    story.append(Paragraph(
        f"Estimated range: <b>${est_min:,.0f}</b> &ndash; <b>${est_max:,.0f}</b>  "
        f"(based on a model margin of ±${mae:,})",
        body_style,
    ))
    story.append(Spacer(1, 14))

    # ---- Chart ----
    chart_buf = _build_chart(df_hist)
    if chart_buf:
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e7eb")))
        story.append(Spacer(1, 10))
        story.append(Paragraph("Prediction History", section_style))
        story.append(RLImage(chart_buf, width=6.2 * inch, height=2.8 * inch))
        story.append(Spacer(1, 10))

    # ---- Footer note ----
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e7eb")))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "This report was automatically generated by the Salary Prediction System. "
        "Salary estimates are based on historical data and machine learning models — "
        "actual salaries may vary.",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8,
                       textColor=colors.HexColor("#9ca3af"), alignment=TA_CENTER),
    ))

    doc.build(story)
    buf.seek(0)
    return buf


# ------------------------------------------------------------------ #
# EMAIL SENDING
# ------------------------------------------------------------------ #

def send_salary_report(
    recipient_email: str,
    username: str,
    pdf_buf: io.BytesIO,
) -> tuple[bool, str]:
    """
    Send the salary report PDF to recipient_email via Gmail SMTP.
    Returns (success: bool, message: str).
    """
    # Support both naming conventions
    sender_email = (os.environ.get("SENDER_EMAIL") or
                    os.environ.get("EMAIL_USER", ""))
    app_password = (os.environ.get("SENDER_APP_PASSWORD") or
                    os.environ.get("EMAIL_PASSWORD", ""))
    email_host   = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
    email_port   = int(os.environ.get("EMAIL_PORT", 587))

    if not sender_email or not app_password:
        return False, (
            "Email credentials not configured. "
            "Set EMAIL_USER and EMAIL_PASSWORD in your .env file."
        )

    try:
        msg = MIMEMultipart()
        msg["From"] = f"Salary Prediction App <{sender_email}>"
        msg["To"] = recipient_email
        msg["Subject"] = f"Your Salary Prediction Report — {datetime.now().strftime('%d %B %Y')}"

        body = f"""Hi {username},

Please find attached your personalised salary prediction report generated by the Salary Prediction App.

The report includes:
  • Your account summary and prediction history
  • Your latest salary estimate with a confidence range
  • A chart showing your salary trend over time

If you have any questions, feel free to revisit the app and run a new prediction.

Best regards,
The Salary Prediction App Team
"""
        msg.attach(MIMEText(body, "plain"))

        # Attach PDF
        pdf_part = MIMEBase("application", "octet-stream")
        pdf_part.set_payload(pdf_buf.read())
        encoders.encode_base64(pdf_part)
        pdf_part.add_header(
            "Content-Disposition",
            f'attachment; filename="Salary_Report_{username}.pdf"',
        )
        msg.attach(pdf_part)

        # Support Port 465 (SSL) or 587 (STARTTLS)
        if email_port == 465:
            server = smtplib.SMTP_SSL(email_host, email_port, timeout=15)
        else:
            server = smtplib.SMTP(email_host, email_port, timeout=15)
            server.starttls()

        with server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())

        return True, f"Report sent successfully to {recipient_email}!"

    except (smtplib.SMTPConnectError, TimeoutError, ConnectionError) as e:
        return False, (
            f"Network Error: Connection timed out or refused. "
            f"Your current Wi-Fi or Firewall may be blocking {email_host} on port {email_port}. "
            "Try changing your Wi-Fi or updating your .env to use EMAIL_PORT=465."
        )
    except smtplib.SMTPAuthenticationError:
        return False, "Gmail authentication failed. Check your SENDER_EMAIL and SENDER_APP_PASSWORD (use an App Password)."
    except smtplib.SMTPException as e:
        return False, f"Email Error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"
