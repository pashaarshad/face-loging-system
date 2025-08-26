from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import os
import secrets
from datetime import datetime

# Import our custom modules
from models.database_simple import Database

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generate a secure secret key
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize database
db = Database()

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    """Main login page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index_simple.html')

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
    """Handle face recognition login - Currently disabled"""
    return jsonify({
        'success': False, 
        'message': 'Face recognition is currently disabled. Please install required packages (opencv-python, face-recognition) and restart the application.'
    })

@app.route('/register')
def register():
    """Registration page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('register_simple.html')

@app.route('/complete-registration', methods=['POST'])
def complete_registration():
    """Complete user registration without face encoding"""
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
        
        # Create user without face encoding
        user_id = db.create_user(username, password, first_name, last_name, gender)
        
        if user_id:
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
    return render_template('dashboard_simple.html', user=user)

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
            'has_face_recognition': False  # Disabled for now
        })
    
    return jsonify({'error': 'User not found'}), 404

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    print("="*60)
    print("FACE RECOGNITION LOGIN SYSTEM - DEMO MODE")
    print("="*60)
    print("🚀 Starting application...")
    print("📝 Note: Face recognition is currently disabled")
    print("💡 To enable face recognition:")
    print("   1. Install Visual Studio Build Tools")
    print("   2. Run: pip install opencv-python face-recognition")
    print("   3. Replace app_simple.py with app.py")
    print("")
    print("🌐 Application will be available at: http://localhost:5000")
    print("🔑 You can register and login with username/password")
    print("="*60)
    
    # Create database tables if they don't exist
    db.init_database()
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)
