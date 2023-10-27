from flask import redirect, render_template, session # Get flask functions
from email_processor import Mail  # The name of your email processing module
import os # Preview of files

def repository(folder):
    # Create dictionary
    repository = {}
    # Get all folders from repository
    directories = os.listdir(folder)
    # For each folder get number of files
    for directory in directories:
        files = os.listdir(os.path.join(folder, directory))
        repository[directory] = len(files)

    return repository

def run_email_processor():
    mail_instance = Mail()
    num_unseen, num_saved_as_html = mail_instance.search_and_save_emails()
    print(f"{num_unseen} unseen emails found.")
    print(f"{num_saved_as_html} emails saved as HTML.")

def update_brands():
    mail_instance = Mail()
    mail_instance.check_missing_brand()
    mail_instance.check_counts()

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code

if __name__ == "__main__":
    update_brands()
