import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email_notification(sender_email, receiver_email, app_password, subject, body):
    # Set up the MIME
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # Attach the body with the msg instance (HTML format)
    msg.attach(MIMEText(body, 'html'))

    # Set up the SMTP server and send the email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
    except Exception as e:
        raise Exception(f"Failed to send email: {e}")
