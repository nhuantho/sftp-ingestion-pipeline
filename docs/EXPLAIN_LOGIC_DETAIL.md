# Explain Logic Detial

**1\. modules/sftp_backend.py**
-----------------------
| Component / Method                         | Purpose                        | Explanation                                          |
| ------------------------------------------ | ------------------------------ | ----------------------------------------------------------- |
| **conn_id**                                | Store SFTP connection ID       | Used by Airflow to load the SFTP connection                 |
| **hook**                                   | Airflow SFTPHook               | Provides SFTP functions (connect, upload, download, list)   |
| **chunk_size**                             | Chunk size for big files       | Large files are uploaded/downloaded in pieces               |
| **_conn**                                  | Cached SFTP connection         | Reused to avoid reconnecting every time                     |
| **get_conn()**                             | Get or create SFTP connection  | Creates connection once, returns the same connection later  |
| **close()**                                | Close SFTP connection safely   | Prevents connection leaks                                   |
| **list_files(path)**                       | Get all files recursively      | Walks directories and collects all file paths               |
| **_walk(sftp, path, file_list)**           | Recursive directory walker     | Adds files and goes deeper into folders                     |
| **upload_file(local_path, remote_path)**   | Upload file to SFTP            | Auto-creates directories; uses chunk upload for large files |
| **download_file(remote_path, local_path)** | Download file from SFTP        | Auto-creates local folders; supports chunk download         |
| **mkdir(path)**                            | Create directories recursively | Works like `mkdir -p`, creates each level safely            |
| **exists(path)**                           | Check if path exists           | Uses `stat()`; returns False if missing                     |

**2\. modules/sync_manager.py**
-----------------------

| Component / Method                              | Purpose                          | Explanation                                                                                               |
| ----------------------------------------------- | -------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| **source**                                      | SFTPBackend                      | Source SFTP backend to read files from                                                                          |
| **target**                                      | SFTPBackend                      | Target SFTP backend to write files to                                                                           |
| **large_file_threshold**                        | int                              | Files above this size are considered “large”                                                                    |
| **logger**                                      | logging.Logger                   | Logs warnings or errors                                                                                         |
| **scan_source(path)**                           | List files in source             | Uses `source.list_files()` to get all files under `path`                                                        |
| **scan_target(path)**                           | List files in target             | Uses `target.list_files()` to get all files under `path`                                                        |
| **diff_files(source_files, target_files)**      | Find new files                   | Returns files that exist in source but not in target                                                            |
| **get_large_files(files)**                      | Detect large files               | Checks size of each file via `source.hook.get_size()` and returns files above threshold                         |
| **sync_files(files, source_root, target_root)** | Copy files from source to target | Downloads each file to a temporary file, then uploads it to target; returns a dict with success/failure per file |

**2\. Others**
--------------

| Files                                | Purpose                 | Explanation                                                                                         |
| ------------------------------------ | ----------------------- | --------------------------------------------------------------------------------------------------- |
| **pyproject.toml**                   | Configuration for tools | Defines standard settings for formatters and type checkers, e.g., `isort` and `mypy`                |
| **conftest.py**                      | Test support            | Provides fixtures and hooks to mock internal Airflow functions and simplify unit tests              |
| **tests/resources/connections.json** | Mock connections        | Stores connection definitions used by tests to simulate Airflow connections                         |
| **.gitignore**                       | Git ignore file         | Lists files and directories to be ignored by Git (e.g., logs, temporary files, environment configs) |
