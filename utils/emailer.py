import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

def send_embed_script_email(to_email: str, bot_id: str):
    msg = EmailMessage()
    msg["Subject"] = "Your Custom Chatbot Embed Script"
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email

    script_tag = f"""<script src="https://www.upindersangha.com/widget.js" data-bot-id="{bot_id}"></script>"""

    msg.set_content(f"""Thanks for trying the chatbot tool!  
Here’s your script tag to embed your chatbot:

{script_tag}

Just paste this inside any HTML page where you want the bot to show up.

- Upinder""")

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(msg)
