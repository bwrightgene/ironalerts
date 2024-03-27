import os
import imaplib
import email
import re
import requests
import time

from dotenv import load_dotenv
load_dotenv()

def create_alert(name, amount):
    url = 'https://streamlabs.com/api/v2.0/alerts'
    headers = {'Authorization': f'Bearer {os.environ.get("STREAMLABS_ACCESS_TOKEN")}'}
    payload = {'type': 'donation', 'message': f'{name} donated {amount} towards the Iron Phi campaign!'}
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

# Email server settings
HOST = '127.0.0.1'
PORT = 1143
USERNAME = os.environ.get('ENV_EMAIL')
PASSWORD = os.environ.get('ENV_EMAIL_PW')
SENDER = 'ironphi@phideltatheta.org'

while True:
    alert_count = 0

    mail = imaplib.IMAP4(HOST, PORT)
    mail.starttls()
    mail.login(USERNAME, PASSWORD)
    mail.select('inbox')

    status, messages = mail.search(None, f'(FROM "{SENDER}")')
    if status == 'OK':
        for num in messages[0].split():
            status, data = mail.fetch(num, '(RFC822)')
            if status == 'OK':
                msg = email.message_from_bytes(data[0][1])

                # Assuming the email is now plain text
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode('utf-8')

                            # Extract name and amount using regular expressions or string processing
                            name_match = re.search(r"Name:\s*(.*)", body)
                            amount_match = re.search(r"Amount:\s*(.*)", body)

                            if name_match and amount_match:
                                name = name_match.group(1).strip()
                                amount = amount_match.group(1).strip()

                                print(f'Name: {name}, Amount: {amount}')

                                # Create an alert using Streamlabs API v2.0
                                response = create_alert(name, amount)
                                print(response)
                                alert_count += 1

                                # Mark email for deletion
                                mail.store(num, '+FLAGS', '\\Deleted')

    # Expunge to remove emails marked for deletion
    mail.expunge()
    mail.close()
    mail.logout()

    print(f'{alert_count} alerts sent.')
    time.sleep(60)  # Wait for 60 seconds before the next iteration
