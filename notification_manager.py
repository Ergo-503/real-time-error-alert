#!/usr/bin/env python3
"""
Notification Manager
===================
This module handles sending notifications via multiple channels (Email and Slack)
when errors are detected in log files. It includes rate limiting to prevent
notification spam and supports various email providers.

The NotificationManager coordinates between different notification channels
and ensures messages are properly formatted and delivered reliably.
"""

import smtplib
import time
import json
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr


class RateLimiter:
    """
    Simple rate limiter to prevent notification spam.
    
    This class tracks when the last notification was sent and enforces
    a minimum time interval between notifications to avoid overwhelming
    users with alerts for the same recurring issue.
    """
    
    def __init__(self, min_interval_seconds=300):  # Default: 5 minutes
        """
        Initialize the rate limiter.
        
        Args:
            min_interval_seconds (int): Minimum seconds between notifications
        """
        self.min_interval = min_interval_seconds
        self.last_notification_time = 0
        
        print(f"⏱️  Rate limiter initialized: {min_interval_seconds} seconds between notifications")
    
    def should_send_notification(self):
        """
        Check if enough time has passed since the last notification.
        
        Returns:
            bool: True if notification should be sent, False if rate limited
        """
        current_time = time.time()
        time_since_last = current_time - self.last_notification_time
        
        if time_since_last >= self.min_interval:
            self.last_notification_time = current_time
            return True
        
        remaining_time = self.min_interval - time_since_last
        print(f"⏸️  Rate limited: {remaining_time:.0f} seconds remaining until next notification allowed")
        return False
    
    def reset(self):
        """Reset the rate limiter (useful for testing or manual override)."""
        self.last_notification_time = 0
        print("🔄 Rate limiter reset")


class EmailNotifier:
    """
    Email notification handler using SMTP.
    
    This class handles sending email alerts through various SMTP providers
    including Gmail, Outlook, and other standard SMTP servers.
    """
    
    def __init__(self, config_manager):
        """
        Initialize email notifier with configuration.
        
        Args:
            config_manager: Configuration manager instance with email settings
        """
        self.config = config_manager
        self.smtp_server = config_manager.get('email', 'smtp_server', fallback='smtp.gmail.com')
        self.smtp_port = config_manager.getint('email', 'smtp_port', fallback=587)
        self.sender_email = config_manager.get('email', 'sender_email')
        self.sender_password = config_manager.get('email', 'sender_password')
        self.recipient_emails = [
            email.strip() 
            for email in config_manager.get('email', 'recipient_emails').split(',')
        ]
        self.sender_name = config_manager.get('email', 'sender_name', fallback='Log Monitor')
        
        print(f"📧 Email notifier initialized:")
        print(f"   Server: {self.smtp_server}:{self.smtp_port}")
        print(f"   Sender: {self.sender_email}")
        print(f"   Recipients: {', '.join(self.recipient_emails)}")
    
    def send_alert(self, error_info):
        """
        Send email alert for detected error.
        
        Args:
            error_info (dict): Error information containing timestamp, level, message, etc.
        
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Create email message
            message = self._create_email_message(error_info)
            
            # Send via SMTP
            self._send_via_smtp(message)
            
            print(f"✅ Email alert sent to {len(self.recipient_emails)} recipient(s)")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email alert: {e}")
            return False
    
    def _create_email_message(self, error_info):
        """
        Create a formatted email message for the error alert.
        
        Args:
            error_info (dict): Error information
        
        Returns:
            MIMEMultipart: Formatted email message
        """
        # Create message container
        message = MIMEMultipart('alternative')
        
        # Set email headers
        message['Subject'] = f"🚨 Log Alert: {error_info['level']} Detected"
        message['From'] = formataddr((self.sender_name, self.sender_email))
        message['To'] = ', '.join(self.recipient_emails)
        
        # Create email body
        text_body = self._create_text_body(error_info)
        html_body = self._create_html_body(error_info)
        
        # Attach both text and HTML versions
        message.attach(MIMEText(text_body, 'plain'))
        message.attach(MIMEText(html_body, 'html'))
        
        return message
    
    def _create_text_body(self, error_info):
        """
        Create plain text email body.
        
        Args:
            error_info (dict): Error information
        
        Returns:
            str: Formatted plain text email body
        """
        return f"""
