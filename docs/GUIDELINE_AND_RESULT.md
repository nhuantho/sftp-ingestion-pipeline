# Guideline And Result

**1\. Build airflow**
---------------------

*   Run: docker compose up (-d)
*   ![alt text](./images/running_success.png)


*   Access `localhost:8080` and require login, type `airflow` to `Username and Password` and push `Sign In`
*   ![alt text](./images/page_login.png)
*   ![alt text](./images/page_home.png)


**2\. Test Scenarios**
---------------------
### Overview
*   ![alt text](./images/overview.png)


*   Push `Trigger` on the top-left of sftp_sync_dag screen, and then push Trigger
*   ![alt text](./images/page_trigger.png)
*   ![alt text](./images/page_dagrun_success.png)


### Results
*   **Happy case**

| # | Scenario                   | Task(s)                  | Result (Check logs of the specific task)                                                                                                                                                                                                                                                                         | 
| - |----------------------------|--------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1 | Detect files on source     | `scan_source`            | Check `INFO - List files: `<br/>![alt text](./images/page_scan_source.png)                                                                                                                                                                                                                                       |
| 2 | Detect files on target     | `scan_target`            | Check `INFO - List files: `<br/>![alt text](./images/page_scan_target.png)                                                                                                                                                                                                                                       |
| 3 | Calculate diff files       | `diff_files`             | Check `INFO - New files: `<br/>![alt text](./images/page_diff_files.png)                                                                                                                                                                                                                                         |
| 4 | Split files                | `split_files`            | Check `INFO - Small files: `<br/>Check `INFO - Large files: `<br/>![alt text](./images/page_split_files.png)                                                                                                                                                                                                     |
| 5 | Extract small files        | `get_small_files`        | Check `INFO - Done. Returned value was: `<br/>![alt text](./images/page_get_small_files.png)                                                                                                                                                                                                                     |
| 6 | Sync small files           | `sync_small_file`        | There are three tasks<br/>![alt text](./images/page_sync_small_file_overview.png)<br/>See detail a task, and check `INFO - Synced: `<br/>![alt text](./images/page_sync_small_file_detail.png)                                                                                                                   |
| 7 | Check files in sftp-target |  | Run: `docker exec -it sftp-ingestion-pipeline-sftp-target-1 ls /home/sftpuser/upload/a/b/c`<br/>![alt text](./images/check_file_sftp_target.png)<br/>Run: `docker exec -it sftp-ingestion-pipeline-sftp-target-1 cat /home/sftpuser/upload/a/b/c/file_1.txt`<br/>![alt text](./images/check_content_sftp_target.png) |

*   **Unidirectional sync**

| # | Scenario                                                          | Task(s)                  | Result (Check logs of the specific task)                                                                                                                                                                                                                                                                        | 
|---|-------------------------------------------------------------------|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1 | Delete `/upload/a/b/c/file_1.txt` on source, and then trigger dag |                     | Run: `docker exec -it sftp-ingestion-pipeline-sftp-source-1 rm -rf /home/sftpuser/upload/a/b/c/file_1.txt`<br/>![alt text](./images/delete_file_1.png)<br/>Did not have new files so `sync_small_file` was skipped<br/>![alt text](./images/page_dagrun_success_2.png)                                          |
| 2 | Detect files on source                                            | `scan_source`            | Check `INFO - List files: `<br/>![alt text](./images/page_scan_source_2.png)                                                                                                                                                                                                                                    |
| 3 | Detect files on target                                            | `scan_target`            | Check `INFO - List files: `<br/>![alt text](./images/page_scan_target_2.png)                                                                                                                                                                                                                                    |
| 4 | Calculate diff files                                              | `diff_files`             | Check `INFO - New files: `<br/>![alt text](./images/page_diff_files_2.png)                                                                                                                                                                                                                                      |
| 5 | Split files                                                       | `split_files`            | Check `INFO - Small files: `<br/>Check `INFO - Large files: `<br/>![alt text](./images/page_split_files_2.png)                                                                                                                                                                                                  |
| 6 | Extract small files                                               | `get_small_files`        | Check `INFO - Done. Returned value was: `<br/>![alt text](./images/page_get_small_files_2.png)                                                                                                                                                                                                                  |
| 7 | Check files in sftp-target (Not change)                           |  | Run: `docker exec -it sftp-ingestion-pipeline-sftp-target-1 ls /home/sftpuser/upload/a/b/c`<br/>![alt text](./images/check_file_sftp_target.png)<br/>`Run docker exec -it sftp-ingestion-pipeline-sftp-target-1 cat /home/sftpuser/upload/a/b/c/file_1.txt`<br/>![alt text](./images/check_content_sftp_target.png) |

*   **Incremental sync**

| # | Scenario                                                       | Task(s)                  | Result (Check logs of the specific task)                                                                                                                                                                                                                                       | 
|---|----------------------------------------------------------------|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1 | Add `/upload/a/b/c/file_4.txt` on source, and then trigger dag |                     | Run: `docker exec -it sftp-ingestion-pipeline-sftp-source-1 bash -c 'echo "File 4 content" > /home/sftpuser/upload/a/b/c/file_4.txt'`<br/>![alt text](./images/add_file_4.png)<br/>Had a new file so `sync_small_file` ran<br/>![alt text](./images/page_dagrun_success_3.png) |
| 2 | Detect files on source                                         | `scan_source`            | Check `INFO - List files: `<br/>![alt text](./images/page_scan_source_3.png)                                                                                                                                                                                                   |
| 3 | Detect files on target                                         | `scan_target`            | Check `INFO - List files: `<br/>![alt text](./images/page_scan_target_3.png)                                                                                                                                                                                                   |
| 4 | Calculate diff files                                           | `diff_files`             | Check `INFO - New files: `<br/>![alt text](./images/page_diff_files_3.png)                                                                                                                                                                                                     |
| 5 | Split files                                                    | `split_files`            | Check `INFO - Small files: `<br/>Check `INFO - Large files: `<br/>![alt text](./images/page_split_files_3.png)                                                                                                                                                                 |
| 6 | Extract small files                                            | `get_small_files`        | Check `INFO - Done. Returned value was: `<br/>![alt text](./images/page_get_small_files_3.png)                                                                                                                                                                                 |
| 7 | Sync small files                                               | `sync_small_file`        | There is one task<br/>![alt text](./images/page_sync_small_file_overview_3.png)<br/>See detail a task, and check `INFO - Synced: `<br/>![alt text](./images/page_sync_small_file_detail_3.png)                                                                                 |
| 8 | Check files in sftp-target (a new file_4.txt)                  |  | Run: `docker exec -it sftp-ingestion-pipeline-sftp-target-1 ls /home/sftpuser/upload/a/b/c`<br/>`Run docker exec -it sftp-ingestion-pipeline-sftp-target-1 cat /home/sftpuser/upload/a/b/c/file_4.txt`<br/>![alt text](./images/check_file_sftp_target_3.png)                  |