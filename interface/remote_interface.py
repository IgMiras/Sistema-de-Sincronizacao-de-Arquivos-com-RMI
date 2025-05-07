#!/usr/bin/env python3
# interface/remote_interface.py
# Remote Interface Definition (IDL) for the File Synchronization System

from enum import Enum
from typing import Dict, Any, Optional, Tuple


class SyncProtocol(Enum):
    """
    Enum defining the different communication protocol styles:
    - R: Simple Request
    - RR: Confirmed Request-Response
    - RRA: Request-Response with Asynchronous Acknowledgment
    """
    R = "R"      # Simple Request
    RR = "RR"    # Confirmed Request-Response
    RRA = "RRA"  # Request-Response with Asynchronous Acknowledgment


class FileStatus:
    """Class representing the status of a file, including version info and content"""
    def __init__(self, content: str, version: str, last_modified: float):
        self.content = content
        self.version = version  # hash of the content
        self.last_modified = last_modified  # timestamp


class RemoteFileInterface:
    """
    Interface defining the methods that will be available remotely.
    This serves as a contract between the client and server.
    """
    
    def get_file_content(self, username: str, password: str) -> Dict[str, Any]:
        """
        Retrieve the content of the master file
        
        Args:
            username: The username for authentication
            password: The password for authentication
            
        Returns:
            Dict containing file content, version, and status
        """
        raise NotImplementedError("This method should be implemented by the server")
    
    def check_master_version(self, username: str, password: str) -> Dict[str, Any]:
        """
        Check the current version (hash) of the master file
        
        Args:
            username: The username for authentication
            password: The password for authentication
            
        Returns:
            Dict containing version info and last modified timestamp
        """
        raise NotImplementedError("This method should be implemented by the server")
    
    def confirm_sync(self, username: str, password: str, sync_id: str) -> Dict[str, Any]:
        """
        Confirm that a synchronization was successful (used in RR protocol)
        
        Args:
            username: The username for authentication
            password: The password for authentication
            sync_id: The ID of the synchronization to confirm
            
        Returns:
            Dict with confirmation status
        """
        raise NotImplementedError("This method should be implemented by the server")
    
    def acknowledge_sync(self, username: str, password: str, sync_id: str) -> Dict[str, Any]:
        """
        Asynchronously acknowledge a synchronization (used in RRA protocol)
        
        Args:
            username: The username for authentication
            password: The password for authentication
            sync_id: The ID of the synchronization to acknowledge
            
        Returns:
            Dict with acknowledgment status
        """
        raise NotImplementedError("This method should be implemented by the server")


# For protocol identification
OPERATIONS = {
    "get_file_content": {
        "path": "/file/content",
        "method": "GET"
    },
    "check_master_version": {
        "path": "/file/version",
        "method": "GET"
    },
    "confirm_sync": {
        "path": "/sync/confirm",
        "method": "POST"
    },
    "acknowledge_sync": {
        "path": "/sync/acknowledge",
        "method": "POST"
    }
}