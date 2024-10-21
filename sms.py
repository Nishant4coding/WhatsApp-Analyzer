from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

def send_sms_twilio(to_number, message_body):
    # Twilio credentials
    account_sid = 'AC08c9a0a62fb011386762471336aaad5e'  # Twilio Account SID
    auth_token = 'ede3e56f2106d30f64d72f979322f71c'  # Twilio Auth Token
    twilio_phone_number = '+19842298210'  # Twilio phone number

    try:
        # Initialize the Twilio client
        client = Client(account_sid, auth_token)

        # Send SMS
        message = client.messages.create(
            body=message_body,
            from_=twilio_phone_number,
            to=to_number
        )

        print(f"Message sent successfully! Message SID: {message.sid}")
    except TwilioRestException as e:
        print(f"Failed to send message: {e}")
