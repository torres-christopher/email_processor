import email    # Email data
import email.header
import imaplib  # IMAP email download
import os       # Work with files
import hashlib  # Hash file names
import sqlite3  # Database
from dotenv import load_dotenv # Hash login details
import random # Random for testingfrom PIL import Image
import codecs # Reading HTML
import requests # URL request
from PIL import Image # Image cropping
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Retrieve the values from environment variables
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')
SERVER = os.getenv('SERVER')

# Define the HTML to Image API endpoint and authentication details
HCTI_API_ENDPOINT = "https://hcti.io/v1/image"  # Adjust the width as needed
HCTI_API_USER_ID = '3f50b9a4-f9b9-4dbd-9d9c-986738eb4578'  # Replace with your API user ID
HCTI_API_KEY = '636ffba5-2588-4ef2-9079-43773676ae38'  # Replace with your API key

class Mail():
    # Initialize class
    def __init__(self):
        # Encrypted connect to the server and go to its inbox - Usually 993 port
        self.user = EMAIL
        self.password = PASSWORD
        self.M = imaplib.IMAP4_SSL(SERVER, '993')
        self.M.login(self.user, self.password)
        # Select which inbox to get e-mails from
        self.M.select('inbox')

    # Decode encoded emails UTF-8
    def header_decode(self, header):
        hdr = ""
        for text, encoding in email.header.decode_header(header):
            if isinstance(text, bytes):
                text = text.decode(encoding or "us-ascii")
            hdr += text
        return hdr

    # Processes email messages and returns sender, subject, date and HTML code
    def process_email(self, message):
        mail_from = message['from']
        mail_subject = message['subject']
        mail_date = message['date'].replace(" (CEST)", "").replace(" (UTC)", "").replace(" (GMT)", "")
        while True:
            if mail_date[0].isnumeric():
                break
            else:
                mail_date = mail_date[1:]

        # Format date
        og_date_format = "%d %b %Y %H:%M:%S %z"
        formated_date = datetime.strptime(mail_date, og_date_format)
        new_date = formated_date.strftime("%d.%m.%Y")

        # Clean sender email address
        if '"' in mail_from or "'" in mail_from:
            mail_from = mail_from.replace('"', '').replace("'", "")

        # Split on start of email address
        sender = mail_from.split('<')

        if len(sender) > 1:
            # Strip trailing whitespaces
            mail_from_name = sender[0].strip().replace('.cz', '').replace('www.', '')
            mail_from_address = sender[1].replace('>', '').strip()
        else:
            # Strip trailing whitespaces
            mail_from_address = sender[0].replace('>', '').strip()
            mail_from_name = sender[0].strip().replace('.cz', '').replace('www.', '')
            mail_from_name = mail_from_name.split('@')[1].rsplit(',', 1)[0]

        if "utf" in mail_from_name or "UTF" in mail_from_name:
            mail_from_name = self.header_decode(mail_from_name)

        if "utf" in mail_subject or "UTF" in mail_subject:
            mail_subject = self.header_decode(mail_subject)

        # Clean data for folder structure
        mail_from_name = mail_from_name.replace('/', '').replace(':', '').replace('*', '').replace('|', '').replace('\\', '').replace('?', '')

        mail_html = ''
        # Check for plain text vs multipart (needs to be separated)
        if message.is_multipart():
            # Multipart has text, annex, and HTML
            for part in message.get_payload():
                # Extract HTML code
                if part.get_content_type() == 'text/html':
                    payload = part.get_payload(decode=True)
                    try:
                        # Attempt to decode the payload as UTF-8
                        payload = payload.decode('utf-8')
                    except UnicodeDecodeError:
                        # If decoding as UTF-8 fails, fallback to 'latin1'
                        payload = payload.decode('latin1')
                    mail_html += payload
        else:
            if message.get_content_type() == 'text/html':
                payload = message.get_payload(decode=True)
                try:
                    # Attempt to decode the payload as UTF-8
                    payload = payload.decode('utf-8')
                except UnicodeDecodeError:
                    # If decoding as UTF-8 fails, fallback to 'latin1'
                    payload = payload.decode('latin1')
                mail_html += payload

        return mail_from_name, mail_from_address, mail_subject, new_date, mail_html

    # Cleans HTML of personal information
    def clean_html(self, html_code):
        clean_code = html_code.replace("christopher.torres.crm@gmail.com", "#####@gmail.com")

        return clean_code

    # Create hash name for files
    def get_hash(self, subject):
        hash_md5 = hashlib.md5(subject.encode('utf-8')).hexdigest()
        return hash_md5

    # Get new or existing directory to save files
    def create_directory(self, content_hash, sender, file_type):
        if file_type == "template":
            main_folder = "templates"
            main_path = "mail_repository"
        elif file_type == "screenshot":
            main_folder = "static"
            main_path = "screenshots"

        directory_path = os.path.join(main_folder, main_path)

        sender = sender.replace(" ","_")
        # Check if the general mail repository exists
        if os.path.exists(directory_path):
            # Get sender path of the repository
            directory_path = os.path.join(main_folder, main_path, sender)
            # Create if not exists
            if not os.path.exists(directory_path):
                os.makedirs(directory_path)
            # Get sender + content path of the repository
            directory_path = os.path.join(directory_path, content_hash)
            # Check for duplicate emails
            if os.path.exists(directory_path):
                # Check for duplicates
                counter = 1
                while os.path.exists(f"{directory_path}_{counter}"):
                    counter += 1

                # Create new directory
                directory_path = os.path.join(f"{directory_path}_{counter}")
                os.makedirs(directory_path)
            # Create new
            else:
                os.makedirs(directory_path)
        return directory_path

    # Saves html file to directory and returns full path
    def save_as_html(self, directory_path, content_hash, html_code):
        file_name = f"index_{content_hash}.html"
        file_path = os.path.join(directory_path, file_name)

        # Create a new file
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(html_code)

        # Return its path
        return file_path

    # Saves data about email into a database
    def save_metadata(self, mail_from_name, mail_from_address, mail_subject, mail_date, file_path, screenshot_path):
        # Call a connection to the database
        con = sqlite3.connect("emails.db")

        # Connect cursor for SQL queries execution
        cur = con.cursor()

        # Check for a familiar sender
        cur.execute("SELECT sender_id FROM senders WHERE sender_name = ?", (mail_from_name,))
        sender_tup = cur.fetchone()

        # Insert a new sender into the table
        if sender_tup is None:
            cur.execute("""
                INSERT INTO senders (sender_name, sender_address) VALUES (?, ?)
            """, (mail_from_name, mail_from_address))
            con.commit()
            cur.execute("SELECT sender_id FROM senders WHERE sender_name = ?", (mail_from_name,))
            sender_tup = cur.fetchone()
            sender_id = sender_tup[0]
        # Get the sender ID
        elif len(sender_tup) > 1:
            raise ValueError("Senders are duplicated")
        else:
            sender_id = sender_tup[0]

        # Insert data into the database
        cur.execute("""
            INSERT INTO emails (subject, date, file_path, image_path, sender_id) VALUES (?, ?, ?, ?, ?)
        """, (mail_subject, mail_date, file_path, screenshot_path, sender_id))
        con.commit()

        # Close connection
        con.close()

    # Saves information about unsaved emails to database
    def save_unsaved(self, mail_from_name, mail_from_address, mail_subject, mail_date):
        # Check default values
        if not mail_from_name:
            mail_from_name = "Empty"
        if not mail_from_address:
            mail_from_address = "Empty"
        if not mail_subject:
            mail_subject = "Empty"
        if not mail_date:
            mail_date = "Empty"

        # Call a connection to the database
        con = sqlite3.connect("emails.db")

        # Connect cursor for SQL queries execution
        cur = con.cursor()

        # Check for a familiar sender
        cur.execute("SELECT sender_id FROM senders WHERE sender_name = ?", (mail_from_name,))
        sender_tup = cur.fetchone()

        # Insert a new sender into the table
        if sender_tup is None:
            cur.execute("""
                INSERT INTO senders (sender_name, sender_address) VALUES (?, ?)
            """, (mail_from_name, mail_from_address))
            con.commit()
            cur.execute("SELECT sender_id FROM senders WHERE sender_name = ?", (mail_from_name,))
            sender_tup = cur.fetchone()
            sender_id = sender_tup[0]
        # Get the sender ID
        elif len(sender_tup) > 1:
            raise ValueError("Senders are duplicated")
        else:
            sender_id = sender_tup[0]

        # Insert data into the database
        cur.execute("""
            INSERT INTO unsaved (subject, date, sender_id) VALUES (?, ?, ?)
        """, (mail_subject, mail_date, sender_id))
        con.commit()

        # Close connection
        con.close()

    # Connects senders to brands in database
    def check_missing_brand(self):
        # Call a connection to the database
        con = sqlite3.connect("emails.db")

        # Connect cursor for SQL queries execution
        cur = con.cursor()

        # Check for empty brands in emails
        cur.execute("SELECT email_id, sender_id FROM emails WHERE brand_id IS NULL")
        sender_tup = cur.fetchall()

        for email_id, sender_id in sender_tup:
            # Check for brand in sender_brands
            cur.execute("SELECT brand_id FROM senders_brands WHERE sender_id = ?", (sender_id,))
            result = cur.fetchone()

            if result:
                brand_id = result[0]
                # Update the emails table with the correct brand_id
                cur.execute("UPDATE emails SET brand_id = ? WHERE email_id = ?", (brand_id, email_id))
                con.commit()

        # Check for empty brands in unsaved
        cur.execute("SELECT email_id, sender_id FROM unsaved WHERE brand_id IS NULL")
        sender_tup = cur.fetchall()

        for email_id, sender_id in sender_tup:
            # Check for brand in sender_brands
            cur.execute("SELECT brand_id FROM senders_brands WHERE sender_id = ?", (sender_id,))
            result = cur.fetchone()

            if result:
                brand_id = result[0]
                # Update the emails table with the correct brand_id
                cur.execute("UPDATE unsaved SET brand_id = ? WHERE email_id = ?", (brand_id, email_id))
                con.commit()


        # Close connection
        con.close()

    # Connects senders to brands in database
    def check_counts(self):
        # Call a connection to the database
        con = sqlite3.connect("emails.db")

        # Connect cursor for SQL queries execution
        cur = con.cursor()

        # Check for empty brands in emails
        cur.execute("""
            SELECT categories.category_id, COUNT(emails.email_id) AS emails_count
            FROM categories
            LEFT JOIN brands ON categories.category_id = brands.category_id
            LEFT JOIN emails ON brands.brand_id = emails.brand_id
            GROUP BY categories.category_id
            HAVING COUNT(emails_count) > 0
            ORDER BY emails_count DESC;
        """)
        counts = cur.fetchall()

        for category_id, count in counts:
            # Update the emails table with the correct brand_id
            cur.execute("UPDATE categories SET email_count = ? WHERE category_id = ?", (count, category_id))
            con.commit()

         # Check for empty brands in emails
        cur.execute("""
            SELECT brands.brand_id, COUNT(emails.email_id) AS emails_count
            FROM brands
            LEFT JOIN emails ON brands.brand_id = emails.brand_id
            GROUP BY brands.brand_id
            HAVING COUNT(emails_count) > 0
            ORDER BY emails_count DESC;
        """)
        counts = cur.fetchall()

        for brand_id, count in counts:
            # Update the emails table with the correct brand_id
            cur.execute("UPDATE brands SET emails_count = ? WHERE brand_id = ?", (count, brand_id))
            con.commit()


        # Close connection
        con.close()

    # Takes screenshots of html emails and saves them to the same folder as emails
    def take_screenshot(self, file_path, screenshot_path):
        # Open HTML template
        f=codecs.open(file_path, 'r')

        # Read HTML
        data = { 'html': f.read() }

        # Get screenshot
        image_response = requests.post(url = HCTI_API_ENDPOINT, data = data, auth=(HCTI_API_USER_ID, HCTI_API_KEY))

        # Get URL
        url = image_response.json()['url']

        # Open the image
        image = Image.open(requests.get(url, stream=True).raw)

        # Save the cropped and resized image
        image.save(screenshot_path)

    # Takes screenshots of html emails and saves them to the same folder as emails
    def crop_screenshot(self, screenshot_path):

        # Screenshot path
        file_path = screenshot_path.replace(".png", "_original.png")

        # Open the image
        image = Image.open(file_path)

        # Get the image dimensions
        width, height = image.size

        # Define the target width
        target_width = 725

        # Calculate the difference between the current width and the target width
        width_diff = width - target_width

        # Calculate the number of pixels to trim from each side
        trim_pixels = width_diff // 2

        # Calculate the coordinates for cropping
        left = trim_pixels
        upper = 0  # You can adjust this if you want to trim from the top
        right = width - trim_pixels
        lower = 967  # You can adjust this if you want to trim from the bottom

        # Crop the image using the calculated box coordinates
        image = image.crop((left, upper, right, lower))

        # Save the cropped and resized image
        image.save(screenshot_path)

    # Main function
    def search_and_save_emails(self):
        with self.M as inbox:
            # Search for ALL messages with None charset parameter. Returns Status and ID of message
            status, data = inbox.search(None, 'UNSEEN')

            # Get the number of unseen emails if any
            num_unseen_emails = len(data[0].split()) if data[0] else 0

            # the list returned is a list of bytes separated by white spaces on this format: [b'1 2 3', b'4 5 6'] so, to separate it first we create an empty list
            mail_ids = []

            # then we go through the list splitting its blocks of bytes and appending to the mail_ids list
            for block in data:
                # the split function called without parameter transforms the text or bytes into a list using the white spaces as separator:
                # b'1 2 3'.split() => [b'1', b'2', b'3']
                mail_ids += block.split()

            num_saved_as_html = 0  # Initialize the count of emails saved as HTML

            # now for every id we'll fetch the email to extract its content
            for i in mail_ids:
                # the fetch function fetch the email given its id and format that you want the message to be
                status, data = inbox.fetch(i, '(RFC822)')
                # Check for unsaved e-mails
                saved = False

                # Data se per RFC822 format comes on a list with a tuple with header, content, and the closing byte b')'
                for response_part in data:
                    # Tuple check
                    if isinstance(response_part, tuple):
                        # we go for the content at its second element skipping the header at the first and the closing at the third
                        message = email.message_from_bytes(response_part[1])

                        # Get data from message
                        mail_from_name, mail_from_address, mail_subject, mail_date, mail_html = self.process_email(message)

                        # Skip if no HTML file detected
                        if not mail_html:
                            continue

                        # Clean html of contact info
                        mail_html = self.clean_html(mail_html)

                        # Create file name
                        content_hash = self.get_hash(mail_subject)

                        # Check file directory or create a new one (template)
                        file_type = "template"
                        directory_path_template = self.create_directory(content_hash, mail_from_name, file_type)

                        # Save email as HTML
                        file_path = self.save_as_html(directory_path_template, content_hash, mail_html)

                        # Check file directory or create a new one (screenshot)
                        file_type = "screenshot"
                        directory_path_screenshot = self.create_directory(content_hash, mail_from_name, file_type)

                        # Take a screenshot of the email's HTML content
                        screenshot_path = os.path.join(directory_path_screenshot, f"{content_hash}_original.png")
                        self.take_screenshot(f"{file_path}", screenshot_path)

                        screenshot_path = os.path.join(directory_path_screenshot, f"{content_hash}.png")
                        self.crop_screenshot(screenshot_path)

                        # Save email metadata to the database
                        self.save_metadata(mail_from_name, mail_from_address, mail_subject, mail_date, file_path, screenshot_path)

                        # Increment the count of emails saved as HTML
                        num_saved_as_html += 1
                        saved = True
                if saved == False:
                    self.save_unsaved(mail_from_name, mail_from_address, mail_subject, mail_date)

            return num_unseen_emails, num_saved_as_html


if __name__ == "__main__":
    print("------------------")
    mail_instance = Mail()
    # path = mail_instance.save_as_html("mail_repository_test/Isobar (MASTER)", "32fca84e687740feb720ca7657c70cf8", "<html></html>")
    num_unseen, num_saved_as_html = mail_instance.search_and_save_emails()
    print(f"{num_unseen} unseen emails found.")
    print(f"{num_saved_as_html} emails saved as HTML.")
