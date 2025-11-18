import os
from abc import ABC, abstractmethod
from typing import List

from airflow.providers.sftp.hooks.sftp import SFTPHook


class StorageBackend(ABC):
    @abstractmethod
    def list_files(self, path: str) -> List[str]:
        pass

    @abstractmethod
    def upload_file(self, local_path: str, remote_path: str) -> None:
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_path: str) -> None:
        pass

    @abstractmethod
    def mkdir(self, path: str) -> None:
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        pass


class StorageSFTPBackend(StorageBackend):
    def __init__(self, conn_id: str):
        self.conn_id = conn_id
        self.hook = SFTPHook(ssh_conn_id=conn_id)

    def list_files(self, path: str) -> List[str]:
        # Recursively list all files under path
        files = []
        for root, dirs, file_names in self.hook.walk(path):
            for f in file_names:
                files.append(os.path.join(root, f))
        return files

    def upload_file(self, local_path: str, remote_path: str) -> None:
        # Ensure remote directory exists
        remote_dir = os.path.dirname(remote_path)
        if not self.exists(remote_dir):
            self.mkdir(remote_dir)
        self.hook.store_file(remote_path, local_path)

    def download_file(self, remote_path: str, local_path: str) -> None:
        # Ensure local directory exists
        local_dir = os.path.dirname(local_path)
        os.makedirs(local_dir, exist_ok=True)
        self.hook.get_file(remote_path, local_path)

    def mkdir(self, path: str) -> None:
        # Recursively create directories on SFTP
        parts = path.strip('/').split('/')
        current = ''
        for part in parts:
            current = f"{current}/{part}" if current else f"/{part}"
            if not self.exists(current):
                self.hook.create_directory(current)

    def exists(self, path: str) -> bool:
        try:
            return self.hook.path_exists(path)
        except Exception:
            return False
