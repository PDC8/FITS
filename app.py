"""
Application to run flask and endpoints
"""
# Imports for image upload and random fit
import base64
import random
# Imports for session_id
import os
from dotenv import load_dotenv
# Imports for flask basics
from flask_cors import CORS
from flask import (
    Flask, render_template, 
    request, jsonify, 
    redirect, url_for, session)
# Imports for CAS auth and login
from flask_login import (
    LoginManager, UserMixin, 
    login_user, logout_user, 
    login_required, current_user
)
from cas import CASClient
# Imports for database
from default_values import default_tables
from database import (
    get_from_table, 
    init_all_default_values, 
    insert_into_table, 
    search_in_table, 
    get_random_clothing_item,
    get_user_id,
    get_netid,
    delete_clothing_item,
    get_all_outfits,
    add_friend,
    get_friends,
    get_all_users,
    get_friend_requests,
    accept_friend
)
# Import for image bg remvoer
from rembg import remove

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv('SECRET_KEY')
CORS(app)  # Enable CORS for all routes

# Flask-Login
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

# Default tables from DB used for api
brands=default_tables['Brands']
sizes=default_tables['Sizes']
types=default_tables['Clothing Types']
colors=default_tables['Colors']
fabrics=default_tables['Fabrics'] 
ALL_TYPE_IDS = [t['type_id'] for t in types]

class User(UserMixin):
    def __init__(self, user_id, netid):
        self.id = user_id  # Use netid as ID temporarily
        self.netid = netid

@login_manager.user_loader
def load_user(user_id):
    netid = get_netid(user_id)
    return User(user_id, netid)


@app.route('/')
def home():
    if current_user.is_authenticated:
        outfits = get_all_outfits() 
        return render_template('index.html', outfits=outfits)
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
        return redirect(url_for('login'))  # No ticket provided
    # Validate ticket with CAS server
    netid, _, _ = cas_client.verify_ticket(ticket)
    if not netid:
        return redirect(url_for('login'))  # Invalid ticket
    # Create or get netid from DB
    user_id = get_user_id(netid)

    # Log the user in
    user = User(user_id, netid)
    login_user(user)
    return redirect(url_for('home'))


@app.route('/random-outfit')
@login_required
def random_fit():
    return render_template('generate-outfit.html')

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
        # Get uploaded file
        uploaded_file = request.files.get('item_image')

        # Remove bg
        if uploaded_file:
            original_image = uploaded_file.read()
            processed_image = remove(original_image)

        # Get form data
        data = {
            'user_id' : current_user.id,
            'item_name' : request.form.get('item_name'),
            'brand_id' : request.form.get('brand_id'),
            'size_id' : request.form.get('size_id'),
            'type_id': request.form.get('type_id'),
            'item_image': processed_image
        }
        # Insert into Clothing Items Table and get primary key
        clothing_item_id = str(insert_into_table('Clothing Items', data, return_col='item_id'))
        
        # Insert into Clothing Colors and Clothing Fabrics Tables
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

# Endpoint to search clothing
@app.route('/api/clothing', methods=['GET'])
@login_required
def search_clothing():
    try:
        # Use query parameters as filter
        filters = request.args.to_dict(flat=False)
        filters['user_id'] = [current_user.id]
        
        # Get all type_ids
        if 'type_id' in filters and filters['type_id'] == [""]:
            filters['type_id'] = ALL_TYPE_IDS
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
@login_required
def random_outfit():
    try:
        # Define mapping from clothing category names to type_id values
        category_mapping = {
            'tops': [1, 2, 3],  # T-Shirt, Tank Top, Sweatshirt
            'bottoms': [4, 5, 6],  # Jeans, Shorts, Skirt
            'shoes': [7],  # Shoes
        }

        outfit = {}
        for category, type_ids in category_mapping.items():
            rand_id = random.choice(type_ids)
            item = get_random_clothing_item(rand_id, current_user.id)
            if item:
                if item.get('item_image'):
                    item['item_image'] = base64.b64encode(item['item_image']).decode('utf-8')
            outfit[category] = item
        return jsonify(outfit), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

