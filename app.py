import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

# Connect to the database
try:
    connection = psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME
    )
    print("Connection successful!")
    
    # Create a cursor to execute SQL queries
    cursor = connection.cursor()
    
    # Example query to insert a new color into the 'colors' table
    # color_id = 2  # Adjust according to your needs or use auto-increment
    # color_name = 'Blue'  # Replace with the color you want to insert
    
    # # Insert statement
    # insert_query = """
    #     INSERT INTO "Colors" (color_id, color_name)
    #     VALUES (%s, %s);
    # """

    # # Execute the insert query
    # cursor.execute(insert_query, (color_id, color_name))
    # connection.commit()  # Commit the transaction
    
    # print(f"Inserted {color_name} into the colors table.")
    
    # Fetch and display all records in the colors table
    cursor.execute("""
                   SELECT * FROM "Colors";
                   """)
    rows = cursor.fetchall()
    print("Current colors in the table:", rows)

    # Close the cursor and connection
    cursor.close()
    connection.close()
    print("Connection closed.")

except Exception as e:
    print(f"Failed to connect: {e}")