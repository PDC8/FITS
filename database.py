import psycopg2
from psycopg2 import sql, Binary
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
    """
    Initializes multiple tables of default values
    """
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

def insert_into_table(table_name, data, return_id=False):
    """
    Inserts data into any table

    Args:
        table_name (str): Name of the table to insert
        data (dict): Column name : insert value pairs
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
                # Convert binary data to PostgreSQL-compatible format
                if 'item_image' in data and data['item_image'] is not None:
                    data['item_image'] = Binary(data['item_image'])

                columns = list(data.keys())
                # print(columns)
                values = list(data.values())
                # print(values)
                cols_ident = sql.SQL(', ').join(map(sql.Identifier, columns))
                vals_placeholders = sql.SQL(', ').join([sql.Placeholder()] * len(values))

                if return_id:
                    query = sql.SQL("""
                        INSERT INTO {table} ({cols})
                        VALUES ({vals})
                        RETURNING item_id
                    """).format(
                        table=sql.Identifier(table_name),
                        cols=cols_ident,
                        vals=vals_placeholders
                    )
                else:
                    query = sql.SQL("""
                        INSERT INTO {table} ({cols})
                        VALUES ({vals})
                    """).format(
                        table=sql.Identifier(table_name),
                        cols=cols_ident,
                        vals=vals_placeholders
                    )
                cursor.execute(query, values)

                if return_id:
                    item_id = cursor.fetchone()[0]
                    connection.commit()
                    return item_id
                else:
                    connection.commit()
                    return True
    except Exception as e:
        print(f"Error inserting into {table_name}: {e}")
    
def search_in_table(table_name, filters):
    """
    Searches a given table based on filters

    Args:
        table_name (str): Name of table to query
        filters (dict): Column name : search value (can be 1 value or a list of values)
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
                conditions = []
                params = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        placeholders = sql.SQL(', ').join(sql.Placeholder() * len(value))
                        conditions.append(sql.SQL("{col} IN ({vals})").format(
                            col=sql.Identifier(key),
                            vals=placeholders
                        ))
                        params.extend(value)
                    else:
                        conditions.append(sql.SQL("{col} = %s").format(col=sql.Identifier(key)))
                        params.append(value)
                where_clause = sql.SQL(' AND ').join(conditions) if conditions else sql.SQL('1=1')
                query = sql.SQL("SELECT * FROM {table} WHERE {where}").format(
                    table=sql.Identifier(table_name),
                    where=where_clause
                )
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                print(results)
                return results
    except Exception as e:
        print(f"Error searching {table_name}: {e}")
        return []

def get_random_clothing_item(clothing_type):
    """
    Fetches a random clothing item given a clothing_type

    Args:
        clothing_type (int) : type_id of the clothing type
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
                query = sql.SQL("SELECT * FROM {table} WHERE type_id = %s ORDER BY RANDOM() LIMIT 1").format(
                    table=sql.Identifier('Clothing Items')
                )
                cursor.execute(query, (clothing_type,))
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, cursor.fetchone()))
    except Exception as e:
        print(f"Error fetching random {clothing_type}: {e}")
        return None
