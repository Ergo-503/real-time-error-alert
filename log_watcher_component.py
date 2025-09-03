#!/usr/bin/env python3
"""
Log Watcher Component
====================
This module provides real-time monitoring of log files using file system events.
It detects when new lines are added to a log file and checks them against configured
error keywords to identify issues that require notification.

The LogWatcher uses the watchdog library to monitor file system events efficiently
without constantly polling the file, making it lightweight and responsive.
"""

import os
import re
import threading
import time
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class LogFileHandler(FileSystemEventHandler):
    """
    File system event handler that processes log file modifications.
    
    This handler is called by the watchdog Observer whenever the monitored
    log file is modified. It reads new lines and checks them for error patterns.
    """
    
    def __init__(self, log_file_path, error_keywords, callback):
        """
        Initialize the log file handler.
        
        Args:
            log_file_path (str): Path to the log file to monitor
            error_keywords (list): List of keywords that indicate errors
            callback (function): Function to call when an error is detected
        """
        self.log_file_path = log_file_path
        self.error_keywords = error_keywords
        self.callback = callback
        
        # Keep track of the last known file position to read only new content
        self.last_position = self._get_file_size()
        
        # Compile regex patterns for efficient matching
        self.error_patterns = [re.compile(keyword, re.IGNORECASE) for keyword in error_keywords]
        
        print(f"📂 Log handler initialized for: {log_file_path}")
        print(f"📏 Initial file size: {self.last_position} bytes")
    
    def _get_file_size(self):
        """
        Get the current size of the log file.
        
        Returns:
            int: File size in bytes, or 0 if file doesn't exist
        """
        try:
            return os.path.getsize(self.log_file_path)
        except (OSError, FileNotFoundError):
            return 0
    
    def on_modified(self, event):
        """
        Called when the log file is modified.
        
        This method:
        1. Checks if the modified file is our target log file
        2. Reads new content that was added since last check
        3. Processes each new line for error patterns
        4. Calls the callback function for any detected errors
        
        Args:
            event: File system event object containing event details
        """
        # Only process modifications to our specific log file
        if event.is_directory or event.src_path != self.log_file_path:
            return
        
        print(f"📝 Log file modified: {event.src_path}")
        
        try:
            # Get current file size
            current_size = self._get_file_size()
            
            # If file was truncated (size decreased), reset position
            if current_size < self.last_position:
                print("🔄 Log file was truncated, resetting position")
                self.last_position = 0
            
            # If no new content, skip processing
            if current_size <= self.last_position:
                return
            
            # Read only the new content that was added
            self._read_new_content(current_size)
            
        except Exception as e:
            print(f"❌ Error processing log file modification: {e}")
    
    def _read_new_content(self, current_size):
        """
        Read and process new content that was added to the log file.
        
        Args:
            current_size (int): Current size of the log file in bytes
        """
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as file:
                # Seek to the last known position
                file.seek(self.last_position)
                
                # Read new content
                new_content = file.read(current_size - self.last_position)
                
                # Update position for next read
                self.last_position = current_size
                
                # Process each new line
                if new_content.strip():
                    lines = new_content.strip().split('\n')
                    print(f"📄 Processing {len(lines)} new log lines")
                    
                    for line in lines:
                        if line.strip():  # Skip empty lines
                            self._process_log_line(line)
        
        except Exception as e:
            print(f"❌ Error reading new log content: {e}")
    
    def _process_log_line(self, line):
        """
        Process a single log line to check for error patterns.
        
        This method:
        1. Checks the line against all configured error patterns
        2. Extracts error information if a match is found
        3. Calls the callback function with error details
        
        Args:
            line (str): A single line from the log file
        """
        # Check each error pattern against the log line
        for pattern, keyword in zip(self.error_patterns, self.error_keywords):
            if pattern.search(line):
                print(f"🚨 Error pattern '{keyword}' found in log line")
                
                # Extract error information from the log line
                error_info = self._extract_error_info(line, keyword)
                
                # Call the callback function to handle the error
                if self.callback:
                    self.callback(error_info)
                
                # Only trigger once per line, even if multiple patterns match
                break
    
    def _extract_error_info(self, line, matched_keyword):
        """
        Extract structured error information from a log line.
        
        This method attempts to parse common log formats to extract:
        - Timestamp
        - Log level
        - Error message
        
        Args:
            line (str): The full log line
            matched_keyword (str): The keyword that triggered the match
        
        Returns:
            dict: Structured error information
        """
        # Common log format patterns
        # Example: "2024-01-15 14:30:25 ERROR: Database connection failed"
        # Example: "[2024-01-15 14:30:25] ERROR Database connection failed"
        
        timestamp_patterns = [
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',  # YYYY-MM-DD HH:MM:SS
            r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]',  # [YYYY-MM-DD HH:MM:SS]
        ]
        
        level_patterns = [
            r'\b(ERROR|CRITICAL|FATAL|EXCEPTION|FAIL)\b',
            r'\b(WARN|WARNING)\b',
        ]
        
        # Try to extract timestamp
        extracted_timestamp = None
        for pattern in timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                extracted_timestamp = match.group(1)
                break
        
        # If no timestamp found in log, use current time
        if not extracted_timestamp:
            extracted_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Try to extract log level
        extracted_level = "UNKNOWN"
        for pattern in level_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                extracted_level = match.group(1).upper()
                break
        
        # Extract the main error message (try to get everything after the level)
        message = line
        if extracted_level in line:
            parts = line.split(extracted_level, 1)
            if len(parts) > 1:
                message = parts[1].strip(':').strip()
        
        return {
            'timestamp': extracted_timestamp,
            'level': extracted_level,
            'message': message.strip(),
            'line': line.strip(),
            'matched_keyword': matched_keyword,
            'detected_at': datetime.now().isoformat()
        }


