import os
import stat

from airflow.providers.sftp.hooks.sftp import SFTPHook

from modules.storage_backends import StorageBackend


class SFTPBackend(StorageBackend):
    def __init__(self, conn_id: str, chunk_size: int = 10 * 1024 * 1024):
        self.conn_id = conn_id
        self.hook = SFTPHook(ssh_conn_id=conn_id)
        self.chunk_size = chunk_size
        self._conn = None

    def get_conn(self):
        if self._conn is None:
            self._conn = self.hook.get_conn()
        return self._conn

    def close(self):
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def list_files(self, path):
        files = []
        with self.hook.get_conn() as sftp:
            self._walk(sftp, path, files)
        return files

    def _walk(self, sftp, path, file_list):
        try:
            entries = sftp.listdir_attr(path)
        except FileNotFoundError:
            print(f"Warning: {path} does not exist, skipping")
            return

        for entry in entries:
            full_path = f"{path.rstrip('/')}/{entry.filename}"
            if stat.S_ISDIR(entry.st_mode):
                self._walk(sftp, full_path, file_list)
            else:
                file_list.append(full_path)

    def upload_file(self, local_path: str, remote_path: str) -> None:
        conn = self.get_conn()

        remote_dir = os.path.dirname(remote_path)
        if not self.exists(remote_dir):
            self.mkdir(remote_dir)

        file_size = os.path.getsize(local_path)

        if file_size > self.chunk_size:
            # Chunk upload
            with conn.open(remote_path, "wb") as rf, open(local_path, "rb") as lf:
                while True:
                    chunk = lf.read(self.chunk_size)
                    if not chunk:
                        break
                    rf.write(chunk)
        else:
            conn.put(local_path, remote_path)

    def download_file(self, remote_path: str, local_path: str) -> None:
        conn = self.get_conn()

        local_dir = os.path.dirname(local_path)
        os.makedirs(local_dir, exist_ok=True)

        size = conn.stat(remote_path).st_size

        if size > self.chunk_size:
            # Chunk download
            with conn.open(remote_path, "rb") as rf, open(local_path, "wb") as lf:
                while True:
                    chunk = rf.read(self.chunk_size)
                    if not chunk:
                        break
                    lf.write(chunk)
        else:
            conn.get(remote_path, local_path)


    def mkdir(self, path: str) -> None:
        conn = self.get_conn()
        parts = path.split("/")
        cur = ""
        for p in parts:
            if not p:
                continue
            cur = cur + "/" + p
            try:
                conn.mkdir(cur)
            except IOError:
                pass

    def exists(self, path: str) -> bool:
        try:
            self.get_conn().stat(path)
            return True
        except Exception:
            return False
