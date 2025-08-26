from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import base64
import hashlib
import json
import pickle
from datetime import datetime
import numpy as np
from PIL import Image, ImageStat
import io
# import cv2  # Not needed for this simple version

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this to a random secret key

# Simple face recognition using image features
def extract_simple_features(image_data):
    """Extract simple features from face image for comparison"""
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
        
        # Resize to standard size for comparison
        image = image.resize((128, 128))
        
        # Convert to numpy array
        img_array = np.array(image)
        
        # Extract various features
        features = {}
        
        # Average color values
        features['avg_r'] = np.mean(img_array[:, :, 0])
        features['avg_g'] = np.mean(img_array[:, :, 1])
        features['avg_b'] = np.mean(img_array[:, :, 2])
        
        # Standard deviation of colors
        features['std_r'] = np.std(img_array[:, :, 0])
        features['std_g'] = np.std(img_array[:, :, 1])
        features['std_b'] = np.std(img_array[:, :, 2])
        
        # Image brightness and contrast
        gray = np.mean(img_array, axis=2)
        features['brightness'] = np.mean(gray)
        features['contrast'] = np.std(gray)
        
        # Center region features (face area)
        center_h, center_w = 64, 64
        center_region = img_array[32:96, 32:96]
        features['center_avg'] = np.mean(center_region)
        features['center_std'] = np.std(center_region)
        
        # Edge detection features
        edges = np.abs(np.diff(gray, axis=0)).sum() + np.abs(np.diff(gray, axis=1)).sum()
        features['edge_density'] = edges / (128 * 128)
        
        # Histogram features
        hist_r = np.histogram(img_array[:, :, 0], bins=8)[0]
        hist_g = np.histogram(img_array[:, :, 1], bins=8)[0]
        hist_b = np.histogram(img_array[:, :, 2], bins=8)[0]
        
        features['hist_r'] = hist_r.tolist()
        features['hist_g'] = hist_g.tolist()
        features['hist_b'] = hist_b.tolist()
        
        return features, None
        
    except Exception as e:
        return None, f"Error processing image: {str(e)}"

def calculate_similarity(features1, features2):
    """Calculate similarity between two feature sets"""
    try:
        similarity_score = 0
        total_weights = 0
        
        # Color similarity
        color_features = ['avg_r', 'avg_g', 'avg_b', 'std_r', 'std_g', 'std_b']
        for feature in color_features:
            if feature in features1 and feature in features2:
                diff = abs(features1[feature] - features2[feature])
                sim = max(0, 1 - diff / 255)  # Normalize to 0-1
                similarity_score += sim * 0.1
                total_weights += 0.1
        
        # Brightness and contrast similarity
        structural_features = ['brightness', 'contrast', 'center_avg', 'center_std', 'edge_density']
        for feature in structural_features:
            if feature in features1 and feature in features2:
                diff = abs(features1[feature] - features2[feature])
                max_val = max(features1[feature], features2[feature], 1)
                sim = max(0, 1 - diff / max_val)
                similarity_score += sim * 0.15
                total_weights += 0.15
        
        # Histogram similarity
        hist_features = ['hist_r', 'hist_g', 'hist_b']
        for feature in hist_features:
            if feature in features1 and feature in features2:
                hist1 = np.array(features1[feature])
                hist2 = np.array(features2[feature])
                # Normalized correlation
                correlation = np.corrcoef(hist1, hist2)[0, 1]
                if not np.isnan(correlation):
                    similarity_score += max(0, correlation) * 0.1
                    total_weights += 0.1
        
        if total_weights > 0:
            return similarity_score / total_weights
        else:
            return 0.0
            
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return 0.0

# Database setup
def init_db():
    conn = sqlite3.connect('face_login_simple_ai.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            face_features TEXT,
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

def find_matching_user(image_data, tolerance=0.7):
    """Find matching user based on face features"""
    # Extract features from input image
    input_features, error = extract_simple_features(image_data)
    
    if error:
        return None
    
    conn = sqlite3.connect('face_login_simple_ai.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, username, face_features FROM users WHERE face_features IS NOT NULL')
    users = cursor.fetchall()
    conn.close()
    
    best_match = None
    best_similarity = 0.0
    
    for user_id, username, stored_features_json in users:
        if stored_features_json:
            try:
                stored_features = json.loads(stored_features_json)
                similarity = calculate_similarity(input_features, stored_features)
                
                if similarity > tolerance and similarity > best_similarity:
                    best_similarity = similarity
                    best_match = {
                        'user_id': user_id,
                        'username': username,
                        'similarity': similarity,
                        'confidence': similarity
                    }
                    
            except Exception as e:
                print(f"Error processing stored features for user {username}: {e}")
                continue
    
    return best_match

def log_login_attempt(username, user_id, attempt_type, success, confidence, ip_address):
    conn = sqlite3.connect('face_login_simple_ai.db')
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
    return render_template('index_simple_ai.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            flash('Username and password are required')
            return render_template('register_simple_ai.html')
        
        # Check if user already exists
        conn = sqlite3.connect('face_login_simple_ai.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            flash('Username already exists')
            conn.close()
            return render_template('register_simple_ai.html')
        
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
    
    return render_template('register_simple_ai.html')

@app.route('/register_face', methods=['POST'])
def register_face():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'})
    
    try:
        data = request.get_json()
        face_data = data.get('face_data')
        
        if not face_data:
            return jsonify({'success': False, 'message': 'No face data provided'})
        
        # Extract features from the face image
        face_features, error = extract_simple_features(face_data)
        
        if error:
            return jsonify({'success': False, 'message': error})
        
        # Store face features in database
        conn = sqlite3.connect('face_login_simple_ai.db')
        cursor = conn.cursor()
        
        features_json = json.dumps(face_features)
        
        cursor.execute('''
            UPDATE users SET face_features = ?, face_images = ? 
            WHERE id = ?
        ''', (features_json, face_data, session['user_id']))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'AI face model trained successfully!'})
    
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
        conn = sqlite3.connect('face_login_simple_ai.db')
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
        
        # Find matching user using AI features
        match = find_matching_user(face_data)
        
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
            return jsonify({'success': False, 'message': 'Face not recognized by our AI. Please try again or use password login.'})

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # Get user's login history
    conn = sqlite3.connect('face_login_simple_ai.db')
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
    
    return render_template('dashboard_simple_ai.html', 
                         username=session['username'],
                         login_history=login_history)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5002)
