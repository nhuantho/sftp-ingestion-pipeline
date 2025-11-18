**Technical Design Document – SFTP to SFTP Sync Using Airflow**
===============================================================

**1\. Objective**
-----------------

The main objective is to build an Apache Airflow DAG that syncs files from the **source SFTP server** to the **target SFTP server**, while keeping the **original folder structure**.The sync must be **one-way**, meaning changes on the target must not affect the source. Deleted files on the source must **not**be deleted on the target.

**2\. Background**
------------------

### **2.1. Current State**

We currently have two SFTP servers.Files are uploaded to the **source** server every day.The target server needs to receive the same files, but there is no sync mechanism yet.

### **2.2. Problems / Requirements**

We need a solution that:

*   Detects new files on the source
    
*   Syncs them to the target with the same directory structure
    
*   Does not delete files on the target
    
*   Works daily with Airflow
    
*   Is easy to extend in the future (e.g., maybe use S3 instead of SFTP)
    
*   Can handle large files safely
    
*   Provides clean code and clear separation of logic
    

**3\. Design Proposal**
-----------------------

### **3.0. Overview Approach**

We will solve two main problems:

1.  **How to sync files from source to target in a correct and clean way**
    
2.  **How to structure the project so the logic is clear, testable, and extendable**
    

### **3.1. Solution for Sync Files**

There are several ways to sync data files between servers or storage systems.We will review the main options:

*   **Rsync**
    
*   **SFTPOperator**
    
*   **Fully Custom Python Logic**
    
*   **Hybrid: Custom Logic + SFTPOperator**
    

### **3.1.1. Rsync**

#### **Pros**

*   Very fast and efficient for syncing many files
    
*   Built-in logic for only copying differences
    
*   Handles large files very well
    
*   Reduces network bandwidth
    

#### **Cons**

*   Requires **SSH access**, not only SFTP
    
*   Cannot run if we only have SFTP endpoint
    
*   Hard to integrate inside Airflow DAG cleanly
    
*   Hard to test (external tool)
    
*   Not flexible if we want to switch to S3 in the future
    

### **3.1.2. SFTPOperator**

#### **Pros**

*   Built-in Airflow operator
    
*   Easy to use in Airflow
    
*   Safe and stable for SFTP
    
*   Good retry and logging support
    

#### **Cons**

*   Only supports **single file operations**
    
*   Cannot automatically sync directories
    
*   We still need to build logic for:
    
    *   directory walking
        
    *   checking existing files
        
    *   comparing source/target
        

### **3.1.3. Fully Custom Python Logic**

#### **Pros**

*   Full control of all logic
    
*   Can implement advanced features such as:
    
    *   file hashing
        
    *   streaming
        
    *   parallel transfer
        
*   Easy to replace storage backend (SFTP / S3 / GCS)
    

#### **Cons**

*   Time-consuming
    
*   Requires more code
    
*   Must manage low-level SFTP operations
    
*   More chance of bugs
    
*   Not necessary because Airflow already provides SFTPHook
    

### **3.1.4. Hybrid: Custom Logic + SFTPOperator**

#### **Pros**

*   Best balance of simplicity and flexibility
    
*   Custom logic handles:
    
    *   directory scanning
        
    *   comparing source/target
        
    *   selecting only new files
        
*   SFTPOperator/SFTPHook handles:
    
    *   network connection
        
    *   uploading and downloading
        
    *   logging and retrying
        
*   Easy to extend (swap SFTP backend with S3 later)
    
*   Easy to test (mock SFTP backend)
    
*   Works well with Airflow
    

#### **Cons**

*   More code than using only SFTPOperator
    
*   Slightly more complex than rsync
    
*   Requires good structure
    

### **3.1.5. Comparison of 4 Sync Options**

We compare **4 options**:

1.  **rsync**
    
2.  **Airflow SFTPOperator**
    
3.  **Fully Custom Python Logic**
    
4.  **Hybrid: Custom Logic + SFTPOperator**
    

We will score each criterion from **1 → 5 points**.

Scoring Rules

*   ⭐ = 1 point
*   🟡 = partial support = 2.5 points
*   ❌ = 0 points
*   ✅ = 5 points

**Comparison Table**

