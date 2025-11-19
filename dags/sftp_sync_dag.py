import logging
from datetime import datetime

from airflow import DAG
from airflow.sdk import task

from modules.sftp_backend import SFTPBackend
from modules.sync_manager import SyncManager

logger = logging.getLogger(__name__)


SOURCE_CONN_ID = "sftp_source"
TARGET_CONN_ID = "sftp_target"

SOURCE_ROOT = "/"
TARGET_ROOT = "/"

LARGE_FILE_THRESHOLD = 1024 * 1024 * 10  # 10MB


dag_args = {
    "owner": "data-team",
    "retries": 2,
}


with DAG(
    dag_id="sftp_sync_dag",
    default_args=dag_args,
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["sftp", "sync", "dag"],
) as dag:

    # init backend
    def init_manager():
        source = SFTPBackend(conn_id=SOURCE_CONN_ID)
        target = SFTPBackend(conn_id=TARGET_CONN_ID)

        return SyncManager(
            source_backend=source,
            target_backend=target,
            large_file_threshold=LARGE_FILE_THRESHOLD,
        )

    @task
    def scan_source():
        manager = init_manager()
        files = manager.scan_source(SOURCE_ROOT)
        logger.info(f"List files: {files}")
        return files


    @task
    def scan_target():
        manager = init_manager()
        files = manager.scan_target(TARGET_ROOT)
        logger.info(f"List files: {files}")
        return files

    @task
    def diff_files(source_files: list, target_files: list):
        manager = init_manager()
        new_files = manager.diff_files(source_files, target_files)
        logger.info(f"New files: {new_files}")
        return new_files

    @task
    def split_files(files: list):
        manager = init_manager()
        large_files = manager.get_large_files(files)
        small_files = list(set(files) - set(large_files))
        logger.info(f"Small files: {small_files}")
        logger.info(f"Large files: {large_files}")
        return {
            "small_files": small_files,
            "large_files": large_files,
        }

    @task
    def get_small_files(file_groups: dict):
        return file_groups["small_files"]

    @task
    def get_large_files(file_groups: dict):
        return file_groups["large_files"]

    def sync_file(file_path: str):
        manager = init_manager()  # creates backend with persistent connection
        try:
            manager.sync_files([file_path], SOURCE_ROOT, TARGET_ROOT)
            logger.info(f"Synced: {file_path}")
        except FileNotFoundError as e:
            logger.error(f"Failed to sync {file_path}: {e}")
        return file_path

    @task
    def sync_small_file(file_path: str):
        sync_file(file_path)

    @task
    def sync_large_file(file_path: str):
        sync_file(file_path)


    source_files = scan_source()
    target_files = scan_target()
    diffed_files = diff_files(source_files, target_files)

    file_groups = split_files(diffed_files)

    small_files = get_small_files(file_groups)
    large_files = get_large_files(file_groups)

    sync_small_file = sync_small_file.expand(file_path=small_files)
    sync_large_file = sync_large_file.expand(file_path=large_files)
