import logging
import os
from typing import (
    Dict, List, Tuple,
)

from modules.sftp_backend import SFTPBackend


class SyncManager:
    def __init__(self, source_backend: SFTPBackend, target_backend: SFTPBackend, large_file_threshold: int = 1024 * 1024 * 10):
        self.source = source_backend
        self.target = target_backend
        self.large_file_threshold = large_file_threshold
        self.logger = logging.getLogger(__name__)

    def scan_source(self, path: str) -> List[str]:
        return self.source.list_files(path)

    def scan_target(self, path: str) -> List[str]:
        return self.target.list_files(path)

    def diff_files(self, source_files: List[str], target_files: List[str]) -> List[str]:
        # Only new files in source
        return [f for f in source_files if f not in target_files]

    def get_large_files(self, files: List[str]) -> List[str]:
        large_files = []
        for f in files:
            try:
                size = self.source.hook.get_size(f)
                if size > self.large_file_threshold:
                    large_files.append(f)
            except Exception:
                self.logger.warning(f"Could not get size for {f}")
        return large_files

    def sync_files(self, files: List[str], source_root: str, target_root: str) -> Dict[str, bool]:
        results = {}
        for f in files:
            rel_path = os.path.relpath(f, source_root)
            target_path = os.path.join(target_root, rel_path)
            try:
                self.target.upload_file(f, target_path)
                results[f] = True
                self.logger.info(f"Synced {f} to {target_path}")
            except Exception as e:
                results[f] = False
                self.logger.error(f"Failed to sync {f}: {e}")
        return results
