import sqlite3
import hashlib
import pickle
import os
from datetime import datetime

class Database:
    def __init__(self, db_path='database/users.db'):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                gender TEXT NOT NULL,
                face_encoding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Create login_attempts table for security
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                attempt_type TEXT, -- 'password' or 'face'
                success BOOLEAN,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username, password, first_name, last_name, gender, face_encoding=None):
        """Create a new user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            face_blob = pickle.dumps(face_encoding) if face_encoding is not None else None
            
            cursor.execute('''
                INSERT INTO users (username, password_hash, first_name, last_name, gender, face_encoding)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, password_hash, first_name, last_name, gender, face_blob))
            
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            return None  # Username already exists
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    def verify_password(self, username, password):
        """Verify user password"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0] == self.hash_password(password)
        return False
    
    def get_user_by_username(self, username):
        """Get user by username"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, first_name, last_name, gender, face_encoding, created_at, last_login
            FROM users WHERE username = ?
        ''', (username,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            face_encoding = pickle.loads(result[5]) if result[5] else None
            return {
                'id': result[0],
                'username': result[1],
                'first_name': result[2],
                'last_name': result[3],
                'gender': result[4],
                'face_encoding': face_encoding,
                'created_at': result[6],
                'last_login': result[7]
            }
        return None
    
    def get_user_by_face(self, face_encoding):
        """Get user by face encoding (for face recognition login)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, first_name, last_name, gender, face_encoding, created_at, last_login
            FROM users WHERE face_encoding IS NOT NULL
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return None
        
        # Compare face encodings
        import face_recognition
        
        for result in results:
            stored_encoding = pickle.loads(result[5])
            if face_recognition.compare_faces([stored_encoding], face_encoding, tolerance=0.6)[0]:
                return {
                    'id': result[0],
                    'username': result[1],
                    'first_name': result[2],
                    'last_name': result[3],
                    'gender': result[4],
                    'face_encoding': stored_encoding,
                    'created_at': result[6],
                    'last_login': result[7]
                }
        return None
    
    def update_last_login(self, username):
        """Update user's last login timestamp"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE username = ?
        ''', (username,))
        
        conn.commit()
        conn.close()
    
    def log_login_attempt(self, username, attempt_type, success, ip_address=None):
        """Log login attempt for security tracking"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO login_attempts (username, attempt_type, success, ip_address)
            VALUES (?, ?, ?, ?)
        ''', (username, attempt_type, success, ip_address))
        
        conn.commit()
        conn.close()
    
    def get_all_users(self):
        """Get all users (for admin purposes)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, first_name, last_name, gender, created_at, last_login
            FROM users ORDER BY created_at DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        users = []
        for result in results:
            users.append({
                'id': result[0],
                'username': result[1],
                'first_name': result[2],
                'last_name': result[3],
                'gender': result[4],
                'created_at': result[5],
                'last_login': result[6]
            })
        
        return users
    
    def username_exists(self, username):
        """Check if username already exists"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', (username,))
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
