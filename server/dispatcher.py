#!/usr/bin/env python3
# server/dispatcher.py
# Dispatcher/Skeleton for handling remote method invocations

import json
import time
import uuid
import os
import logging
from typing import Dict, Any, Optional, Callable, List

from ..common.auth import verify_user
from ..common.protocol import create_response, create_sync_response
from .file_handler import FileHandler


class SyncRecord:
    """Class to track sync operations for RR and RRA protocols"""
    def __init__(self, sync_id: str, client_ip: str, username: str):
        self.sync_id = sync_id
        self.client_ip = client_ip
        self.username = username
        self.request_time = time.time()
        self.confirmed = False
        self.acknowledged = False
        self.confirmation_time = None
        self.acknowledgment_time = None


class Dispatcher:
    """
    Server-side dispatcher (skeleton) that handles remote method invocations.
    This is the component that receives remote calls and executes the actual methods.
    """
    
    def __init__(self, master_file_path: str, users_file: str, log_file: str):
        """
        Initialize the dispatcher
        
        Args:
            master_file_path: Path to the master file
            users_file: Path to the users file with authentication info
            log_file: Path to the synchronization log file
        """
        self.file_handler = FileHandler(master_file_path)
        self.users_file = users_file
        self.log_file = log_file
        self.sync_records: Dict[str, SyncRecord] = {}
        
        # Set up logging
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Configure the synchronization logger"""
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        # Configure logging
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def log_sync_attempt(self, client_ip: str, username: str, operation: str, success: bool, 
                         error: Optional[str] = None) -> None:
        """
        Log a synchronization attempt
        
        Args:
            client_ip: The IP address of the client
            username: The username making the attempt
            operation: The operation being performed
            success: Whether the attempt was successful
            error: Error message if the attempt failed (optional)
        """
        status = "SUCCESS" if success else "FAILED"
        message = f"SYNC {status} - IP: {client_ip} - User: {username} - Operation: {operation}"
        
        if error:
            message += f" - Error: {error}"
            
        logging.info(message)

    def handle_request(self, method: str, params: Dict[str, Any], client_ip: str) -> Dict[str, Any]:
        """
        Handle a remote method invocation request
        
        Args:
            method: The name of the method to invoke
            params: Parameters for the method call
            client_ip: The IP address of the client
            
        Returns:
            A response dictionary with the result of the invocation
        """
        # Dynamic method dispatch using reflection (getattr)
        # This simulates dynamic skeletons
        try:
            if not hasattr(self, method):
                self.log_sync_attempt(client_ip, params.get("username", "unknown"), 
                                     method, False, "Method not found")
                return create_response(False, error=f"Method '{method}' not found")
                
            # Get the method and call it
            handler = getattr(self, method)
            if not callable(handler):
                self.log_sync_attempt(client_ip, params.get("username", "unknown"), 
                                     method, False, "Not a callable method")
                return create_response(False, error=f"'{method}' is not a callable method")
                
            # Call the method with parameters and client IP
            return handler(client_ip=client_ip, **params)
            
        except Exception as e:
            self.log_sync_attempt(client_ip, params.get("username", "unknown"), 
                                 method, False, str(e))
            return create_response(False, error=f"Error processing request: {str(e)}")

    def authenticate(self, username: str, password: str, client_ip: str) -> bool:
        """
        Authenticate a user
        
        Args:
            username: The username to authenticate
            password: The password to authenticate
            client_ip: The IP address of the client
            
        Returns:
            True if authentication was successful, False otherwise
        """
        is_authenticated = verify_user(username, password, self.users_file)
        
        if not is_authenticated:
            self.log_sync_attempt(client_ip, username, "authentication", False, 
                                 "Invalid credentials")
        
        return is_authenticated

    # Remote methods that can be invoked by clients

    def get_file_content(self, username: str, password: str, client_ip: str, 
                         protocol: str = "R") -> Dict[str, Any]:
        """
        Get the content of the master file (remotely invokable)
        
        Args:
            username: The username for authentication
            password: The password for authentication
            client_ip: The IP address of the client
            protocol: The communication protocol (R, RR, or RRA)
            
        Returns:
            A response dictionary with the file content
        """
        # Authenticate the user
        if not self.authenticate(username, password, client_ip):
            return create_response(False, error="Authentication failed")
        
        try:
            # Get the file status
            file_status = self.file_handler.get_file_status()
            
            # Generate a sync ID for tracking
            sync_id = str(uuid.uuid4())
            
            # Log the sync attempt
            self.log_sync_attempt(client_ip, username, f"get_file_content ({protocol})", True)
            
            # For RR and RRA protocols, store the sync record for later confirmation
            if protocol in ("RR", "RRA"):
                self.sync_records[sync_id] = SyncRecord(sync_id, client_ip, username)
            
            # Return the response with the file content
            return create_sync_response(
                success=True,
                content=file_status["content"],
                version=file_status["version"],
                sync_id=sync_id
            )
            
        except Exception as e:
            self.log_sync_attempt(client_ip, username, f"get_file_content ({protocol})", 
                                 False, str(e))
            return create_response(False, error=f"Error getting file content: {str(e)}")

    def check_master_version(self, username: str, password: str, client_ip: str) -> Dict[str, Any]:
        """
        Check the version of the master file (remotely invokable)
        
        Args:
            username: The username for authentication
            password: The password for authentication
            client_ip: The IP address of the client
            
        Returns:
            A response dictionary with the file version information
        """
        # Authenticate the user
        if not self.authenticate(username, password, client_ip):
            return create_response(False, error="Authentication failed")
        
        try:
            # Get the version and last modified time
            version = self.file_handler.get_version()
            last_modified = self.file_handler.get_last_modified()
            
            # Log the sync attempt
            self.log_sync_attempt(client_ip, username, "check_master_version", True)
            
            # Return the response with version info
            return create_response(True, {
                "version": version,
                "last_modified": last_modified
            })
            
        except Exception as e:
            self.log_sync_attempt(client_ip, username, "check_master_version", False, str(e))
            return create_response(False, error=f"Error checking version: {str(e)}")

    def confirm_sync(self, username: str, password: str, sync_id: str, 
                     client_ip: str) -> Dict[str, Any]:
        """
        Confirm a synchronization (for RR protocol)
        
        Args:
            username: The username for authentication
            password: The password for authentication
            sync_id: The ID of the sync to confirm
            client_ip: The IP address of the client
            
        Returns:
            A response dictionary with the confirmation status
        """
        # Authenticate the user
        if not self.authenticate(username, password, client_ip):
            return create_response(False, error="Authentication failed")
        
        # Check if the sync record exists
        if sync_id not in self.sync_records:
            self.log_sync_attempt(client_ip, username, "confirm_sync", False, 
                                 f"Unknown sync ID: {sync_id}")
            return create_response(False, error=f"Unknown sync ID: {sync_id}")
        
        # Update the sync record
        record = self.sync_records[sync_id]
        record.confirmed = True
        record.confirmation_time = time.time()
        
        # Log the confirmation
        self.log_sync_attempt(client_ip, username, "confirm_sync", True)
        
        return create_response(True, {"sync_id": sync_id, "confirmed": True})

    def acknowledge_sync(self, username: str, password: str, sync_id: str, 
                         client_ip: str) -> Dict[str, Any]:
        """
        Acknowledge a synchronization (for RRA protocol)
        
        Args:
            username: The username for authentication
            password: The password for authentication
            sync_id: The ID of the sync to acknowledge
            client_ip: The IP address of the client
            
        Returns:
            A response dictionary with the acknowledgment status
        """
        # Authenticate the user
        if not self.authenticate(username, password, client_ip):
            return create_response(False, error="Authentication failed")
        
        # Check if the sync record exists
        if sync_id not in self.sync_records:
            self.log_sync_attempt(client_ip, username, "acknowledge_sync", False, 
                                 f"Unknown sync ID: {sync_id}")
            return create_response(False, error=f"Unknown sync ID: {sync_id}")
        
        # Update the sync record
        record = self.sync_records[sync_id]
        record.acknowledged = True
        record.acknowledgment_time = time.time()
        
        # Log the acknowledgment
        self.log_sync_attempt(client_ip, username, "acknowledge_sync", True)
        
        return create_response(True, {"sync_id": sync_id, "acknowledged": True})