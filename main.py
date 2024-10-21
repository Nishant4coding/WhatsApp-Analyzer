import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from email_utils import send_email_notification
from sms import send_sms_twilio
import functions
from textblob import TextBlob

st.title('WhatsApp Chat Analyzer')

# File uploader for WhatsApp chat file
file = st.file_uploader("Choose a WhatsApp Chat File", type=["txt"])

# Function to create email content with additional insights
def create_email_content(reminders, df):
    email_body = ""

    # Adding reminders
    if reminders:
        email_body += "Here are your high-priority reminders:\n"
        for reminder in reminders:
            email_body += f"- {reminder}\n"
    else:
        email_body += "No reminders found.\n"

    # Chat Statistics
    email_body += "\nChat Statistics:\n"
    total_messages = df.shape[0]
    total_words = df['Message'].apply(lambda x: len(x.split())).sum()
    media_shared = df['Media'].count() if 'Media' in df.columns else 0
    deleted_messages = df['Deleted'].count() if 'Deleted' in df.columns else 0

    email_body += f"Total Messages: {total_messages}\n"
    email_body += f"Total Words: {total_words}\n"
    email_body += f"Media Shared: {media_shared}\n"
    email_body += f"Messages Deleted: {deleted_messages}\n"

    # Sentiment analysis
    df['Sentiment'] = df['Message'].apply(lambda x: TextBlob(x).sentiment.polarity)
    avg_sentiment = df['Sentiment'].mean()
    email_body += f"\nAverage Sentiment Score: {avg_sentiment:.2f}\n"

    # Active hours analysis
    df['Date'] = df['Date'].astype(str)  # Ensure 'Date' is a string
    df['Time'] = df['Time'].astype(str)  # Ensure 'Time' is a string

    df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], dayfirst=dayfirst)
    df['Hour'] = df['DateTime'].dt.hour

    hourly_activity = df['Hour'].value_counts().idxmax()
    email_body += f"\nMost Active Hour: {hourly_activity}:00\n"

    return email_body

if file:
    df = functions.generateDataFrame(file)
    try:
        # User selects date format in the text file
        dayfirst = st.radio("Select Date Format in Text File:", ('dd-mm-yy', 'mm-dd-yy'))
        dayfirst = True if dayfirst == 'dd-mm-yy' else False
        
        users = functions.getUsers(df)
        users_s = st.sidebar.selectbox("Select User to View Analysis", users)
        selected_user = ""

        if st.sidebar.button("Show Analysis"):
            selected_user = users_s
            st.title(f"Showing Results for: {selected_user}")

            df = functions.PreProcess(df, dayfirst)

            if selected_user != "Everyone":
                df = df[df['User'] == selected_user]

            df, media_cnt, deleted_msgs_cnt, links_cnt, word_count, msg_count, links_dict, reminders = functions.getStats(df)

            if reminders:
                try:
                    email_content = create_email_content(reminders, df)
                    send_email_notification(
                        sender_email="nishant.21scse1010736@galgotiasuniversity.edu.in",
                        receiver_email="srivastava4nishant@gmail.com",
                        app_password="mvug rrbt gwwt ieei",
                        subject="WhatsApp Chat Analysis Insights",
                        body=email_content
                    )
                    st.success("Analysis insights sent via email successfully!")

                    for reminder in reminders:
                        send_sms_twilio(
                            to_number="+918005151678",
                            message_body=f"Reminder: {reminder}"
                        )
                    st.success("SMS alerts sent successfully!")

                except Exception as e:
                    st.error(f"Error sending email or SMS: {e}")
            else:
                st.warning("No reminders to send.")

            if selected_user == 'Everyone':
                x = df['User'].value_counts().head()
                name = x.index
                count = x.values
                st.title("Messaging Frequency")
                st.subheader('Messaging Percentage Count of Users')
                col1, col2 = st.columns(2)
                with col1:
                    st.dataframe(round((df['User'].value_counts() / df.shape[0]) * 100, 2).reset_index().rename(
                        columns={'User': 'name', 'count': 'percent'}))
                with col2:
                    fig, ax = plt.subplots()
                    ax.bar(name, count)
                    ax.set_xlabel("Users")
                    ax.set_ylabel("Messages Sent")
                    plt.xticks(rotation='vertical')
                    st.pyplot(fig)

            # Emoji Analysis
            emojiDF = functions.getEmoji(df)
            st.title("Emoji Analysis")
            col1, col2 = st.columns(2)
            with col1:
                st.dataframe(emojiDF)
            with col2:
                fig, ax = plt.subplots()
                ax.pie(emojiDF[1].head(), labels=emojiDF[0].head(), autopct="%0.2f", shadow=True)
                plt.legend()
                st.pyplot(fig)

            # Common Word Analysis
            commonWord = functions.MostCommonWords(df)
            fig, ax = plt.subplots()
            ax.bar(commonWord[0], commonWord[1])
            ax.set_xlabel("Words")
            ax.set_ylabel("Frequency")
            plt.xticks(rotation='vertical')
            st.title('Most Frequent Words Used In Chat')
            st.pyplot(fig)

            # Monthly Timeline
            timeline = functions.getMonthlyTimeline(df)
            fig, ax = plt.subplots()
            ax.plot(timeline['time'], timeline['Message'])
            ax.set_xlabel("Month")
            ax.set_ylabel("Messages Sent")
            plt.xticks(rotation='vertical')
            st.title('Monthly Timeline')
            st.pyplot(fig)

            # Daily Timeline
            functions.dailytimeline(df)

            st.title('Most Busy Days')
            functions.WeekAct(df)
            st.title('Most Busy Months')
            functions.MonthAct(df)

            # WordCloud Visualization
            st.title("Wordcloud")
            df_wc = functions.create_wordcloud(df)
            fig, ax = plt.subplots()
            ax.imshow(df_wc)
            st.pyplot(fig)

            # Weekly Activity Map
            st.title("Weekly Activity Map")
            user_heatmap = functions.activity_heatmap(df)
            fig, ax = plt.subplots()
            ax = sns.heatmap(user_heatmap)
            st.pyplot(fig)

    except Exception as e:
        st.subheader("Unable to Process Your Request: " + str(e))
