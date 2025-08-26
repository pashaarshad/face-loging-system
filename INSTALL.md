# Installation Guide - Face Recognition Login System

## Prerequisites

Since this is a fresh Windows system, you'll need to install the following:

### 1. Python Installation

1. **Download Python**:
   - Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)
   - Download Python 3.11 or later (recommended)

2. **Install Python**:
   - Run the downloaded installer
   - **IMPORTANT**: Check "Add Python to PATH" during installation
   - Check "Install pip"
   - Choose "Install Now"

3. **Verify Installation**:
   ```cmd
   python --version
   pip --version
   ```

### 2. Visual C++ Build Tools (Required for face_recognition)

1. **Download**:
   - Go to [https://visualstudio.microsoft.com/visual-cpp-build-tools/](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   - Download "Build Tools for Visual Studio"

2. **Install**:
   - Run the installer
   - Select "C++ build tools" workload
   - Install (this may take 15-30 minutes)

## Quick Setup (Automated)

1. **Open Command Prompt**:
   - Press `Win + R`, type `cmd`, press Enter
   - Navigate to your project folder:
     ```cmd
     cd C:\Users\Admin\Desktop\CodePlay\face-loging-system
     ```

2. **Run Setup Script**:
   ```cmd
   setup.bat
   ```
   
   This will:
   - Check Python installation
   - Create virtual environment
   - Install all required packages
   - Set up the application

3. **Run Application**:
   ```cmd
   run.bat
   ```

## Manual Setup (If automated setup fails)

### Step 1: Create Virtual Environment
```cmd
python -m venv face_login_env
face_login_env\Scripts\activate
```

### Step 2: Upgrade pip
```cmd
python -m pip install --upgrade pip
```

### Step 3: Install Packages One by One
```cmd
pip install Flask==2.3.3
pip install opencv-python==4.8.1.78
pip install numpy==1.24.3
pip install Pillow==10.0.1
pip install Flask-WTF==1.1.1
pip install WTForms==3.0.1
pip install python-dotenv==1.0.0
pip install Werkzeug==2.3.7

# Face recognition (may take longer)
pip install face-recognition==1.3.0
```

### Step 4: Run Application
```cmd
python app.py
```

## Troubleshooting

### Common Issues:

1. **"Python was not found"**:
   - Reinstall Python with "Add to PATH" checked
   - Restart Command Prompt after installation

2. **"Microsoft Visual C++ 14.0 is required"**:
   - Install Visual C++ Build Tools as described above
   - Restart and try again

3. **Face recognition installation fails**:
   - Make sure Visual C++ Build Tools are installed
   - Try installing cmake first: `pip install cmake`
   - Then install dlib: `pip install dlib`
   - Finally install face-recognition: `pip install face-recognition`

4. **Camera not working**:
   - Check camera permissions in Windows Settings
   - Ensure no other application is using the camera
   - Try using a different browser

5. **ModuleNotFoundError**:
   - Ensure virtual environment is activated
   - Reinstall the missing package: `pip install [package-name]`

### Performance Tips:

1. **For better face recognition performance**:
   - Ensure good lighting
   - Look directly at camera
   - Remove glasses if possible
   - Avoid shadows on face

2. **For better system performance**:
   - Close unnecessary applications
   - Use a modern browser (Chrome, Firefox, Edge)
   - Ensure stable internet connection

## Security Notes

- Face encodings are stored securely in SQLite database
- Passwords are hashed using SHA-256
- Sessions are managed securely
- All data is stored locally on your machine

## Features Overview

### ✅ Implemented Features:
- Dual authentication (password + face recognition)
- User registration with face capture
- Secure login/logout
- Beautiful responsive UI
- Real-time face recognition
- Dashboard with user information
- Database management
- Error handling and validation

### 🚀 Future Enhancements:
- Login history tracking
- Profile picture upload
- Multi-factor authentication
- Admin panel
- Email notifications
- Mobile app support

## Usage Instructions

1. **First Time Setup**:
   - Run `setup.bat` to install dependencies
   - Run `run.bat` to start the application
   - Open browser to `http://localhost:5000`

2. **Registration**:
   - Click "Register"
   - Fill in personal information
   - Capture face 3 times for better accuracy
   - Complete registration

3. **Login Options**:
   - **Method 1**: Username + Password
   - **Method 2**: Face Recognition
   - Both methods redirect to dashboard

4. **Dashboard**:
   - View profile information
   - Check security status
   - Access quick actions
   - Logout securely

## Support

If you encounter any issues:

1. Check the troubleshooting section above
2. Ensure all prerequisites are installed correctly
3. Try running setup.bat again
4. Check Windows Event Logs for system errors

## File Structure

```
face-loging-system/
├── app.py                 # Main Flask application
├── setup.bat             # Automated setup script
├── run.bat               # Application runner
├── requirements.txt      # Python dependencies
├── README.md            # Project documentation
├── INSTALL.md           # This installation guide
├── models/
│   ├── database.py      # Database operations
│   └── face_recognition.py # Face recognition logic
├── static/
│   ├── css/style.css    # Custom styles
│   ├── js/main.js      # JavaScript functionality
│   └── uploads/        # Face images storage
├── templates/          # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── register.html
│   ├── dashboard.html
│   ├── face_capture.html
│   ├── 404.html
│   └── 500.html
└── database/           # SQLite database files
```

## Development Mode

To run in development mode with debugging:

```cmd
set FLASK_ENV=development
python app.py
```

This enables:
- Auto-reload on code changes
- Detailed error messages
- Debug toolbar

---

**Ready to start? Run `setup.bat` and then `run.bat`!** 🚀
