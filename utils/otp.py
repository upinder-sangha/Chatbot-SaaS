import os
import random
import smtplib
import html
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

# Simple in-memory storage for OTPs (in production, use Redis or database)
otp_storage = {}


def generate_otp():
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))


def store_otp(email: str, otp: str, expiry_minutes: int = 10):
    """Store OTP with expiry time"""
    expiry_time = datetime.now() + timedelta(minutes=expiry_minutes)
    otp_storage[email] = {"otp": otp, "expiry": expiry_time, "verified": False}


def verify_otp(email: str, otp: str) -> bool:
    """Verify if OTP is valid and not expired"""
    if email not in otp_storage:
        return False

    stored_data = otp_storage[email]

    # Check if OTP is expired
    if datetime.now() > stored_data["expiry"]:
        del otp_storage[email]
        return False

    # Check if OTP matches
    if stored_data["otp"] == otp:
        stored_data["verified"] = True
        return True

    return False


def is_verified(email: str) -> bool:
    """Check if email has been verified"""
    return email in otp_storage and otp_storage[email]["verified"]


def send_otp_email(to_email: str, otp: str) -> None:
    """Send OTP verification email"""
    safe_to_email = html.escape(to_email)

    # Create multipart/alternative email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your Docative Verification Code"
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg["Reply-To"] = SENDER_EMAIL
    msg["MIME-Version"] = "1.0"

    # HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verify Your Email</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .container {{
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 30px;
                text-align: center;
                border: 1px solid #e9ecef;
            }}
            .logo {{
                font-size: 24px;
                font-weight: bold;
                color: #6366f1;
                margin-bottom: 20px;
            }}
            .code {{
                font-size: 36px;
                font-weight: bold;
                color: #4f46e5;
                letter-spacing: 8px;
                margin: 30px 0;
                padding: 15px;
                background-color: #f0f1ff;
                border-radius: 8px;
                display: inline-block;
            }}
            .message {{
                margin-bottom: 30px;
                font-size: 16px;
            }}
            .footer {{
                margin-top: 30px;
                font-size: 12px;
                color: #6c757d;
            }}
            .button {{
                display: inline-block;
                background-color: #6366f1;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                text-decoration: none;
                font-weight: bold;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">Docative</div>
            <h2>Verify Your Email Address</h2>
            <div class="message">
                <p>Thank you for creating a chatbot with Docative! To complete your setup, please enter the verification code below on the website:</p>
            </div>
            <div class="code">{otp}</div>
            <div class="message">
                <p>This code will expire in 10 minutes for security reasons.</p>
                <p>If you didn't request this code, please ignore this email.</p>
            </div>
            <div class="footer">
                <p>© {datetime.now().year} Docative. All rights reserved.</p>
                <p>This is an automated message, please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Attach HTML content
    html_part = MIMEText(html_content, "html")
    msg.attach(html_part)

    # Send email
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