# Endpoint to delete clothing item
@app.route('/api/clothing/<item_id>', methods=['DELETE'])
@login_required
def delete_clothing(item_id):
    """
    Endpoint to delete a clothing item based solely on the item_id.
    """
    try:
        rows_deleted = delete_clothing_item(item_id)
        if rows_deleted:
            return jsonify({"message": "Clothing item deleted successfully."}), 200
        else:
            return jsonify({"error": "Clothing item not found."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
@app.route('/delete')
@login_required
def delete_page():
    return render_template('delete.html', brands=brands, sizes=sizes, types=types, colors=colors, fabrics=fabrics)


# Endpoint to save outfit
@app.route('/api/outfits', methods=['POST'])
@login_required
def save_outfit():
    try:
        # Parse the request JSON
        data = request.json
        outfit_name = data.get('name', 'Unnamed Outfit')
        items = data.get('items', [])

        if not items:
            return jsonify({'error': 'No items provided to save the outfit.'}), 400

         # Step 1: Insert the outfit into the outfits table
        outfit_data = {
            'user_id': current_user.id,  # Assuming Flask-Login is used for user management
            'outfit_name': outfit_name
        }
        outfit_id = insert_into_table('Outfits', outfit_data, return_col='outfit_id')
        print(outfit_id, current_user.id)
        # Step 2: Insert each item into the outfit_items table
        for item in items:
            outfit_item_data = {
                'item_id': item['item_id'],
                'outfit_id': outfit_id,
                'position_x': item['position']['x'],
                'position_y': item['position']['y']
            }
            insert_into_table('Outfit Items', outfit_item_data)

        return jsonify({'message': 'Outfit saved successfully!', 'outfit_id': outfit_id}), 201

    except Exception as e:
        print(f"Error saving outfit: {e}")
        return jsonify({'error': 'An error occurred while saving the outfit.'}), 500

@app.route('/api/outfits', methods=['GET'])
def get_outfits():
    try:
        # Fetch all outfits and their items from the database
        outfits = get_all_outfits()
        
        return jsonify(outfits), 200
    except Exception as e:
        print(f"Error fetching outfits: {e}")
        return jsonify({'error': 'Failed to fetch outfits'}), 500


# Friends endpoints:
@app.route('/api/users', methods=['GET'])
@login_required
def list_users():
    users = get_all_users()
    return jsonify([{'user_id': uid, 'netid': netid} for uid, netid in users]), 200

@app.route('/api/friends', methods=['POST'])
@login_required
def add_friend_route():
    data = request.json or {}
    fid = data.get('friend_id')
    if not fid:
        return jsonify({'error': 'friend_id is required'}), 400
    try:
        add_friend(current_user.id, fid)
        return jsonify({'message': 'Friend added'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/friends', methods=['GET'])
@login_required
def get_friends_route():
    friends = get_friends(current_user.id)
    return jsonify([{'user_id': fid, 'netid': netid} for fid, netid in friends]), 200

@app.route('/api/friends/outfits', methods=['GET'])
@login_required
def get_friends_outfits_route():
    fids = [fid for fid, _ in get_friends(current_user.id)]
    outfits = get_all_outfits()
    return jsonify([o for o in outfits if o['user_id'] in fids]), 200

@app.route('/friends')
@login_required
def friends_page():
    return render_template('friends.html')

@app.route('/api/friend-requests', methods=['GET'])
@login_required
def friend_requests_route():
    reqs = get_friend_requests(current_user.id)
    return jsonify([{'requester_id': rid, 'netid': netid} for rid, netid in reqs]), 200

@app.route('/api/friends/accept', methods=['POST'])
@login_required
def accept_friend_route():
    data = request.json or {}
    rid = data.get('requester_id')
    if not rid:
        return jsonify({'error': 'requester_id is required'}), 400
    try:
        accept_friend(rid, current_user.id)
        return jsonify({'message': 'Friend request accepted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/friends/<int:friend_id>')
@login_required
def friend_outfits_page(friend_id):
    # Only allow if they’re actually mutual friends
    mutual_ids = [fid for fid, _ in get_friends(current_user.id)]
    if friend_id not in mutual_ids:
        return redirect(url_for('friends_page'))
    # Fetch all outfits and filter to this friend
    all_outfits = get_all_outfits()
    friend_outfits = [o for o in all_outfits if o['user_id'] == friend_id]
    friend_netid = get_netid(friend_id)
    return render_template(
        'friend_outfits.html',
        outfits=friend_outfits,
        friend_netid=friend_netid
    )



#Testing database.py functions
# init_all_default_values(default_tables)
# get_from_table("Sizes")
# insert_into_table("Users", {"name" : "Testing", "email" : "testing123@gmail.com", "password" : "should be hashed"})
# search_in_table("Clothing Items")
# get_random_clothing_item(1)

