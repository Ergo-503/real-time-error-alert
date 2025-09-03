#!/usr/bin/env python3
"""
Configuration Manager
====================
This module handles loading and managing configuration settings for the Log Monitor.
It uses INI file format for easy configuration and provides default values for
all settings to ensure the system works out of the box.

The ConfigManager class centralizes all configuration logic and provides
validation and fallback mechanisms for robust operation.
"""

import os
import configparser
from pathlib import Path


class ConfigManager:
    """
    Configuration manager that handles loading settings from config.ini file.
    
    This class provides a centralized way to manage all configuration settings
    including log file paths, email settings, Slack webhooks, and monitoring rules.
    It includes validation and provides sensible defaults for all settings.
    """
    
    def __init__(self, config_file='config.ini'):
        """
        Initialize configuration manager and load settings.
        
        Args:
            config_file (str): Path to the configuration file (default: config.ini)
        """
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        
        print(f"🔧 Loading configuration from: {config_file}")
        
        # Load configuration file
        self._load_configuration()
        
        # Validate critical settings
        self._validate_configuration()
        
        print("✅ Configuration loaded successfully")
    
    def _load_configuration(self):
        """
        Load configuration from INI file.
        Creates a default configuration file if none exists.
        """
        if os.path.exists(self.config_file):
            # Load existing configuration
            self.config.read(self.config_file)
            print(f"📖 Configuration loaded from existing file")
        else:
            # Create default configuration file
            print(f"📝 Configuration file not found, creating default: {self.config_file}")
            self._create_default_config()
            self.config.read(self.config_file)
    
    def _create_default_config(self):
        """
        Create a default configuration file with example settings.
        This helps users get started quickly with proper configuration structure.
        """
        default_config = """# Log Monitor Demo Configuration
# =====================================
# This file contains all configuration settings for the log monitoring system.
# Update the values below according to your environment and requirements.

[general]
# Path to the log file to monitor (relative or absolute path)
log_file_path = sample.log

# Error keywords to watch for in log files (comma-separated)
error_keywords = ERROR, CRITICAL, EXCEPTION, FATAL, FAIL

# Minimum seconds between notifications to prevent spam
rate_limit_seconds = 300

[email]
# SMTP server configuration for sending email alerts
# Gmail SMTP settings (most common)
smtp_server = smtp.gmail.com
smtp_port = 587

# Sender email credentials
# For Gmail, you may need to use an "App Password" instead of your regular password
# See: https://support.google.com/accounts/answer/185833
sender_email = your.email@gmail.com
sender_password = your_app_password_here

# Display name for outgoing emails
sender_name = Log Monitor Demo

# Recipient email addresses (comma-separated for multiple recipients)
recipient_emails = admin@yourcompany.com, devteam@yourcompany.com

[slack]
# Slack webhook URL for sending notifications
# Create an Incoming Webhook in your Slack workspace:
# 1. Go to https://api.slack.com/apps
# 2. Create new app or select existing one
# 3. Go to Incoming Webhooks and create new webhook
# 4. Copy the webhook URL here
webhook_url = https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Slack channel to send notifications to (include # for public channels)
channel = #alerts

# Username that will appear as the sender in Slack
username = Log Monitor

# Alternative SMTP configurations for other email providers:
# 
# Outlook/Hotmail:
# smtp_server = smtp-mail.outlook.com
# smtp_port = 587
#
# Yahoo:
# smtp_server = smtp.mail.yahoo.com  
# smtp_port = 587
#
# Custom SMTP:
# smtp_server = your.smtp.server.com
# smtp_port = 587 (or 465 for SSL)
"""
        
        # Write default configuration to file
        with open(self.config_file, 'w') as f:
            f.write(default_config)
        
        print(f"✅ Default configuration created at: {self.config_file}")
        print("💡 Please edit config.ini with your actual email and Slack settings")
    
    def _validate_configuration(self):
        """
        Validate critical configuration settings and warn about missing values.
        This helps users identify configuration issues early.
        """
        print("🔍 Validating configuration...")
        
        warnings = []
        
        # Validate general settings
        if not self.get_log_file_path():
            warnings.append("Log file path not specified in [general] section")
        
        if not self.get_error_keywords():
            warnings.append("No error keywords specified in [general] section")
        
        # Validate email settings
        if self.has_section('email'):
            if not self.get('email', 'sender_email'):
                warnings.append("Email sender_email not configured")
            if not self.get('email', 'sender_password'):
                warnings.append("Email sender_password not configured")
            if not self.get('email', 'recipient_emails'):
                warnings.append("Email recipient_emails not configured")
        
        # Validate Slack settings
        if self.has_section('slack'):
            webhook = self.get('slack', 'webhook_url')
            if not webhook or webhook.startswith('https://hooks.slack.com/services/YOUR'):
                warnings.append("Slack webhook_url not configured or using placeholder")
        
        # Display warnings
        if warnings:
            print("⚠️  Configuration warnings:")
            for warning in warnings:
                print(f"   • {warning}")
            print("💡 Some features may not work until configuration is updated")
        else:
            print("✅ Configuration validation passed")
    
    def get_log_file_path(self):
        """
        Get the path to the log file to monitor.
        
        Returns:
            str: Absolute path to the log file
        """
        log_path = self.get('general', 'log_file_path', fallback='sample.log')
        
        # Convert to absolute path
        abs_path = Path(log_path).resolve()
        
        return str(abs_path)
    
    def get_error_keywords(self):
        """
        Get the list of error keywords to watch for in logs.
        
        Returns:
            list: List of error keywords (strings)
        """
        keywords_str = self.get('general', 'error_keywords', fallback='ERROR, CRITICAL, EXCEPTION, FATAL')
        
        # Split by comma and clean up whitespace
        keywords = [keyword.strip() for keyword in keywords_str.split(',')]
        
        # Remove empty strings
        keywords = [k for k in keywords if k]
        
        return keywords
    
    def get_rate_limit_seconds(self):
        """
        Get the rate limiting interval in seconds.
        
        Returns:
            int: Minimum seconds between notifications
        """
        return self.getint('general', 'rate_limit_seconds', fallback=300)
    
    def is_email_configured(self):
        """
        Check if email notifications are properly configured.
        
        Returns:
            bool: True if email settings are complete, False otherwise
        """
        if not self.has_section('email'):
            return False
        
        required_fields = ['sender_email', 'sender_password', 'recipient_emails']
        for field in required_fields:
            if not self.get('email', field):
                return False
        
        return True
    
    def is_slack_configured(self):
        """
        Check if Slack notifications are properly configured.
        
        Returns:
            bool: True if Slack settings are complete, False otherwise
        """
        if not self.has_section('slack'):
            return False
        
        webhook_url = self.get('slack', 'webhook_url')
        if not webhook_url or webhook_url.startswith('https://hooks.slack.com/services/YOUR'):
            return False
        
        return True
    
    def get_email_settings(self):
        """
        Get all email configuration settings as a dictionary.
        
        Returns:
            dict: Email configuration settings
        """
        if not self.has_section('email'):
            return {}
        
        return {
            'smtp_server': self.get('email', 'smtp_server', fallback='smtp.gmail.com'),
            'smtp_port': self.getint('email', 'smtp_port', fallback=587),
            'sender_email': self.get('email', 'sender_email'),
            'sender_password': self.get('email', 'sender_password'),
            'sender_name': self.get('email', 'sender_name', fallback='Log Monitor'),
            'recipient_emails': [
                email.strip() 
                for email in self.get('email', 'recipient_emails', fallback='').split(',')
                if email.strip()
            ]
        }
    
    def get_slack_settings(self):
        """
        Get all Slack configuration settings as a dictionary.
        
        Returns:
            dict: Slack configuration settings
        """
        if not self.has_section('slack'):
            return {}
        
        return {
            'webhook_url': self.get('slack', 'webhook_url'),
            'channel': self.get('slack', 'channel', fallback='#alerts'),
            'username': self.get('slack', 'username', fallback='Log Monitor')
        }
    
    def print_configuration_summary(self):
        """
        Print a summary of the current configuration for debugging.
        This helps users verify their settings without exposing sensitive data.
        """
        print("\n" + "=" * 60)
        print("📋 CONFIGURATION SUMMARY")
        print("=" * 60)
        
        # General settings
        print("🔧 General Settings:")
        print(f"   Log file: {self.get_log_file_path()}")
        print(f"   Error keywords: {', '.join(self.get_error_keywords())}")
        print(f"   Rate limit: {self.get_rate_limit_seconds()} seconds")
        
        # Email settings
        print("\n📧 Email Settings:")
        if self.is_email_configured():
            email_settings = self.get_email_settings()
            print(f"   Status: ✅ Configured")
            print(f"   SMTP Server: {email_settings['smtp_server']}:{email_settings['smtp_port']}")
            print(f"   Sender: {email_settings['sender_email']}")
            print(f"   Recipients: {len(email_settings['recipient_emails'])} configured")
        else:
            print(f"   Status: ❌ Not configured")
        
        # Slack settings
        print("\n📱 Slack Settings:")
        if self.is_slack_configured():
            slack_settings = self.get_slack_settings()
            print(f"   Status: ✅ Configured")
            print(f"   Channel: {slack_settings['channel']}")
            print(f"   Username: {slack_settings['username']}")
        else:
            print(f"   Status: ❌ Not configured")
        
        print("=" * 60)
    
    # Wrapper methods for configparser functionality
    def has_section(self, section):
        """Check if configuration section exists."""
        return self.config.has_section(section)
    
    def get(self, section, option, fallback=None):
        """Get configuration value with fallback."""
        return self.config.get(section, option, fallback=fallback)
    
    def getint(self, section, option, fallback=None):
        """Get integer configuration value with fallback."""
        return self.config.getint(section, option, fallback=fallback)
    
    def getboolean(self, section, option, fallback=None):
        """Get boolean configuration value with fallback."""
        return self.config.getboolean(section, option, fallback=fallback)
    
    def sections(self):
        """Get all configuration sections."""
        return self.config.sections()


# Demo/testing functionality
if __name__ == "__main__":
    """
    Simple test to demonstrate configuration management functionality.
    This can be run independently to test configuration loading and validation.
    """
    print("🧪 ConfigManager Test Mode")
    print("=" * 50)
    
    try:
        # Create configuration manager
        config = ConfigManager()
        
        # Print configuration summary
        config.print_configuration_summary()
        
        # Test specific configuration methods
        print("\n🔍 Testing configuration methods:")
        print(f"   Log file path: {config.get_log_file_path()}")
        print(f"   Error keywords: {config.get_error_keywords()}")
        print(f"   Rate limit: {config.get_rate_limit_seconds()} seconds")
        print(f"   Email configured: {config.is_email_configured()}")
        print(f"   Slack configured: {config.is_slack_configured()}")
        
        print("\n✅ Configuration test completed successfully")
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        print("💡 Check if config.ini file is accessible and properly formatted")