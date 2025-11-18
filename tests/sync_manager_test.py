import unittest
from unittest.mock import MagicMock
from modules.sync_manager import SyncManager
from modules.sftp_backend import SFTPBackend

class TestSyncManager(unittest.TestCase):
    def setUp(self):
        self.source = MagicMock(spec=SFTPBackend)
        self.source.hook = MagicMock()
        self.target = MagicMock(spec=SFTPBackend)
        self.target.hook = MagicMock()
        self.manager = SyncManager(self.source, self.target, large_file_threshold=1024 * 1024 * 10)

    def test_unidirectional_sync_preserves_structure(self):
        # Simulate files on source for 3 days
        source_files = [
            '/a/b/c/file_1.txt',
            '/a/b/c/file_2.txt',
            '/a/b/c/file_3.txt'
        ]
        # Simulate files on target (file_1.txt already synced)
        target_files = [
            '/a/b/c/file_1.txt'
        ]
        self.source.list_files.return_value = source_files
        self.target.list_files.return_value = target_files

        # Only file_2.txt and file_3.txt should be synced
        diff = self.manager.diff_files(source_files, target_files)
        self.assertEqual(diff, ['/a/b/c/file_2.txt', '/a/b/c/file_3.txt'])

        # Simulate successful upload
        self.target.upload_file = MagicMock()
        results = self.manager.sync_files(diff, '/a/b/c', '/a/b/c')
        self.assertTrue(all(results.values()))
        self.target.upload_file.assert_any_call('/a/b/c/file_2.txt', '/a/b/c/file_2.txt')
        self.target.upload_file.assert_any_call('/a/b/c/file_3.txt', '/a/b/c/file_3.txt')

    def test_no_deletion_on_target(self):
        # Simulate file deleted on source but present on target
        source_files = ['/a/b/c/file_1.txt']
        target_files = ['/a/b/c/file_1.txt', '/a/b/c/file_2.txt']
        self.source.list_files.return_value = source_files
        self.target.list_files.return_value = target_files

        # Only file_2.txt is missing on source, but should NOT be deleted from target
        diff = self.manager.diff_files(source_files, target_files)
        self.assertEqual(diff, [])
        # No sync should occur
        self.target.upload_file = MagicMock()
        results = self.manager.sync_files(diff, '/a/b/c', '/a/b/c')
        self.assertEqual(results, {})

    def test_sync_new_files_multiple_days(self):
        # Day 1
        source_files_day1 = ['/a/b/c/file_1.txt']
        target_files_day1 = []
        self.source.list_files.return_value = source_files_day1
        self.target.list_files.return_value = target_files_day1
        diff1 = self.manager.diff_files(source_files_day1, target_files_day1)
        self.assertEqual(diff1, ['/a/b/c/file_1.txt'])

        # Day 2
        source_files_day2 = ['/a/b/c/file_1.txt', '/a/b/c/file_2.txt']
        target_files_day2 = ['/a/b/c/file_1.txt']
        self.source.list_files.return_value = source_files_day2
        self.target.list_files.return_value = target_files_day2
        diff2 = self.manager.diff_files(source_files_day2, target_files_day2)
        self.assertEqual(diff2, ['/a/b/c/file_2.txt'])

        # Day 3
        source_files_day3 = ['/a/b/c/file_1.txt', '/a/b/c/file_2.txt', '/a/b/c/file_3.txt']
        target_files_day3 = ['/a/b/c/file_1.txt', '/a/b/c/file_2.txt']
        self.source.list_files.return_value = source_files_day3
        self.target.list_files.return_value = target_files_day3
        diff3 = self.manager.diff_files(source_files_day3, target_files_day3)
        self.assertEqual(diff3, ['/a/b/c/file_3.txt'])

if __name__ == '__main__':
    unittest.main()
