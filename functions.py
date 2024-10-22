import pandas as pd
import re
import urlextract
# from textblob import TextBlob
# import smtplib
# from email.mime.text import MIMEText
# from twilio.rest import Client

# Generate DataFrame from uploaded file
def generateDataFrame(file):
    data = file.read().decode("utf-8").replace('\u202f', ' ').replace('\n', ' ')
    dt_format = r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s?(?:AM\s|PM\s|am\s|pm\s)?-\s'
    messages = re.split(dt_format, data)[1:]
    date_times = re.findall(dt_format, data)
    
    date, time, users, message = [], [], [], []
    for dt in date_times:
        date.append(re.search(r'\d{1,2}/\d{1,2}/\d{2,4}', dt).group())
        time.append(re.search(r'\d{1,2}:\d{2}\s?(?:AM|PM|am|pm)?', dt).group())

    for msg in messages:
        split_msg = re.split(r'([\w\W]+?):\s', msg)
        if len(split_msg) < 3:
            users.append("Notifications")
            message.append(split_msg[0])
        else:
            users.append(split_msg[1])
            message.append(split_msg[2])

    df = pd.DataFrame(list(zip(date, time, users, message)), columns=["Date", "Time(U)", "User", "Message"])
    return df

# Get unique users from chat data
def getUsers(df):
    users = df['User'].unique().tolist()
    users.sort()
    if 'Notifications' in users:
        users.remove('Notifications')
    users.insert(0, 'Everyone')
    return users

# Preprocess the data
def PreProcess(df, dayfirst):
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=dayfirst)
    df['Time'] = pd.to_datetime(df['Time(U)']).dt.time
    df['year'] = df['Date'].dt.year
    df['month'] = df['Date'].dt.month
    df['day'] = df['Date'].dt.day_name()
    df['hour'] = df['Time'].apply(lambda x: int(str(x)[:2]))
    return df

# Extract statistics, reminders, and links from chat data
def getStats(df):
    media = df[df['Message'] == "<Media omitted>"]
    media_count = media.shape[0]
    df.drop(media.index, inplace=True)

    deleted_msgs = df[df['Message'] == "This message was deleted"]
    deleted_msg_count = deleted_msgs.shape[0]
    df.drop(deleted_msgs.index, inplace=True)

    notifications = df[df['User'] == 'Notifications']
    df.drop(notifications.index, inplace=True)

    extractor = urlextract.URLExtract()
    links, reminders, urgent_links = [], [], []

    for msg in df['Message']:
        extracted_links = extractor.find_urls(msg)
        if extracted_links:
            links.extend(extracted_links)
            
            urgent_links_in_message = [link for link in extracted_links if "forms.google" in link or "meet.google" in link]
            
            if urgent_links_in_message:
                urgent_links.extend(urgent_links_in_message)
            
        if any(keyword in msg.lower() for keyword in ['reminder', 'urgent', 'asap', 'due']):
            reminders.append(msg)


    word_count = df['Message'].apply(lambda x: len(x.split())).sum()
    msg_count = df.shape[0]
    links_dict = {'all_links': links, 'reminders': reminders}

    return df, media_count, deleted_msg_count, len(links), word_count, msg_count, links_dict, reminders, urgent_links

# Send email notification
# def send_email_notification(sender_email, receiver_email, app_password, subject, body):
#     msg = MIMEText(body)
#     msg['Subject'] = subject
#     msg['From'] = sender_email
#     msg['To'] = receiver_email

#     with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
#         smtp.login(sender_email, app_password)
#         smtp.sendmail(sender_email, receiver_email, msg.as_string())

# # Send SMS via Twilio
# def send_sms_twilio(to_number, message_body):
#     account_sid = 'your_twilio_account_sid'
#     auth_token = 'your_twilio_auth_token'
#     client = Client(account_sid, auth_token)

#     message = client.messages.create(
#         body=message_body,
#         from_='+your_twilio_phone_number',
#         to=to_number
#     )
#     return message.sid
