import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from email_utils import send_email_notification
import functions
from textblob import TextBlob
from datetime import datetime, timedelta
from transformers import pipeline
import tensorflow as tf 



# # summarizer = pipeline("summarization", model="t5-small")
# def summarize_chat(chat_text):
#     summary = summarizer(chat_text, max_length=100, min_length=30, do_sample=False)
#     return summary[0]['summary_text']

st.title('WhatsApp Chat Analyzer')

# Upload file
file = st.file_uploader("Choose a WhatsApp Chat File", type=["txt"])

# Email content function
def create_email_content(reminders, df, links_dict):
    email_body = ""

    # Reminders
    if reminders:
        # chat_summary = summarize_chat(" ".join(reminders))
        email_body += "Here are your high-priority reminders:\n{chat_summary}\n"
        for reminder in reminders:
            email_body += f"- {reminder}\n"
            # Add urgent links to email body
    if urgent_links:
        email_body += "\nHere are your urgent links:\n"
        for link in urgent_links:
            email_body += f"- {link}\n"
            # email_body += f"- {link}\n"
    else:
        email_body += "No reminders found.\n"

    # Chat statistics
    total_messages = df.shape[0]
    total_words = df['Message'].apply(lambda x: len(x.split())).sum()
    media_shared = df['Media'].count() if 'Media' in df.columns else 0
    deleted_messages = df['Deleted'].count() if 'Deleted' in df.columns else 0

    email_body += f"\nChat Statistics:\nTotal Messages: {total_messages}\nTotal Words: {total_words}\n"
    email_body += f"Media Shared: {media_shared}\nMessages Deleted: {deleted_messages}\n"

    # Sentiment analysis
    df['Sentiment'] = df['Message'].apply(lambda x: TextBlob(x).sentiment.polarity)
    avg_sentiment = df['Sentiment'].mean()
    email_body += f"\nAverage Sentiment Score: {avg_sentiment:.2f}\n"

    # Active hour analysis
    df['DateTime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str), dayfirst=dayfirst)
    df['Hour'] = df['DateTime'].dt.hour
    most_active_hour = df['Hour'].value_counts().idxmax()
    email_body += f"Most Active Hour: {most_active_hour}:00\n"

    return email_body

if file:
    df = functions.generateDataFrame(file)
    
    try:
        # User selects date format in the text file
        dayfirst = st.radio("Select Date Format in Text File:", ('mm-dd-yy'))
        dayfirst = True if dayfirst == 'dd-mm-yy' else False

        users = functions.getUsers(df)
        users_s = st.sidebar.selectbox("Select User to View Analysis", users)
        selected_user = ""

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
            


            if reminders or urgent_links:
                email_content = create_email_content(reminders, df, urgent_links)
                try:
                    send_email_notification(
                        sender_email="nishant.21scse1010736@galgotiasuniversity.edu.in",
                        receiver_email="srivastava4nishant@gmail.com",
                        app_password="mvug rrbt gwwt ieei",
                        subject="WhatsApp Chat Analysis Insights",
                        body=email_content
                    )
                    st.success("Analysis insights sent via email successfully!")

                    # for reminder in reminders:
                    #     send_sms_twilio(
                    #         to_number="+918005151678",
                    #         message_body=f"Reminder: {reminder}"
                    #     )
                    # st.success("SMS alerts sent successfully!")

                except Exception as e:
                    st.error(f"Error sending email or SMS: {e}")
            else:
                st.warning("No reminders to send.")

            # Messaging frequency chart
            if selected_user == 'Everyone':
                user_counts = df['User'].value_counts().head()
                st.title("Messaging Frequency")
                st.subheader('User Messaging Percentages')
                col1, col2 = st.columns(2)
                with col1:
                    st.dataframe((df['User'].value_counts(normalize=True) * 100).round(2))
                with col2:
                    fig, ax = plt.subplots()
                    ax.bar(user_counts.index, user_counts.values)
                    ax.set_xlabel("Users")
                    ax.set_ylabel("Messages Sent")
                    plt.xticks(rotation='vertical')
                    st.pyplot(fig)
    except Exception as e:
        st.error(f"Error processing the file: {e}")
