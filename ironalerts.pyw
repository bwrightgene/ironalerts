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
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending alert: {e}")
        return None

while True:
    alert_count = 0  # Initialize the count of alerts for this iteration

    # Proton Mail Bridge credentials and settings
    HOST = '127.0.0.1'
    PORT = 1143
    USERNAME = os.environ.get('ENV_EMAIL')
    PASSWORD = os.environ.get('ENV_EMAIL_PW')

    try:
        # Connect to email server using STARTTLS
        mail = imaplib.IMAP4(HOST, PORT)
        mail.starttls()
        mail.login(USERNAME, PASSWORD)
        mail.select('inbox')

        # Search for emails from specific sender
        SENDER = 'ironphi@phideltatheta.org'
        SUBJECT = "You've Received an Iron Phi Donation!"
        criteria = '(FROM "{}" SUBJECT "{}")'.format(SENDER, SUBJECT)
        status, response = mail.search(None, criteria)

        if status == 'OK':
            email_ids = response[0].split()
            for email_id in email_ids:
                status, data = mail.fetch(email_id, '(RFC822)')
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
                                if response:
                                    alert_count += 1

                                # Mark email for deletion
                                mail.store(email_id, '+FLAGS', '\\Deleted')

        # Expunge to permanently remove emails marked for deletion
        mail.expunge()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        mail.close()
        mail.logout()

    print(f'{alert_count} alerts sent.')

    time.sleep(30)
