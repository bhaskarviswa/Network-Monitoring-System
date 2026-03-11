import os

class Config:
    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///network_monitor.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Monitoring intervals (in seconds)
    POLLING_INTERVAL = 120  # Poll switches every 120 seconds (2 minutes)
    
    # SSH timeout
    SSH_TIMEOUT = 5  # Reduced to 5 seconds for faster polling
    
    # Alert thresholds
    CPU_THRESHOLD = 80  # CPU usage percentage
    MEMORY_THRESHOLD = 80  # Memory usage percentage
    INTERFACE_ERROR_THRESHOLD = 100  # Interface errors count
    
    # Email notifications
    # IMPORTANT: Configure these settings before enabling email alerts
    # For Gmail: Use App Password (not your regular password)
    # Generate App Password: https://myaccount.google.com/apppasswords
    ENABLE_EMAIL_ALERTS = False  # Set to True after configuring email settings
    SMTP_SERVER = 'smtp.gmail.com'  # For Gmail
    SMTP_PORT = 587  # For Gmail with TLS
    SMTP_USERNAME = 'your-email@gmail.com'  # Your email address
    SMTP_PASSWORD = 'your-app-password-here'  # Your Gmail App Password (16 characters)
    ALERT_EMAIL_TO = ['admin@example.com', 'team@example.com']  # List of email addresses to receive alerts
