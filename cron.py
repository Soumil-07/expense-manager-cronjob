import os
import re
import imaplib
import email
from bs4 import BeautifulSoup
from datetime import datetime
import psycopg2

# --- ENV Vars ---

IMAP_HOST = "imap.gmail.com"
IMAP_USER = os.getenv("EMAIL_USER")       # your Gmail address
IMAP_PASS = os.getenv("EMAIL_PASS")       # Gmail App Password
DEFAULT_ACCOUNT_ID = 1                    # map all transactions here
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

# Patterns
amount_pattern = r"Rs\.?\s?([\d,]+\.\d{2})"
date_pattern   = r"on\s+(\d{2}-\d{2}-\d{2})"
type_pattern   = r"\b(credited|debited)\b"

DEFAULT_ACCOUNT_ID = 1

def parse_transaction(body: str):
    amount_match = re.search(amount_pattern, body, re.IGNORECASE)
    date_match   = re.search(date_pattern, body, re.IGNORECASE)
    type_match   = re.search(type_pattern, body, re.IGNORECASE)

    if not (amount_match and date_match and type_match):
        print("❌ Could not parse email:\n", body)
        return None

    txn_type = type_match.group(1).lower()
    amount = float(amount_match.group(1).replace(",", ""))
    # Correctly parse DD-MM-YY
    date_obj = datetime.strptime(date_match.group(1), "%d-%m-%y")
    account_id = DEFAULT_ACCOUNT_ID

    return {
        "type": "income" if txn_type == "credited" else "expense",
        "amount": amount,
        "category": "Uncategorized",
        "title": "New Transaction",
        "account_id": account_id,
        "date": date_obj,
        "tags": []
    }


def get_email_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                body = part.get_payload(decode=True).decode(errors="ignore")
                break
            elif ctype == "text/html":
                html = part.get_payload(decode=True).decode(errors="ignore")
                body = BeautifulSoup(html, "html.parser").get_text(separator=" ")
                break
    else:
        payload = msg.get_payload(decode=True).decode(errors="ignore")
        if msg.get_content_type() == "text/html":
            body = BeautifulSoup(payload, "html.parser").get_text(separator=" ")
        else:
            body = payload
    return " ".join(body.split())  # normalize whitespace


def save_transaction(conn, txn):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO transactions (type, amount, category, title, account_id, date, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (txn["type"], txn["amount"], txn["category"], txn["title"],
             txn["account_id"], txn["date"], txn["tags"])
        )
    conn.commit()


def main():
    # --- Connect IMAP ---
    mail = imaplib.IMAP4_SSL(IMAP_HOST)
    mail.login(IMAP_USER, IMAP_PASS)
    mail.select("inbox")

    # Fetch unread HDFC alerts
    status, messages = mail.search(None, '(UNSEEN FROM "alerts@hdfcbank.net")')
    email_ids = messages[0].split()

    if not email_ids:
        print("📭 No new emails.")
        return

    # --- Connect DB ---
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

    for eid in email_ids:
        res, msg_data = mail.fetch(eid, "(RFC822)")
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        body = get_email_body(msg)
        print(body)
        txn = parse_transaction(body)
        print(txn)

        if txn:
            save_transaction(conn, txn)
            print("✅ Saved transaction:", txn)
            # Mark email as read
            mail.store(eid, '+FLAGS', '\\Seen')

    conn.close()
    mail.logout()


if __name__ == "__main__":
    main()

