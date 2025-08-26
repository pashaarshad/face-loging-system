// Main JavaScript file for Face Recognition Login System

// Global variables
let isDebugMode = false;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Check if debug mode is enabled
    isDebugMode = window.location.search.includes('debug=true');
    
    // Initialize common features
    initializeBootstrapComponents();
    initializeFormValidation();
    initializeKeyboardShortcuts();
    initializeProgressiveEnhancement();
    
    // Log initialization
    if (isDebugMode) {
        console.log('Face Recognition Login System initialized');
    }
}

function initializeBootstrapComponents() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

function initializeFormValidation() {
    // Add real-time validation to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input[required], select[required]');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                clearFieldError(this);
            });
        });
    });
}

function validateField(field) {
    const value = field.value.trim();
    const fieldName = field.getAttribute('name');
    let isValid = true;
    let errorMessage = '';
    
    // Basic required validation
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        errorMessage = `${getFieldLabel(field)} is required`;
    }
    
    // Specific field validations
    switch (fieldName) {
        case 'username':
            if (value && value.length < 3) {
                isValid = false;
                errorMessage = 'Username must be at least 3 characters';
            }
            break;
            
        case 'password':
            if (value && value.length < 6) {
                isValid = false;
                errorMessage = 'Password must be at least 6 characters';
            }
            break;
            
        case 'firstName':
        case 'lastName':
            if (value && !/^[a-zA-Z\s]+$/.test(value)) {
                isValid = false;
                errorMessage = 'Name should only contain letters and spaces';
            }
            break;
    }
    
    // Show/hide error
    if (!isValid) {
        showFieldError(field, errorMessage);
    } else {
        clearFieldError(field);
    }
    
    return isValid;
}

function showFieldError(field, message) {
    clearFieldError(field);
    
    field.classList.add('is-invalid');
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
}

function clearFieldError(field) {
    field.classList.remove('is-invalid');
    
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

function getFieldLabel(field) {
    const label = field.parentNode.querySelector('label');
    if (label) {
        return label.textContent.replace('*', '').trim();
    }
    return field.getAttribute('name') || 'Field';
}

function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Alt + L for login page
        if (e.altKey && e.key === 'l') {
            e.preventDefault();
            window.location.href = '/';
        }
        
        // Alt + R for register page
        if (e.altKey && e.key === 'r') {
            e.preventDefault();
            window.location.href = '/register';
        }
        
        // Alt + D for dashboard (if logged in)
        if (e.altKey && e.key === 'd') {
            e.preventDefault();
            window.location.href = '/dashboard';
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                const modal = bootstrap.Modal.getInstance(openModal);
                if (modal) {
                    modal.hide();
                }
            }
        }
    });
}

function initializeProgressiveEnhancement() {
    // Add loading states to buttons
    const buttons = document.querySelectorAll('button[type="submit"], .btn-primary');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            if (!this.disabled) {
                addLoadingState(this);
            }
        });
    });
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                alert.classList.add('fade');
                setTimeout(() => {
                    if (alert.parentNode) {
                        alert.remove();
                    }
                }, 300);
            }
        }, 5000);
    });
}

function addLoadingState(button) {
    const originalText = button.innerHTML;
    button.setAttribute('data-original-text', originalText);
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
    button.disabled = true;
    
    // Auto-remove loading state after 10 seconds as fallback
    setTimeout(() => {
        removeLoadingState(button);
    }, 10000);
}

function removeLoadingState(button) {
    const originalText = button.getAttribute('data-original-text');
    if (originalText) {
        button.innerHTML = originalText;
        button.removeAttribute('data-original-text');
    }
    button.disabled = false;
}

// Camera and Face Recognition Utilities
class CameraManager {
    constructor() {
        this.stream = null;
        this.video = null;
        this.canvas = null;
        this.ctx = null;
    }
    
