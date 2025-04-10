import psycopg2, base64
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

def get_connection():
    """
    Creates and returns a PostgreSQL database connection.
    """
    return psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME
    )

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
        with get_connection() as connection:
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
        with get_connection() as connection:

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

def insert_into_table(table_name, data, return_col=None):
    """
    Inserts data into any table

    Args:
        table_name (str): Name of the table to insert
        data (dict): Column name : insert value pairs
    """
    try:
        with get_connection() as connection:

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
                if return_col:
                    query = sql.SQL("""
                        INSERT INTO {table} ({cols})
                        VALUES ({vals})
                        RETURNING {return_col}
                    """).format(
                        table=sql.Identifier(table_name),
                        cols=cols_ident,
                        vals=vals_placeholders,
                        return_col=sql.Identifier(return_col)
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
                if return_col:
                    ret_id = cursor.fetchone()[0]
                    connection.commit()
                    return ret_id
                else:
                    connection.commit()
                    return True
    except Exception as e:
        print(f"Error inserting into {table_name}: {e}")
    
def search_in_table(table_name, filters):
    """
    Search 'Clothing Items' based on user filters.
    Bridging tables:
      - "Clothing Colors" (with columns: c_color_id, item_id, color_id)
      - "Clothing Fabrics" (with columns: c_fabric_id, item_id, fabric_id)
    Main table:
      - "Clothing Items" (with columns: item_id, item_name, brand_id, size_id, type_id, item_image, etc.)

    The user can filter by:
      item_name (partial match, ILIKE)
      brand_id, size_id, type_id (IN matching)
      color_id (IN matching via "Clothing Colors")
      fabric_id (IN matching via "Clothing Fabrics")
    """
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                # Start from the main table "Clothing Items" (aliased as ci)
                base_query = """
                    SELECT DISTINCT ci.*
                    FROM "Clothing Items" ci
                """

                # We only join bridging tables if user selected color or fabric
                joined_color = False
                joined_fabric = False

                # If color_id is provided and not empty, join "Clothing Colors"
                if 'color_id' in filters and len(filters['color_id']) > 0 and filters['color_id'][0] != '':
                    base_query += """
                    JOIN "Clothing Colors" cc ON cc.item_id = ci.item_id
                    """
                    joined_color = True

                # If fabric_id is provided and not empty, join "Clothing Fabrics"
                if 'fabric_id' in filters and len(filters['fabric_id']) > 0 and filters['fabric_id'][0] != '':
                    base_query += """
                    JOIN "Clothing Fabrics" cf ON cf.item_id = ci.item_id
                    """
                    joined_fabric = True

                # Build WHERE conditions
                conditions = []
                params = []

                # 1 item_name partial match
                if 'item_name' in filters and len(filters['item_name']) > 0 and filters['item_name'][0] != '':
                    conditions.append("ci.item_name ILIKE %s")
                    params.append(f"%{filters['item_name'][0]}%")

                # 2 brand_id, size_id, type_id => normal columns on "Clothing Items"
                for col_name in ['user_id', 'brand_id', 'size_id', 'type_id']:
                    if col_name in filters:
                        valid_vals = [v for v in filters[col_name] if v != '']  # remove empty
                        if valid_vals:
                            placeholders = ",".join(["%s"] * len(valid_vals))
                            conditions.append(f"ci.{col_name} IN ({placeholders})")
                            params.extend(valid_vals)

                # 3 color_id => bridging table "Clothing Colors" (alias cc)
                if joined_color:
                    valid_colors = [v for v in filters['color_id'] if v != '']
                    if valid_colors:
                        placeholders = ",".join(["%s"] * len(valid_colors))
                        conditions.append(f"cc.color_id IN ({placeholders})")
                        params.extend(valid_colors)

                # 4 fabric_id => bridging table "Clothing Fabrics" (alias cf)
                if joined_fabric:
                    valid_fabrics = [v for v in filters['fabric_id'] if v != '']
                    if valid_fabrics:
                        placeholders = ",".join(["%s"] * len(valid_fabrics))
                        conditions.append(f"cf.fabric_id IN ({placeholders})")
                        params.extend(valid_fabrics)

                # Combine conditions
                if conditions:
                    base_query += " WHERE " + " AND ".join(conditions)

                # Run the final query
                cursor.execute(base_query, params)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                results = [dict(zip(columns, row)) for row in rows]
                return results

    except Exception as e:
        print("Error searching bridging tables:", e)
        return []



def get_random_clothing_item(clothing_type, user_id):
    """
    Fetches a random clothing item given a clothing_type

    Args:
        clothing_type (int) : type_id of the clothing type
        user_id (int) : user_id of the clothing
    """
    try:
        with get_connection() as connection:
            
            print("Connection successful!")

            with connection.cursor() as cursor:
                query = sql.SQL("SELECT * FROM {table} WHERE type_id = %s AND user_id = %s ORDER BY RANDOM() LIMIT 1").format(
                    table=sql.Identifier('Clothing Items')
                )
                cursor.execute(query, (clothing_type, user_id))
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, cursor.fetchone()))
    except Exception as e:
        print(f"Error fetching random {clothing_type}: {e}")
        return None

