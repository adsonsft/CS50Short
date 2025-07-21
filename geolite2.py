from flask import request

import geoip2.database
import geoip2.errors

# Path to geolite2 database
db = './geolite2/GeoLite2-City.mmdb'
reader = geoip2.database.Reader(db)

def get_user_location(ip):
    """Uses Geolite2 to get user city and country by the ip"""
    
    try:
        response = reader.city(ip)
        country = response.country.name or "unknown"
        city = response.city.name or "unknown"
    except geoip2.errors.AddressNotFoundError:
        country = city = "unknown"

    return {
            "country": country,
            "city": city
            }
