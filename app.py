from flask import Flask, render_template, request, jsonify, redirect, url_for
from models import db, Switch, Metric, Alert
from monitor import NetworkMonitor
from config import Config
import json
from datetime import datetime, timedelta

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

# Initialize monitor
monitor = NetworkMonitor(app)

@app.route('/')
def index():
    """Dashboard view"""
    switches = Switch.query.all()
    total_switches = len(switches)
    up_switches = len([s for s in switches if s.status == 'up'])
    down_switches = len([s for s in switches if s.status == 'down'])
    
    # Get all unacknowledged alerts for count
    all_unack_alerts = Alert.query.filter_by(acknowledged=False).all()
    total_alerts = len(all_unack_alerts)
    
    # Get recent alerts for display (limited to 10)
    recent_alerts = Alert.query.filter_by(acknowledged=False).order_by(Alert.timestamp.desc()).limit(10).all()
    
    return render_template('index.html',
                         switches=switches,
                         total_switches=total_switches,
                         up_switches=up_switches,
                         down_switches=down_switches,
                         alerts=recent_alerts,
                         total_alerts=total_alerts)

@app.route('/switches')
def switches():
    """List all switches"""
    all_switches = Switch.query.all()
    return render_template('switches.html', switches=all_switches)

@app.route('/switch/<int:switch_id>')
def switch_detail(switch_id):
    """Detailed view of a single switch"""
    switch = Switch.query.get_or_404(switch_id)
    
    # Get recent metrics (last 24 hours)
    since = datetime.utcnow() - timedelta(hours=24)
    metrics = Metric.query.filter(
        Metric.switch_id == switch_id,
        Metric.timestamp >= since
    ).order_by(Metric.timestamp.desc()).all()
    
    # Get alerts for this switch
    alerts = Alert.query.filter_by(switch_id=switch_id).order_by(Alert.timestamp.desc()).limit(20).all()
    
    return render_template('switch_detail.html', switch=switch, metrics=metrics, alerts=alerts)

@app.route('/switch/add', methods=['GET', 'POST'])
def add_switch():
    """Add a new switch"""
    if request.method == 'POST':
        switch = Switch(
            name=request.form['name'],
            ip_address=request.form['ip_address'],
            username=request.form['username'],
            password=request.form['password'],
            device_type=request.form.get('device_type', 'cisco_ios')
        )
        db.session.add(switch)
        db.session.commit()
        return redirect(url_for('switches'))
    
    return render_template('add_switch.html')

@app.route('/switch/<int:switch_id>/delete', methods=['POST'])
def delete_switch(switch_id):
    """Delete a switch"""
    switch = Switch.query.get_or_404(switch_id)
    db.session.delete(switch)
    db.session.commit()
    return redirect(url_for('switches'))

@app.route('/alerts')
def alerts():
    """View all alerts"""
    all_alerts = Alert.query.order_by(Alert.timestamp.desc()).all()
    return render_template('alerts.html', alerts=all_alerts)

