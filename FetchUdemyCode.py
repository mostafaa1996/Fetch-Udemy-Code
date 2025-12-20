import imaplib
import email
import datetime
import re
import requests
import json
import os

GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
PHONE_NUMBER_ID = os.environ["PHONE_NUMBER_ID"]
TOKEN = os.environ["TOKEN"]
RECIPIENT = os.environ["RECIPIENT"]
Target = ""

STATE_FILE = "./last_email_id.json"

def load_last_id():
    if os.path.exists(STATE_FILE) and os.path.getsize(STATE_FILE) > 0:
        with open(STATE_FILE, "r") as f :
            return json.load(f).get("last_id")
    return None


def save_last_id(eid):
    # Convert bytes to string or int as needed
    if isinstance(eid, bytes):
        eid = eid.decode('utf-8')  # or int.from_bytes(eid, 'big')
    elif eid is None:
        eid = 0  # Default value
    with open(STATE_FILE, "w") as f:
        json.dump({"last_id": eid}, f)

def get_latest_email(subject_filter=None):
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
    mail.select("inbox")
    current_date = datetime.date.today()
    # yesterday = current_date - datetime.timedelta(days=7)
    # current_date_str = current_date.strftime('%Y-%m-%d')

    status, messages = mail.search(None, 'FROM "no-reply@e.udemymail.com" SINCE ' + current_date.strftime('%d-%b-%Y'))
    email_ids = messages[0].split()
    if not email_ids:
        return None, None, None

    latest = email_ids[-1]
    if isinstance(latest, bytes):
        latest = latest.decode('utf-8')  # or int.from_bytes(eid, 'big')

    last_saved = load_last_id()

    print(latest , "  *************  " , last_saved)

    if latest == last_saved:
        return None, None, None


    status, msg_data = mail.fetch(latest, "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])

    subject = msg["subject"]
    payload = ""

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True).decode()
    else:
        payload = msg.get_payload(decode=True).decode()

    save_last_id(latest)
    return latest, subject, payload


if __name__ == "__main__":
    latest, subject, payload = get_latest_email("ALERT")
    # print(latest , payload)
    if latest is None:
        print("No new email.")
        exit(0)
    print("**********************************************************")
    string  = payload
    print(string)
    match = re.search(r'\d{6}', string)
    if match:
         numerical_value = match.group()
        #  print(numerical_value)
         Target = numerical_value
    else:
         print("No numerical value found.")
    # print("**********************************************************")
    print(Target)
    if Target is None:
        Target = "No code available"
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": RECIPIENT,
        "type": "text",
        "text": {"body": Target}
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print("Status:", response.status_code)
    print("Response:", response.text)

