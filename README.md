### Guideline And Result: [Link documents](docs/GUIDELINE_AND_RESULT.md)

### Technical Design Document: [Link documents](docs/TECHNICAL_DESIGN_DOCUMENT.md)
You can refer to the detailed TDD to understand the system implementation. Below is a summary of the TDD.
#### Summary TDD:
#### **1\. Sync Approach**
*   **Hybrid: Custom Logic + SFTPOperator**
    *   Chosen to balance **simplicity, maintainability, and flexibility**.
    *   Handles **one-way sync**, preserving the source directory structure.
    *   Supports **large files** via chunked and streaming transfers.
    *   Easily extensible to **other storage backends** like S3 or MinIO.

#### **2\. Rejected Options**

| Option             | Reason for Rejection                                                                             |
| ------------------ | ------------------------------------------------------------------------------------------------ |
| Rsync              | Requires SSH access; cannot work with SFTP-only endpoints; hard to integrate in Airflow.         |
| Pure SFTPOperator  | Only supports single-file operations; lacks directory syncing and efficient large-file handling. |
| Fully Custom Logic | Time-consuming, more error-prone; low-level SFTP operations handled better with SFTPHook.        |

#### **3\. Assumptions**

*   Files on source **are added but not deleted**; target does not delete files.
*   Transfers may be **interrupted**, so **resumable, chunked transfers** are implemented.
*   The system should be **extensible** for future storage backends.
*   Airflow **task-level retries** handle transient network errors.
*   Validation using **checksums** is optional but can ensure integrity.
    

#### **4\. Trade-offs**

*   Slightly more code complexity than using only SFTPOperator, but provides **flexibility and maintainability**.
*   Hybrid approach avoids the complexity of fully custom SFTP logic while still supporting directory sync, large files, and resumable transfers.
*   Using Airflow operators/hooks ensures **integration, logging, and retry support**, at the cost of writing some custom orchestration logic in Python.

### Build Test plan: [Link documents](docs/BUILD_TEST_PLAN.md) 

### Explain Airflow Setup: [Link documents](docs/EXPLAIN_AIRFLOW_SETUP.md)  

### Explain Logic Detail: [Link documents](docs/EXPLAIN_LOGIC_DETAIL.md)  