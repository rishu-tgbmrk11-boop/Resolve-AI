# email_utils.py
import imaplib
import smtplib
import email
import re
from email.mime.text import MIMEText
from email.header import decode_header
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

# Max characters of the email body to send to the LLM
MAX_BODY_LENGTH = 1200

# Keywords that identify noise emails we don't want to process
NOISE_SENDER_KEYWORDS = ["no-reply", "noreply", "notifications", "alert", "google"]


def _clean_sender(from_field: str) -> str:
    """Extract just the email address from a From field like 'Name <email@x.com>'."""
    match = re.search(r"<(.+?)>", from_field)
    if match:
        return match.group(1).strip()
    return from_field.strip()


def _clean_body(body: str) -> str:
    """Remove URLs, extra whitespace, and trim the body to a reasonable length."""
    # Remove URLs
    body = re.sub(r"https?://\S+", "[link removed]", body)
    # Collapse multiple blank lines
    body = re.sub(r"\n\s*\n+", "\n\n", body)
    # Strip leading/trailing whitespace
    body = body.strip()
    # Truncate
    if len(body) > MAX_BODY_LENGTH:
        body = body[:MAX_BODY_LENGTH] + "... [truncated]"
    return body


def fetch_unread_emails() -> list:
    """Connects to Gmail IMAP and returns a list of cleaned, unread email dicts."""
    if not EMAIL_ADDRESS or not EMAIL_APP_PASSWORD:
        print("⚠️ Email credentials missing in .env")
        return []

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        mail.select("inbox")

        status, messages = mail.search(None, "UNSEEN")
        email_ids = messages[0].split()

        emails = []
        for e_id in email_ids:
            status, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])

                    # Decode subject
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")

                    # Clean sender
                    raw_from = msg.get("From", "")
                    sender_email = _clean_sender(raw_from)

                    # Skip obvious noise emails
                    if any(kw in sender_email.lower() for kw in NOISE_SENDER_KEYWORDS):
                        print(f"⏭️  Skipping noise email from {sender_email}")
                        continue

                    # Get body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode(errors="ignore")
                                break
                    else:
                        body = msg.get_payload(decode=True).decode(errors="ignore")

                    # Clean body
                    body = _clean_body(body)

                    emails.append({
                        "id": e_id.decode(),
                        "from": sender_email,
                        "subject": subject,
                        "body": body
                    })

        mail.logout()
        return emails

    except Exception as e:
        print(f"❌ IMAP error: {e}")
        return []


def send_reply(to_address: str, original_subject: str, reply_body: str) -> bool:
    """Sends a reply email using SMTP. Returns True on success."""
    if not EMAIL_ADDRESS or not EMAIL_APP_PASSWORD:
        print("⚠️ Email credentials missing in .env")
        return False

    try:
        msg = MIMEText(reply_body)
        msg["Subject"] = f"Re: {original_subject}"
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_address

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_address, msg.as_string())

        print(f"✅ Reply sent to {to_address}")
        return True

    except Exception as e:
        print(f"❌ SMTP error: {e}")
        return False