LOG MONITOR ALERT
=================

An error has been detected in your application logs:

🕐 Timestamp: {error_info['timestamp']}
🚨 Level: {error_info['level']}
📝 Message: {error_info['message']}
🔍 Matched Keyword: {error_info['matched_keyword']}

Full Log Line:
{error_info['line']}

Detection Details:
- Detected at: {error_info['detected_at']}
- System: Log Monitor Demo

This is an automated alert. Please investigate the issue promptly.

---
Log Monitor Demo System
        """.strip()
    
    def _create_html_body(self, error_info):
        """
        Create HTML email body with better formatting.
        
        Args:
            error_info (dict): Error information
        
        Returns:
            str: Formatted HTML email body
        """
        # Choose color based on error level
        level_colors = {
            'CRITICAL': '#dc3545',  # Red
            'ERROR': '#fd7e14',     # Orange
            'FATAL': '#dc3545',     # Red
            'EXCEPTION': '#fd7e14', # Orange
            'WARNING': '#ffc107',   # Yellow
            'WARN': '#ffc107',      # Yellow
        }
        
        level_color = level_colors.get(error_info['level'], '#6c757d')  # Default gray
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Log Monitor Alert</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: {level_color}; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <h2 style="margin: 0;">🚨 Log Monitor Alert</h2>
                    <p style="margin: 5px 0 0 0;">Error Level: <strong>{error_info['level']}</strong></p>
                </div>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <h3 style="margin-top: 0; color: #495057;">Error Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px; font-weight: bold; width: 150px;">🕐 Timestamp:</td>
                            <td style="padding: 8px;">{error_info['timestamp']}</td>
                        </tr>
                        <tr style="background-color: white;">
                            <td style="padding: 8px; font-weight: bold;">🚨 Level:</td>
                            <td style="padding: 8px;"><span style="color: {level_color}; font-weight: bold;">{error_info['level']}</span></td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; font-weight: bold;">📝 Message:</td>
                            <td style="padding: 8px;">{error_info['message']}</td>
                        </tr>
                        <tr style="background-color: white;">
                            <td style="padding: 8px; font-weight: bold;">🔍 Keyword:</td>
                            <td style="padding: 8px;">{error_info['matched_keyword']}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="background-color: #e9ecef; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <h4 style="margin-top: 0;">Full Log Line:</h4>
                    <code style="background-color: #f8f9fa; padding: 10px; display: block; border-radius: 3px; font-size: 12px; overflow-x: auto;">
                        {error_info['line']}
                    </code>
                </div>
                
                <div style="border-top: 1px solid #dee2e6; padding-top: 15px; font-size: 12px; color: #6c757d;">
                    <p><strong>Detection Details:</strong></p>
                    <ul style="margin: 0; padding-left: 20px;">
                        <li>Detected at: {error_info['detected_at']}</li>
                        <li>System: Log Monitor Demo</li>
                    </ul>
                    <p style="margin-top: 15px;"><em>This is an automated alert from your Log Monitor system. Please investigate the issue promptly.</em></p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _send_via_smtp(self, message):
        """
        Send email message via SMTP server.
        
        Args:
            message (MIMEMultipart): Email message to send
        """
        # Connect to SMTP server
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            # Enable TLS encryption
            server.starttls()
            
            # Login to email account
            server.login(self.sender_email, self.sender_password)
            
            # Send email to all recipients
            server.send_message(message)


class SlackNotifier:
    """
    Slack notification handler using webhooks.
    
    This class sends formatted alerts to Slack channels via incoming webhooks,
    providing real-time notifications to development teams.
    """
    
    def __init__(self, config_manager):
        """
        Initialize Slack notifier with webhook configuration.
        
        Args:
            config_manager: Configuration manager instance with Slack settings
        """
        self.webhook_url = config_manager.get('slack', 'webhook_url')
        self.channel = config_manager.get('slack', 'channel', fallback='#alerts')
        self.username = config_manager.get('slack', 'username', fallback='Log Monitor')
        
        print(f"📱 Slack notifier initialized:")
        print(f"   Channel: {self.channel}")
        print(f"   Username: {self.username}")
        print(f"   Webhook configured: {'✅' if self.webhook_url else '❌'}")
    
    def send_alert(self, error_info):
        """
        Send Slack alert for detected error.
        
        Args:
            error_info (dict): Error information containing timestamp, level, message, etc.
        
        Returns:
            bool: True if Slack message was sent successfully, False otherwise
        """
        try:
            # Create Slack message payload
            payload = self._create_slack_payload(error_info)
            
            # Send to Slack webhook
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            # Check if request was successful
            response.raise_for_status()
            
            print(f"✅ Slack alert sent to {self.channel}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to send Slack alert: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error sending Slack alert: {e}")
            return False
    
    def _create_slack_payload(self, error_info):
        """
        Create Slack message payload with rich formatting.
        
        Args:
            error_info (dict): Error information
        
        Returns:
            dict: Slack webhook payload
        """
        # Choose emoji and color based on error level
        level_config = {
            'CRITICAL': {'emoji': '🔥', 'color': 'danger'},
            'ERROR': {'emoji': '🚨', 'color': 'danger'},
            'FATAL': {'emoji': '💀', 'color': 'danger'},
            'EXCEPTION': {'emoji': '⚠️', 'color': 'warning'},
            'WARNING': {'emoji': '⚠️', 'color': 'warning'},
            'WARN': {'emoji': '⚠️', 'color': 'warning'},
        }
        
        config = level_config.get(error_info['level'], {'emoji': '📢', 'color': 'good'})
        
        # Create main alert text
        alert_text = f"{config['emoji']} *Log Monitor Alert*: {error_info['level']} detected"
        
        # Create detailed attachment
        attachment = {
            "color": config['color'],
            "title": f"{error_info['level']}: {error_info['message'][:100]}...",
            "fields": [
                {
                    "title": "Timestamp",
                    "value": error_info['timestamp'],
                    "short": True
                },
                {
                    "title": "Level",
                    "value": error_info['level'],
                    "short": True
                },
                {
                    "title": "Matched Keyword",
                    "value": error_info['matched_keyword'],
                    "short": True
                },
                {
                    "title": "Detection Time",
                    "value": error_info['detected_at'],
                    "short": True
                },
                {
                    "title": "Error Message",
                    "value": f"```{error_info['message']}```",
                    "short": False
                }
            ],
            "footer": "Log Monitor Demo",
            "footer_icon": "https://cdn-icons-png.flaticon.com/512/2919/2919906.png",
            "ts": int(time.time())
        }
        
        # Add full log line if different from message
        if error_info['line'] != error_info['message']:
            attachment["fields"].append({
                "title": "Full Log Line",
                "value": f"```{error_info['line']}```",
                "short": False
            })
        
        return {
            "channel": self.channel,
            "username": self.username,
            "icon_emoji": ":warning:",
            "text": alert_text,
            "attachments": [attachment]
        }


class NotificationManager:
    """
    Main notification coordinator that manages multiple notification channels.
    
    This class coordinates between email and Slack notifications, handles rate limiting,
    and provides a unified interface for sending alerts across all channels.
    """
    
    def __init__(self, config_manager):
        """
        Initialize notification manager with all configured channels.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        
        # Initialize rate limiter
        rate_limit_seconds = config_manager.getint('general', 'rate_limit_seconds', fallback=300)
        self.rate_limiter = RateLimiter(rate_limit_seconds)
        
        # Initialize notification channels
        self.email_notifier = None
        self.slack_notifier = None
        
        # Set up email notifications if configured
        if config_manager.has_section('email') and config_manager.get('email', 'sender_email'):
            try:
                self.email_notifier = EmailNotifier(config_manager)
                print("📧 Email notifications enabled")
            except Exception as e:
                print(f"⚠️  Email notifications disabled due to configuration error: {e}")
        
        # Set up Slack notifications if configured
        if config_manager.has_section('slack') and config_manager.get('slack', 'webhook_url'):
            try:
                self.slack_notifier = SlackNotifier(config_manager)
                print("📱 Slack notifications enabled")
            except Exception as e:
                print(f"⚠️  Slack notifications disabled due to configuration error: {e}")
        
        # Ensure at least one notification channel is available
        if not self.email_notifier and not self.slack_notifier:
            print("⚠️  WARNING: No notification channels are configured!")
            print("   Please configure either email or Slack notifications in config.ini")
    
    def should_send_notification(self):
        """
        Check if notifications should be sent based on rate limiting.
        
        Returns:
            bool: True if notification should be sent, False if rate limited
        """
        return self.rate_limiter.should_send_notification()
    
    def send_email_alert(self, error_info):
        """
        Send email alert if email notifications are configured.
        
        Args:
            error_info (dict): Error information
        
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if self.email_notifier:
            return self.email_notifier.send_alert(error_info)
        else:
            print("⚠️  Email notifications not configured - skipping email alert")
            return False
    
    def send_slack_alert(self, error_info):
        """
        Send Slack alert if Slack notifications are configured.
        
        Args:
            error_info (dict): Error information
        
        Returns:
            bool: True if Slack message was sent successfully, False otherwise
        """
        if self.slack_notifier:
            return self.slack_notifier.send_alert(error_info)
        else:
            print("⚠️  Slack notifications not configured - skipping Slack alert")
            return False
    
    def send_all_alerts(self, error_info):
        """
        Send alerts through all configured notification channels.
        
        Args:
            error_info (dict): Error information
        
        Returns:
            dict: Results from each notification channel
        """
        results = {
            'email_sent': False,
            'slack_sent': False,
            'any_sent': False
        }
        
        # Check rate limiting first
        if not self.should_send_notification():
            print("⏸️  Rate limited - skipping all notifications")
            return results
        
        print(f"📤 Sending notifications for {error_info['level']} error...")
        
        # Send email alert
        results['email_sent'] = self.send_email_alert(error_info)
        
        # Send Slack alert
        results['slack_sent'] = self.send_slack_alert(error_info)
        
        # Determine if any notification was sent
        results['any_sent'] = results['email_sent'] or results['slack_sent']
        
        if results['any_sent']:
            print("✅ Notification alerts sent successfully")
        else:
            print("❌ All notification attempts failed")
        
        return results
    
    def test_notifications(self):
        """
        Send test notifications through all configured channels.
        This method is useful for verifying configuration and connectivity.
        """
        print("🧪 Testing notification channels...")
        
        # Create test error info
        test_error = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'level': 'TEST',
            'message': 'This is a test notification from Log Monitor Demo',
            'line': f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} TEST: This is a test notification from Log Monitor Demo',
            'matched_keyword': 'TEST',
            'detected_at': datetime.now().isoformat()
        }
        
        # Reset rate limiter for testing
        self.rate_limiter.reset()
        
        # Send test notifications
        results = self.send_all_alerts(test_error)
        
        print("\n🧪 Test Results:")
        print(f"   Email: {'✅ Sent' if results['email_sent'] else '❌ Failed'}")
        print(f"   Slack: {'✅ Sent' if results['slack_sent'] else '❌ Failed'}")
        
        return results


# Demo/testing functionality
if __name__ == "__main__":
    """
    Simple test to demonstrate notification functionality.
    This can be run independently to test email and Slack notifications.
    """
    from config_manager import ConfigManager
    
    print("🧪 NotificationManager Test Mode")
    print("=" * 50)
    
    try:
        # Load configuration
        config = ConfigManager()
        
        # Create notification manager
        notifier = NotificationManager(config)
        
        # Run test notifications
        notifier.test_notifications()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("💡 Please ensure config.ini is properly configured with email and/or Slack settings")