from flask import render_template

def error(title, message, code="bad_request"):
    """Send error messagens when something wrong occour"""
    
    # Create one dict to send data in one variable instead multiple
    error = {
        "title": title,
        "message": message
        }

    # A constant with one dict of error codes and your names
    CODES = {
        "bad_request": 400,
        "unauthorized": 401,
        "not_found": 404,
        "internal_server_error": 500
        }

    # Get the error number in the previous dict by the name of the error
    for c in CODES:
        if code == c:
            code = CODES[c]
        else:
            code = 400

    return render_template("error.html", error=error), code
