import sqlite3

conn = sqlite3.connect("bysykkel.db")
cursor = conn.cursor()

cursor.execute("""
ALTER TABLE User ADD COLUMN Email TEXT;
""")

conn.commit()
conn.close()

print("Column added")
