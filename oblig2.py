import sqlite3
from shiny import reactive, render
from shiny.express import input, ui, render
import pandas as pd

# Reactive value used to trigger updates in tables after checkout and dropoff
data_refresh = reactive.Value(False)

#           --TASK 1A--
ui.hr()
ui.h2("User Registration")

with ui.card():
    ui.input_text("name", "Name:")
    ui.input_text("phone", "Phone number:")
    ui.input_text("email", "Email:")
    ui.input_action_button("submit", "Submit", class_="btn-success", style="width: 300px;")


#           --TASK 1B--
alphabet = "abcdefghijklmnopqrstuvwxyzæøå"

@render.text
@reactive.event(input.submit)
def name_status():
    name = input.name()
    if not name or not any(char.isalpha() for char in name):
        return f"{name} - Not valid"
    isValid = all(char.lower() in alphabet or char == " " for char in name)
    return f"{name} - {'Valid' if isValid else 'Not valid'}"

@render.text
@reactive.event(input.submit)
def phone_status():
    phone = input.phone()
    isValid = phone.isdigit() and len(phone) == 8
    status = "Valid" if isValid else "Not valid"
    return f"{phone} - {status}"

@render.text
@reactive.event(input.submit)
def email_status():
    email = input.email()
    isValid = "@" in email
    status = "Valid" if isValid else "Not valid"
    return f"{email} - {status}"

