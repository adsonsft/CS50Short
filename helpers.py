from functools import wraps
from flask import redirect, session
import random
import string

from sqlite import get_db
from errors import error

URL_LENGTH = 6

def login_required(f):
    """Decorate routers to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def generate_short_url():
    """Generate random string using ascii letters and digits"""

    char = string.ascii_letters + string.digits

    while True:
        # Generate the url string
        s_url = ''.join(random.choice(char) for _ in range(URL_LENGTH))

        # Connect to database 
        db = get_db()
        cursor = db.cursor()
        
        # Check if the url already exists
        url = cursor.execute("SELECT * FROM links WHERE s_url = ?", (s_url,)).fetchone()
        cursor.close()
        
        # If not exists return it
        if not url:
            return s_url

