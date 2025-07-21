from flask import Flask, g, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import user_agents
import random
import json

from helpers import login_required, generate_short_url
from sqlite import get_db
from errors import error
from geolite2 import get_user_location


# Init flask
app = Flask(__name__)
app.config["SECRET_KEY"] = "057a7b59849f432730f91071aaaadec993c7f30c52c7bb4e55e5baf55b3af500"

@app.teardown_appcontext
def close_connection(exception):
    """Close database connection"""
    db = getattr(g, '_database', None)

    # If the conetion exists close it
    if db is not None:
        db.close()

@app.route("/")
@login_required
def home():
    """Show homepage"""
    
    # Connect to database
    db = get_db()
    cursor = db.cursor()

    # Get user data
    query = """
    SELECT links.id, links.description, links.f_url, links.s_url, links.created_at, click_counters.clicks
    FROM links
    LEFT JOIN click_counters ON click_counters.link_id = links.id
    WHERE user_id = ?
    ORDER BY links.created_at DESC
    """
    links = cursor.execute(query, (session["user_id"],)).fetchall()
    cursor.close()

    return render_template("index.html", links=links) 

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Check if the username exists
        if not username:
            return error(
                    "Bad Request",
                    "Username is required",
                    "bad_request"
                    )

        # Check if the password exists
        if not password:
            return error(
                    "Bad Request",
                    "Password is required",
                    "bad_request"
                    )

        # Check if the user exist in the database
        db = get_db()
        cursor = db.cursor()
        user = cursor.execute("SELECT id, hash FROM users WHERE username = ?", (username,)).fetchone()
        cursor.close()

        # Check if the username exists
        # Check if the passwords are equals
        if not user or not check_password_hash(user["hash"], password):
            return error(
                    "Invalid Credentials",
                    "Invalid username and/or password",
                    "unauthorized"
                    )

        # Remember which user has logged in
        session["user_id"] = user["id"]

        return redirect("/")

    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect to login form
    return redirect("/login")

@app.route("/<s_url>")
def redirect_url(s_url):
    """Redirect the user to the original URL"""
    
    # Check url length
    if len(s_url) != 6:
        return error(
                "Not Found",
                "URL not found",
                "not_found"
                )

    # Connect into dabase
    db = get_db()
    cursor = db.cursor()

    # Query the short url in the database
    link = cursor.execute("SELECT id, f_url FROM links WHERE s_url = ?", (s_url,)).fetchone()

    # Check if the link exists
    if link:
        # Get link_id, referrer, country, city, device, os, browser
        referer = request.headers["referer"].lower()

        # Use the lib user-agents to parse the User-Agent header
        ua_string = request.headers["User-Agent"]
        ua = user_agents.parse(ua_string)

        # Now, get parsed information
        # Device type
        if ua.is_mobile:
            device = "mobile"
        elif ua.is_tablet:
            device = "tablet"
        elif ua.is_pc:
            device = "desktop"
        else:
            device = "other"

        # Operational system
        os = ua.os.family.lower()

        # Browser
        browser = ua.browser.family.lower()

        # Get the user ip
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)

        # Get user location using geolite2
        location = get_user_location(ip)

        # Create a tupla with the info to insert in the database
        click_events = (
                link["id"],
                referer,
                location["country"],
                location["city"],
                os,
                browser,
                device
                )
        
        try:
            # Insert that information in the database
            cursor.execute("INSERT INTO click_events (link_id, referer, country, city, os, browser, device) VALUES(?, ?, ?, ?, ?, ?, ?)", click_events)

            # Increment the click_counter table
            cursor.execute("INSERT INTO click_counters (link_id, clicks) VALUES(?, 1) ON CONFLICT(link_id) DO UPDATE SET clicks = clicks + 1", (link["id"],))

            db.commit()
        except db.DatabaseError:
            db.rollback()

            return error(
                    "Internal Server Error",
                    "There was a problem processing your request. Try again later",
                    "internal_server_error"
                    )
        finally:
            if cursor:
                cursor.close()

        return redirect(link["f_url"])
    else:
        if cursor:
            cursor.close()

        return error(
                "Not Found",
                "URL not found",
                "not_found"
                )

@app.route("/register", methods=["GET", "POST"])
def register():
    """"Register the user"""

    if request.method == "POST":
        # Get the request informations
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Check if the username exists
        if not username:
            return error(
                    "Bad Request",
                    "Username is required",
                    "bad_request"
                    )

        # Check if the password exists
        if not password:
            return error(
                    "Bad Request",
                    "Password is required",
                    "bad_request"
                    )

        # Check if the confirmation exists
        if not confirmation:
            return error(
                    "Bad Request",
                    "Confirmation is required",
                    "bad_request"
                    )

        # Check if the password and the confirmation are equals
        if not password == confirmation:
            return error(
                    "Bad Request",
                    "Password and confirmation are not equals",
                    "bad_request"
                    )

        # Hash the password
        password_hash = generate_password_hash(password)

        # Init database connection
        db = get_db()
        cursor = db.cursor()

        # Try to insert in the database
        try:
            cursor.execute("INSERT INTO users (username, hash) VALUES(?, ?)", (username, password_hash))
            db.commit()
        # If already have the user in database
        except db.IntegrityError:
            db.rollback()

            return error(
                    "Bad Request",
                    "Username already exists",
                    "bad_request"
                    )
        # If other error occur
        except db.DatabaseError:
            db.rollback()

            return error(
                    "Internal Server Error",
                    "User doesn't registered. Please, try again later",
                    "internal_server_error"
                    )
        finally:
            if cursor:
                cursor.close()

        return redirect("/login")

    else:
        # If the method is GET, just render the page
        return render_template("register.html")

