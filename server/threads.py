#!/usr/bin/env python3
# server/threads.py
# Thread handling for the server to process multiple client requests concurrently

import threading
import json
import time
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
from typing import Dict, Any, Optional, Tuple, Callable, Type

from common.auth import parse_auth_header
from common.protocol import decode_request
from .dispatcher import Dispatcher


class RequestHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for the synchronization server.
    Handles incoming HTTP requests and routes them to the dispatcher.
    """
    
    # Class-level variable to hold the dispatcher reference
    dispatcher: Optional[Dispatcher] = None
    
    # Define the API endpoints and their corresponding methods
    ENDPOINTS = {
        "/file/content": "get_file_content",
        "/file/version": "check_master_version",
        "/sync/confirm": "confirm_sync",
        "/sync/acknowledge": "acknowledge_sync"
    }
    
    def log_message(self, format, *args):
        """Override to redirect logging to our file logger"""
        # This redirects the built-in server logging to our custom logger
        pass
    
    def _set_response(self, status_code: int = 200, content_type: str = "application/json"):
        """Set the response headers"""
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")  # CORS for development
        self.end_headers()
    
    def _get_client_ip(self) -> str:
        """Get the client's IP address"""
        client_ip = self.client_address[0]
        # Check for X-Forwarded-For header in case of proxy
        if "X-Forwarded-For" in self.headers:
            forwarded_for = self.headers["X-Forwarded-For"]
            client_ip = forwarded_for.split(",")[0].strip()
        return client_ip
    
    def _parse_request_data(self) -> Dict[str, Any]:
        """Parse the request body"""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            request_body = self.rfile.read(content_length)
            return decode_request(request_body)
        return {}
    
    def _parse_query_params(self) -> Dict[str, Any]:
        """Parse query parameters"""
        parsed_url = urlparse(self.path)
        return {k: v[0] for k, v in parse_qs(parsed_url.query).items()}
    
    def _get_auth_credentials(self) -> Tuple[str, str]:
        """Get authentication credentials from header"""
        auth_header = self.headers.get("Authorization", "")
        return parse_auth_header(auth_header)
    
    def _get_endpoint_and_method(self) -> Tuple[str, Optional[str]]:
        """Get the endpoint path and corresponding method name"""
        parsed_url = urlparse(self.path)
        endpoint = parsed_url.path
        
        # Remove trailing slash if present
        if endpoint.endswith("/"):
            endpoint = endpoint[:-1]
            
        # Look up the method name for this endpoint
        method_name = self.ENDPOINTS.get(endpoint)
        
        return endpoint, method_name
    
    def _handle_request(self, method_name: str, params: Dict[str, Any]) -> None:
        """Handle a method request and send the response"""
        if not self.dispatcher:
            self._set_response(500)
            self.wfile.write(json.dumps({
                "success": False,
                "error": "Server dispatcher not initialized"
            }).encode())
            return
        
        client_ip = self._get_client_ip()
        
        # Get username and password from auth header
        username, password = self._get_auth_credentials()
        
        # Add authentication credentials to params
        params["username"] = username
        params["password"] = password
        
        # Execute the method via the dispatcher
        result = self.dispatcher.handle_request(method_name, params, client_ip)
        
        # Send the response
        self._set_response(200 if result.get("success", False) else 400)
        self.wfile.write(json.dumps(result).encode())
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", 
                        "Content-Type, Authorization, X-Requested-With")
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        endpoint, method_name = self._get_endpoint_and_method()
        
        if not method_name:
            self._set_response(404)
            self.wfile.write(json.dumps({
                "success": False,
                "error": f"Unknown endpoint: {endpoint}"
            }).encode())
            return
        
        # Parse query parameters
        params = self._parse_query_params()
        
        # Handle the request
        self._handle_request(method_name, params)
    
    def do_POST(self):
        """Handle POST requests"""
        endpoint, method_name = self._get_endpoint_and_method()
        
        if not method_name:
            self._set_response(404)
            self.wfile.write(json.dumps({
                "success": False,
                "error": f"Unknown endpoint: {endpoint}"
            }).encode())
            return
        
        # Parse request body
        params = self._parse_request_data()
        
        # Handle the request
        self._handle_request(method_name, params)


class ThreadedHTTPServer(HTTPServer):
    """HTTP Server that handles each request in a new thread"""
    
    def __init__(self, server_address, request_handler_class, dispatcher):
        """
        Initialize the server
        
        Args:
            server_address: Tuple of (host, port)
            request_handler_class: The RequestHandler class
            dispatcher: The Dispatcher instance
        """
        super().__init__(server_address, request_handler_class)
        # Set the dispatcher for the request handler
        request_handler_class.dispatcher = dispatcher


def start_server(host: str, port: int, dispatcher: Dispatcher) -> ThreadedHTTPServer:
    """
    Start the HTTP server in a new thread
    
    Args:
        host: The host to bind to
        port: The port to bind to
        dispatcher: The Dispatcher instance
        
    Returns:
        The server instance
    """
    # Create and start the server
    server = ThreadedHTTPServer((host, port), RequestHandler, dispatcher)
    
    # Start the server in a separate thread
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True  # The thread will exit when the main thread exits
    server_thread.start()
    
    print(f"Server started at http://{host}:{port}")
    return server


def stop_server(server: ThreadedHTTPServer) -> None:
    """
    Stop the HTTP server
    
    Args:
        server: The server instance to stop
    """
    if server:
        server.shutdown()
        server.server_close()
        print("Server stopped")