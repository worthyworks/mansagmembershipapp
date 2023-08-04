import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import yagmail
import pandas as pd
from datetime import datetime
from dateutil.parser import parse as parse_date

def create_connection():
    return sqlite3.connect('mansag.db')

def setup_tables():
    # Connect to the SQLite database and create tables if they don't exist
    conn = create_connection()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS membership
                 (id INTEGER PRIMARY KEY,
                  name TEXT NOT NULL,
                  email TEXT NOT NULL,
                  specialty TEXT NOT NULL,
                  status INTEGER DEFAULT 0,
                  date_subscribed DATETIME NOT NULL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS administrators
                 (id INTEGER PRIMARY KEY,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL)''')

    # Add default administrators if not already present
    c.executemany('''INSERT OR IGNORE INTO administrators (username, password)
                     VALUES (?, ?)''', [('mansagadmin', 'worthymansag'), ('admin2', 'password2'), ('nladep', 'nimzing')])

    conn.commit()
    conn.close()

def is_subscription_expired(date_subscribed):
    current_date = datetime.utcnow().date()
    expiration_date = date_subscribed.date() + timedelta(days=365)
    return expiration_date < current_date



def login():
    st.subheader("Admin Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        # Check the username and password against the database
        conn = create_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM administrators WHERE username=? AND password=?", (username, password))
        admin = c.fetchone()
        conn.close()
        if admin:
            st.session_state.logged_in = True
        else:
            st.error("Invalid username or password")
            
def add_member():
    st.subheader("👯‍♀️ Add Member")
    name = st.text_input("Name")
    email = st.text_input("Email")
    specialty = st.text_input("Specialty")
    status = st.selectbox("Status", ["Active", "Inactive"])
    date_subscribed = st.date_input("Date Subscribed", datetime.now())
    
    if st.button("Add"):
        # Convert status to 1 for "Active" and 0 for "Inactive"
        status_value = 1 if status == "Active" else 0
        # Format the date to UK-based format (DD/MM/YYYY)
        formatted_date = date_subscribed.strftime("%d/%m/%Y")

        # Insert the new member into the database
        conn = create_connection()
        c = conn.cursor()
        c.execute("INSERT INTO membership (name, email, specialty, status, date_subscribed) VALUES (?, ?, ?, ?, ?)",
                  (name, email, specialty, status_value, date_subscribed))
        conn.commit()
        conn.close()

        st.success("Member added successfully!")
        
def update_member_view(member_id):
    update_member(member_id)
    st.success(f"Subscription status updated for member with ID {member_id}")

        

def send_bulk_emails():
    st.subheader("📮 Send Bulk Emails")
    subject = st.text_input("Subject:")
    body = st.text_area("Email Body:")

    if st.button("Send Emails"):
        # Fetch email addresses from the database
        conn = create_connection()
        c = conn.cursor()
        c.execute("SELECT email FROM membership")
        recipients = [row[0] for row in c.fetchall()]
        conn.close()

        try:
            # Replace 'your_email' and 'your_password' with your actual email credentials
            yag = yagmail.SMTP('info@worthy-works.com', 'vflvdwlxolxlnbjq')
            for recipient in recipients:
                yag.send(to=recipient, subject=subject, contents=body)

            yag.close()
            st.success("Emails sent successfully!")
        except Exception as e:
            st.error("Error sending emails. Please check your email settings and try again.")
            
def send_individual_email(email):
    st.write(f"Send an email to: {email}")
    mailto_link = f"mailto:{email}"
    st.markdown(f'<a href="{mailto_link}" target="_blank">{email}</a>', unsafe_allow_html=True)
    
def highlight_expired_subs(row):
    # Get the current date
    current_date = datetime.utcnow().date()

    # Convert the date_subscribed cell value to a pandas Timestamp object
    date_subscribed = pd.to_datetime(row['date_subscribed']).date()

    # Check if the subscription date is earlier than today's date
    if date_subscribed < current_date:
        return ['background-color: #FFCCCC'] * len(row)  # Light red background for expired members
    return [''] * len(row)



def render_html(val):
    return f'<span style="font-size: 14px">{val}</span>'
def add_actions_buttons(row):

    # Return an empty string since we don't need to display anything else in the "Actions" column
    return ""



def view_members():
    conn = create_connection()
    df = pd.read_sql_query("SELECT * FROM membership", conn)
    conn.close()

    st.subheader("👀 View Members")

    # Convert the date_subscribed column to pandas Timestamp objects and then to the desired format
    df['date_subscribed'] = pd.to_datetime(df['date_subscribed'], errors='coerce').dt.strftime("%d/%m/%Y")

    # Drop rows with invalid date_subscribed values
    df = df.dropna(subset=['date_subscribed'])

    # Update status and apply color-coding for expired subscriptions
    current_date = datetime.utcnow().date()

    df['status'] = df['date_subscribed'].apply(lambda x: "Active" if pd.to_datetime(x, format="%d/%m/%Y", errors='coerce').date() + timedelta(days=365) >= current_date else "Inactive")
    # Convert the status column to strings
    df['status'] = df['status'].astype(str)

    # Display the table with column headers and apply background color to rows
    # Using apply to apply the render_html function to the entire "Actions" column
    # Add an "Actions" column with buttons for each member
    df['Actions'] = df.apply(add_actions_buttons, axis=1)

    # Display the table with column headers and apply background color to rows
    st.write(df.to_html(escape=False, index=False, render_links=True), unsafe_allow_html=True)








def search_and_display_members():
    search_term = st.text_input("Search by name, specialty, or status:")
    conn = create_connection()
    df = pd.read_sql_query("SELECT * FROM membership", conn)
    conn.close()

    st.subheader("🔍 Search Members")

    if search_term:
        # Convert the date_subscribed column to pandas Timestamp objects and then to the desired format
        df['date_subscribed'] = pd.to_datetime(df['date_subscribed'], errors='coerce').dt.strftime("%d-%m-%Y")

        # Drop rows with invalid date_subscribed values
        df = df.dropna(subset=['date_subscribed'])

        # Convert the status column to strings
        df['status'] = df['status'].astype(str)

        # Apply color formatting for expired subscriptions
        df_style = df.style.apply(highlight_expired_subs, axis=1)

        # Filter the DataFrame to display only members whose name, specialty, or status match the search term
        filtered_df = df[
            (df['name'].str.contains(search_term, case=False)) |
            (df['specialty'].str.contains(search_term, case=False)) |
            (df['status'].str.contains(search_term, case=False))
        ]

        # Display the table with column headers and color formatting
        st.write(filtered_df.style.apply(highlight_expired_subs, axis=1).to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.warning("Enter a search term to find members.")









def delete_member(member_id):
    # Implement the logic to delete the member with the given member_id from the database
    conn = create_connection()
    c = conn.cursor()
    c.execute("DELETE FROM membership WHERE id=?", (member_id,))
    conn.commit()
    conn.close()




def update_member(member_id):
    st.subheader(f"Update Member {member_id}")
    conn = create_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM membership WHERE id=?", (member_id,))
    member = c.fetchone()
    conn.close()

    if not member:
        st.error(f"Member with ID {member_id} not found.")
        return

    # Convert the fetched row into a dictionary to access column values by name
    member_dict = {
        "id": member[0],
        "name": member[1],
        "email": member[2],
        "specialty": member[3],
        "status": member[4],
        "date_subscribed": member[5],
    }

    # Display the current member details
    st.write(f"**Name:** {member_dict['name']}")
    st.write(f"**Email:** {member_dict['email']}")
    st.write(f"**Specialty:** {member_dict['specialty']}")
    st.write(f"**Status:** {'Active' if member_dict['status'] == 1 else 'Inactive'}")
    st.write(f"**Date Subscribed:** {parse_date(member_dict['date_subscribed']).strftime('%Y-%m-%d')}")

    with st.form("update_form"):
        # Allow the user to update the status and date of subscription
        name = st.text_input("Update Name", value=member_dict["name"])
        email = st.text_input("Update Email", value=member_dict["email"])
        specialty = st.text_input("Update Specialty", value=member_dict["specialty"])
        status_update = st.selectbox("Update Status", ["Active", "Inactive"], index=member_dict["status"])
        date_subscribed_update = st.date_input(
            "Update Date Subscribed", parse_date(member_dict["date_subscribed"]).date()
        )

        if st.form_submit_button("Save"):
            # Convert status to 1 for "Active" and 0 for "Inactive"
            status_value = 1 if status_update == "Active" else 0

            # Update the member in the database
            conn = create_connection()
            c = conn.cursor()
            c.execute(
                "UPDATE membership SET name=?, email=?, specialty=?, status=?, date_subscribed=? WHERE id=?",
                (name, email, specialty, status_value, date_subscribed_update.strftime("%Y-%m-%d"), member_id),
            )
            conn.commit()
            conn.close()

            # Display the updated member details
            st.write(f"**Updated Name:** {name}")
            st.write(f"**Updated Email:** {email}")
            st.write(f"**Updated Specialty:** {specialty}")
            st.write(f"**Updated Status:** {'Active' if status_value == 1 else 'Inactive'}")
            st.write(f"**Updated Date Subscribed:** {date_subscribed_update.strftime('%Y-%m-%d')}")

            st.success(f"Member with ID {member_id} updated successfully!")








def main():
    st.title("🏠 Mansag Membership App")

    # Setup tables and default administrators if necessary
    setup_tables()
    
   


    # Commented out the login section for now
    # if not st.session_state.logged_in:
    #     login()
    #     return

    option = st.sidebar.selectbox("Select an option", ["Home", "Add Member", "View Members", "Search Members", "Send Bulk Emails", "Logout"])

    if option == "Home":
        st.subheader("Welcome to the Mansag Membership App!")
        st.write("Use the sidebar to navigate.")
        
    elif option == "Add Member":
        add_member()

    elif option == "View Members":
        view_members()

        
    elif option == "Search Members":
        search_and_display_members()



    elif option == "Send Bulk Emails":
        send_bulk_emails()

   

    elif option == "Logout":
        st.session_state.logged_in = False
        st.experimental_rerun()

if __name__ == "__main__":
    main()
