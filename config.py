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
    ENABLE_EMAIL_ALERTS = True
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587
    SMTP_USERNAME = 'netmonitorcutmap@gmail.com'
    SMTP_PASSWORD = 'ubqelzrmyjyjtgki'
    ALERT_EMAIL_TO = ['netmonitorcutmap@gmail.com']
