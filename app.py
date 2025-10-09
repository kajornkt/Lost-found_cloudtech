from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)

# Dummy database for demonstration
items_db = {
    123: {
        'id': 123,
        'name': 'Blue Bag',
        'category': 'Found',
        'user_id': 1, # ID of the user who posted this item
        'user_name': 'Alice Smith',
        'place': 'University Library',
        'description': 'A small blue leather handbag, found near the main entrance on Monday morning. Contains a pair of glasses and a pen.',
        'images': [
            'https://images.unsplash.com/photo-1718029584285-b9f123f832f0?q=80&w=1974&auto=format&fit=crop',
            'https://images.unsplash.com/photo-1579761502672-ff81434c4f92?q=80&w=2070&auto=format&fit=crop',
            'https://images.unsplash.com/photo-1594223274512-ad4803739b7c?q=80&w=2070&auto=format&fit=crop'
        ],
        'contact_phone': '081-234-5678',
        'social_links': {
            'line': 'https://line.me/ti/p/~alice_smith',
            'facebook': 'https://facebook.com/alice.smith',
            'instagram': 'https://instagram.com/alice_photos',
            # 'twitter': '', # Empty means don't show
            # 'discord': '',
        }
    },
    201: {
        'id': 201,
        'name': 'Lost Keys',
        'category': 'Lost',
        'user_id': 2,
        'user_name': 'Bob Johnson',
        'place': 'Cafeteria',
        'description': 'Set of car keys with a small blue keychain. Lost sometime during lunch break.',
        'images': [
            'https://images.unsplash.com/photo-1550995166-f00d8325cfd1?q=80&w=1974&auto=format&fit=crop',
            'https://images.unsplash.com/photo-1582239327918-6f68c743828d?q=80&w=2070&auto=format&fit=crop',
        ],
        'contact_phone': '092-876-5432',
        'social_links': {
            'facebook': 'https://facebook.com/bob.j',
            'twitter': 'https://x.com/bob_j_tweets'
        }
    }
}

# Dummy user authentication (replace with real user management)
users_db = {
    1: {'username': 'alice'},
    2: {'username': 'bob'},
    3: {'username': 'viewer'}
}

@app.route('/')
def global_page():
    # In a real app, you'd fetch a list of items from your database
    return render_template('index.html', items=items_db.values())

@app.route('/item_details.html')
def item_details():
    item_id = request.args.get('id', type=int) # Get item ID from URL query parameter
    
    if item_id is None:
        return "Error: No item ID provided.", 400

    item = items_db.get(item_id)
    if not item:
        return "Item not found.", 404

    # Simulate logged-in user (replace with actual session/user management)
    # For testing, you can change current_user_id
    current_user_id = 3 # Let's say user with ID 3 is viewing
    # In a real app: current_user_id = session.get('user_id')

    # Determine if contact info should be shown
    show_contact_info = (current_user_id is not None) # Example: show if any user is logged in
    # More complex logic: show_contact_info = (current_user_id == item['user_id']) # Only owner can see

    # Filter social links to only include those that are not empty
    active_social_links = {
        platform: link for platform, link in item['social_links'].items() if link
    }

    return render_template(
        'item_details.html',
        item=item,
        show_contact_info=show_contact_info,
        social_links=active_social_links,
        # You would also pass current_user_id if needed for other logic
    )

@app.route('/login')
def login_route():
    # A simplified login for demo
    session['user_id'] = 3 # Log in user 3
    return redirect(url_for('global_page'))

@app.route('/logout')
def logout_route():
    session.pop('user_id', None)
    return redirect(url_for('global_page'))

if __name__ == '__main__':
    app.run(debug=True)