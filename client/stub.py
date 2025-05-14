#!/usr/bin/env python3
# client/stub.py
# Client stub/proxy for making remote calls to the server

import json
import time
import urllib.request
import urllib.error
from urllib.parse import urlencode
from typing import Dict, Any, Optional

from common.auth import create_auth_header
from common.protocol import (
    SyncProtocol, 
    encode_request, 
    parse_response, 
    create_confirmation,
    create_acknowledgment
)


class RemoteFileStub:
    """
    Client-side stub (proxy) for making remote calls to the server.
    This abstracts the network communication and presents a simple interface
    to the client code.
    """
    
    def __init__(self, server_url: str, username: str, password: str):
        """
        Initialize the stub with server connection details
        
        Args:
            server_url: The URL of the server (e.g., http://localhost:8000)
            username: The username for authentication
            password: The password for authentication
        """
        self.server_url = server_url.rstrip('/')
        self.username = username
        self.password = password
        
        # Endpoints mapping
        self.endpoints = {
            "get_file_content": "/file/content",
            "check_master_version": "/file/version",
            "confirm_sync": "/sync/confirm",
            "acknowledge_sync": "/sync/acknowledge"
        }
    
    def _create_auth_headers(self) -> Dict[str, str]:
        """
        Create authentication headers for requests
        
        Returns:
            A dictionary of headers including authentication
        """
        return {
            "Authorization": create_auth_header(self.username, self.password),
            "Content-Type": "application/json"
        }
    
    def _make_get_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make a GET request to the server
        
        Args:
            endpoint: The endpoint to request
            params: Query parameters (optional)
            
        Returns:
            The parsed response from the server
        """
        url = f"{self.server_url}{endpoint}"
        
        # Add query parameters if provided
        if params:
            url = f"{url}?{urlencode(params)}"
        
        try:
            # Create the request with authentication headers
            request = urllib.request.Request(url, headers=self._create_auth_headers())
            
            # Make the request
            with urllib.request.urlopen(request) as response:
                response_data = response.read().decode('utf-8')
                return parse_response(response_data)
                
        except urllib.error.HTTPError as e:
            # Handle HTTP errors
            error_message = f"HTTP Error: {e.code} - {e.reason}"
            if e.fp:
                error_data = e.fp.read().decode('utf-8')
                try:
                    error_json = json.loads(error_data)
                    if "error" in error_json:
                        error_message = error_json["error"]
                except:
                    pass
            return {
                "success": False,
                "error": error_message
            }
            
        except urllib.error.URLError as e:
            # Handle URL errors (e.g., connection refused)
            return {
                "success": False,
                "error": f"Connection error: {str(e.reason)}"
            }
            
        except Exception as e:
            # Handle other exceptions
            return {
                "success": False,
                "error": f"Error: {str(e)}"
            }
    
    def _make_post_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a POST request to the server
        
        Args:
            endpoint: The endpoint to request
            data: The data to send in the request body
            
        Returns:
            The parsed response from the server
        """
        url = f"{self.server_url}{endpoint}"
        
        try:
            # Encode the request data
            encoded_data = encode_request(data)
            
            # Create the request with authentication headers
            request = urllib.request.Request(
                url, 
                data=encoded_data,
                headers=self._create_auth_headers(),
                method="POST"
            )
            
            # Make the request
            with urllib.request.urlopen(request) as response:
                response_data = response.read().decode('utf-8')
                return parse_response(response_data)
                
        except urllib.error.HTTPError as e:
            # Handle HTTP errors
            error_message = f"HTTP Error: {e.code} - {e.reason}"
            if e.fp:
                error_data = e.fp.read().decode('utf-8')
                try:
                    error_json = json.loads(error_data)
                    if "error" in error_json:
                        error_message = error_json["error"]
                except:
                    pass
            return {
                "success": False,
                "error": error_message
            }
            
        except urllib.error.URLError as e:
            # Handle URL errors (e.g., connection refused)
            return {
                "success": False,
                "error": f"Connection error: {str(e.reason)}"
            }
            
        except Exception as e:
            # Handle other exceptions
            return {
                "success": False,
                "error": f"Error: {str(e)}"
            }
    
    def get_file_content(self, protocol: SyncProtocol = SyncProtocol.R) -> Dict[str, Any]:
        """
        Get the content of the master file
        
        Args:
            protocol: The communication protocol used (R, RR, or RRA)

        Returns:
            A response dictionary containing the file content and sync ID
        """
        return self._make_get_request(self.endpoints["get_file_content"], {
            "protocol": protocol.name
        })

    def check_master_version(self) -> Dict[str, Any]:
        """
        Check the current version (hash) and last modified time of the master file

        Returns:
            A response dictionary containing version info and timestamp
        """
        return self._make_get_request(self.endpoints["check_master_version"])

    def confirm_sync(self, sync_id: str) -> Dict[str, Any]:
        """
        Confirm that the file was successfully synchronized (used in RR protocol)

        Args:
            sync_id: The ID of the synchronization to confirm

        Returns:
            A response dictionary confirming the operation
        """
        confirmation = create_confirmation(sync_id)
        return self._make_post_request(self.endpoints["confirm_sync"], confirmation)

    def acknowledge_sync(self, sync_id: str) -> Dict[str, Any]:
        """
        Asynchronously acknowledge the synchronization (used in RRA protocol)

        Args:
            sync_id: The ID of the synchronization to acknowledge

        Returns:
            A response dictionary confirming the acknowledgment
        """
        acknowledgment = create_acknowledgment(sync_id)
        return self._make_post_request(self.endpoints["acknowledge_sync"], acknowledgment)