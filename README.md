Email Scraper and Organizer
===========================
This web application is built with Python and Flask to fetch and display emails from a Gmail account. It provides the ability to sort and organize emails by brands and categories.


|                |                                   |
|----------------------- |-------------------------------------------      |
| Name                  | Christopher Torres |
| Country of Origin     | Czech Republic |
| Project Title         | Email Monitor |
| Video URL             | [URL of Your Video] |
| Project Description   | The primary objective of this project is to enhance email management and organization. By providing a web application that allows users to easily sort, categorize, and access their emails by brand and category. This streamlined email management system helps me, a CRM specialist who codes emails daily, to find inspiration from various industries and enhance my own work. |


Prerequisites
-------------

Before running the application, ensure you have the following:

-   A Gmail account
-   Python 3.x installed
-   A .env file with your Gmail account and HCTI API credentials (EMAIL, PASSWORD, SERVER, HCTI_API_USER_ID, HCTI_API_KEY)
-   Required Python libraries
    - Flask - For creating the web interface of the application
    - Imaplib - Manages the Gmail account, fetches emails, and manages folders
    - Email - For parsing and processing email content
    - APScheduler - Schedules periodic tasks for checking emails
    - Pillow - Provides image processing capabilities for taking and cropping screenshots
    - sqlite3 - Manages email metadata in the local database.
    - Codecs -  Ensures correct decoding and processing of email content


Functionality
-------------

The application comprises three main components: Flask web interface, email processor, and helper functions.

### 1\. Flask Web Interface

The Flask web interface is the user-facing part of the application. It provides several routes to interact with the data:

-   **"/"**: The home page displays a random selection of emails from the database, along with a few random brands. The main purpose of this page is to provide a glimpse of the available emails and brands.

-   **"/brands"**: This page lists brands and allows users to filter them by category. It displays a list of brands with email counts and lets you explore different categories.

-   **"/categories"**: This page lists email categories. It also shows the count of emails within each category and allows you to view emails from a specific category.

-   **"/emails"**: Displays email details for a specific brand. It accepts a brand ID as a query parameter and shows all emails associated with that brand.

-   **"/preview"**: This route lets you preview a specific email by providing its email ID as a query parameter.

-   **"/getFile"**: Is a nested route for /preview that allows its &lt;iframe> to render email templates by providing its email ID as a query parameter.

-   **"/about"**: Provides information about the application.

-   **"/status"**: Displays a summary of the email repository, including the number of emails in each category.

-   **"/check_status"**: Provides a simple API route to check if the application is running.

### 2\. Email Processor

The email processor is responsible for connecting to your Gmail account, downloading new emails, and saving them into the local database. Key functionalities of the email processor include:

-   Connecting to the Gmail account via IMAP and fetching unseen emails.
-   Extracting metadata from the email, including sender name, sender address, subject, and date.
-   Cleaning the HTML content to remove personal information (my email address, phone or name).
-   Saving the email as HTML in the 'mail_repository' folder.
-   Taking a screenshot of the HTML content, cropping it and saving it.
-   Saving email metadata to the SQLite database.
-   Handling cases where the sender's information is missing or not in the expected format.

### 3\. Helper Functions

The helper functions include:

-   **repository(folder)**: Returns a dictionary representing the structure of email folders. Is used in the /status route
-   **run_email_processor()**: Initiates the email processing, fetching unseen emails, and saving them.
-   **update_brands()**: Updates the brand and category information in the database since it is a separate function from email_processor.
-   **apology(message, code=400)**: Renders an error message.

Usage
-----

1.  Set up your Gmail account and ensure you have the required credentials in your .env file.
2.  Install the necessary Python libraries.
3.  Run the Flask application (`app.py`) to start the web interface.
4.  Configure the APScheduler in your Flask application to periodically run the `run_email_processor()` function to check for new emails.
5.  Visit the web interface and start exploring your emails by brand and category.

Note
----

-   The application assumes you have a folder structure in 'mail_repository' and 'static' to organize and display email files.
-   The application connects to a Gmail account, but you can customize it for other email providers (I tried Czech provider Seznam.cz and it worked fine).
-   The 'check_missing_brand' function connects senders to brands in the database.
-   The 'check_counts' function updates email counts for categories and brands.
-   Make sure to adapt the code and settings to your needs and production environment.

Happy email organizing!
