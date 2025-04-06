"""
Application to run flask and endpoints
"""
#imports for image upload and random fit
import base64
import random
#imports for session_id
import os
from dotenv import load_dotenv
#imports for flask basics
from flask_cors import CORS
from flask import (
    Flask, render_template, 
    request, jsonify, 
    redirect, url_for, session)
#imports for CAS auth and login
from flask_login import (
    LoginManager, UserMixin, 
    login_user, logout_user, 
    login_required, current_user
)
from cas import CASClient
#imports for database
from default_values import default_tables
from database import (
    get_from_table, 
    init_all_default_values, 
    insert_into_table, 
    search_in_table, 
    get_random_clothing_item,
)

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv('SECRET_KEY')
CORS(app)  #enable CORS for all routes

#flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

#Yale CAS Configuration
CAS_SERVER_URL = 'https://secure6.its.yale.edu/cas/login'
CAS_SERVICE_URL = 'https://localhost:8000/login/callback' # TODO: Replace later if deployed

#CAS Client
cas_client = CASClient(
    version=3,
    service_url=CAS_SERVICE_URL,
    server_url=CAS_SERVER_URL
)

#default tables from DB used for api
brands=default_tables['Brands']
sizes=default_tables['Sizes']
types=default_tables['Clothing Types']
colors=default_tables['Colors']
fabrics=default_tables['Fabrics'] 
ALL_TYPE_IDS = [t['type_id'] for t in types]

class User(UserMixin):
    def __init__(self, netid):
        self.id = netid  # Use netid as ID temporarily
        self.netid = netid

@login_manager.user_loader
def load_user(netid):
    return User(netid)  # Temporary: No DB lookup


@app.route('/')
def home():
    if current_user.is_authenticated:
        return render_template('index.html')
    else:
        return render_template('login.html')

@app.route('/login')
def login():
    cas_login_url = cas_client.get_login_url()
    return redirect(cas_login_url)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/login/callback')
def cas_callback():
    ticket = request.args.get('ticket')
    if not ticket:
        return redirect(url_for('login'))  #no ticket provided
    #validate ticket with CAS server
    user, attributes, _ = cas_client.verify_ticket(ticket)
    if not user:
        return redirect(url_for('login'))  #invalid ticket
    #log the user in
    user_obj = User(user)
    login_user(user_obj)
    return redirect(url_for('home'))


@app.route('/random-outfit')
@login_required
def random_fit():
    return render_template('random-outfit.html')

@app.route('/search')
@login_required
def search():
    return render_template('search.html',
                           brands=brands,
                           sizes=sizes,
                           types=types,
                           colors=colors,
                           fabrics=fabrics
                        )

@app.route('/upload')
@login_required
def upload():
    return render_template('upload.html', 
                           brands=brands,
                           sizes=sizes,
                           types=types,
                           colors=colors,
                           fabrics=fabrics 
                        )

@app.route('/api/clothing', methods=['POST'])
@login_required
def create_clothing():
    try:
        #get uploaded file
        uploaded_file = request.files.get('item_image')

        #get form data
        data = {
            'user_id' : request.form.get('user_id'),
            'item_name' : request.form.get('item_name'),
            'brand_id' : request.form.get('brand_id'),
            'size_id' : request.form.get('size_id'),
            'type_id': request.form.get('type_id'),
            'item_image': uploaded_file.read() if uploaded_file else None
        }
        #insert into Clothing Items Table and get primary key
        clothing_item_id = str(insert_into_table('Clothing Items', data, True))
        
        #insert into Clothing Colors and Clothing Fabrics Tables
        color_ids = request.form.getlist('color_id')
        for id in color_ids:
            id = str(id)
            insert_into_table('Clothing Colors', {'item_id' : clothing_item_id, 'color_id' : id})
        fabric_ids = request.form.getlist('fabric_id')
        for id in fabric_ids:
            id = str(id)
            insert_into_table('Clothing Fabrics', {'item_id' : clothing_item_id, 'fabric_id' : id})
        print(color_ids, fabric_ids)
        return redirect(url_for('home'))
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#endpoint to search clothing
@app.route('/api/clothing', methods=['GET'])
@login_required
def search_clothing():
    try:
        #use query parameters as filter
        filters = request.args.to_dict(flat=False)
        #get all type_ids
        if 'type_id' in filters and filters['type_id'] == [""]:
            filters['type_id'] = ALL_TYPE_IDS
        results = search_in_table('Clothing Items', filters)
        for item in results:
            if item.get('item_image'):
                #convert bytes to base64 string
                item['item_image'] = base64.b64encode(item['item_image']).decode('utf-8')
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


#endpoint to generate random outfit
@app.route('/api/outfit/random', methods=['GET'])
@login_required
def random_outfit():
    try:
        #define mapping from clothing category names to type_id values
        category_mapping = {
            'tops': [1, 2, 3],  #T-Shirt, Tank Top, Sweatshirt
            'bottoms': [4, 5, 6],  #Jeans, Shorts, Skirt
            'shoes': [7],  #Shoes
        }

        outfit = {}
        for category, type_ids in category_mapping.items():
            rand_id = random.choice(type_ids)
            item = get_random_clothing_item(rand_id)
            if item:
                if item.get('item_image'):
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

