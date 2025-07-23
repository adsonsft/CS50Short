# CS50Short
#### Video Demo: https://youtu.be/XtgZmoRJVXw
#### Description: A simple application to shorten long URLs into short ones.

## Overview
CS50Short is a link shortener made as a final project for Harvard's CS50 course. The application allows users to take long URLs and generate a unique, short version with just 6 characters. These shortened links can be easily shared and tracked. Users can create accounts, log in, manage their links, and view detailed statistics about how and where their links are being accessed.

The application is built using Flask, SQLite, and includes features like user authentication, URL shortening, redirection, and analytics tracking with charts.

It includes 8 routes:

- `/` (Homepage or My Links)
- `/login`
- `/logout`
- `/register`
- `/short`
- `/<s_url>` (Redirect)
- `/statistics`
- `/statistics/<s_url>` (Dashboard)

## Homepage or "My Links" (`/`)
This is the main page for logged-in users. It accepts only GET and POST methods.
On this page, users can create a new link and see all the links they have created. Each link is displayed in a table with the following information:

- Description of the link
- Original (full) URL
- Shortened URL
- Number of times the link has been clicked
- How long the link has existed (age)

Users can edit the description of each link, but they cannot delete links. This decision was made to keep a full record of created URLs and their statistics.

## Register (`/register`)
This page allows a new user to create an account. It asks for:

- A username
- A password
- Password confirmation

The application checks if the password and confirmation match. Then, it uses the werkzeug.security library to securely hash the password before saving it into the database. This prevents storing passwords as plain text, which is a security risk.

If the registration is successful, the user is redirected to the login page.

## Login (`/login`)
This page allows users to log into their accounts. The login process is similar to the one taught in the CS50 Finance project.

The user enters their username and password. The application checks if the username exists in the database. Then it uses werkzeug.security to compare the hashed password. If everything is correct, the user's ID is saved in the Flask session, which keeps them logged in. After that, they are redirected to the homepage.

## Shorten URL (`/short`)
This route is used to create shortened links. It only accepts POST requests.

The user provides a full URL. The application then generates a random 6-character string using Python’s `string.ascii_letters` and `string.digits`. It uses `random.choice()` inside a loop to select one character at a time and build the final string.

After generating the 6-character string, the system checks the database to make sure this short code is unique. If it already exists, the process repeats until a new, unused code is found.

This means that if the same full URL is submitted more than once, it will generate different short URLs each time.

Once the unique short link is created, it is saved in the database along with the full URL, a timestamp, and the user’s ID. Then the user is redirected to the homepage where the new link appears.

Important: At this point, the link does not yet have a description.

The description can only be added or updated later from the homepage, through a POST request. Before updating, the system checks that the currently logged-in user owns the link (by comparing `session["user_id"]` and `link.user_id`).

## Redirect Route (`/<s_url>`)
This route is the core functionality of the application.

When a user visits a short link, the application looks for the corresponding full URL in the database. If it finds it:

- It logs the click event in the database (click_events table)
- It updates the total click count for that link
- It redirects the user to the original full URL

If the short link does not exist, the user is sent to a 404 error page.

For each click, the following data is collected:

- Referer (where the user came from)
- Country and City, detected by IP using GeoLite2 (the IP itself is not stored)
- Browser (like Chrome, Firefox, etc.)
- Operating System (Windows, Android, etc.)
- Device Type (mobile, desktop, tablet)

This information is used to generate usage statistics for each link.

## Statistics Overview (`/statistics`)

This page shows a simplified view of all the user's links, similar to the homepage, but with fewer details for quick access.

Each link is displayed with:

- Its description
- Total number of clicks
- How long the link has existed
- A button to access the full dashboard

Users cannot edit anything on this page. It is only for viewing and navigating to deeper statistics.

## Dashboard (`/statistics/<s_url>`)
The dashboard provides detailed analytics for a specific short link. It shows summarized data collected from the click_events table.

The data is sorted by the highest number of events in each category. For example, if most users clicked using Chrome, then "Chrome" will be shown as the top browser.

The dashboard displays the following information:

- Full URL
- short URL
- Total number of clicks
- Device types used to access the link (mobile, desktop, etc.)
- Number of clicks per day (for the last 10 days)
- Top 5 most used browsers
- Top 5 most used operating systems
- Top 5 referers
- Top 5 cities

These statistics are displayed using Chart.js to create visual pie charts and bar graphs.

With this information, the link owner can better understand their audience. For example, they may choose to focus marketing on mobile users or on people from a specific location.