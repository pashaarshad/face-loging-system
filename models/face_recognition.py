import cv2
import face_recognition
import numpy as np
import os
import base64
from PIL import Image
import io

class FaceRecognitionSystem:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.face_encodings = []
        self.face_names = []
    
    def capture_face_from_camera(self):
        """Capture face from webcam"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            return None, "Camera not accessible"
        
        print("Position your face in front of the camera and press SPACE to capture, ESC to cancel")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert to RGB for face_recognition
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Find faces in the frame
            face_locations = face_recognition.face_locations(rgb_frame)
            
            # Draw rectangles around faces
            for (top, right, bottom, left) in face_locations:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, "Face detected - Press SPACE to capture", 
                           (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            cv2.imshow('Face Capture - Press SPACE to capture, ESC to cancel', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 32:  # SPACE key
                if face_locations:
                    cap.release()
                    cv2.destroyAllWindows()
                    return rgb_frame, None
                else:
                    print("No face detected. Please position your face properly.")
            elif key == 27:  # ESC key
                break
        
        cap.release()
        cv2.destroyAllWindows()
        return None, "Capture cancelled"
    
    def extract_face_encoding(self, image_array):
        """Extract face encoding from image array"""
        try:
            # Find face locations
            face_locations = face_recognition.face_locations(image_array)
            
            if not face_locations:
                return None, "No face detected in the image"
            
            if len(face_locations) > 1:
                return None, "Multiple faces detected. Please ensure only one face is visible"
            
            # Get face encoding
            face_encodings = face_recognition.face_encodings(image_array, face_locations)
            
            if face_encodings:
                return face_encodings[0], None
            else:
                return None, "Could not extract face features"
                
        except Exception as e:
            return None, f"Error processing image: {str(e)}"
    
    def extract_face_encoding_from_base64(self, base64_image):
        """Extract face encoding from base64 image"""
        try:
            # Decode base64 image
            image_data = base64.b64decode(base64_image.split(',')[1])
            image = Image.open(io.BytesIO(image_data))
            image_array = np.array(image)
            
            # Convert BGR to RGB if necessary
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                image_array = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
            
            return self.extract_face_encoding(image_array)
            
        except Exception as e:
            return None, f"Error processing base64 image: {str(e)}"
    
    def compare_faces(self, known_encoding, unknown_encoding, tolerance=0.6):
        """Compare two face encodings"""
        try:
            results = face_recognition.compare_faces([known_encoding], unknown_encoding, tolerance=tolerance)
            distance = face_recognition.face_distance([known_encoding], unknown_encoding)
            
            return results[0], distance[0]
        except Exception as e:
            print(f"Error comparing faces: {e}")
            return False, 1.0
    
    def save_face_image(self, image_array, filename, upload_path='static/uploads'):
        """Save face image to file"""
        try:
            if not os.path.exists(upload_path):
                os.makedirs(upload_path)
            
            filepath = os.path.join(upload_path, filename)
            image = Image.fromarray(image_array)
            image.save(filepath)
            return filepath
        except Exception as e:
            print(f"Error saving image: {e}")
            return None
    
    def validate_face_quality(self, image_array):
        """Validate if the face image is of good quality"""
        try:
            # Check image dimensions
            height, width = image_array.shape[:2]
            if height < 100 or width < 100:
                return False, "Image resolution too low"
            
            # Find face locations
            face_locations = face_recognition.face_locations(image_array)
            
            if not face_locations:
                return False, "No face detected"
            
            if len(face_locations) > 1:
                return False, "Multiple faces detected"
            
            # Check face size
            top, right, bottom, left = face_locations[0]
            face_height = bottom - top
            face_width = right - left
            
            if face_height < 50 or face_width < 50:
                return False, "Face too small in image"
            
            # Check if face takes reasonable portion of image
            face_area_ratio = (face_height * face_width) / (height * width)
            if face_area_ratio < 0.1:
                return False, "Face too small relative to image"
            
            return True, "Face quality is good"
            
        except Exception as e:
            return False, f"Error validating face: {str(e)}"
    
    def capture_multiple_faces(self, count=3):
        """Capture multiple face images for better accuracy"""
        captured_encodings = []
        captured_images = []
        
        for i in range(count):
            print(f"Capturing face {i+1} of {count}")
            image, error = self.capture_face_from_camera()
            
            if error:
                return None, None, error
            
            # Validate face quality
            is_valid, message = self.validate_face_quality(image)
            if not is_valid:
                print(f"Poor quality image: {message}. Please try again.")
                i -= 1  # Retry this capture
                continue
            
            # Extract encoding
            encoding, error = self.extract_face_encoding(image)
            if error:
                print(f"Error extracting face: {error}. Please try again.")
                i -= 1  # Retry this capture
                continue
            
            captured_encodings.append(encoding)
            captured_images.append(image)
            
            print(f"Successfully captured face {i+1}")
        
        # Average the encodings for better accuracy
        if captured_encodings:
            average_encoding = np.mean(captured_encodings, axis=0)
            return average_encoding, captured_images, None
        
        return None, None, "Failed to capture any valid faces"
    
    def detect_liveness(self, image_array):
        """Basic liveness detection (can be enhanced)"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            
            # Calculate image sharpness using Laplacian variance
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # If variance is too low, image might be blurry or a photo
            if laplacian_var < 100:
                return False, "Image appears to be blurry or not a live person"
            
            # Additional checks can be added here
            # e.g., eye blink detection, head movement, etc.
            
            return True, "Liveness check passed"
            
        except Exception as e:
            return False, f"Liveness detection error: {str(e)}"
