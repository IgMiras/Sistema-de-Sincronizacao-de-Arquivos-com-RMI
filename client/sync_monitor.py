# client/sync_monitor.py
# Monitors changes in the master file on the server and synchronizes the slave

import os
import time
from typing import Optional
from .stub import RemoteFileStub
from ..common.protocol import SyncProtocol, create_confirmation, create_acknowledgment


class SyncMonitor:
    def __init__(self, stub: RemoteFileStub, slave_file_path: str, protocol: SyncProtocol):
        self.stub = stub
        self.slave_file_path = slave_file_path
        self.protocol = protocol
        self.last_version: Optional[str] = None

    def _save_to_slave(self, content: str) -> None:
        os.makedirs(os.path.dirname(self.slave_file_path), exist_ok=True)
        with open(self.slave_file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _read_slave_version(self) -> Optional[str]:
        if not os.path.exists(self.slave_file_path):
            return None
        with open(self.slave_file_path, "r", encoding="utf-8") as f:
            import hashlib
            return hashlib.md5(f.read().encode()).hexdigest()

    def check_for_updates(self):
        version_info = self.stub.check_master_version()
        if not version_info.get("success"):
            print("[!] Failed to fetch version info:", version_info.get("error"))
            return

        server_version = version_info["data"]["version"]

        # Check if file has changed
        local_version = self._read_slave_version()
        if local_version != server_version:
            print("[*] Change detected. Syncing...")
            sync_response = self.stub.get_file_content(protocol=self.protocol)

            if not sync_response.get("success"):
                print("[!] Failed to sync file:", sync_response.get("error"))
                return

            self._save_to_slave(sync_response["data"]["content"])
            print("[+] File synchronized (protocol:", self.protocol.name, ")")

            # Send confirmations if needed
            sync_id = sync_response["data"]["sync_id"]
            if self.protocol == SyncProtocol.RR:
                self.stub.confirm_sync(sync_id)
            elif self.protocol == SyncProtocol.RRA:
                # Simulate asynchronous acknowledgment after some delay
                time.sleep(1)
                self.stub.acknowledge_sync(sync_id)

    def run_loop(self, interval: int = 5):
        print(f"[*] Starting sync monitor (checking every {interval} seconds)...")
        while True:
            self.check_for_updates()
            time.sleep(interval)
