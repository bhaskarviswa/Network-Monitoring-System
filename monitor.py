from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import json
from models import db, Switch, Metric, Alert
from ssh_collector import SSHCollector
from email_notifier import EmailNotifier
from config import Config

class NetworkMonitor:
    def __init__(self, app):
        self.app = app
        self.scheduler = BackgroundScheduler()
        self.email_notifier = EmailNotifier()
        
    def start(self):
        """Start the monitoring scheduler"""
        self.scheduler.add_job(
            func=self.poll_all_switches,
            trigger='interval',
            seconds=Config.POLLING_INTERVAL,
            id='poll_switches',
            name='Poll all switches',
            replace_existing=True
        )
        self.scheduler.start()
        print(f"Network monitor started. Polling every {Config.POLLING_INTERVAL} seconds.")
    
    def stop(self):
        """Stop the monitoring scheduler"""
        self.scheduler.shutdown()
        print("Network monitor stopped.")
    
    def poll_all_switches(self):
        """Poll all registered switches"""
        with self.app.app_context():
            switches = Switch.query.all()
            print(f"[{datetime.now()}] Polling {len(switches)} switches...")
            
            for switch in switches:
                try:
                    self.poll_switch(switch)
                except Exception as e:
                    print(f"Error polling {switch.name}: {str(e)}")
    
    def poll_switch(self, switch):
        """Poll a single switch and store metrics"""
        collector = SSHCollector(
            switch.ip_address,
            switch.username,
            switch.password,
            switch.device_type
        )
        
        metrics_data = collector.collect_metrics()
        
        if metrics_data:
            # Update switch status
            switch.status = 'up'
            switch.last_seen = datetime.utcnow()
            
            # Store metrics
            metric = Metric(
                switch_id=switch.id,
                cpu_usage=metrics_data.get('cpu_usage'),
                memory_usage=metrics_data.get('memory_usage'),
                uptime=metrics_data.get('uptime'),
                interface_data=json.dumps(metrics_data.get('interfaces', []))
            )
            db.session.add(metric)
            
            # Check for alerts
            self.check_alerts(switch, metrics_data)
            
            print(f"✓ {switch.name} ({switch.ip_address}) - CPU: {metrics_data.get('cpu_usage')}%, Memory: {metrics_data.get('memory_usage')}%")
        else:
            switch.status = 'down'
            self.create_alert(switch, 'connectivity', 'critical', f'Switch {switch.name} is unreachable')
            print(f"✗ {switch.name} ({switch.ip_address}) - Unreachable")
        
        db.session.commit()
    
    def check_alerts(self, switch, metrics_data):
        """Check metrics against thresholds and create alerts"""
        # CPU threshold
        cpu = metrics_data.get('cpu_usage')
        if cpu and cpu > Config.CPU_THRESHOLD:
            self.create_alert(
                switch,
                'cpu',
                'warning',
                f'High CPU usage: {cpu}% (threshold: {Config.CPU_THRESHOLD}%)'
            )
        
        # Memory threshold
        memory = metrics_data.get('memory_usage')
        if memory and memory > Config.MEMORY_THRESHOLD:
            self.create_alert(
                switch,
                'memory',
                'warning',
                f'High memory usage: {memory}% (threshold: {Config.MEMORY_THRESHOLD}%)'
            )
        
        # Interface errors
        interfaces = metrics_data.get('interfaces', [])
        for interface in interfaces:
            total_errors = interface.get('input_errors', 0) + interface.get('output_errors', 0)
            if total_errors > Config.INTERFACE_ERROR_THRESHOLD:
                self.create_alert(
                    switch,
                    'interface',
                    'warning',
                    f"Interface {interface['name']} has {total_errors} errors"
                )
    
    def create_alert(self, switch, alert_type, severity, message):
        """Create an alert if it doesn't already exist"""
        print(f"🔔 Creating alert for {switch.name}: {alert_type} - {severity} - {message}")
        
        # Check if similar unacknowledged alert exists
        existing = Alert.query.filter_by(
            switch_id=switch.id,
            alert_type=alert_type,
            acknowledged=False
        ).first()
        
        if not existing:
            alert = Alert(
                switch_id=switch.id,
                alert_type=alert_type,
                severity=severity,
                message=message
            )
            db.session.add(alert)
            print(f"📝 Alert added to database for {switch.name}")
            
            # Send email notification for critical alerts or connectivity issues
            if severity == 'critical' or alert_type == 'connectivity':
                print(f"📧 Attempting to send email for {switch.name} - {alert_type}")
                try:
                    email_sent = self.email_notifier.send_alert(
                        switch.name,
                        switch.ip_address,
                        alert_type,
                        severity,
                        message
                    )
                    if email_sent:
                        print(f"✅ Email sent successfully for {switch.name}")
                    else:
                        print(f"❌ Email failed to send for {switch.name}")
                except Exception as e:
                    print(f"❌ Email error for {switch.name}: {str(e)}")
            else:
                print(f"ℹ️ No email sent for {switch.name} - severity: {severity}, type: {alert_type}")
        else:
            print(f"⚠️ Alert already exists for {switch.name} - {alert_type}")
