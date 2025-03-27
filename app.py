"""
Application to run flask and endpoints
"""
import urllib.request
import urllib.error

from flask import Flask, render_template, request, make_response
from flask_cors import CORS
from markupsafe import escape

from database import get_from_table, init_all_default_values, insert_into_table, search_in_table, get_random_clothing_item
from default_values import default_tables


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes




# @app.route('/api/clothing', methods=['POST'])
# def create_clothing():
#     try:
#         # Get uploaded image as binary data
#         image = request.files.get('image')
#         if image:
#             image_data = image.read()  # Read bytes directly
#         else:
#             image_data = None

#         # Extract other form data
#         data = request.form
#         category = data.get('category')
#         color_id = data.get('color_id')
#         # Add other fields

#         # Insert into database
#         insert_into_table('Clothing', {
#             'category': category,
#             'color_id': color_id,
#             'image_data': image_data,  # Store binary data
#             # Add other columns
#         })
#         return jsonify({'message': 'Clothing item created'}), 201
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500


# # Endpoint to search clothing
# @app.route('/api/clothing', methods=['GET'])
# def search_clothing():
#     filters = request.args.to_dict()
#     results = search_in_table('Clothing', filters)
#     return jsonify(results)

# # Endpoint for random outfit generation
# @app.route('/api/outfit/random', methods=['GET'])
# def random_outfit():
#     categories = ['top', 'bottom', 'shoes']
#     outfit = {}
#     for category in categories:
#         item = get_random_from_category(category)
#         outfit[category] = item
#     return jsonify(outfit)



#Testing database.py functions
# init_all_default_values(default_tables)
# get_from_table("Sizes")
# insert_into_table("Colors", {"color_id" : "10", "color_name" : "Cyan"})
# search_in_table("Colors", {'color_id' : ['1', '2']})
# get_random_clothing_item(1)