| Criteria                          | rsync     | SFTPOperator | Fully Custom Python Logic | Hybrid: Custom Logic + SFTPOperator |
| --------------------------------- | --------- | ------------ | ------------ | ------------------------------ |
| Speed                             | ⭐⭐⭐⭐⭐ (5) | ⭐⭐ (2)       | ⭐⭐⭐ (3)      | ⭐⭐⭐ (3)                        |
| Supports SFTP-only                | ❌ (0)     | ✅ (5)        | ✅ (5)        | ✅ (5)                          |
| Preserves directory tree          | ⭐⭐⭐⭐⭐ (5) | ❌ (0)        | 🟡 (2.5)     | ⭐⭐⭐⭐ (4)                       |
| Large file handling               | ⭐⭐⭐⭐⭐ (5) | ⭐⭐ (2)       | ⭐⭐⭐⭐ (4)     | ⭐⭐⭐⭐ (4)                       |
| Resumable                         | ⭐⭐⭐⭐ (4)  | ❌ (0)        | 🟡 (2.5)     | ⭐⭐ (2)                         |
| Airflow integration               | ⭐⭐ (2)    | ⭐⭐⭐⭐ (4)     | ⭐⭐⭐ (3)      | ⭐⭐⭐⭐ (4)                       |
| Extensibility                     | ❌ (0)     | 🟡 (2.5)     | ⭐⭐⭐⭐⭐ (5)    | ⭐⭐⭐⭐ (4)                       |
| Future-proof                      | ❌ (0)     | 🟡 (2.5)     | ⭐⭐⭐⭐ (4)     | ⭐⭐⭐⭐ (4)                       |
| Code complexity (higher = easier) | ⭐⭐⭐⭐ (4)  | ⭐⭐⭐ (3)      | ⭐ (1)        | ⭐⭐⭐ (3)                        |
| Large-scale sync                  | ⭐⭐⭐⭐⭐ (5) | ⭐⭐ (2)       | ⭐⭐⭐ (3)      | ⭐⭐⭐⭐ (4)                       |

**Total Points**

| Option                                   | Total Points     |
| ---------------------------------------- | ---------------- |
| rsync                                    | **30**           |
| SFTPOperator                             | **23**           |
| Fully Custom Python Logic                             | **33**           |
| **Hybrid: Custom Logic + SFTPOperator** | **37 — Highest** |


### **3.1.6. Conclusion**
The **Hybrid approach** using **Custom Python Logic + SFTPOperator** is the best option because:

*   Fully supports SFTP-only servers
    
*   Offers balance between performance and flexibility
    
*   Most maintainable and future-proof
    
*   Cleanest integration with Airflow
    
*   Allows adding file rules, validation, filtering, hashing, retries, etc.


### **3.2. Key Techniques**

### **3.2.1.Chunked Transfer**
   - Files larger than a configurable threshold are split into smaller blocks.
   - Each block is uploaded/downloaded sequentially to avoid memory overflow.
   - Facilitates retries of only failed chunks instead of the entire file.

### **3.2.2.Streaming I/O**
   - Files are read from source and written to target in blocks (e.g., 1–10 MB per block).
   - Prevents loading the entire file into memory, reducing RAM usage and improving stability.

### **3.2.3.Resume Support**
   - Partially transferred files are tracked using metadata (e.g., file path, size, completed chunks).
   - In case of failure, the pipeline resumes from the last completed block, reducing redundant transfers.

### **3.2.4.Validation**
   - Optional checksum (MD5 or SHA) verification for each file or chunk ensures data integrity.
   - Helps detect corrupted or incomplete transfers.

### **3.2.5.Retries**
   - Airflow’s task-level retry mechanism is used to handle transient network errors.
   - Combined with chunked transfers and resume support, retries are efficient even for very large files.


### **3.3. Define Project Structure**

A clean project structure helps maintainability and testing.

```
sftp-ingestion-pipeline/
│
├── conf/
│   ├── dependencies/
│   │   ├── external-requirements.txt   # Libs are not providers of airflow
│   │   └── internal-requirements.txt   # Libs are providers of airflow, ensure compatiable with airflow
│   ├── Dockerfile                      # Airflow image and Python environment
│   ├── docker-compose.yml              # Airflow services (Scheduler, Worker, ApiServer, DagProcessor)
│   └── Taskfile.yml                    # Manage building image
│
├── dags/
│   └── sftp_sync_dag.py                # Airflow DAG: orchestrates the ingestion pipeline
│
├── modules/
│   ├── storage_backends.py             # Abstract storage interface (for SFTP/S3)
│   ├── sftp_backend.py                 # Implementation using Airflow SFTPHook
│   └── sync_manager.py                 # Core logic: scanning, diffing, scheduling transfers
│
├── tests/
│   ├── storage_backends_test.py        # Mock storage (for SFTP/S3) server for testing
    ├── sftp_backend_test.py            # Mock SFTP server for testing
│   └── sync_manager_test.py            # Unit tests for sync logic
│
├── .gitignore
└── README.md                           # Project overview and instructions
```

