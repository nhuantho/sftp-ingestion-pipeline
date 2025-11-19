import logging
import os
import tempfile
from typing import List

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

    # Only get new files in the source
    def diff_files(self, source_files: List[str], target_files: List[str]) -> List[str]:
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

    def sync_files(self, files: List[str], source_root: str, target_root: str):
        results = {}
        for f in files:
            rel_path = os.path.relpath(f, source_root) if source_root != "/" else f.lstrip("/")
            target_path = os.path.join(target_root, rel_path)

            try:
                with tempfile.NamedTemporaryFile(delete=True) as tmp:
                    tmp_path = tmp.name

                    self.source.download_file(f, tmp_path)
                    self.target.upload_file(tmp_path, target_path)

                results[f] = True
            except Exception as e:
                results[f] = False
                print(f"[ERR] Failed to sync {f}: {e}")

        return results
