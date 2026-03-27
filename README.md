# INF115 Assignment 2

## About the Project
This is a city bike system built with Python Shiny and SQL

The app lets users:
- Register (with validation for name, phone, and email)
- Checkout bikes from stations
- Drop off bikes at other stations
- Report maintenance problems on bikes
- Filter users, stations, and bikes
- See station availability as a percentage
- View maps for each station (OpenStreetMap)

All database updates happen automatically when using the app

## How to Run
1. Install Python libraries if needed:
   ```bash
   pip install shiny pandas

2. Make sure the bysykkel.db database file is in the same folder

3. If needed, create missing tables. Run the Python files that create tables:
    ```bash
    python "task(1c).py"
    python "task(3c_CreateTable).py"

* This creates the Email column for Users and creates the Report and Reparation tables

* You only need to run these once if the database doesn't have these tables yet
    
4. Start the Shiny app:
    ```bash
    shiny run --reload oblig2.py

5. Open your browser (usually http://127.0.0.1:8000)

## About Subscriptions
The application does not include functionality for handling subscriptions because:

1. The task description does not require using subscriptions

2. The subscription table in the database is incomplete:

    *  The status column is NULL

    * The end column is NULL

    * Most subscriptions are outdated

3. A full subscription system would require:

    * New UI for purchasing subscriptions

    * Logic to calculate start/end dates

    * Changes to the checkout process to block users without an active subscription

Since it was outside the task requirements, subscription management was skipped.
However, the subscription table is available in the database for future use

## Acknowledgments
* I used the W3Schools SQL tutorial throughout the assignment to help with different SQL queries and how to use them:
    * https://www.w3schools.com/sql/default.asp

* I also used the following cheat sheets for help with Shiny Express in Python:
    * https://rstudio.github.io/cheatsheets/shiny-python.pdf
    * https://rstudio.github.io/cheatsheets/html/shiny-python.html

