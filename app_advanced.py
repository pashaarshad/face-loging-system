from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import base64
import hashlib
import json
import pickle
from datetime import datetime
import face_recognition
import numpy as np
from PIL import Image
import io

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this to a random secret key

# Face encodings database
FACE_ENCODINGS_FILE = 'face_encodings.pkl'

# Database setup
def init_db():
    conn = sqlite3.connect('face_login_advanced.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            face_encoding BLOB,
            face_images TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Login attempts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            user_id INTEGER,
            attempt_type TEXT,
            success BOOLEAN,
            confidence REAL,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def load_face_encodings():
    """Load all face encodings from file"""
    if os.path.exists(FACE_ENCODINGS_FILE):
        with open(FACE_ENCODINGS_FILE, 'rb') as f:
            return pickle.load(f)
    return {}

def save_face_encodings(encodings_dict):
    """Save face encodings to file"""
    with open(FACE_ENCODINGS_FILE, 'wb') as f:
        pickle.dump(encodings_dict, f)

def process_face_image(image_data):
    """Process base64 image and extract face encoding"""
    try:
        # Remove data URL prefix if present
        if 'data:image' in image_data:
            image_data = image_data.split(',')[1]
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert PIL image to numpy array
        image_array = np.array(image)
        
        # Find face locations and encodings
        face_locations = face_recognition.face_locations(image_array, model="hog")
        
        if len(face_locations) == 0:
            return None, "No face detected in the image"
        
        if len(face_locations) > 1:
            return None, "Multiple faces detected. Please ensure only one face is visible"
        
        # Get face encoding
        face_encodings = face_recognition.face_encodings(image_array, face_locations)
        
        if len(face_encodings) == 0:
            return None, "Could not encode the face"
        
        return face_encodings[0], None
        
    except Exception as e:
        return None, f"Error processing image: {str(e)}"

def find_matching_user(face_encoding, tolerance=0.6):
    """Find matching user based on face encoding"""
    conn = sqlite3.connect('face_login_advanced.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, username, face_encoding FROM users WHERE face_encoding IS NOT NULL')
    users = cursor.fetchall()
    conn.close()
    
    best_match = None
    best_distance = float('inf')
    
    for user_id, username, stored_encoding_blob in users:
        if stored_encoding_blob:
            try:
                # Deserialize the stored encoding
                stored_encoding = pickle.loads(stored_encoding_blob)
                
                # Calculate face distance
                face_distance = face_recognition.face_distance([stored_encoding], face_encoding)[0]
                
                # Check if this is the best match so far
                if face_distance < tolerance and face_distance < best_distance:
                    best_distance = face_distance
                    best_match = {
                        'user_id': user_id,
                        'username': username,
                        'distance': face_distance,
                        'confidence': 1 - face_distance
                    }
                    
            except Exception as e:
                print(f"Error processing stored encoding for user {username}: {e}")
                continue
    
    return best_match

def log_login_attempt(username, user_id, attempt_type, success, confidence, ip_address):
    conn = sqlite3.connect('face_login_advanced.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO login_attempts (username, user_id, attempt_type, success, confidence, ip_address)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (username, user_id, attempt_type, success, confidence, ip_address))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index_advanced.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            flash('Username and password are required')
            return render_template('register_advanced.html')
        
        # Check if user already exists
        conn = sqlite3.connect('face_login_advanced.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            flash('Username already exists')
            conn.close()
            return render_template('register_advanced.html')
        
        # Create new user
        password_hash = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO users (username, password_hash)
            VALUES (?, ?)
        ''', (username, password_hash))
        conn.commit()
        conn.close()
        
        flash('Registration successful! You can now log in.')
        return redirect(url_for('index'))
    
    return render_template('register_advanced.html')

@app.route('/register_face', methods=['POST'])
def register_face():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'})
    
    try:
        data = request.get_json()
        face_data = data.get('face_data')
        
        if not face_data:
            return jsonify({'success': False, 'message': 'No face data provided'})
        
        # Process the face image and get encoding
        face_encoding, error = process_face_image(face_data)
        
        if error:
            return jsonify({'success': False, 'message': error})
        
        # Store face encoding in database
        conn = sqlite3.connect('face_login_advanced.db')
        cursor = conn.cursor()
        
        # Serialize the face encoding
        encoding_blob = pickle.dumps(face_encoding)
        
        cursor.execute('''
            UPDATE users SET face_encoding = ?, face_images = ? 
            WHERE id = ?
        ''', (encoding_blob, face_data, session['user_id']))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Face registered successfully!'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    face_data = data.get('face_data')
    login_type = data.get('type', 'password')
    
    if login_type == 'password':
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password are required'})
        
        # Get user from database
        conn = sqlite3.connect('face_login_advanced.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password_hash FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            log_login_attempt(username, None, 'password', False, 0.0, request.remote_addr)
            return jsonify({'success': False, 'message': 'User not found'})
        
        user_id, db_username, password_hash = user
        
        if check_password_hash(password_hash, password):
            session['user_id'] = user_id
            session['username'] = db_username
            log_login_attempt(username, user_id, 'password', True, 1.0, request.remote_addr)
            return jsonify({'success': True, 'message': 'Login successful!'})
        else:
            log_login_attempt(username, user_id, 'password', False, 0.0, request.remote_addr)
            return jsonify({'success': False, 'message': 'Invalid password'})
    
    elif login_type == 'face':
        if not face_data:
            return jsonify({'success': False, 'message': 'No face data provided'})
        
        # Process the face image and get encoding
        face_encoding, error = process_face_image(face_data)
        
        if error:
            log_login_attempt('unknown', None, 'face', False, 0.0, request.remote_addr)
            return jsonify({'success': False, 'message': error})
        
        # Find matching user
        match = find_matching_user(face_encoding)
        
        if match:
            session['user_id'] = match['user_id']
            session['username'] = match['username']
            log_login_attempt(match['username'], match['user_id'], 'face', True, match['confidence'], request.remote_addr)
            return jsonify({
                'success': True, 
                'message': f'Welcome back, {match["username"]}!',
                'username': match['username'],
                'confidence': round(match['confidence'] * 100, 1)
            })
        else:
            log_login_attempt('unknown', None, 'face', False, 0.0, request.remote_addr)
            return jsonify({'success': False, 'message': 'Face not recognized. Please try again or use password login.'})

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # Get user's login history
    conn = sqlite3.connect('face_login_advanced.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT attempt_type, success, confidence, timestamp
        FROM login_attempts 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 10
    ''', (session['user_id'],))
    login_history = cursor.fetchall()
    conn.close()
    
    return render_template('dashboard_advanced.html', 
                         username=session['username'],
                         login_history=login_history)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5001)
