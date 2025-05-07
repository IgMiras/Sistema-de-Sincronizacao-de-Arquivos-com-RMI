#!/usr/bin/env python3
# common/protocol.py
# Protocol definitions for the file synchronization system

import json
import uuid
import time
from enum import Enum
from typing import Dict, Any, Optional


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


def create_response(success: bool, data: Any = None, error: str = None) -> Dict[str, Any]:
    """
    Create a standardized response structure
    
    Args:
        success: Whether the operation was successful
        data: The data to include in the response (optional)
        error: Error message if the operation failed (optional)
        
    Returns:
        A dictionary with the response structure
    """
    response = {
        "success": success,
        "timestamp": time.time()
    }
    
    if data is not None:
        response["data"] = data
        
    if error is not None:
        response["error"] = error
        
    return response


def create_sync_response(success: bool, content: str = None, version: str = None, 
                        sync_id: str = None, error: str = None) -> Dict[str, Any]:
    """
    Create a response specifically for synchronization operations
    
    Args:
        success: Whether the sync operation was successful
        content: The file content (optional)
        version: The file version/hash (optional)
        sync_id: A unique ID for the sync operation (optional)
        error: Error message if the operation failed (optional)
        
    Returns:
        A dictionary with the sync response structure
    """
    # Generate a unique ID for this sync operation if one wasn't provided
    if sync_id is None:
        sync_id = str(uuid.uuid4())
        
    data = {
        "sync_id": sync_id,
        "timestamp": time.time()
    }
    
    if content is not None:
        data["content"] = content
        
    if version is not None:
        data["version"] = version
        
    return create_response(success, data, error)


def parse_response(response_data: str) -> Dict[str, Any]:
    """
    Parse a response from JSON string
    
    Args:
        response_data: The JSON string to parse
        
    Returns:
        A dictionary with the parsed response
    """
    try:
        return json.loads(response_data)
    except json.JSONDecodeError:
        return create_response(False, error="Invalid response format")


def encode_request(data: Dict[str, Any]) -> bytes:
    """
    Encode a request dictionary to JSON bytes
    
    Args:
        data: The request data to encode
        
    Returns:
        JSON-encoded bytes
    """
    return json.dumps(data).encode('utf-8')


def decode_request(request_data: bytes) -> Dict[str, Any]:
    """
    Decode a JSON request from bytes
    
    Args:
        request_data: The bytes to decode
        
    Returns:
        A dictionary with the decoded request
    """
    try:
        return json.loads(request_data.decode('utf-8'))
    except json.JSONDecodeError:
        return {}


def create_confirmation(sync_id: str) -> Dict[str, Any]:
    """
    Create a confirmation message (for RR protocol)
    
    Args:
        sync_id: The sync ID to confirm
        
    Returns:
        A dictionary with the confirmation structure
    """
    return {
        "confirmation": True,
        "sync_id": sync_id,
        "timestamp": time.time()
    }


def create_acknowledgment(sync_id: str) -> Dict[str, Any]:
    """
    Create an acknowledgment message (for RRA protocol)
    
    Args:
        sync_id: The sync ID to acknowledge
        
    Returns:
        A dictionary with the acknowledgment structure
    """
    return {
        "acknowledgment": True,
        "sync_id": sync_id,
        "timestamp": time.time()
    }