class LogWatcher:
    """
    Main log watcher class that coordinates file monitoring.
    
    This class sets up the watchdog Observer and FileSystemEventHandler
    to monitor log files for changes in real-time.
    """
    
    def __init__(self, log_file_path, error_keywords, callback):
        """
        Initialize the log watcher.
        
        Args:
            log_file_path (str): Path to the log file to monitor
            error_keywords (list): List of error keywords to watch for
            callback (function): Function to call when errors are detected
        """
        self.log_file_path = str(Path(log_file_path).resolve())
        self.log_directory = os.path.dirname(self.log_file_path)
        self.error_keywords = error_keywords
        self.callback = callback
        
        # Validate that the log file exists or can be created
        self._validate_log_file()
        
        # Set up file system observer and event handler
        self.observer = Observer()
        self.event_handler = LogFileHandler(
            self.log_file_path, 
            self.error_keywords, 
            self.callback
        )
        
        # Configure the observer to watch the log file's directory
        self.observer.schedule(
            self.event_handler,
            path=self.log_directory,
            recursive=False  # Only watch the specific directory, not subdirectories
        )
        
        print(f"👁️  LogWatcher configured to monitor: {self.log_file_path}")
    
    def _validate_log_file(self):
        """
        Validate that the log file exists and is accessible.
        Creates the file if it doesn't exist.
        """
        log_path = Path(self.log_file_path)
        
        # Create directory if it doesn't exist
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create log file if it doesn't exist
        if not log_path.exists():
            print(f"📝 Creating log file: {self.log_file_path}")
            log_path.touch()
        
        # Check if file is readable
        if not os.access(self.log_file_path, os.R_OK):
            raise PermissionError(f"Cannot read log file: {self.log_file_path}")
        
        print(f"✅ Log file validated: {self.log_file_path}")
    
    def start(self):
        """
        Start monitoring the log file.
        
        This method starts the watchdog Observer in a separate thread,
        allowing the main program to continue running while monitoring
        file changes in the background.
        """
        try:
            print(f"🚀 Starting log file watcher...")
            self.observer.start()
            print(f"✅ Log watcher started successfully")
            print(f"📁 Monitoring directory: {self.log_directory}")
            print(f"📄 Target file: {os.path.basename(self.log_file_path)}")
            
        except Exception as e:
            print(f"❌ Failed to start log watcher: {e}")
            raise
    
    def stop(self):
        """
        Stop monitoring the log file.
        
        This method gracefully shuts down the watchdog Observer
        and waits for any pending operations to complete.
        """
        if self.observer.is_alive():
            print("🛑 Stopping log file watcher...")
            self.observer.stop()
            self.observer.join(timeout=5)  # Wait up to 5 seconds for cleanup
            print("✅ Log watcher stopped")
        else:
            print("⚠️  Log watcher was not running")
    
    def is_running(self):
        """
        Check if the log watcher is currently running.
        
        Returns:
            bool: True if the observer is active, False otherwise
        """
        return self.observer.is_alive()


# Demo/testing functionality
if __name__ == "__main__":
    """
    Simple test to demonstrate the LogWatcher functionality.
    This can be run independently to test the log watching capability.
    """
    def test_callback(error_info):
        """Test callback function for demonstrations."""
        print(f"🔔 TEST ALERT: {error_info['level']} detected!")
        print(f"   Message: {error_info['message']}")
        print(f"   Time: {error_info['timestamp']}")
        print()
    
    # Test configuration
    test_log_file = "test_sample.log"
    test_keywords = ["ERROR", "CRITICAL", "EXCEPTION", "FAIL"]
    
    print("🧪 LogWatcher Test Mode")
    print("=" * 40)
    
    try:
        # Create test log watcher
        watcher = LogWatcher(test_log_file, test_keywords, test_callback)
        watcher.start()
        
        print(f"✅ Test watcher started. Add some error lines to '{test_log_file}' to see alerts!")
        print("   Example: echo '2024-01-15 12:00:00 ERROR: Test error message' >> test_sample.log")
        print("⏹️  Press Ctrl+C to stop the test")
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")
        watcher.stop()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        if 'watcher' in locals():
            watcher.stop()