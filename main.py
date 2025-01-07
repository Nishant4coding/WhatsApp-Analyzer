import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from wordcloud import WordCloud
import functions
from email_utils import send_email_notification
from functions import generateDataFrame

st.title('WhatsApp Chat Analyzer')

# Upload file
file = st.file_uploader("Choose a WhatsApp Chat File", type=["txt"])

# Apps Script URL for scheduling events
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyHFBgUNx7PCljn2g9EWCbeEaVzrr9megVgly338qmOTWt8k-g-5s9CW43YK03AJG4V/exec"

# Email content function
def create_email_content(reminders, df, links_dict):
    email_body = """
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <h2 style="color: #4CAF50;">WhatsApp Chat Insights</h2>
        <p style="font-size: 16px; color: #555;">Here are your chat analysis and insights:</p>
    """
    
    # Reminders Section
    if reminders:
        email_body += """
        <h3 style="color: #ff6347;">High-Priority Reminders:</h3>
        <ul style="list-style-type: none; padding: 0;">
        """
        for reminder in reminders:
            email_body += f'<li style="background-color: #f2f2f2; padding: 8px; margin-bottom: 5px; border-radius: 5px;">{reminder}</li>'
        email_body += "</ul>"
    else:
        email_body += "<p>No high-priority reminders found.</p>"

    # Urgent Links Section
    if links_dict:
        email_body += """
        <h3 style="color: #ff6347;">Urgent Links:</h3>
        <ul style="list-style-type: none; padding: 0;">
        """
        for link in links_dict:
            email_body += f'<li style="background-color: #f2f2f2; padding: 8px; margin-bottom: 5px; border-radius: 5px;"><a href="{link}" style="text-decoration: none; color: #1E90FF;">{link}</a></li>'
        email_body += "</ul>"
    else:
        email_body += "<p>No urgent links found.</p>"

    # Chat Statistics
    total_messages = df.shape[0]
    total_words = df['Message'].apply(lambda x: len(x.split())).sum()
    media_shared = df['Media'].count() if 'Media' in df.columns else 0
    deleted_messages = df['Deleted'].count() if 'Deleted' in df.columns else 0

    email_body += f"""
    <h3 style="color: #ff6347;">Chat Statistics:</h3>
    <ul style="list-style-type: none; padding: 0;">
        <li style="background-color: #f2f2f2; padding: 8px; margin-bottom: 5px; border-radius: 5px;">Total Messages: {total_messages}</li>
        <li style="background-color: #f2f2f2; padding: 8px; margin-bottom: 5px; border-radius: 5px;">Total Words: {total_words}</li>
        <li style="background-color: #f2f2f2; padding: 8px; margin-bottom: 5px; border-radius: 5px;">Media Shared: {media_shared}</li>
        <li style="background-color: #f2f2f2; padding: 8px; margin-bottom: 5px; border-radius: 5px;">Messages Deleted: {deleted_messages}</li>
    </ul>
    """

    # Most Active Hour
    df['DateTime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str), dayfirst=True)
    df['Hour'] = df['DateTime'].dt.hour
    most_active_hour = df['Hour'].value_counts().idxmax()
    email_body += f"<p>Most Active Hour: {most_active_hour}:00</p>"

    # Closing Section
    email_body += """
        <p style="color: #888; font-size: 14px;">Best Regards,<br>WhatsApp Chat Analyzer</p>
    </body>
    </html>
    """
    return email_body

# Function to send urgent links to the calendar
def schedule_event_with_appscript(email, link):
    payload = {
        "email": email,
        "link": link,
        "title": "Urgent Meeting",
        "description": "This is an urgent meeting scheduled via WhatsApp Chat Analyzer.",
        "start_time": (datetime.now() + timedelta(minutes=10)).isoformat() + "Z",
        "end_time": (datetime.now() + timedelta(minutes=70)).isoformat() + "Z"
    }

    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(APPS_SCRIPT_URL, json=payload, headers=headers)
        if response.status_code == 200 and response.json().get("status") == "success":
            return True, "Event scheduled successfully!"
        else:
            return False, response.json().get("message", "Failed to schedule event.")
    except Exception as e:
        return False, f"Error scheduling event: {e}"

if file:
    df = generateDataFrame(file)

    try:
        # User selects date format in the text file
        dayfirst = st.radio("Select Date Format in Text File:", ('mm-dd-yy'))
        dayfirst = True if dayfirst == 'dd-mm-yy' else False

        users = functions.getUsers(df)
        users_s = st.sidebar.selectbox("Select User to View Analysis", users)
        selected_user = ""

        # Receiver Email Input
        receiver_email = st.sidebar.text_input("Enter Receiver Email Address", "")

        # Filter Option: Time Range Selection
        st.sidebar.title("Select Time Range")
        time_range = st.sidebar.radio(
            "Choose the Time Range:",
            ('Today', 'This Week', 'This Month', 'All Time')
        )

        if st.sidebar.button("Show Analysis"):
            selected_user = users_s
            st.title(f"Showing Results for: {selected_user}")

            # Preprocess the data
            df = functions.PreProcess(df, dayfirst)

            if selected_user != "Everyone":
                df = df[df['User'] == selected_user]

            # Ensure 'Date' column is in datetime format
            df['Date'] = pd.to_datetime(df['Date'])

            # Convert 'Date' column to just the date part (without time)
            df['Date'] = df['Date'].dt.date

            today = datetime.now().date()

            # Filter based on selected time range
            if time_range == 'Today':
                df = df[df['Date'] == today]
            elif time_range == 'This Week':
                start_of_week = today - timedelta(days=today.weekday())
                df = df[df['Date'] >= start_of_week]
            elif time_range == 'This Month':
                start_of_month = today.replace(day=1)
                df = df[df['Date'] >= start_of_month]

            # Get stats
            df, media_cnt, deleted_msgs_cnt, links_cnt, word_count, msg_count, links_dict, urgent_links, reminders = functions.getStats(df)

            st.write(f"Time Range: {time_range}")
            st.write(f"Total Messages in Selected Range: {msg_count}")

            # Send email and schedule events for urgent links
            if urgent_links and receiver_email:
                for link in urgent_links:
                    success, message = schedule_event_with_appscript(receiver_email, link)
                    if success:
                        st.success(f"Scheduled urgent link to calendar: {link}")
                    else:
                        st.error(f"Failed to schedule link: {message}")

                email_content = create_email_content(reminders, df, urgent_links)
                try:
                    send_email_notification(
                        sender_email="nishant.21scse1010736@galgotiasuniversity.edu.in",
                        receiver_email=receiver_email,
                        app_password="mvug rrbt gwwt ieei",
                        subject="WhatsApp Chat Analysis Insights",
                        body=email_content
                    )
                    st.success("Analysis insights sent via email successfully!")
                except Exception as e:
                    st.error(f"Error sending email: {e}")
            elif not receiver_email:
                st.warning("Please enter a receiver email address to schedule events.")

    except Exception as e:
        st.error(f"Error processing the file: {e}")
