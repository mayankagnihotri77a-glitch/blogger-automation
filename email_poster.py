import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_post_via_email(title, html_content):
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")
    receiver_email = os.getenv("BLOGGER_EMAIL")

    if not sender_email or not sender_password or not receiver_email:
        print("[X] Missing Email Credentials in .env")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = title
    msg["From"] = sender_email
    msg["To"] = receiver_email

    # Attach HTML Content
    # We wrap it in <html><body> to ensure Blogger treats it as HTML
    full_html = f"<html><body>{html_content}</body></html>"
    part = MIMEText(full_html, "html")
    msg.attach(part)

    try:
        print(f"   Connecting to SMTP (sending to {receiver_email})...")
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("[OK] Email Sent Successfully! (Blogger will publish it shortly)")
        return True
    except Exception as e:
        print(f"[X] Email Posting Failed: {e}")
        return False