@render.text
@reactive.event(input.submit)
def submission_status():
    name = input.name()
    phone = input.phone()
    email = input.email()

    name_valid = all(c.lower() in alphabet for c in name if c.isalpha())
    phone_valid = phone.isdigit() and len(phone) == 8
    email_valid = "@" in email

    if name_valid and phone_valid and email_valid:
        conn = sqlite3.connect("bysykkel.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM User 
            WHERE LOWER(User_name) = ? AND Phone_number = ? AND LOWER(Email) = ?
        """, (name.lower(), phone, email.lower()))
        existing_user = cursor.fetchone()

       # Check if user already exists (same number, email, and name)
        if existing_user:
            conn.close()
            return "This user already has an existing account."

        cursor.execute("""
            INSERT INTO User (User_name, Phone_number, Email)
            VALUES (?, ?, ?)
        """, (name, phone, email.lower()))
        conn.commit()
        conn.close()
        return f"User {name} has been registered!"
    else:
        return "Please correct the invalid inputs."


#           --TASK 2A--
ui.hr()
ui.h2("Filter Users")

with ui.card():
    ui.input_text("filter_user", "Filter users by name:")
    ui.input_action_button("filter_users", "Filter", class_="btn-primary", style="width: 300px;")
    ui.input_action_button("reset_users", "Reset", class_="btn-secondary", style="width: 300px;")

search_term = reactive.value("")

@reactive.effect
@reactive.event(input.filter_users)
def update_search_term():
    search_term.set(input.filter_user())

@reactive.effect
@reactive.event(input.reset_users)
def reset_search_term():
    search_term.set("")
    ui.update_text("filter_user", value="")

# Refresh the user list after a new user has been registered
@reactive.effect
@reactive.event(input.submit)
def force_refresh_users_on_submit():
    search_term.set("___temp___")
    search_term.set("")

@render.data_frame
def filtered_user_table():
    term = search_term.get()  
    conn = sqlite3.connect("bysykkel.db")
    query = """
        SELECT User_ID, User_name, Phone_number
        FROM User
        WHERE User_name LIKE ?
        ORDER BY User_name ASC
    """
    df = pd.read_sql_query(query, conn, params=(f"%{term}%",))
    conn.close()

    df.columns = ["User ID", "Name", "Phone number"]
    return df

#           --TASK 2B--
ui.hr()
ui.h2("Trips ended per station")

with ui.card():
    @render.data_frame
    @reactive.event(data_refresh)  # Re-render when data_refresh changes after checkout/dropoff
    def trips_table():
        conn = sqlite3.connect("bysykkel.db") 
        cursor = conn.cursor()
        query = """
            SELECT 
                s.Station_ID,
                s.Station_name,
                COUNT(t.End_station)
            FROM Trip t
            JOIN Station s ON t.End_station = s.Station_ID
            GROUP BY s.Station_ID, s.Station_name
            ORDER BY COUNT(t.End_station) DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        df = pd.DataFrame(rows, columns=["Station ID", "Station name", "Number of trips"])
        return df
    

#           --TASK 2C--
ui.hr()
ui.h2("Filter stations and bikes to view availability")

with ui.card():
    ui.input_text("station_name", "Filter by station name:", value="")
    ui.input_text("bike_name", "Filter by bike name:", value="")
    ui.input_action_button("filter_availability", "Filter", class_="btn-primary", style="width: 300px;")
    ui.input_action_button("reset_availability", "Reset", class_="btn-secondary", style="width: 300px;")

station_filter = reactive.value("")
bike_filter = reactive.value("")

@reactive.effect
@reactive.event(input.filter_availability)
def update_filters():
    station_filter.set(input.station_name().strip())
    bike_filter.set(input.bike_name().strip())

@reactive.effect
@reactive.event(input.reset_availability)
def reset_filters():
    station_filter.set("")
    bike_filter.set("")
    ui.update_text("station_name", value="")
    ui.update_text("bike_name", value="")    

@render.data_frame
@reactive.event(data_refresh)  # Re-render when data_refresh changes after checkout/dropoff
def filtered_station_bike():
    station_term = station_filter.get()
    bike_term = bike_filter.get()
    
    conn = sqlite3.connect("bysykkel.db")

    query = """
        SELECT station.Station_name, bike.Bike_name
        FROM Bike bike
        JOIN Station station ON bike.Last_station_ID = station.Station_ID
        WHERE bike.Current_status = 'Parked'
    """
    params = []
    
    # Add filter for station name if given
    if station_term:
        query += " AND station.Station_name LIKE ?"
        params.append(f"%{station_term}%")

    # Add filter for bike name if given
    if bike_term:
        query += " AND bike.Bike_name LIKE ?"
        params.append(f"%{bike_term}%")
    
    query += " ORDER BY station.Station_name, bike.Bike_name"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    df.columns = ["Station", "Bike"]
    return df


#           --TASK 3A-- 
ui.hr()
ui.h2("Checkout a bike")


# Connect to database once to load initial dropdown options, user + stations
conn = sqlite3.connect("bysykkel.db")
cursor = conn.cursor()

initial_users = [row[0] for row in cursor.execute("SELECT DISTINCT User_name FROM User ORDER BY User_name")]
initial_stations = [row[0] for row in cursor.execute("SELECT DISTINCT Station_name FROM Station ORDER BY Station_name")]
conn.close()

with ui.card():
    ui.input_select("checkout_user", "Select user", choices=["-- Select user --"] + initial_users)
    ui.input_select("checkout_station", "Select station", choices=["-- Select station --"] + initial_stations)
    ui.input_action_button("checkout", "Checkout", class_="btn-success", style="width: 300px;")

active_trip = {}

# Update the user dropdown if a new user is registered
@reactive.effect
@reactive.event(input.submit)
def update_checkout_user_dropdown():
    conn = sqlite3.connect("bysykkel.db")
    cursor = conn.cursor()
    updated_users = [row[0] for row in cursor.execute("SELECT DISTINCT User_name FROM User ORDER BY User_name")]
    conn.close() 
    ui.update_select("checkout_user", choices=["-- Select user --"] + updated_users)

@render.text
@reactive.event(input.checkout)
def do_checkout():
    # Force refresh the database before checkout: 
    # If a new user was added via registration, we need to make sure the changes are fully saved
    # into the database. SQL might not "see" the new user yet.
    conn = sqlite3.connect("bysykkel.db").close()

    # Open a fresh new connection for the real checkout process
    conn = sqlite3.connect("bysykkel.db")
    cursor = conn.cursor()

    user_name = input.checkout_user().strip()
    station_name = input.checkout_station()

    if user_name.startswith("--") or station_name.startswith("--"):
        return "Please select both a user and a station before checking out."

    cursor.execute("SELECT User_ID FROM User WHERE User_name = ?", (user_name,))
    user_row = cursor.fetchone()
    user_id = user_row[0]

    cursor.execute("SELECT Station_ID FROM Station WHERE Station_name = ?", (station_name,))
    station_row = cursor.fetchone()
    station_id = station_row[0]

    cursor.execute("""
        SELECT Trip_ID FROM Trip 
        WHERE User_ID = ? AND End_time IS NULL
    """, (user_id,))
    active_trip_row = cursor.fetchone()
    if active_trip_row:
        conn.close()
        return f"{user_name} already has an active trip."
    
    cursor.execute("""
        SELECT Bike_ID, Bike_name 
        FROM Bike
        WHERE Last_station_ID = ? AND Current_status = 'Parked'
        LIMIT 1
    """, (station_id,))
    bike_row = cursor.fetchone()
    if not bike_row:
        return f"No available bikes at {station_name} right now."
    
    bike_id, bike_name = bike_row

    cursor.execute("""
        UPDATE Bike
        SET Current_status = 'Active'
        WHERE Bike_ID = ?
    """, (bike_id,))

    cursor.execute("""
        UPDATE Station
        SET Available_parking = Available_parking + 1
        WHERE Station_ID = ?
    """, (station_id,))

    cursor.execute("""
        INSERT INTO Trip (User_ID, Bike_ID, Start_station, Start_time)
        VALUES (?, ?, ?, DATETIME('now'))
    """, (user_id, bike_id, station_id))

    conn.commit()

    cursor.execute("SELECT last_insert_rowid()")
    trip_id = cursor.fetchone()[0]

    conn.close()

    active_trip['trip_id'] = trip_id
    active_trip['user_id'] = user_id
    active_trip['bike_id'] = bike_id
    active_trip['bike_name'] = bike_name
    active_trip['start_station_id'] = station_id

    data_refresh.set(not data_refresh.get())   # Trigger refresh so UI tables update immediately
    return f"{user_name} has checked out bike '{bike_name}' from {station_name}. Trip started!"


#           --TASK 3B--
ui.hr()
ui.h2("Dropoff a bike")

conn = sqlite3.connect("bysykkel.db")
cursor = conn.cursor()

initial_users = [row[0] for row in cursor.execute("SELECT DISTINCT User_name FROM User ORDER BY User_name")]
initial_stations = [row[0] for row in cursor.execute("SELECT DISTINCT Station_name FROM Station ORDER BY Station_name")]
conn.close()

with ui.card():
    ui.input_select("dropoff_user", "Select user", choices=["-- Select user --"] + initial_users)
    ui.input_select("dropoff_station", "Select station", choices=["-- Select station --"] + initial_stations)
    ui.input_action_button("dropoff", "Dropoff", class_="btn-success", style="width: 300px;")

# Used to trigger complaint form after dropoff
dropoff = reactive.Value(False)

# Update the user dropdown if a new user is registered
@reactive.effect
@reactive.event(input.submit)
def update_dropoff_user_dropdown():
    conn = sqlite3.connect("bysykkel.db")
    cursor = conn.cursor()
    users = [row[0] for row in cursor.execute("SELECT DISTINCT User_name FROM User ORDER BY User_name")]
    conn.close() 
    ui.update_select("dropoff_user", choices=["-- Select user --"] + users)

@render.text
@reactive.event(input.dropoff)
def do_dropoff():
    conn = sqlite3.connect("bysykkel.db") 
    cursor = conn.cursor() 
    user_name = input.dropoff_user().strip()
    station_name = input.dropoff_station()

    if user_name.startswith("--") or station_name.startswith("--"):
        return "Please select both a user and a station before returning the bike."

    cursor.execute("SELECT User_ID FROM User WHERE User_name = ?", (user_name,))
    user_row = cursor.fetchone()
    user_id = user_row[0]

    cursor.execute("SELECT Station_ID FROM Station WHERE Station_name = ?", (station_name,))
    station_row = cursor.fetchone()
    station_id = station_row[0]

    cursor.execute("SELECT Available_parking FROM Station WHERE Station_ID = ?", (station_id,))
    available_row = cursor.fetchone()
    available_parking = available_row[0]

    if available_parking <= 0:
        return f"No available parking at {station_name}. Please select another station."

    cursor.execute("""
        SELECT Trip_ID, Bike.Bike_ID, Bike_name
        FROM Trip
        JOIN Bike ON Trip.Bike_ID = Bike.Bike_ID
        WHERE Trip.User_ID = ? AND Trip.End_time IS NULL
        LIMIT 1
    """, (user_id,))
    trip_row = cursor.fetchone()
    if not trip_row:
        return f"No active trip found for {user_name}."

    trip_id, bike_id, bike_name = trip_row

    cursor.execute("""
        UPDATE Bike
        SET Current_status = 'Parked', Last_station_ID = ?
        WHERE Bike_ID = ?
    """, (station_id, bike_id))

    cursor.execute("""
        UPDATE Station
        SET Available_parking = Available_parking - 1
        WHERE Station_ID = ?
    """, (station_id,))

    cursor.execute("""
        UPDATE Trip
        SET End_station = ?, End_time = DATETIME('now')
        WHERE Trip_ID = ?
    """, (station_id, trip_id))

    conn.commit()
    conn.close()

    active_trip['trip_id'] = trip_id
    active_trip['user_id'] = user_id
    active_trip['bike_id'] = bike_id
    active_trip['bike_name'] = bike_name
    active_trip['end_station_id'] = station_id

    dropoff.set(True) # Trigger the complaint form to show
    data_refresh.set(not data_refresh.get()) # Refresh UI tables
    return f"{user_name} has returned bike '{bike_name}' to {station_name}. Trip ended."


#           --TASK 3C--
ui.hr()
with ui.card():
    @render.ui
    @reactive.event(dropoff) # Only show complaint section after dropoff happens
    def complaint_section():
        if dropoff():
            return ui.div(
                ui.h2("Report a complaint (only after dropoff)"),
                ui.input_radio_buttons("has_complaint", "Any problem(s)?", choices=["No", "Yes"]),
                ui.input_selectize("complaint_type", "Select problem(s)", choices=dict(zip(range(len(complaints)), complaints)), multiple=True),
                ui.input_action_button("submit_complaint", "Submit complaint", class_="btn-success", style="width: 300px;")
            )
        return ui.span() # If no dropoff, don't show anything

complaints = [
    "Flat tire", "Brakes not working", "Gear issue", "Loose chain", "Broken handle", "Missing seat",
    "Wobbly wheel", "Damaged pedal", "Rusty frame", "Faulty bell", "Leaking tire", "Loose bolts or nuts"
]

@render.text
@reactive.event(input.submit_complaint)
def complaint_result():
    if not dropoff():
        return ""
    
    if input.has_complaint() == "Yes":
        complaint_ids = input.complaint_type()
        if complaint_ids:
            con = sqlite3.connect("bysykkel.db")
            cur = con.cursor()

            user_id = active_trip['user_id']
            bike_id = active_trip['bike_id']

            for complaint_id in complaint_ids:
                cur.execute("""
                    INSERT INTO Report (User_ID, Bike_ID, Problem)
                    VALUES (?, ?, ?)
                """, (user_id, bike_id, complaints[int(complaint_id)]))

                report_id = cur.lastrowid

                cur.execute("""
                    INSERT INTO Reparation (Report_ID, Bike_ID, Status)
                    VALUES (?, ?, ?)
                """, (report_id, bike_id, "Pending"))
                
            con.commit()
            con.close()

            dropoff.set(False) # Reset dropoff so complaint form hides again
            return "Complaint(s) have been submitted successfully!"
        else:
            return "No complaint selected."
        
    dropoff.set(False)
    return "You selected 'No' for reporting a complaint."


#           --TASK 4--
ui.hr()
ui.h2("Station availability mapping")

# Open connection to fetch initial station names for dropdown
conn = sqlite3.connect("bysykkel.db")
cursor = conn.cursor()

initial_stations = [row[0] for row in cursor.execute("SELECT Station_name FROM Station ORDER BY Station_name")]
conn.close()

with ui.card():
    ui.input_selectize(
        "station_select",
        "Select a station",
        choices=["-- Select station --"] + initial_stations
    )
    ui.input_switch("trip_in_progress", "Trip in progress", value=False)

@render.table(render_links=True, escape=False)
@reactive.event(input.station_select, input.trip_in_progress)
@reactive.event(data_refresh) # Re-render also if database updates (trip, dropoff)
def station_availability():
    selected_station = input.station_select()
    if selected_station == "-- Select Station --" or not selected_station:
        return pd.DataFrame(columns=["Name", "Availability", "Location"])

    trip_in_progress = input.trip_in_progress()

    # Open fresh database connection every time user changes inputs
    conn = sqlite3.connect("bysykkel.db") 
    cursor = conn.cursor()

    query = """
        SELECT 
            Station_name,
            Max_parking,
            Available_parking,
            Latitude,
            Longitude
        FROM Station
        WHERE Station_name = ?
    """
    cursor.execute(query, (selected_station,))
    row = cursor.fetchone()
    conn.close()

    # Check if no station was found
    if not row:
        return pd.DataFrame(columns=["Name", "Availability", "Location"])

    station_name, max_parking, available_parking, latitude, longitude = row # Unpack the fetched station rows into separate variables
    occupied_spots = max_parking - available_parking

    # Calculate availability percentage based on trip in progress or not
    if trip_in_progress:
        availability = (available_parking / max_parking) * 100 
    else:
        availability = (occupied_spots / max_parking) * 100 

    map_link = f'<a href="https://www.openstreetmap.org/#map=17/{latitude}/{longitude}">Map</a>'

    df = pd.DataFrame({
        "Name": [station_name],
        "Availability": [f"{availability:.0f}%"],
        "Location": [map_link]
    })
    return df