@app.route("/short", methods=["POST"])
@login_required
def short():
    """Shorten the link"""

    # Init database connection
    db = get_db()
    cursor = db.cursor()

    # Get description
    description = request.form.get("description")
    if description:
        # get the link id
        link_id = request.form.get("link_id")

        # Check if the user is the owner of the link
        owner_id = cursor.execute("SELECT user_id FROM links WHERE id = ?", (link_id,)).fetchone()
        if owner_id and owner_id["user_id"] == session["user_id"]:
            try:
                # Insert or change the link description in the database
                cursor.execute("UPDATE links SET description = ? WHERE id = ?", (description, link_id))
                db.commit()
            except db.databaseError:
                db.rollback()

                return error(
                        "Internal Server Error",
                        "There was a problem processing your request. Try again later",
                        "internal_server_error"
                        )
            finally:
                if cursor:
                    cursor.close()

            return redirect("/")
        else:
            if cursor:
                cursor.close()

            return error(
                    "Not Found",
                    "Link not found",
                    "not_found"
                    )

    # Get the full URL
    f_url = request.form.get("f_url")

    # Check if the full URL exists
    if not f_url:
        return error(
                "Bad Request",
                "URL is required",
                "bad_request"
                )

    # Generate the short url
    s_url = generate_short_url(f_url)

    # Try to insert in database
    try:
        cursor.execute("INSERT INTO links (user_id, f_url, s_url) VALUES(?, ?, ?)", (session["user_id"], f_url, s_url))
        db.commit()
    # If occour something wrong return with error
    except db.DatabaseError:
        db.rollback()

        return error(
                "Internal Server Error",
                "There was a problem processing your request. Try again later",
                "internal_server_error"
                )
    finally:
        if cursor:
            cursor.close()

    # Return to homepage and show the table with the urls
    return redirect("/")

@app.route("/statistics")
@login_required
def statistics():
    """Show statistics page"""

    # Connect to database
    db = get_db()
    cursor = db.cursor()

    # Get user data
    query = """
    SELECT
        links.id,
        links.description,
        links.created_at,
        links.s_url,
        click_counters.clicks
    FROM links
    LEFT JOIN click_counters ON click_counters.link_id = links.id
    WHERE user_id = ?
    ORDER BY links.created_at DESC
    """
    
    # Get the current user links data
    links = cursor.execute(query, (session["user_id"],)).fetchall()
    cursor.close()

    return render_template("statistics.html", links=links) 

@app.route("/statistics/<s_url>")
@login_required
def details(s_url):
    """Show statistics from each link"""

    # Check url length
    if len(s_url) != 6:
        return error(
                "Not Found",
                "URL not found",
                "not_found"
                )

    # Connect into dabase
    db = get_db()
    cursor = db.cursor()

    # Check if the link exists
    link = cursor.execute("SELECT * FROM links WHERE s_url = ?", (s_url,)).fetchone()

    # Check if the current user is the owner
    # Find the short URL in the database
    if link and link["user_id"] == session["user_id"]:
        query = """
            WITH filtered_links AS (
                SELECT * FROM click_events WHERE link_id = ?
            )
            SELECT 
                clicks,
                (SELECT json_group_object(referer, total) FROM (SELECT referer, COUNT(*) AS total FROM filtered_links GROUP BY referer ORDER BY total DESC LIMIT 5)) AS referers,
                (SELECT json_group_object(country, total) FROM (SELECT country, COUNT(*) AS total FROM filtered_links GROUP BY country ORDER BY total DESC LIMIT 5)) AS countries,
                (SELECT json_group_object(city, total) FROM (SELECT city, COUNT(*) AS total FROM filtered_links GROUP BY city ORDER BY total DESC LIMIT 10)) AS cities,
                (SELECT json_group_object(os, total) FROM (SELECT os, COUNT(*) AS total FROM filtered_links GROUP BY os ORDER BY total DESC LIMIT 5)) AS os,
                (SELECT json_group_object(browser, total) FROM (SELECT browser, COUNT(*) AS total FROM filtered_links GROUP BY browser ORDER BY total DESC LIMIT 5)) AS browsers,
                (SELECT json_group_object(device, total) FROM (SELECT device, COUNT(*) AS total FROM filtered_links GROUP BY device ORDER BY total DESC LIMIT 5)) AS devices,
                (SELECT json_group_object(day, total) FROM (SELECT strftime('%Y-%m-%d', created_at) AS day, COUNT(*) AS total FROM filtered_links GROUP BY day ORDER BY day DESC LIMIT 10)) AS clicks_per_day
            FROM links
            JOIN click_counters ON link_id = links.id
            WHERE link_id = ?
        """

        # If the link exist, get all its data and group all of them in top's 5
        result = cursor.execute(query, (link["id"], link["id"])).fetchone()


        if result:
            # Export its data
            data = {
                    "description": link["description"],
                    "f_url": link["f_url"],
                    "s_url": link["s_url"],
                    "created_at": link["created_at"],
                    "clicks": result["clicks"],
                    "referers": json.loads(result["referers"] or "{}"),
                    "countries": json.loads(result["countries"] or "{}"),
                    "cities": json.loads(result["cities"] or "{}"),
                    "os": json.loads(result["os"] or "{}"),
                    "browsers": json.loads(result["browsers"] or "{}"),
                    "devices": json.loads(result["devices"] or "{}"),
                    "clicks_per_day": json.loads(result["clicks_per_day"] or "{}")
                    }

        cursor.close()

        # Then return the page with the data
        return render_template("statistics_details.html", data=data)
    else:
        if cursor:
            cursor.close()

        return error(
                "Not Found",
                "URL not found",
                "not_found"
                )


