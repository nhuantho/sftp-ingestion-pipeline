import os
from typing import List

from airflow.providers.sftp.hooks.sftp import SFTPHook

from modules.storage_backends import StorageBackend


class SFTPBackend(StorageBackend):
    def __init__(self, conn_id: str, chunk_size: int = 1024 * 1024 * 10):
        self.conn_id = conn_id
        self.chunk_size = chunk_size
        self.hook = SFTPHook(ssh_conn_id=conn_id)

    def list_files(self, path: str) -> List[str]:
        files = []
        for root, dirs, file_names in self.hook.walk(path):
            for f in file_names:
                files.append(os.path.join(root, f))
        return files

    def upload_file(self, local_path: str, remote_path: str) -> None:
        remote_dir = os.path.dirname(remote_path)
        if not self.exists(remote_dir):
            self.mkdir(remote_dir)
        file_size = os.path.getsize(local_path)
        if file_size > self.chunk_size:
            with open(local_path, 'rb') as f:
                offset = 0
                while offset < file_size:
                    chunk = f.read(self.chunk_size)
                    self.hook.store_file(remote_path, chunk, append=True)
                    offset += len(chunk)
        else:
            self.hook.store_file(remote_path, local_path)

    def download_file(self, remote_path: str, local_path: str) -> None:
        local_dir = os.path.dirname(local_path)
        os.makedirs(local_dir, exist_ok=True)
        file_size = self.hook.get_size(remote_path)
        if file_size > self.chunk_size:
            with open(local_path, 'wb') as f:
                offset = 0
                while offset < file_size:
                    chunk = self.hook.read_file(remote_path, offset, self.chunk_size)
                    f.write(chunk)
                    offset += len(chunk)
        else:
            self.hook.get_file(remote_path, local_path)

    def mkdir(self, path: str) -> None:
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
