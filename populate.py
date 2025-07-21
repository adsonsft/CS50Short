import sys
import sqlite3
import random
from datetime import datetime, timedelta

referers = [
        "https://google.com",
        "https://youtube.com",
        "https://facebook.com",
        "https://x.com",
        "https://instagram.com",
        "https://linkedin.com",
        "https://bing.com",
        "https://reddit.com"
        ]
referers_weights = [45, 20, 15, 5, 5, 5, 3, 2]

countries = [
        "Brazil",
        "United States of America",
        "Canada",
        "Mexico",
        "Portugal",
        "Spain",
        "France",
        "Germany",
        "Netherlands"
        ]
countries_weights = [35, 30, 5, 5, 5, 5, 5, 5, 5]

cities = {
    "Brazil": {
        "names": ["São Paulo", "Rio de Janeiro", "Brasília", "Salvador", "Belo Horizonte"],
        "weights": [11895578, 6729894, 2982818, 2568928, 2416339]
    },
    "United States of America": {
        "names": ["New York", "Los Angeles", "Chicago", "Houston", "Washington, D.C."],
        "weights": [8478072, 3878704, 2721308, 2390125, 702250]
    },
    "Canada": {
        "names": ["Toronto", "Montreal", "Calgary", "Ottawa", "Vancouver"],
        "weights": [2794356, 1762949, 1306784, 1000000, 662248]
    },
    "Mexico": {
        "names": ["Mexico City", "Tijuana", "Puebla", "Guadalajara", "Monterrey"],
        "weights": [9209944, 1810645, 1542232, 1385629, 1142952]
    },
    "Portugal": {
        "names": ["Lisboa", "Porto", "Braga", "Coimbra", "Faro"],
        "weights": [545142, 231800, 181494, 106768, 64560]
    },
    "Spain": {
        "names": ["Madrid", "Barcelona", "Valencia", "Seville", "Bilbao"],
        "weights": [2824000, 1454000, 736000, 695000, 351000]
    },
    "France": {
        "names": ["Paris", "Marseille", "Lyon", "Toulouse", "Nice"],
        "weights": [2229621, 855393, 500715, 458298, 342295]
    },
    "Germany": {
        "names": ["Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt"],
        "weights": [3520000, 1790000, 1450000, 1060000, 733000]
    },
    "Netherlands": {
        "names": ["Amsterdam", "Rotterdam", "The Hague", "Utrecht", "Eindhoven"],
        "weights": [821752, 623652, 537833, 375161, 231642]
    }
}

operational_systems = [
    "Android",
    "Linux",
    "iOS",
    "Windows",
    "macOS",
    "iPadOS"
    ]
operational_systems_weights = [0.40, 0.30, 0.15, 0.10, 0.03, 0.02]

browsers = [
    "Chrome",
    "Firefox",
    "Edge",
    "Safari",
    "Opera",
    "Brave"
]
browsers_weights = [0.65, 0.15, 0.10, 0.05, 0.03, 0.02]

db = sqlite3.connect("short.db")
db.row_factory = sqlite3.Row
cursor = db.cursor()

LINK_ID = 8
CLICK_EVENTS_QUANTITY = random.randint(200, 1500)

"""
For loop to populate the click_events table
with data from the lists above
"""
for _ in range(CLICK_EVENTS_QUANTITY):
    # Now chose one of each list above
    referer = random.choices(referers, referers_weights, k=1)[0]
    country = random.choices(countries, countries_weights, k=1)[0]
    city = random.choices(cities[country]["names"], cities[country]["weights"], k=1)[0]
    os = random.choices(operational_systems, operational_systems_weights, k=1)[0]
    browser = random.choices(browsers, browsers_weights, k=1)[0]

    # Chose one type of device based in the os
    if os == "Android":
        device = random.choice(["Mobile", "Tablet"])
    elif os == "iOS":
        device = "Mobile"
    elif os == "iPadOS":
        device = "Tablet"
    else:
        device = "Desktop"
    
    # Chose a random datatime between July first and today
    start_date = datetime(2025, 7, 1)
    end_date = datetime.now()
    delta_date = end_date - start_date
    random_seconds = random.randint(0, int(delta_date.total_seconds()))
    random_datetime = start_date + timedelta(seconds=random_seconds)
    
    
    # Check if the link exists
    link_exist = cursor.execute("SELECT * FROM links WHERE link_id = ?", (LINK_ID,))
    cursor.close()

    # If the link doesn't exist stop the program
    if not link_exist:
        sys.exit(1)

    try:
        cursor.execute("INSERT INTO click_events (link_id, referer, country, city, os, browser, device, created_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", (LINK_ID, referer, country, city, os, browser, device, random_datetime))
        cursor.execute("UPDATE click_counters SET clicks = clicks + 1 WHERE link_id = ?", (LINK_ID,)) 
        db.commit()
    except db.DatabaseError:
        db.rollback()
        cursor.close()
        db.close()

