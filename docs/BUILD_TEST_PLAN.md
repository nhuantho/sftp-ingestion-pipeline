# Test plan for SFTP to SFTP Sync DAG

**1\. Objective**
-----------------

Verify that the Airflow DAG correctly synchronizes files from the **SFTP Source** server to the **SFTP Target** server while preserving the directory structure and adhering to the following constraints:

*   Synchronization is **unidirectional** (source → target only).
    
*   Files deleted from **source** must **remain** on **target**.
    
*   Only **new files** on source are transferred.
    
*   Both **small** and **large** files are handled:
    
    *   Small files → direct upload
        
    *   Large files → chunk-based upload

```
SFTP-SOURCE  →  SFTP-TARGET
```

The DAG must:

*   Detect files that exist on **source** but not on **target**
    
*   Synchronize files while **preserving directory structure**
    
*   Ensure **unidirectional sync** (target cannot affect source)
    
*   Ensure deleted files from source **remain intact** on target
    
*   Support **small file sync** (large file sync not covered in this test)
    
*   Use XCom to pass data between tasks

This test uses two SFTP servers:

| Service         | Local bind directory | Remote path      |
| --------------- | -------------------- | ---------------- |
| **sftp-source** | `./sftp_source_data` | `/home/sftpuser` |
| **sftp-target** | `./sftp_target_data` | `/home/sftpuser` |

Initial file set:

```
./sftp_source_data/upload/a/b/c/file_1.txt
./sftp_source_data/upload/a/b/c/file_2.txt
./sftp_source_data/upload/a/b/c/file_3.txt
```
Only **small-file sync** (sync\_small\_file) will be validated.

2. **DAG Tasks Under Test**
---------------------------

| Task Name           | Purpose                                         |
| ------------------- | ----------------------------------------------- |
| **scan_source**     | List files on source server and push to XCom    |
| **scan_target**     | List files on target server and push to XCom    |
| **diff_files**      | Compute new files = source_files − target_files |
| **split_files**     | Split into small_files + large_files            |
| **get_small_files** | Extract small_files from XCom                   |
| **get_large_files** | Extract large_files (ignored in this test)      |
| **sync_small_file** | Sync small files from source → target           |
| **sync_large_file** | Not tested                                      |

This test plan will only validate:

```
scan_source
scan_target
diff_files
split_files
get_small_files
sync_small_file
```
3. **Test Environment Setup**
---------------------------

### 3.1 Containers
Spin up two SFTP containers:

*   `sftp-source`
    
*   `sftp-target`

Each exposes `/home/sftpuser`

### 3.2 Bind-Mounted Directories

```
./sftp_source_data → /home/sftpuser
./sftp_target_data → /home/sftpuser
```

### 3.3 Initial File Data
Place the files in the source directory:

```
./sftp_source_data/upload/a/b/c/file_1.txt
./sftp_source_data/upload/a/b/c/file_2.txt
./sftp_source_data/upload/a/b/c/file_3.txt
```

Ensure the target starts empty:

```
./sftp_target_data/upload/  (empty)
```

4. **Test Scenarios**
---------------------------

| # | Scenario               | Task(s)           | Input                                                  | Expected Output / Result                                                                                                   | Verification                                                                |
| - |------------------------| ----------------- | ------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| 1 | Detect files on source | `scan_source`     | `/upload` on source SFTP                               | `["/upload/a/b/c/file_1.txt", "/upload/a/b/c/file_2.txt", "/upload/a/b/c/file_3.txt"]`                                     | Check XCom of `scan_source`                                                 |
| 2 | Detect files on target | `scan_target`     | `/upload` on target SFTP                               | `[]`                                                                                                                       | Check XCom of `scan_target`                                                 |
| 3 | Calculate diff files   | `diff_files`      | `source_files` = 3 files, `target_files` = empty       | `["/upload/a/b/c/file_1.txt", "/upload/a/b/c/file_2.txt", "/upload/a/b/c/file_3.txt"]`                                     | Check XCom of `diff_files`                                                  |
| 4 | Split files            | `split_files`     | `diff_files` output                                    | `{"small_files": ["/upload/a/b/c/file_1.txt", "/upload/a/b/c/file_2.txt", "/upload/a/b/c/file_3.txt"], "large_files": []}` | Check XCom of `split_files`                                                 |
| 5 | Extract small files    | `get_small_files` | `split_files` output                                   | `["/upload/a/b/c/file_1.txt", "/upload/a/b/c/file_2.txt", "/upload/a/b/c/file_3.txt"]`                                     | Check XCom of `get_small_files`                                             |
| 6 | Sync small files       | `sync_small_file` | `get_small_files` output                               | Files exist on target SFTP: `/upload/a/b/c/file_1.txt`, `/upload/a/b/c/file_2.txt`, `/upload/a/b/c/file_3.txt`             | Compare source vs target files, verify directory structure and file content |
| 7 | Unidirectional sync    | `sync_small_file` | Delete `/upload/a/b/c/file_1.txt` on source, rerun DAG | `/upload/a/b/c/file_1.txt` **still exists** on target                                                                      | Verify target still contains deleted file                                   |
| 8 | Incremental sync       | `sync_small_file` | Add `/upload/a/b/c/file_4.txt` on source, rerun DAG    | Only `file_4.txt` is synced to target                                                                                      | Check target SFTP contains `/upload/a/b/c/file_4.txt` only                  |

5. **Success Criteria**
---------------------------
| Test Case              | Expected Result               |
| ---------------------- | ----------------------------- |
| Scan source            | Detects all source files      |
| Scan target            | Empty on first run            |
| Diff                   | Computes new files only       |
| Split                  | All files classified as small |
| Sync small             | All small files replicated    |
| Directory preservation | Paths match exactly           |
| Unidirectional         | No deletion on target         |
| Incremental sync       | New files appended correctly  |
