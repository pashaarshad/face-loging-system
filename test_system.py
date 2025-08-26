#!/usr/bin/env python3
"""
Test script for Face Recognition Login System
This script tests all major components before running the main application.
"""

import sys
import os
import importlib

def test_python_version():
    """Test Python version compatibility"""
    print("🐍 Testing Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False

def test_package_imports():
    """Test if all required packages can be imported"""
    print("\n📦 Testing package imports...")
    
    packages = [
        ('flask', 'Flask'),
        ('cv2', 'OpenCV'),
        ('face_recognition', 'Face Recognition'),
        ('numpy', 'NumPy'),
        ('PIL', 'Pillow'),
        ('sqlite3', 'SQLite3'),
        ('hashlib', 'Hashlib'),
        ('pickle', 'Pickle'),
        ('datetime', 'DateTime'),
        ('secrets', 'Secrets'),
        ('base64', 'Base64'),
    ]
    
    success_count = 0
    total_count = len(packages)
    
    for package, name in packages:
        try:
            importlib.import_module(package)
            print(f"✅ {name} - OK")
            success_count += 1
        except ImportError as e:
            print(f"❌ {name} - Failed: {e}")
    
    print(f"\n📊 Package Test Results: {success_count}/{total_count} packages imported successfully")
    return success_count == total_count

def test_file_structure():
    """Test if all required files exist"""
    print("\n📁 Testing file structure...")
    
    required_files = [
        'app.py',
        'requirements.txt',
        'models/database.py',
        'models/face_recognition.py',
        'static/css/style.css',
        'static/js/main.js',
        'templates/base.html',
        'templates/index.html',
        'templates/register.html',
        'templates/dashboard.html',
    ]
    
    required_dirs = [
        'models',
        'static',
        'static/css',
        'static/js',
        'static/uploads',
        'templates',
        'database',
    ]
    
    success_count = 0
    total_count = len(required_files) + len(required_dirs)
    
    # Test directories
    for dir_path in required_dirs:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            print(f"✅ Directory: {dir_path}")
            success_count += 1
        else:
            print(f"❌ Directory missing: {dir_path}")
    
    # Test files
    for file_path in required_files:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            print(f"✅ File: {file_path}")
            success_count += 1
        else:
            print(f"❌ File missing: {file_path}")
    
    print(f"\n📊 File Structure Test Results: {success_count}/{total_count} items found")
    return success_count == total_count

def test_database_creation():
    """Test database creation and basic operations"""
    print("\n🗄️ Testing database creation...")
    
    try:
        from models.database import Database
        
        # Test database initialization
        db = Database()
        print("✅ Database class imported")
        
        # Test database initialization
        db.init_database()
        print("✅ Database tables created")
        
        # Test basic operations
        test_user_id = db.create_user(
            username="testuser",
            password="testpass123",
            first_name="Test",
            last_name="User",
            gender="Other"
        )
        
        if test_user_id:
            print("✅ Test user created")
            
            # Test password verification
            if db.verify_password("testuser", "testpass123"):
                print("✅ Password verification works")
            else:
                print("❌ Password verification failed")
                return False
            
            # Test user retrieval
            user = db.get_user_by_username("testuser")
            if user:
                print("✅ User retrieval works")
            else:
                print("❌ User retrieval failed")
                return False
                
        else:
            print("❌ Test user creation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_face_recognition_system():
    """Test face recognition system initialization"""
    print("\n👤 Testing face recognition system...")
    
    try:
        from models.face_recognition import FaceRecognitionSystem
        
        # Test class import and initialization
        face_system = FaceRecognitionSystem()
        print("✅ Face recognition system initialized")
        
        # Test face cascade loading
        if face_system.face_cascade is not None:
            print("✅ Face cascade classifier loaded")
        else:
            print("❌ Face cascade classifier failed to load")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Face recognition test failed: {e}")
        return False

def test_flask_app():
    """Test Flask application initialization"""
    print("\n🌐 Testing Flask application...")
    
    try:
        # Import and create app
        from app import app
        print("✅ Flask app imported")
        
        # Test app configuration
        if app.secret_key:
            print("✅ Secret key configured")
        else:
            print("❌ Secret key not configured")
            return False
        
        # Test route registration
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        expected_routes = ['/', '/login', '/register', '/dashboard', '/logout']
        
        missing_routes = [route for route in expected_routes if route not in routes]
        if not missing_routes:
            print("✅ All main routes registered")
        else:
            print(f"❌ Missing routes: {missing_routes}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and provide summary"""
    print("🚀 Face Recognition Login System - Component Tests")
    print("=" * 60)
    
    tests = [
        ("Python Version", test_python_version),
        ("Package Imports", test_package_imports),
        ("File Structure", test_file_structure),
        ("Database System", test_database_creation),
        ("Face Recognition", test_face_recognition_system),
        ("Flask Application", test_flask_app),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} - Exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The system is ready to run.")
        print("\nTo start the application:")
        print("1. Run: python app.py")
        print("2. Open browser to: http://localhost:5000")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please fix the issues before running.")
        print("\nSuggested actions:")
        if not results[1][1]:  # Package imports failed
            print("- Run: pip install -r requirements.txt")
        if not results[2][1]:  # File structure failed
            print("- Ensure all files are in correct locations")
        if not results[3][1]:  # Database failed
            print("- Check SQLite installation and permissions")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
