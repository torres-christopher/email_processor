from flask import Flask, render_template, jsonify, request # Flask
from flask_apscheduler import APScheduler # Daily schedule
from email_processor import Mail  # The name of your email processing module
import os, random # Preview of files
import sqlite3  # Database

from helpers import repository, run_email_processor, update_brands, apology # Get helpers functions


app = Flask(__name__)
scheduler = APScheduler()

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico')

@app.route("/")
def index():
    # Call a connection to the database
    con = sqlite3.connect("emails.db")

    # Connect cursor for SQL queries execution
    cur = con.cursor()

    # Check for emails
    cur.execute("SELECT emails.email_id, brands.brand_name, emails.subject, emails.image_path FROM emails INNER JOIN brands ON emails.brand_id = brands.brand_id LIMIT 4")
    emails = cur.fetchall()

    # Check for brands
    cur.execute("SELECT brand_id, brand_name FROM brands WHERE emails_count > 0")
    brands_all = cur.fetchall()
    brands_range = len(brands_all)

    # Determine the number of brands to select (minimum of 6 or the number of available brands)
    num_brands_to_select = min(6, brands_range)

    # Generate a list of random indices
    rand_indices = random.sample(range(brands_range), num_brands_to_select)

    # Create a list of brands based on the random indices
    brands = [brands_all[i] for i in rand_indices]

    con.close()

    return render_template("index.html", emails = emails, brands = brands)

@app.route("/brands", methods=["GET"])
def brands():
    # Call a connection to the database
    con = sqlite3.connect("emails.db")

    # Connect cursor for SQL queries execution
    cur = con.cursor()

    # Check for categories
    if "category" in request.args:
        category = request.args['category']
        cur.execute("SELECT brand_id, brand_name FROM brands WHERE emails_count > 0 AND category_id = ?", (category,))
    else:
        cur.execute("SELECT brand_id, brand_name FROM brands WHERE emails_count > 0")

    brands_all = cur.fetchall()
    print(brands_all)
    rows = 1
    counter = 0
    n = len(brands_all)
    print(n)
    while (n % 6) == 0:
        n //= 6
        counter += 1

    if counter > 1:
        rows = rows + counter - 1
    print(rows)

    con.close()

    return render_template("brands.html", brands = brands_all, counter = rows)

@app.route("/categories")
def categories():
    # Call a connection to the database
    con = sqlite3.connect("emails.db")

    # Connect cursor for SQL queries execution
    cur = con.cursor()

    # Check for categories
    cur.execute("SELECT category_id, name FROM categories WHERE email_count > 0")
    categories_all = cur.fetchall()

    # How many emails
    rows = 1
    counter = 0
    n = len(categories_all)

    # Sort into a row of 6
    while (n % 6) == 0:
        n //= 6
        counter += 1

    if counter > 1:
        rows = rows + counter - 1
    print(rows)

    con.close()

    return render_template("categories.html", categories = categories_all, counter = rows)

@app.route("/emails", methods=["GET"])
def emails():

    # Call a connection to the database
    con = sqlite3.connect("emails.db")

    # Connect cursor for SQL queries execution
    cur = con.cursor()

    if "search" in request.args:
        # Get data from page
        search = request.args['search']

        # Check for categories
        cur.execute("SELECT email_id, subject, date, image_path FROM emails WHERE brand_id = ?", (search,))
        emails = cur.fetchall()

        rows = 1
        counter = 0
        n = len(emails)

        # Sort into a row of 6
        while (n % 6) == 0:
            n //= 6
            counter += 1

        if counter > 1:
            rows = rows + counter - 1

        con.close()

        return render_template("emails.html", emails = emails, counter = rows)
    else:
        return apology("Wrong route", 400)


@app.route("/preview")
def preview():
    if "email_id" in request.args:
        # Get data from page
        email_id = request.args['email_id']
        return render_template("preview.html", email_id = email_id)
    else:
        return apology("No email found", 400)

@app.route('/getFile')
def getFile():
    # Call a connection to the database
    con = sqlite3.connect("emails.db")

    # Connect cursor for SQL queries execution
    cur = con.cursor()

    if "email_id" in request.args:
        # Get data from page
        email_id = request.args['email_id']

        # Check for categories
        cur.execute("SELECT file_path FROM emails WHERE email_id = ?", (email_id,))
    else:
        cur.execute("SELECT email_id, subject, date, image_path FROM emails LIMIT 12")

    emails = cur.fetchall()

    dic = emails[0]
    file_path = dic[0].replace("templates/","")

    con.close()
    return render_template(f'{file_path}')

"""
@app.route('/randomFile')
def randomFile():
    # Use the specified template folder for this route
    random_folder_top = random.choice(os.listdir("templates/mail_repository"))
    random_folder_bottom = random.choice(os.listdir(f"templates/mail_repository/{random_folder_top}/"))
    random_file = random.choice(os.listdir(f"templates/mail_repository/{random_folder_top}/{random_folder_bottom}"))
    return render_template(f'/mail_repository/{random_folder_top}/{random_folder_bottom}/{random_file}')
"""

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/status")
def status():
    structure = repository("templates/mail_repository")
    return render_template("status.html", repository=structure)


@app.route("/check_status")
def check_status():
    # Add any status checking you want here
    return jsonify({"status": "running"})


if __name__ == "__main__":
    scheduler.add_job(id="email_processor", func=run_email_processor, trigger="cron", day_of_week="mon-sun", hour=6, minute=00, second=00)  # Run email processor every day at 06:00

    scheduler.start()
    app.run(debug=True, use_reloader=True)  # Set debug to False for production
    # update_brands()
