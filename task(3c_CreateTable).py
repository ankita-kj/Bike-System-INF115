import sqlite3

# Create table for report and reparation (part of task 3c)
def create_tables():
    conn = sqlite3.connect("bysykkel.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Report (
        Report_ID INTEGER PRIMARY KEY,
        User_ID INTEGER,
        Bike_ID INTEGER,
        Problem TEXT,
        FOREIGN KEY (User_ID) REFERENCES User(User_ID),
        FOREIGN KEY (Bike_ID) REFERENCES Bike(Bike_ID)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Reparation (
        Reparation_ID INTEGER PRIMARY KEY,
        Report_ID INTEGER,
        Bike_ID INTEGER,
        Status TEXT,
        FOREIGN KEY (Report_ID) REFERENCES Report(Report_ID),
        FOREIGN KEY (Bike_ID) REFERENCES Bike(Bike_ID)
    )
    """)

    conn.commit()
    conn.close()

create_tables()