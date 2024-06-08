import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('travel2.sqlite')
# Create a cursor object
cursor = conn.cursor()
# Fetch table names from the database
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# Print the table names
for table in tables:
    table_name = table[0]

    # Query to fetch column information for the specified table
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()

    # Display the column information
    print("colomns of table", table_name, ":")
    for column in columns:
        
        print(column[1]) 

# test data in the tables
# cursor.execute("SELECT * FROM hotels limit 5;")
# tables_inf = cursor.fetchall()
# print(tables_inf)

cursor.execute("SELECT * FROM hotels limit 5;")
data = cursor.fetchall()
print(data)
# Close the connection
conn.close()
