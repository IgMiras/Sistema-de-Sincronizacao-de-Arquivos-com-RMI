# client/client_main.py
# Main entry point for the synchronization client

import os
import sys
import argparse
from enum import Enum

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from client.stub import RemoteFileStub
from client.sync_monitor import SyncMonitor
from common.protocol import SyncProtocol


def main():
    parser = argparse.ArgumentParser(description="File Synchronization Client")
    parser.add_argument("--server", type=str, default="http://localhost:8000", help="Server URL")
    parser.add_argument("--username", type=str, required=True, help="Username for authentication")
    parser.add_argument("--password", type=str, required=True, help="Password for authentication")
    parser.add_argument("--protocol", type=str, choices=[p.name for p in SyncProtocol], default="R",
                        help="Protocol to use: R, RR, or RRA")
    parser.add_argument("--interval", type=int, default=5, help="Interval between checks (in seconds)")
    parser.add_argument("--slave", type=str, default="client/slave.txt", help="Path to slave file")

    args = parser.parse_args()

    protocol = SyncProtocol[args.protocol.upper()]

    # Initialize stub and monitor
    stub = RemoteFileStub(args.server, args.username, args.password)
    monitor = SyncMonitor(stub, args.slave, protocol)

    # Start the synchronization loop
    try:
        monitor.run_loop(interval=args.interval)
    except KeyboardInterrupt:
        print("\n[!] Client stopped.")


if __name__ == "__main__":
    main()