**Key Modules Description**

*   `storage_backends.py`
    
    *   Defines abstract base classes/interfaces for storage operations
        
    *   Allows easy extension to other storage systems (S3)
        
*   `sftp_backend.py`
    
    *   Implements the storage interface for SFTP using Airflow SFTPHook
        
    *   Handles connection, upload, directory creation, and error handling
  
    *   Handles chunked upload/download using **SFTPHook** and streaming reads/writes.

        
*   `sync_manager.py`
    
    *   Core orchestrator of the pipeline
        
    *   Scans the source SFTP server
        
    *   Computes file differences (new or changed files)
        
    *   Submits tasks to SFTPHook/SFTPOperator for transfer
        
    *   Logs operations and handles exceptions

    *   Determines which files exceed the large-file threshold.
        
*   `sftp_sync_dag.py`
    
    *   Defines the Airflow DAG for scheduling the sync
        
    *   Dynamically generates tasks based on the file scan
        
    *   Implements retries, task dependencies, and monitoring
        
*   `tests/`
    
    *   Mock storage (for SFTP/S3) server for testing without a real server

    *   Unit tests for sync logic
        
    *   Mock SFTP backend for testing without a real server
        
*   `conf/`
    
    *   Docker setup for Airflow services
        
    *   Dependencies and environment setup
    

**4\. Action Plan**
-------------------

A clean and modular project structure improves maintainability, testing, and extensibility. The following action plan outlines the steps for implementing the structure of `sftp-ingestion-pipeline`, including core logic development and testing.

| Step | Tasks                                                                                                                                                                                                                                                                                                                                                                                                |
|------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Environment Setup** | - Create `conf/Dockerfile` for Airflow image and Python environment<br>- Create `conf/docker-compose.yml` to deploy Scheduler, Worker, ApiServer, DagProcessor<br>- Create `conf/Taskfile.yml` to manage building image<br>- Define `conf/dependencies/external-requirements.txt` and `conf/dependencies/internal-requirements.txt` for Python dependencies                                                            |
| **Storage Interface** | - Implement `modules/storage_backends.py` abstract base class for storage operations<br>- Ensure interface supports: list files, upload, download, directory creation, exists check<br>- Allows future extension to S3/MinIO<br>- Implement all testings for all logics                                                                                                                              |
| **SFTP Backend** | - Implement `modules/sftp_backend.py` using Airflow `SFTPHook`<br>- Support connection management, file upload/download, directory creation, error handling<br>- Implement **chunked/streaming transfers** for large files<br>- Include logging and retry handling<br>- Implement all testings for all logics                                                                                        |
| **Core Sync Logic** | - Implement `modules/sync_manager.py`:<br>&nbsp;&nbsp;- Recursively scan source SFTP server<br>&nbsp;&nbsp;- Compare with target server to detect new/changed files<br>&nbsp;&nbsp;- Determine files exceeding large-file threshold<br>&nbsp;&nbsp;- Submit tasks to `sftp_backend.py` for transfer<br>&nbsp;&nbsp;- Log operations and handle exceptions<br>- Implement all testings for all logics |
| **Airflow DAG** | - Create `dags/sftp_sync_dag.py`:<br>&nbsp;&nbsp;- Define DAG schedule for periodic syncs<br>&nbsp;&nbsp;- Generate dynamic tasks based on scan results<br>&nbsp;&nbsp;- Integrate `sync_manager` and `sftp_backend`<br>&nbsp;&nbsp;- Implement retries, alerts, and monitoring                                                                                                                      |
| **Validation & Integration** | - Run DAG in Airflow using Docker Compose<br>- Validate end-to-end transfer of small and large files<br>- Verify logging, retries, and monitoring<br>- Ensure modularity allows swapping storage backend (e.g., S3) without changing core logic                                                                                                                                                      |

**Outcome:**  
Following this structure ensures that the **core logic is fully testable**, large files are handled efficiently, and the project is maintainable, extensible, and ready for production-level integration.
