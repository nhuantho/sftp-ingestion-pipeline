import unittest
from unittest.mock import MagicMock, patch

from modules.sftp_backend import SFTPBackend
from modules.sync_manager import SyncManager


class TestSyncManager(unittest.TestCase):
    def setUp(self):
        self.source = MagicMock(spec=SFTPBackend)
        self.source.hook = MagicMock()  # Add mock hook for get_size
        self.target = MagicMock(spec=SFTPBackend)
        self.manager = SyncManager(self.source, self.target, large_file_threshold=1024 * 1024 * 10)

    def test_scan_source(self):
        self.source.list_files.return_value = ['/src/file1.txt', '/src/file2.txt']
        files = self.manager.scan_source('/src')
        self.assertEqual(files, ['/src/file1.txt', '/src/file2.txt'])

    def test_scan_target(self):
        self.target.list_files.return_value = ['/dst/file1.txt']
        files = self.manager.scan_target('/dst')
        self.assertEqual(files, ['/dst/file1.txt'])

    def test_diff_files(self):
        src = ['/src/file1.txt', '/src/file2.txt']
        dst = ['/src/file1.txt']
        diff = self.manager.diff_files(src, dst)
        self.assertEqual(diff, ['/src/file2.txt'])

    def test_get_large_files(self):
        self.source.hook.get_size.side_effect = [5 * 1024 * 1024, 20 * 1024 * 1024]
        files = ['/src/small.txt', '/src/large.txt']
        large_files = self.manager.get_large_files(files)
        self.assertEqual(large_files, ['/src/large.txt'])

    def test_sync_files_success(self):
        self.target.upload_file = MagicMock()
        files = ['/src/file1.txt', '/src/file2.txt']
        result = self.manager.sync_files(files, '/src', '/dst')
        self.assertTrue(all(result.values()))
        self.target.upload_file.assert_any_call('/src/file1.txt', '/dst/file1.txt')
        self.target.upload_file.assert_any_call('/src/file2.txt', '/dst/file2.txt')

    def test_sync_files_failure(self):
        def fail_upload(src, dst):
            if 'fail' in src:
                raise Exception('fail')
        self.target.upload_file.side_effect = fail_upload
        files = ['/src/file1.txt', '/src/fail.txt']
        result = self.manager.sync_files(files, '/src', '/dst')
        self.assertTrue(result['/src/file1.txt'])
        self.assertFalse(result['/src/fail.txt'])

if __name__ == '__main__':
    unittest.main()
