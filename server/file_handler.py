#!/usr/bin/env python3
# server/file_handler.py
# Handler for master file operations on the server

import os
import hashlib
import time
import threading
from typing import Dict, Any, Tuple


class FileHandler:
    """
    Class responsible for handling operations on the master file.
    Implements file reading, writing, and version checking.
    """
    
    def __init__(self, file_path: str):
        """
        Initialize the FileHandler with the path to the master file
        
        Args:
            file_path: Path to the master file
        """
        self.file_path = file_path
        self.lock = threading.RLock()  # Reentrant lock for thread safety
        
        # Create the file if it doesn't exist
        if not os.path.exists(file_path):
            self._ensure_file_exists()
    
    def _ensure_file_exists(self) -> None:
        """Ensure the master file exists, creating it if necessary"""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, 'w') as f:
            f.write("# Master file for RMI File Synchronization System\n")
    
    def get_content(self) -> str:
        """
        Get the content of the master file
        
        Returns:
            The content of the file as a string
        """
        with self.lock:
            # Check if file exists
            if not os.path.exists(self.file_path):
                self._ensure_file_exists()
                
            # Read the file content
            with open(self.file_path, 'r') as f:
                return f.read()
    
    def update_content(self, content: str) -> bool:
        """
        Update the content of the master file
        
        Args:
            content: The new content to write
            
        Returns:
            True if the update was successful, False otherwise
        """
        with self.lock:
            try:
                with open(self.file_path, 'w') as f:
                    f.write(content)
                return True
            except Exception:
                return False
    
    def get_version(self) -> str:
        """
        Calculate the current version (hash) of the master file
        
        Returns:
            A string hash representing the current version
        """
        content = self.get_content()
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_last_modified(self) -> float:
        """
        Get the last modification time of the master file
        
        Returns:
            The last modified timestamp as a float
        """
        with self.lock:
            if os.path.exists(self.file_path):
                return os.path.getmtime(self.file_path)
            else:
                self._ensure_file_exists()
                return os.path.getmtime(self.file_path)
    
    def get_file_status(self) -> Dict[str, Any]:
        """
        Get the current status of the master file
        
        Returns:
            A dictionary with content, version, and last_modified information
        """
        with self.lock:
            content = self.get_content()
            version = hashlib.md5(content.encode()).hexdigest()
            last_modified = self.get_last_modified()
            
            return {
                "content": content,
                "version": version,
                "last_modified": last_modified
            }