import psycopg2
from psycopg2 import sql
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

def init_all_default_values(default_tables):
    for key, value in default_tables.items():
        initialize_default_values(key, value)

def initialize_default_values(table_name, default_rows):
    """
    Initializes default values in the specified table if they don't already exist.
    
    Args:
        table_name (str): Name of the table to initialize
        default_rows (list of dict): List of dictionaries where each dictionary
            represents a row with column names as keys
    """
    try:
        # Establish connection using context manager
        with psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME
        ) as connection:
            
            print("Connection successful!")
        
            with connection.cursor() as cursor:
                for row in default_rows:
                    # Extract columns and values from the row
                    columns = list(row.keys())
                    values = list(row.values())
                    
                    # Build SQL components safely
                    cols_ident = sql.SQL(', ').join(map(sql.Identifier, columns))
                    vals_placeholders = sql.SQL(', ').join([sql.Placeholder()] * len(values))
                    conditions = sql.SQL(' AND ').join(
                        [sql.SQL("{} = %s").format(sql.Identifier(col)) for col in columns]
                    )

                    # Construct the query
                    query = sql.SQL("""
                        INSERT INTO {table} ({cols})
                        SELECT {vals}
                        WHERE NOT EXISTS (
                            SELECT 1 FROM {table} WHERE {conditions}
                        )
                    """).format(
                        table=sql.Identifier(table_name),
                        cols=cols_ident,
                        vals=vals_placeholders,
                        conditions=conditions
                    )

                    # Execute with values duplicated for SELECT and WHERE clauses
                    cursor.execute(query, values + values)
                
                print(f"Default values initialized for {table_name}")
                
    except Exception as e:
        print(f"Error initializing defaults for {table_name}: {e}")
        if 'connection' in locals():
            connection.rollback()


def get_from_table(table_name):
    """
    Retreives all the values in the table table_name
    
    Args:
    table_name (str): name of the table
    """
    try:
        with psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME
        ) as connection:
            
            print("Connection successful!")

            with connection.cursor() as cursor:
                #Protect from SQL injections
                query = sql.SQL("SELECT * FROM {table}").format(
                    table=sql.Identifier(table_name)
                )
                cursor.execute(query)
                
                rows = cursor.fetchall()
                #Prints the values to terminal for debugging
                print(f"Current values in the table {table_name}: {rows}")

    except Exception as e:
        print(f"Error getting values from {table_name}: {e}")
        if 'connection' in locals():
            connection.rollback()