    async initialize(videoElement, canvasElement) {
        this.video = videoElement;
        this.canvas = canvasElement;
        this.ctx = this.canvas.getContext('2d');
        
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                }
            });
            
            this.video.srcObject = this.stream;
            return true;
        } catch (error) {
            console.error('Camera initialization failed:', error);
            return false;
        }
    }
    
    captureFrame() {
        if (!this.video || !this.canvas) {
            return null;
        }
        
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        this.ctx.drawImage(this.video, 0, 0);
        
        return this.canvas.toDataURL('image/jpeg', 0.8);
    }
    
    stop() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        if (this.video) {
            this.video.srcObject = null;
        }
    }
    
    isSupported() {
        return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    }
}

// Notification System
class NotificationManager {
    static show(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show notification-toast`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            max-width: 400px;
            animation: slideInRight 0.3s ease-out;
        `;
        
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after duration
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.remove('show');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 300);
            }
        }, duration);
        
        return notification;
    }
    
    static success(message, duration = 5000) {
        return this.show(`<i class="fas fa-check-circle me-2"></i>${message}`, 'success', duration);
    }
    
    static error(message, duration = 7000) {
        return this.show(`<i class="fas fa-exclamation-circle me-2"></i>${message}`, 'danger', duration);
    }
    
    static warning(message, duration = 6000) {
        return this.show(`<i class="fas fa-exclamation-triangle me-2"></i>${message}`, 'warning', duration);
    }
    
    static info(message, duration = 5000) {
        return this.show(`<i class="fas fa-info-circle me-2"></i>${message}`, 'info', duration);
    }
}

// API Utility Functions
class ApiClient {
    static async post(url, data) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw new Error('Network error occurred');
        }
    }
    
    static async get(url) {
        try {
            const response = await fetch(url);
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw new Error('Network error occurred');
        }
    }
}

// Form Validation Utilities
class FormValidator {
    static validateForm(formElement) {
        const inputs = formElement.querySelectorAll('input[required], select[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            if (!validateField(input)) {
                isValid = false;
            }
        });
        
        return isValid;
    }
    
    static getFormData(formElement) {
        const formData = new FormData(formElement);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = value.trim();
        }
        
        return data;
    }
}

// Local Storage Utilities
class StorageManager {
    static set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('Failed to save to localStorage:', error);
        }
    }
    
    static get(key) {
        try {
            const value = localStorage.getItem(key);
            return value ? JSON.parse(value) : null;
        } catch (error) {
            console.error('Failed to read from localStorage:', error);
            return null;
        }
    }
    
    static remove(key) {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.error('Failed to remove from localStorage:', error);
        }
    }
    
    static clear() {
        try {
            localStorage.clear();
        } catch (error) {
            console.error('Failed to clear localStorage:', error);
        }
    }
}

// Performance Monitoring
class PerformanceMonitor {
    static measure(name, fn) {
        const start = performance.now();
        const result = fn();
        const end = performance.now();
        
        if (isDebugMode) {
            console.log(`${name} took ${end - start} milliseconds`);
        }
        
        return result;
    }
    
    static async measureAsync(name, fn) {
        const start = performance.now();
        const result = await fn();
        const end = performance.now();
        
        if (isDebugMode) {
            console.log(`${name} took ${end - start} milliseconds`);
        }
        
        return result;
    }
}

// Error Handling
window.addEventListener('error', function(e) {
    if (isDebugMode) {
        console.error('Global error:', e.error);
    }
    
    // Show user-friendly error message
    NotificationManager.error('An unexpected error occurred. Please try again.');
});

window.addEventListener('unhandledrejection', function(e) {
    if (isDebugMode) {
        console.error('Unhandled promise rejection:', e.reason);
    }
    
    // Show user-friendly error message
    NotificationManager.error('A network error occurred. Please check your connection.');
});

// Expose utilities globally
window.CameraManager = CameraManager;
window.NotificationManager = NotificationManager;
window.ApiClient = ApiClient;
window.FormValidator = FormValidator;
window.StorageManager = StorageManager;
window.PerformanceMonitor = PerformanceMonitor;

// Add CSS for notifications
const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .notification-toast {
        box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
        border-radius: 0.5rem;
    }
`;
document.head.appendChild(notificationStyles);
