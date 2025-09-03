# 🔍 Real-time Log Monitor Demo

A Python-based log monitoring system that automatically sends email and Slack notifications when errors are detected in application logs. This demo version provides real-time error detection with configurable alerting to help teams identify and resolve issues quickly.

## ✨ Features

- **Real-time Monitoring**: Uses file system events to detect log changes instantly
- **Multi-channel Notifications**: Supports both email (SMTP) and Slack webhooks
- **Configurable Error Detection**: Customizable keywords and patterns for error identification
- **Rate Limiting**: Built-in spam prevention to avoid notification overload
- **Rich Formatting**: Well-formatted HTML emails and structured Slack messages
- **Easy Configuration**: Simple INI-based configuration with helpful defaults
- **Graceful Shutdown**: Proper cleanup and signal handling
- **Extensive Logging**: Detailed console output for monitoring and debugging

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Log Watcher   │────│ Notification     │────│ Email & Slack       │
│                 │    │ Manager          │    │ Notifiers           │
│ • File Monitor  │    │                  │    │                     │
│ • Error Parser  │    │ • Rate Limiter   │    │ • SMTP Client       │
│ • Pattern Match │    │ • Channel Coord  │    │ • Webhook Client    │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
         │                        │                         │
         │                        │                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│ Config Manager  │    │   Main Process   │    │    Log File         │
│                 │    │                  │    │                     │
│ • INI Parser    │    │ • Signal Handler │    │ • sample.log        │
│ • Validation    │    │ • Main Loop      │    │ • Real-time writes  │
│ • Defaults      │    │ • Error Handler  │    │ • Pattern detection │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the project files
git clone <repository-url>
cd log-monitor-demo

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configuration

The system automatically creates a `config.ini` file on first run. Edit it with your settings:

```ini
[general]
log_file_path = sample.log
error_keywords = ERROR, CRITICAL, EXCEPTION, FATAL, FAIL
rate_limit_seconds = 300

[email]
smtp_server = smtp.gmail.com
smtp_port = 587
sender_email = your.email@gmail.com
sender_password = your_app_password_here
sender_name = Log Monitor Demo
recipient_emails = admin@yourcompany.com, devteam@yourcompany.com

[slack]
webhook_url = https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
channel = #alerts
username = Log Monitor
```

### 3. Run the Monitor

```bash
# Start the log monitor
python main.py
```

### 4. Test the System

```bash
# In another terminal, simulate errors by adding to the log file
echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: Test error message" >> sample.log
echo "$(date '+%Y-%m-%d %H:%M:%S') CRITICAL: Critical system failure" >> sample.log
```

## 📁 Project Structure

```
log-monitor-demo/
├── main.py              # Main entry point and orchestrator
├── log_watcher.py       # Real-time file monitoring component  
├── notifier.py          # Email and Slack notification handlers
├── config_manager.py    # Configuration management and validation
├── config.ini           # Configuration file (auto-generated)
├── sample.log           # Example log file for testing
├── requirements.txt     # Python dependencies
└── README.md           # This documentation file
```

## ⚙️ Configuration Guide

### Email Configuration

#### Gmail Setup
1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password:
   - Go to Google Account settings → Security
   - Select "App passwords" under 2-Step Verification
   - Generate password for "Mail"
   - Use this password in `config.ini`

```ini
[email]
smtp_server = smtp.gmail.com
smtp_port = 587
sender_email = your.email@gmail.com
sender_password = your_16_character_app_password
```

#### Other Email Providers

**Outlook/Hotmail:**
```ini
smtp_server = smtp-mail.outlook.com
smtp_port = 587
```

**Yahoo:**
```ini
smtp_server = smtp.mail.yahoo.com
smtp_port = 587
```

### Slack Configuration

1. Create a Slack App:
   - Go to https://api.slack.com/apps
   - Click "Create New App" → "From scratch"
   - Choose your workspace

2. Enable Incoming Webhooks:
   - Go to "Incoming Webhooks" in your app settings
   - Turn on "Activate Incoming Webhooks"
   - Click "Add New Webhook to Workspace"
   - Choose the channel and authorize

3. Copy webhook URL to `config.ini`:
```ini
[slack]
webhook_url = https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX
channel = #alerts
username = Log Monitor
```

## 🎯 Usage Examples

### Basic Monitoring
```bash
# Monitor default log file with default settings
python main.py
```

### Custom Log File
```ini
# Edit config.ini
[general]
log_file_path = /var/log/myapp/application.log
```

### Custom Error Patterns
```ini
# Edit config.ini - add your specific error keywords
[general]
error_keywords = ERROR, CRITICAL, FATAL, OutOfMemory, SQLException, TimeoutException
```

### Testing Notifications
```python
# Run notification test
python notifier.py
```

## 🔧 Component Details

### LogWatcher (`log_watcher.py`)
- **File System Events**: Uses `watchdog` library for efficient file monitoring
- **Pattern Matching**: Regex-based error detection with configurable keywords
- **Log Parsing**: Extracts timestamps, error levels, and messages from log lines
- **Thread Safety**: Runs monitoring in background thread

