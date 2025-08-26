from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import base64
import hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this to a random secret key

# Database setup
def init_db():
    conn = sqlite3.connect('face_login.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            face_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Login attempts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            attempt_type TEXT,
            success BOOLEAN,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def log_login_attempt(username, attempt_type, success, ip_address):
    conn = sqlite3.connect('face_login.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO login_attempts (username, attempt_type, success, ip_address)
        VALUES (?, ?, ?, ?)
    ''', (username, attempt_type, success, ip_address))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index_webcam.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            flash('Username and password are required')
            return render_template('register_webcam.html')
        
        # Check if user already exists
        conn = sqlite3.connect('face_login.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            flash('Username already exists')
            conn.close()
            return render_template('register_webcam.html')
        
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
    
    return render_template('register_webcam.html')

@app.route('/register_face', methods=['POST'])
def register_face():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'})
    
    try:
        data = request.get_json()
        face_data = data.get('face_data')
        
        if not face_data:
            return jsonify({'success': False, 'message': 'No face data provided'})
        
        # Store face data for the logged-in user
        conn = sqlite3.connect('face_login.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET face_data = ? WHERE id = ?', 
                      (face_data, session['user_id']))
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
    
    if not username:
        return jsonify({'success': False, 'message': 'Username is required'})
    
    # Get user from database
    conn = sqlite3.connect('face_login.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, password_hash, face_data FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        log_login_attempt(username, login_type, False, request.remote_addr)
        return jsonify({'success': False, 'message': 'User not found'})
    
    user_id, db_username, password_hash, stored_face_data = user
    
    if login_type == 'password':
        if not password:
            return jsonify({'success': False, 'message': 'Password is required'})
        
        if check_password_hash(password_hash, password):
            session['user_id'] = user_id
            session['username'] = db_username
            log_login_attempt(username, 'password', True, request.remote_addr)
            return jsonify({'success': True, 'message': 'Login successful!'})
        else:
            log_login_attempt(username, 'password', False, request.remote_addr)
            return jsonify({'success': False, 'message': 'Invalid password'})
    
    elif login_type == 'face':
        if not stored_face_data:
            log_login_attempt(username, 'face', False, request.remote_addr)
            return jsonify({'success': False, 'message': 'No face data registered for this user'})
        
        if not face_data:
            return jsonify({'success': False, 'message': 'No face data provided'})
        
        # Simple face comparison (in real implementation, use proper face recognition)
        # This is a simplified comparison - you can enhance this with proper face recognition
        face_hash = hashlib.sha256(face_data.encode()).hexdigest()
        stored_hash = hashlib.sha256(stored_face_data.encode()).hexdigest()
        
        # For demo purposes, we'll use a simple similarity check
        similarity = calculate_similarity(face_data, stored_face_data)
        
        if similarity > 0.8:  # 80% similarity threshold
            session['user_id'] = user_id
            session['username'] = db_username
            log_login_attempt(username, 'face', True, request.remote_addr)
            return jsonify({'success': True, 'message': 'Face login successful!'})
        else:
            log_login_attempt(username, 'face', False, request.remote_addr)
            return jsonify({'success': False, 'message': 'Face not recognized'})

def calculate_similarity(face1, face2):
    """Simple similarity calculation - in production, use proper face recognition"""
    if not face1 or not face2:
        return 0.0
    
    # Simple hash-based comparison for demo
    hash1 = hashlib.sha256(face1.encode()).hexdigest()
    hash2 = hashlib.sha256(face2.encode()).hexdigest()
    
    # Count matching characters (very basic similarity)
    matches = sum(c1 == c2 for c1, c2 in zip(hash1, hash2))
    return matches / len(hash1)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # Get user's login history
    conn = sqlite3.connect('face_login.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT attempt_type, success, timestamp
        FROM login_attempts 
        WHERE username = ? 
        ORDER BY timestamp DESC 
        LIMIT 10
    ''', (session['username'],))
    login_history = cursor.fetchall()
    conn.close()
    
    return render_template('dashboard_webcam.html', 
                         username=session['username'],
                         login_history=login_history)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
