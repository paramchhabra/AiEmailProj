import sqlite3
from classify import classify_text, email_classify  # Importing the functions

# Function to insert email data into the SQL database
def insert_email_data(email_content, email_type):
    conn = sqlite3.connect('emails_type.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emails_type (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Content TEXT NOT NULL,
            Type TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        INSERT INTO emails_type (content, type) VALUES (?, ?)
    ''', (email_content, email_type))

    conn.commit()
    conn.close()

# Function to print all entries in the emails table
def print_email_table():
    conn = sqlite3.connect('emails_type.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM emails_type')
    rows = cursor.fetchall()

    print("ID | Content | Category")
    print("-" * 50)
    for row in rows:
        print(f"{row[0]} | {row[1][:30]}... | {row[2]}")  # Print first 30 chars of content for brevity

    conn.close()


# Example usage of email_classify and storing data
email_text = "26-07-2023 14:30 Rajesh Patel rajesh.patel@vit.ac.in Internship Opportunity at Google We are excited to announce that we have partnered with Google to offer a 3-month internship program for students. The program is designed to provide hands-on experience in software development and will include a stipend of $5000. If you are interested, please reply to this email by August 1st."

# Classify email and get category
email_prediction = email_classify(email_text)  
insert_email_data(email_text, email_prediction)  # Storing  the data
print_email_table()  # Printing the email table after insertion

