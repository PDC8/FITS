"""
Application to run flask and endpoints
"""
import urllib.request
import urllib.error
import base64

from flask import Flask, render_template, request, make_response, jsonify, redirect, url_for
from flask_cors import CORS
from markupsafe import escape

from database import (
    get_from_table, 
    init_all_default_values, 
    insert_into_table, 
    search_in_table, 
    get_random_clothing_item
)
from default_values import default_tables

import psycopg2
from psycopg2 import sql, Binary
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/random-outfit')
def random_fit():
    return render_template('random-outfit.html')

@app.route('/search')
def search():
    return render_template('search.html')

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/api/clothing', methods=['POST'])
def create_clothing():
    try:
        # Get uploaded file
        uploaded_file = request.files.get('item_image')

        # Get form data
        data = {
            'user_id' : request.form.get('user_id'),
            'item_name' : request.form.get('item_name'),
            'brand_id' : request.form.get('brand_id'),
            'size_id' : request.form.get('size_id'),
            'type_id': request.form.get('type_id'),
            'item_image': uploaded_file.read() if uploaded_file else None
        }
        # Insert into database
        insert_into_table('Clothing Items', data)
        return redirect(url_for('home'))
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint to search clothing
@app.route('/api/clothing', methods=['GET'])
def search_clothing():
    try:
        # Use query parameters as filter
        filters = request.args.to_dict(flat=False)
        results = search_in_table('Clothing Items', filters)
        for item in results:
            if item.get('item_image'):
                # Convert bytes to base64 string
                item['item_image'] = base64.b64encode(item['item_image']).decode('utf-8')
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint to generate random outfit
@app.route('/api/outfit/random', methods=['GET'])
def random_outfit():
    try:
        # Define mapping from clothing category names to type_id values
        category_mapping = {
            'top': 1,
            'bottom': 2,
            'shoes': 3
        }
        outfit = {}
        for category, type_id in category_mapping.items():
            item = get_random_clothing_item(type_id)
            if item:
                if item.get('item_image'):
                    # Convert image bytes to a base64 string
                    item['item_image'] = base64.b64encode(item['item_image']).decode('utf-8')
            outfit[category] = item
        return jsonify(outfit), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# # Endpoint to retrieve clothing image
# @app.route('/api/clothing/image/<int:clothing_id>', methods=['GET'])
# def get_clothing_image(clothing_id):
#     try:
#         # Retrieve image binary from the database
#         with psycopg2.connect(
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             host=os.getenv("host"),
#             port=os.getenv("port"),
#             dbname=os.getenv("dbname")
#         ) as connection:
#             with connection.cursor() as cursor:
#                 query = sql.SQL("SELECT item_image FROM {table} WHERE id = %s").format(
#                     table=sql.Identifier('Clothing')
#                 )
#                 cursor.execute(query, (clothing_id,))
#                 row = cursor.fetchone()
#                 if not row or not row[0]:
#                     return jsonify({"error": "Image not found"}), 404
#                 image_data = row[0]
#         # Return the image data with an appropriate MIME type (assuming JPEG)
#         response = make_response(image_data)
#         response.headers.set('Content-Type', 'image/jpeg')
#         return response
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500



#Testing database.py functions
# init_all_default_values(default_tables)
# get_from_table("Sizes")
# insert_into_table("Users", {"name" : "Testing", "email" : "testing123@gmail.com", "password" : "should be hashed"})
# search_in_table("Clothing Items")
# get_random_clothing_item(1)

