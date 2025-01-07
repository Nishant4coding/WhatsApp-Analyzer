import re
import pandas as pd
import urlextract
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

# Function to generate DataFrame from chat file
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
    # Handle missing or invalid time values by filling them with a default time (e.g., '00:00')
    df['Time(U)'] = df['Time(U)'].apply(lambda x: x if re.match(r'\d{1,2}:\d{2}', x) else '00:00')

    # Convert 'Date' and 'Time(U)' to proper datetime format
    try:
        df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%y', errors='coerce')  # Handle date format like 12/10/24
        df['Time'] = pd.to_datetime(df['Time(U)'], format='%H:%M', errors='coerce').dt.time  # Handle time format like 22:05
    except Exception as e:
        print(f"Error processing Date/Time columns: {e}")

    # Fill NaT (invalid or missing values) with a default time (e.g., '00:00')
    df['Time'] = df['Time'].fillna('00:00')

    # Add new columns for year, month, day, and hour
    df['year'] = df['Date'].dt.year
    df['month'] = df['Date'].dt.month
    df['day'] = df['Date'].dt.day_name()
    
    # Safely extract hour by checking for NaT or missing time
    df['hour'] = df['Time'].apply(lambda x: int(str(x)[:2]) if pd.notna(x) else 0)  # Extract hour from time

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
def send_email_notification(sender_email, receiver_email, app_password, subject, body):
    msg = MIMEText(body, 'html')  # Send as HTML for better formatting
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender_email, app_password)
        smtp.sendmail(sender_email, receiver_email, msg.as_string())