def get_user_id(netid):
    """
    Given netid, creates a new user_id if netid is new
    or retrieves user_id from DB

    Args:
        netid (str) : Yale netid
    """
    try:
        with get_connection() as connection:
            print("Connection successful!")
            with connection.cursor() as cursor:
                query = sql.SQL("""
                    INSERT INTO {table} 
                    (netid) VALUES (%s)
                    ON CONFLICT (netid) DO UPDATE SET netid = EXCLUDED.netid
                    RETURNING user_id
                """).format(table=sql.Identifier('Users'))
                
                cursor.execute(query, (netid,))
                user_id = cursor.fetchone()[0]
                connection.commit()
                return user_id
    except Exception as e:
        print(f"Error loading user_id: {e}")
        return None
    
def get_netid(user_id):
    """
    Given user_id return the netid

    Args:
        user_id (str)
    """
    try:
        with get_connection() as connection:
            print("Connection successful!")
            with connection.cursor() as cursor:
                query = sql.SQL("""
                    SELECT netid FROM {table} 
                    WHERE user_id = %s
                """).format(table=sql.Identifier('Users'))
                
                cursor.execute(query, (user_id,))
                netid = cursor.fetchone()[0]
                return netid
    except Exception as e:
        print(f"Error loading netid: {e}")
        return None

def delete_clothing_item(item_id, user_id):
    """
    Deletes a clothing item from the 'Clothing Items' table
    if it belongs to the user. Cascade deletion in the database
    will remove associated dependencies (e.g., colors, fabrics).
    
    Args:
        item_id (str or int): The ID of the clothing item.
        user_id (str or int): The ID of the user.
    
    Returns:
        int: The number of rows deleted (1 if successful, 0 if not).
    """
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                query = sql.SQL("DELETE FROM {table} WHERE item_id = %s AND user_id = %s").format(
                    table=sql.Identifier("Clothing Items")
                )
                cursor.execute(query, (item_id, user_id))
                connection.commit()
                return cursor.rowcount  # Will be 1 if deletion happened, 0 otherwise.
    except Exception as e:
        print(f"Error deleting clothing item: {e}")
        return 0

def delete_clothing_item(item_id):
    """
    Deletes a clothing item from the 'Clothing Items' table based solely on its item_id.
    Note: This function no longer checks for user ownership.
    
    Args:
        item_id (str or int): The ID of the clothing item.
        
    Returns:
        int: The number of rows deleted (1 if successful, 0 if not).
    """
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                query = sql.SQL("DELETE FROM {table} WHERE item_id = %s").format(
                    table=sql.Identifier("Clothing Items")
                )
                cursor.execute(query, (item_id,))
                connection.commit()
                return cursor.rowcount
    except Exception as e:
        print(f"Error deleting clothing item: {e}")
        return 0


def get_all_outfits():
    """
    Fetch all outfits with their items grouped by outfit_id
    """
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                query = sql.SQL("""
                    SELECT 
                        o.outfit_id,
                        o.outfit_name,
                        o.user_id,
                        JSON_AGG(
                            JSON_BUILD_OBJECT(
                                'item_id', oi.item_id,
                                'position_x', oi.position_x,
                                'position_y', oi.position_y,
                                'item_name', ci.item_name,
                                'item_image', ENCODE(ci.item_image, 'base64')
                            )
                        ) AS items
                    FROM 
                        {outfits_table} o
                    JOIN 
                        {outfit_items_table} oi ON o.outfit_id = oi.outfit_id
                    JOIN 
                        {clothing_items_table} ci ON oi.item_id = ci.item_id
                    GROUP BY 
                        o.outfit_id, o.outfit_name, o.user_id
                    ORDER BY 
                        o.outfit_id
                """).format(
                    outfits_table=sql.Identifier('Outfits'),
                    outfit_items_table=sql.Identifier('Outfit Items'),
                    clothing_items_table=sql.Identifier('Clothing Items')
                )

                cursor.execute(query)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                results = [dict(zip(columns, row)) for row in rows]

                return results

    except Exception as e:
        print(f"Error fetching outfits with items: {e}")
        return []