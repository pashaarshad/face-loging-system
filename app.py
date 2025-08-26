from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import os
import base64
import numpy as np
from datetime import datetime
import secrets

# Import our custom modules
from models.database import Database
from models.face_recognition import FaceRecognitionSystem

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generate a secure secret key
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize database and face recognition system
db = Database()
face_system = FaceRecognitionSystem()

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    """Main login page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    """Handle traditional username/password login"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'})
    
    # Verify credentials
    if db.verify_password(username, password):
        user = db.get_user_by_username(username)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['first_name'] = user['first_name']
            session['last_name'] = user['last_name']
            
            # Update last login
            db.update_last_login(username)
            db.log_login_attempt(username, 'password', True, request.remote_addr)
            
            return jsonify({'success': True, 'message': 'Login successful'})
    
    # Log failed attempt
    db.log_login_attempt(username, 'password', False, request.remote_addr)
    return jsonify({'success': False, 'message': 'Invalid username or password'})

@app.route('/face-login', methods=['POST'])
def face_login():
    """Handle face recognition login"""
    try:
        data = request.get_json()
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'success': False, 'message': 'No image provided'})
        
        # Extract face encoding from the captured image
        encoding, error = face_system.extract_face_encoding_from_base64(image_data)
        
        if error:
            db.log_login_attempt('unknown', 'face', False, request.remote_addr)
            return jsonify({'success': False, 'message': error})
        
        # Find user by face encoding
        user = db.get_user_by_face(encoding)
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['first_name'] = user['first_name']
            session['last_name'] = user['last_name']
            
            # Update last login
            db.update_last_login(user['username'])
            db.log_login_attempt(user['username'], 'face', True, request.remote_addr)
            
            return jsonify({'success': True, 'message': 'Face recognition login successful'})
        else:
            db.log_login_attempt('unknown', 'face', False, request.remote_addr)
            return jsonify({'success': False, 'message': 'Face not recognized. Please register first or use username/password login.'})
    
    except Exception as e:
        print(f"Face login error: {e}")
        return jsonify({'success': False, 'message': 'Face recognition system error'})

@app.route('/register')
def register():
    """Registration page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/face-capture')
def face_capture():
    """Face capture page for registration"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('face_capture.html')

@app.route('/capture-face', methods=['POST'])
def capture_face():
    """Handle face capture during registration"""
    try:
        data = request.get_json()
        image_data = data.get('image')
        capture_count = data.get('capture_count', 1)
        
        if not image_data:
            return jsonify({'success': False, 'message': 'No image provided'})
        
        # Extract face encoding
        encoding, error = face_system.extract_face_encoding_from_base64(image_data)
        
        if error:
            return jsonify({'success': False, 'message': error})
        
        # Store encoding in session temporarily
        if 'face_encodings' not in session:
            session['face_encodings'] = []
        
        session['face_encodings'].append(encoding.tolist())  # Convert numpy array to list for JSON serialization
        session.modified = True
        
        if capture_count >= 3:
            # Average the encodings
            encodings_array = np.array(session['face_encodings'])
            average_encoding = np.mean(encodings_array, axis=0)
            session['final_face_encoding'] = average_encoding.tolist()
            session.modified = True
            
            return jsonify({
                'success': True, 
                'message': 'Face capture completed successfully!',
                'completed': True
            })
        else:
            return jsonify({
                'success': True, 
                'message': f'Face {capture_count} captured. Please capture {3 - capture_count} more.',
                'completed': False
            })
    
    except Exception as e:
        print(f"Face capture error: {e}")
        return jsonify({'success': False, 'message': 'Face capture system error'})

@app.route('/complete-registration', methods=['POST'])
def complete_registration():
    """Complete user registration with face encoding"""
    try:
        data = request.get_json()
        
        # Get form data
        username = data.get('username', '').strip()
        password = data.get('password', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        gender = data.get('gender', '').strip()
        
        # Validate input
        if not all([username, password, first_name, last_name, gender]):
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        if len(username) < 3:
            return jsonify({'success': False, 'message': 'Username must be at least 3 characters'})
        
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'})
        
        # Check if username exists
        if db.username_exists(username):
            return jsonify({'success': False, 'message': 'Username already exists'})
        
        # Get face encoding from session
        face_encoding = session.get('final_face_encoding')
        if not face_encoding:
            return jsonify({'success': False, 'message': 'Face capture not completed. Please capture your face first.'})
        
        # Convert back to numpy array
        face_encoding = np.array(face_encoding)
        
        # Create user
        user_id = db.create_user(username, password, first_name, last_name, gender, face_encoding)
        
        if user_id:
            # Clear face data from session
            session.pop('face_encodings', None)
            session.pop('final_face_encoding', None)
            
            # Log the user in automatically
            session['user_id'] = user_id
            session['username'] = username
            session['first_name'] = first_name
            session['last_name'] = last_name
            
            return jsonify({'success': True, 'message': 'Registration completed successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Registration failed. Please try again.'})
    
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'success': False, 'message': 'Registration system error'})

@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user = db.get_user_by_username(session['username'])
    return render_template('dashboard.html', user=user)

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/api/user-stats')
def user_stats():
    """Get user statistics for dashboard"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = db.get_user_by_username(session['username'])
    if user:
        return jsonify({
            'username': user['username'],
            'full_name': f"{user['first_name']} {user['last_name']}",
            'gender': user['gender'],
            'member_since': user['created_at'],
            'last_login': user['last_login'],
            'has_face_recognition': user['face_encoding'] is not None
        })
    
    return jsonify({'error': 'User not found'}), 404

@app.route('/test-camera')
def test_camera():
    """Test camera functionality"""
    return render_template('test_camera.html')

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    print("="*50)
    print("FACE RECOGNITION LOGIN SYSTEM")
    print("="*50)
    print("Starting application...")
    print("Make sure you have:")
    print("1. Python installed")
    print("2. All required packages installed (see requirements.txt)")
    print("3. Camera permissions enabled")
    print("4. Visual C++ Build Tools installed (for face_recognition)")
    print("\nApplication will be available at: http://localhost:5000")
    print("="*50)
    
    # Create database tables if they don't exist
    db.init_database()
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)
