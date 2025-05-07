#!/usr/bin/env python3
# server/server_main.py
# Main entry point for the synchronization server

import os
import sys
import signal
import argparse
import json
from typing import Dict, Any

# Add the parent directory to the path to allow imports from sibling packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server.dispatcher import Dispatcher
from server.threads import start_server, stop_server
from common.auth import add_user


def create_default_users_file(users_file: str) -> None:
    """
    Create a default users file with a demo user if it doesn't exist
    
    Args:
        users_file: Path to the users file
    """
    if not os.path.exists(users_file):
        print(f"Creating default users file at {users_file}")
        os.makedirs(os.path.dirname(users_file), exist_ok=True)
        
        # Add a default user
        add_user("admin", "password", users_file)
        print("Created default user: admin / password")


def create_directory_structure() -> Dict[str, str]:
    """
    Create the server directory structure and return paths
    
    Returns:
        A dictionary with paths to important files
    """
    # Define paths
    server_dir = os.path.dirname(os.path.abspath(__file__))
    master_file = os.path.join(server_dir, "master.txt")
    users_file = os.path.join(server_dir, "users.json")
    log_file = os.path.join(server_dir, "sync.log")
    
    # Ensure the server directory exists
    os.makedirs(server_dir, exist_ok=True)
    
    # Create a default master file if it doesn't exist
    if not os.path.exists(master_file):
        with open(master_file, 'w') as f:
            f.write("# Master file for RMI File Synchronization System\n")
            f.write("# Initial content created on server startup\n")
            f.write("This is the master file. Edit this content to test synchronization.\n")
    
    # Create a default users file if it doesn't exist
    create_default_users_file(users_file)
    
    return {
        "master_file": master_file,
        "users_file": users_file,
        "log_file": log_file
    }


def add_new_user(users_file: str, username: str, password: str) -> None:
    """
    Add a new user to the users file
    
    Args:
        users_file: Path to the users file
        username: Username to add
        password: Password for the new user
    """
    if add_user(username, password, users_file):
        print(f"User '{username}' added successfully")
    else:
        print(f"Failed to add user '{username}'")


def list_users(users_file: str) -> None:
    """
    List all users in the users file
    
    Args:
        users_file: Path to the users file
    """
    if not os.path.exists(users_file):
        print("No users file found")
        return
    
    try:
        with open(users_file, 'r') as f:
            users = json.load(f)
            
        print("\nRegistered users:")
        for username in users.keys():
            print(f"- {username}")
        print()
    except Exception as e:
        print(f"Error reading users file: {str(e)}")


def handle_shutdown(server) -> None:
    """
    Handle server shutdown
    
    Args:
        server: The server instance
    """
    print("\nShutting down server...")
    stop_server(server)
    sys.exit(0)


def main():
    """Main entry point for the server"""
    parser = argparse.ArgumentParser(description="File Synchronization Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--add-user", nargs=2, metavar=("USERNAME", "PASSWORD"), 
                       help="Add a new user")
    parser.add_argument("--list-users", action="store_true", help="List all users")
    
    args = parser.parse_args()
    
    # Create directory structure
    paths = create_directory_structure()
    
    # Handle user management commands
    if args.add_user:
        add_new_user(paths["users_file"], args.add_user[0], args.add_user[1])
        if not args.list_users:  # Exit if we're not also listing users
            return
    
    if args.list_users:
        list_users(paths["users_file"])
        return
    
    # Create the dispatcher
    dispatcher = Dispatcher(
        master_file_path=paths["master_file"],
        users_file=paths["users_file"],
        log_file=paths["log_file"]
    )
    
    # Start the server
    server = start_server(args.host, args.port, dispatcher)
    
    # Register signal handlers for clean shutdown
    signal.signal(signal.SIGINT, lambda sig, frame: handle_shutdown(server))
    signal.signal(signal.SIGTERM, lambda sig, frame: handle_shutdown(server))
    
    print(f"Server running at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the server")
    
    # Keep the main thread alive to accept SIGINT (Ctrl+C)
    try:
        signal.pause()
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    main()