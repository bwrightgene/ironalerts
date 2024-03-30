import os
import imaplib
import email
import re
import requests
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

def create_alert(name, amount):
    url = "https://streamlabs.com/api/v2.0/alerts"
    access_token = os.environ.get("STREAMLABS_ACCESS_TOKEN")

    querystring = {
        "access_token": access_token,
        "type": "donation",
        "message": f"{name} donated {amount} towards the Iron Phi campaign!",
        "duration": "3000",
        "special_text_color": "Orange"
    }

    response = requests.post(url, params=querystring)
    print(f'Request URL: {response.url}')  # Show the full URL after the query string is applied
    print(f'Status Code: {response.status_code}')
    print(f'Response: {response.text}')

    if response.status_code == 200:
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            print('Failed to decode JSON from response.')
            return None
    else:
        print('Received non-200 status code.')
        return None

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
    print(f'Search status: {status}, Messages: {messages}')  # Debug print for email search
    if status == 'OK':
        for num in messages[0].split():
            status, data = mail.fetch(num, '(RFC822)')
            if status == 'OK':
                msg = email.message_from_bytes(data[0][1])

                body = None
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/html":
                            body = part.get_payload(decode=True).decode('utf-8')
                            break
                else:
                    body = msg.get_payload(decode=True).decode('utf-8')

                if body:
                    soup = BeautifulSoup(body, 'html.parser')
                    text_content = soup.get_text()  # Get the plain text content of the email

                    name_match = re.search(r"Name:\s*(.+)", text_content)
                    amount_match = re.search(r"Amount:\s*(.+)", text_content)

                    if name_match and amount_match:
                        name = name_match.group(1).strip()
                        amount = amount_match.group(1).strip()

                        print(f'Extracted Name: {name}, Amount: {amount}')  # Debug print for extracted data

                        # Create an alert using Streamlabs API v2.0
                        create_alert(name, amount)
                        alert_count += 1

                        # Mark email for deletion
                        mail.store(num, '+FLAGS', '\\Deleted')

    mail.expunge()
    mail.close()
    mail.logout()

    print(f'{alert_count} alerts sent.')
    time.sleep(30)
