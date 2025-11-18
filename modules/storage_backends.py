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