@app.route('/alert/<int:alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    alert = Alert.query.get_or_404(alert_id)
    alert.acknowledged = True
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/analytics')
def analytics():
    """Analytics page"""
    # Get metrics for the last 7 days
    since = datetime.utcnow() - timedelta(days=7)
    metrics = Metric.query.filter(Metric.timestamp >= since).all()
    
    # Calculate analytics data
    total_metrics = len(metrics)
    avg_cpu = sum(m.cpu_usage for m in metrics if m.cpu_usage) / max(1, len([m for m in metrics if m.cpu_usage]))
    avg_memory = sum(m.memory_usage for m in metrics if m.memory_usage) / max(1, len([m for m in metrics if m.memory_usage]))
    
    # Get top devices by alerts
    alert_counts = db.session.query(
        Switch.name, 
        db.func.count(Alert.id).label('alert_count')
    ).join(Alert).group_by(Switch.id).order_by(db.desc('alert_count')).limit(5).all()
    
    return render_template('analytics.html', 
                         total_metrics=total_metrics,
                         avg_cpu=round(avg_cpu, 1),
                         avg_memory=round(avg_memory, 1),
                         alert_counts=alert_counts)

@app.route('/logs')
def logs():
    """System logs page"""
    # Get recent alerts as logs
    logs = Alert.query.order_by(Alert.timestamp.desc()).limit(100).all()
    return render_template('logs.html', logs=logs)

@app.route('/settings')
def settings():
    """Settings page"""
    return render_template('settings.html')

@app.route('/settings', methods=['POST'])
def update_settings():
    """Update settings"""
    try:
        # Get form data
        enable_email = 'enable_email' in request.form
        smtp_server = request.form.get('smtp_server', 'smtp.gmail.com')
        smtp_port = int(request.form.get('smtp_port', 587))
        smtp_username = request.form.get('smtp_username', '')
        smtp_password = request.form.get('smtp_password', '')
        alert_emails = request.form.get('alert_emails', '').split(',')
        alert_emails = [email.strip() for email in alert_emails if email.strip()]
        
        # Read current config file
        with open('config.py', 'r') as f:
            config_content = f.read()
        
        # Update config content with new values
        import re
        config_content = re.sub(r'ENABLE_EMAIL_ALERTS = .*', f'ENABLE_EMAIL_ALERTS = {enable_email}', config_content)
        config_content = re.sub(r'SMTP_SERVER = .*', f"SMTP_SERVER = '{smtp_server}'", config_content)
        config_content = re.sub(r'SMTP_PORT = .*', f'SMTP_PORT = {smtp_port}', config_content)
        config_content = re.sub(r'SMTP_USERNAME = .*', f"SMTP_USERNAME = '{smtp_username}'", config_content)
        if smtp_password:  # Only update password if provided
            config_content = re.sub(r'SMTP_PASSWORD = .*', f"SMTP_PASSWORD = '{smtp_password}'", config_content)
        config_content = re.sub(r'ALERT_EMAIL_TO = .*', f"ALERT_EMAIL_TO = {alert_emails}", config_content)
        
        # Write updated config back to file
        with open('config.py', 'w') as f:
            f.write(config_content)
        
        # Reload the config module to apply changes immediately
        import importlib
        import config
        importlib.reload(config)
        
        return jsonify({
            'status': 'success', 
            'message': f'Settings saved successfully! Email alerts are now {"enabled" if enable_email else "disabled"}. Changes applied immediately.'
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to save settings: {str(e)}'})

@app.route('/test-email', methods=['POST'])
def test_email():
    """Test email functionality"""
    try:
        # Reload config to get latest settings
        import importlib
        import config
        importlib.reload(config)
        
        from email_notifier import EmailNotifier
        notifier = EmailNotifier()
        
        if not notifier.enabled:
            return jsonify({'status': 'error', 'message': 'Email alerts are disabled. Please enable them first and save settings.'})
        
        success = notifier.send_alert(
            'Test Switch',
            '192.168.1.100',
            'connectivity',
            'info',
            'This is a test email from your Network Monitoring System. If you received this, email alerts are working correctly!'
        )
        
        if success:
            return jsonify({'status': 'success', 'message': 'Test email sent successfully! Check your inbox.'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to send test email. Please check your email settings and Gmail App Password.'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Email test failed: {str(e)}'})


@app.route('/api/search')
def api_search():
    """API endpoint for searching devices"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    switches = Switch.query.filter(
        db.or_(
            Switch.name.ilike(f'%{query}%'),
            Switch.ip_address.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    results = []
    for switch in switches:
        results.append({
            'id': switch.id,
            'name': switch.name,
            'ip_address': switch.ip_address,
            'status': switch.status,
            'url': url_for('switch_detail', switch_id=switch.id)
        })
    
    return jsonify(results)

@app.route('/api/metrics/<int:switch_id>')
def api_metrics(switch_id):
    """API endpoint for switch metrics"""
    hours = request.args.get('hours', 24, type=int)
    since = datetime.utcnow() - timedelta(hours=hours)
    
    metrics = Metric.query.filter(
        Metric.switch_id == switch_id,
        Metric.timestamp >= since
    ).order_by(Metric.timestamp.asc()).all()
    
    data = {
        'timestamps': [m.timestamp.isoformat() for m in metrics],
        'cpu': [m.cpu_usage for m in metrics],
        'memory': [m.memory_usage for m in metrics]
    }
    
    return jsonify(data)

def init_db():
    """Initialize the database"""
    with app.app_context():
        db.create_all()
        print("Database initialized.")

if __name__ == '__main__':
    init_db()
    monitor.start()
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        monitor.stop()