### NotificationManager (`notifier.py`)
- **Email Notifications**: HTML and plain text formatted emails via SMTP
- **Slack Integration**: Rich formatted messages with color coding and attachments
- **Rate Limiting**: Prevents notification spam with configurable cooldown
- **Error Handling**: Robust retry logic and graceful failure handling

### ConfigManager (`config_manager.py`)
- **INI File Management**: Loads and validates configuration settings
- **Default Generation**: Creates example config file if none exists
- **Validation**: Checks for required settings and provides helpful warnings
- **Environment Support**: Handles relative and absolute file paths

## 🚨 Error Handling

The system includes comprehensive error handling:

- **Configuration Errors**: Clear messages for missing or invalid settings
- **Network Issues**: Retry logic for email and Slack delivery failures
- **File Access**: Graceful handling of permission and file system issues
- **Signal Handling**: Clean shutdown on SIGINT (Ctrl+C) and SIGTERM

## 📊 Monitoring and Debugging

### Console Output
The system provides detailed console output for monitoring:
```
🚀 Initializing Log Monitor Demo...
📁 Monitoring log file: /path/to/sample.log
🔍 Watching for keywords: ERROR, CRITICAL, EXCEPTION, FATAL
✅ Initialization complete!

🔍 Starting log file monitoring...
👀 Watching for errors in real-time...
⏹️  Press Ctrl+C to stop

⚠️  ERROR DETECTED: ERROR - Database connection timeout after 30 seconds
📤 Sending notifications...
✅ Email notification sent successfully
✅ Slack notification sent successfully
```

### Log File Formats
The system can parse common log formats:
```
# Timestamp-based logs
2024-01-15 14:30:25 ERROR: Database connection failed

# Bracketed timestamps  
[2024-01-15 14:30:25] ERROR Database connection failed

# Application logs
ERROR 2024-01-15T14:30:25Z Application crashed with exception
```

## 🔒 Security Considerations

- **Credentials**: Store email passwords and API keys securely
- **File Permissions**: Ensure log files are readable by the monitor process
- **Network Security**: Use secure SMTP (TLS) and HTTPS webhooks
- **Rate Limiting**: Prevent potential DoS through excessive notifications

## 🧪 Testing

### Unit Testing
```bash
# Test individual components
python config_manager.py    # Test configuration loading
python log_watcher.py       # Test file monitoring
python notifier.py          # Test notifications
```

### Integration Testing
```bash
# Start monitor in one terminal
python main.py

# Simulate errors in another terminal
echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: Test integration" >> sample.log
```

## 🚀 Production Deployment

### As a Systemd Service (Linux)

1. Create service file:
```ini
# /etc/systemd/system/log-monitor.service
[Unit]
Description=Log Monitor Service
After=network.target

[Service]
Type=simple
User=logmonitor
Group=logmonitor
WorkingDirectory=/opt/log-monitor
ExecStart=/usr/bin/python3 /opt/log-monitor/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. Enable and start:
```bash
sudo systemctl enable log-monitor
sudo systemctl start log-monitor
sudo systemctl status log-monitor
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

```bash
# Build and run
docker build -t log-monitor .
docker run -v /host/logs:/app/logs -v /host/config.ini:/app/config.ini log-monitor
```

## 🔮 Future Enhancements

This demo version can be extended with:

- **Database Storage**: Store error history and statistics
- **Web Dashboard**: Real-time monitoring interface
- **Multiple Log Files**: Monitor multiple files simultaneously
- **Custom Parsers**: Support for structured logs (JSON, XML)
- **Machine Learning**: Anomaly detection and pattern recognition
- **Metrics Integration**: Prometheus/Grafana integration
- **Mobile Notifications**: Push notifications via services like Pushover
- **Advanced Filtering**: Complex rules engine for error classification

## ❓ Troubleshooting

### Common Issues

**"Config file not found"**
- The system auto-creates `config.ini` on first run
- Ensure write permissions in the current directory

**"Email authentication failed"**
- For Gmail, use App Passwords instead of account password
- Check SMTP server and port settings
- Verify firewall allows SMTP connections

**"Slack webhook failed"**
- Verify webhook URL is correct and complete
- Check if Slack app has necessary permissions
- Test webhook with curl: `curl -X POST -H 'Content-type: application/json' --data '{"text":"Test"}' YOUR_WEBHOOK_URL`

**"Log file not found"**
- Check file path in config.ini (relative or absolute)
- Ensure read permissions on log file
- Verify log file exists or will be created by your application

**"No notifications received"**
- Check rate limiting (default 5 minutes between notifications)
- Verify error keywords match your log format
- Test with manual log entries to confirm detection

### Debug Mode
Add debug output by modifying the main script:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 License

This is a demo/educational project. Feel free to modify and use in your own projects.

## 🤝 Contributing

This is a demo version, but improvements are welcome:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For questions or issues with this demo:
1. Check the troubleshooting section above
2. Review configuration settings
3. Test individual components
4. Check console output for error messages

---

*Happy monitoring! 🔍📊*