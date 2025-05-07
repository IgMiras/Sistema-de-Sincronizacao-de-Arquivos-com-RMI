#!/usr/bin/env python3
# common/auth.py
# Authentication utilities shared between client and server

import json
import hashlib
import base64
import os
from typing import Tuple, Dict, Optional


def hash_password(password: str) -> str:
    """
    Create a secure hash of the password
    
    Args:
        password: The password to hash
        
    Returns:
        A string hash of the password
    """
    # In a production system, you'd want to use a proper password hashing algorithm
    # with salt, but for simplicity, we'll use SHA-256
    return hashlib.sha256(password.encode()).hexdigest()


def create_auth_header(username: str, password: str) -> str:
    """
    Create an HTTP Basic Authentication header value
    
    Args:
        username: The username to authenticate with
        password: The password to authenticate with
        
    Returns:
        A string containing the Basic auth header value
    """
    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


def parse_auth_header(auth_header: str) -> Tuple[str, str]:
    """
    Parse an HTTP Basic Authentication header
    
    Args:
        auth_header: The auth header to parse
        
    Returns:
        A tuple of (username, password)
    """
    if not auth_header or not auth_header.startswith("Basic "):
        return "", ""
    
    try:
        encoded = auth_header[6:]  # Remove "Basic "
        decoded = base64.b64decode(encoded).decode()
        username, password = decoded.split(":", 1)
        return username, password
    except Exception:
        return "", ""


def verify_user(username: str, password: str, users_file: str) -> bool:
    """
    Verify a user's credentials against the users file
    
    Args:
        username: The username to verify
        password: The password to verify
        users_file: Path to the JSON file containing user credentials
        
    Returns:
        True if the credentials are valid, False otherwise
    """
    if not os.path.exists(users_file):
        return False
    
    try:
        with open(users_file, 'r') as f:
            users = json.load(f)
            
        if username in users:
            stored_hash = users[username]
            password_hash = hash_password(password)
            return stored_hash == password_hash
    except Exception:
        pass
    
    return False


def add_user(username: str, password: str, users_file: str) -> bool:
    """
    Add a new user to the users file
    
    Args:
        username: The username to add
        password: The password for the new user
        users_file: Path to the JSON file containing user credentials
        
    Returns:
        True if the user was added successfully, False otherwise
    """
    users = {}
    
    # Load existing users if the file exists
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r') as f:
                users = json.load(f)
        except Exception:
            pass
    
    # Add or update the user
    users[username] = hash_password(password)
    
    # Save the updated users
    try:
        os.makedirs(os.path.dirname(users_file), exist_ok=True)
        with open(users_file, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except Exception:
        return False