#!/usr/bin/env python3
"""
Real-time Log Monitor Demo
==========================
Entry point for the log monitoring system that automatically sends email and Slack notifications
when errors are detected in application logs.

This demo version provides:
- Real-time log file monitoring using file system events
- Email notifications via Gmail SMTP
- Slack notifications via webhook
- Configurable error filtering based on keywords
- Basic rate limiting to prevent notification spam
- Simple INI-based configuration

Author: Demo Version
"""

import sys
import time
import signal
from pathlib import Path

from log_watcher import LogWatcher
from notifier import NotificationManager
from config_manager import ConfigManager


class LogMonitorDemo:
    """
    Main orchestrator class that coordinates all components of the log monitoring system.
    
    This class:
    1. Loads configuration from config.ini
    2. Sets up the log file watcher
    3. Configures notification channels (email & Slack)
    4. Handles graceful shutdown on interruption
    """
    
    def __init__(self):
        """Initialize the log monitor with configuration and components."""
        print("🚀 Initializing Log Monitor Demo...")
        
        # Load configuration from config.ini file
        self.config = ConfigManager()
        
        # Initialize notification manager with email and Slack settings
        self.notifier = NotificationManager(self.config)
        
        # Set up log file watcher that will call our callback when errors are found
        log_file_path = self.config.get_log_file_path()
        self.log_watcher = LogWatcher(
            log_file_path=log_file_path,
            error_keywords=self.config.get_error_keywords(),
            callback=self.handle_error_detected
        )
        
        # Flag to control the main loop
        self.running = False
        
        print(f"📁 Monitoring log file: {log_file_path}")
        print(f"🔍 Watching for keywords: {', '.join(self.config.get_error_keywords())}")
        print("✅ Initialization complete!\n")
    
    def handle_error_detected(self, error_info):
        """
        Callback function that gets called when an error is detected in the log file.
        
        This function:
        1. Receives error information from the log watcher
        2. Applies rate limiting to prevent spam
        3. Sends notifications via configured channels
        
        Args:
            error_info (dict): Dictionary containing:
                - timestamp: when the error occurred
                - level: error level (ERROR, CRITICAL, etc.)
                - message: the actual error message
                - line: full log line
        """
        print(f"⚠️  ERROR DETECTED: {error_info['level']} - {error_info['message'][:100]}...")
        
        # Check rate limiting - don't spam notifications
        if self.notifier.should_send_notification():
            print("📤 Sending notifications...")
            
            # Send email notification
            email_sent = self.notifier.send_email_alert(error_info)
            if email_sent:
                print("✅ Email notification sent successfully")
            else:
                print("❌ Failed to send email notification")
            
            # Send Slack notification
            slack_sent = self.notifier.send_slack_alert(error_info)
            if slack_sent:
                print("✅ Slack notification sent successfully")
            else:
                print("❌ Failed to send Slack notification")
            
            print()  # Empty line for readability
        else:
            print("⏸️  Rate limited - skipping notification to prevent spam\n")
    
    def setup_signal_handlers(self):
        """
        Set up signal handlers for graceful shutdown.
        This allows the program to clean up properly when interrupted.
        """
        def signal_handler(signum, frame):
            print(f"\n🛑 Received signal {signum}. Shutting down gracefully...")
            self.stop()
        
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    def start(self):
        """
        Start the log monitoring process.
        
        This method:
        1. Sets up signal handlers for graceful shutdown
        2. Starts the log file watcher in a separate thread
        3. Enters the main loop to keep the program running
        4. Handles any unexpected errors
        """
        try:
            self.setup_signal_handlers()
            self.running = True
            
            print("🔍 Starting log file monitoring...")
            print("👀 Watching for errors in real-time...")
            print("⏹️  Press Ctrl+C to stop\n")
            
            # Start the log watcher (this runs in a separate thread)
            self.log_watcher.start()
            
            # Main loop - keep the program running
            while self.running:
                time.sleep(1)  # Sleep to prevent high CPU usage
                
                # Periodic status check (every 60 seconds)
                if int(time.time()) % 60 == 0:
                    print(f"💓 Log monitor is running... (monitoring {self.log_watcher.log_file_path})")
                    time.sleep(1)  # Avoid printing multiple times in the same second
        
        except KeyboardInterrupt:
            print("\n🛑 Keyboard interrupt received")
            self.stop()
        except Exception as e:
            print(f"\n💥 Unexpected error occurred: {e}")
            self.stop()
            sys.exit(1)
    
    def stop(self):
        """
        Stop the log monitoring process gracefully.
        
        This method:
        1. Sets the running flag to False
        2. Stops the log file watcher
        3. Performs cleanup operations
        """
        print("🔄 Stopping log monitor...")
        self.running = False
        
        if hasattr(self, 'log_watcher'):
            self.log_watcher.stop()
        
        print("✅ Log monitor stopped successfully")


def main():
    """
    Main entry point of the application.
    
    This function:
    1. Displays a startup banner
    2. Creates and starts the log monitor
    3. Handles any startup errors
    """
    print("=" * 60)
    print("🔍 REAL-TIME LOG MONITOR DEMO")
    print("=" * 60)
    print("📧 Features: Email & Slack notifications")
    print("⚡ Real-time error detection and alerting")
    print("🛡️  Built-in rate limiting and error handling")
    print("=" * 60)
    print()
    
    try:
        # Create and start the log monitor
        monitor = LogMonitorDemo()
        monitor.start()
        
    except FileNotFoundError as e:
        print(f"❌ Configuration or log file not found: {e}")
        print("💡 Please check your config.ini file and ensure the log file exists")
        sys.exit(1)
        
    except Exception as e:
        print(f"💥 Failed to start log monitor: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()