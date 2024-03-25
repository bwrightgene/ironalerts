import os
from dotenv import load_dotenv
import imaplib
import email
from bs4 import BeautifulSoup
import requests
import time

# Load environment variables from .env file
load_dotenv()

def create_alert(name, amount):
    url = 'https://streamlabs.com/api/v2.0/alerts'
    headers = {
        'Authorization': f'Bearer {os.environ.get("STREAMLABS_ACCESS_TOKEN")}'
    }
    payload = {
        'type': 'donation',
        'message': f'{name} donated {amount} towards the Iron Phi campaign!'
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

# Proton Mail Bridge credentials and settings
HOST = '127.0.0.1'
PORT = 1143
USERNAME = os.environ.get('ENV_EMAIL')
PASSWORD = os.environ.get('ENV_EMAIL_PW')
SENDER = 'ironphi@phideltatheta.org'

while True:
    alert_count = 0  # Initialize the count of alerts for this iteration

    # Connect to email server using STARTTLS
    mail = imaplib.IMAP4(HOST, PORT)
    mail.starttls()
    mail.login(USERNAME, PASSWORD)
    mail.select('inbox')

    # Search for emails from specific sender
    status, messages = mail.search(None, f'(FROM "{SENDER}")')
    if status == 'OK':
        for num in messages[0].split():
            status, data = mail.fetch(num, '(RFC822)')
            if status == 'OK':
                msg = email.message_from_bytes(data[0][1])
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/html":
                            body = part.get_payload(decode=True)
                            soup = BeautifulSoup(body, 'html.parser')
                            
                            name = soup.find(text="Name:").find_next().text.strip()
                            amount = soup.find(text="Amount:").find_next().text.strip()

                            # Create an alert using Streamlabs API v2.0
                            response = create_alert(name, amount)
                            alert_count += 1

                            # Mark email for deletion
                            mail.store(num, '+FLAGS', '\\Deleted')

    # Expunge to permanently remove emails marked for deletion
    mail.expunge()
    mail.close()
    mail.logout()

    print(f'{alert_count} alerts sent.')

    # Set the delay for how often it checks for donations
    time.sleep(30)
