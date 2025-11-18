import unittest
from unittest.mock import MagicMock, patch

from modules.storage_backends import StorageSFTPBackend

class TestStorageSFTPBackend(unittest.TestCase):
    def setUp(self):
        self.conn_id = 'test_sftp_conn_id'
        patcher = patch('modules.storage_backends.SFTPHook', autospec=True)
        self.mock_sftp_hook_class = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_sftp_hook = self.mock_sftp_hook_class.return_value
        self.backend = StorageSFTPBackend(self.conn_id)
        self.backend.hook = self.mock_sftp_hook
        # Add 'walk' method to the mock hook after assignment
        self.backend.hook.walk = MagicMock()

    def test_list_files(self):
        self.backend.hook.walk.return_value = [
            ('/root', ['subdir'], ['file1.txt', 'file2.txt']),
            ('/root/subdir', [], ['file3.txt'])
        ]
        files = self.backend.list_files('/root')
        self.assertEqual(set(files), {'/root/file1.txt', '/root/file2.txt', '/root/subdir/file3.txt'})

    def test_upload_file(self):
        self.backend.hook.path_exists.return_value = False
        self.backend.hook.create_directory = MagicMock()
        self.backend.hook.store_file = MagicMock()
        self.backend.upload_file('local.txt', '/remote/dir/file.txt')
        self.backend.hook.create_directory.assert_called()
        self.backend.hook.store_file.assert_called_with('/remote/dir/file.txt', 'local.txt')

    def test_download_file(self):
        self.backend.hook.get_file = MagicMock()
        with patch('os.makedirs') as makedirs:
            self.backend.download_file('/remote/file.txt', '/local/dir/file.txt')
            makedirs.assert_called_with('/local/dir', exist_ok=True)
            self.backend.hook.get_file.assert_called_with('/remote/file.txt', '/local/dir/file.txt')

    def test_mkdir(self):
        self.backend.hook.path_exists.side_effect = [False, False]
        self.backend.hook.create_directory = MagicMock()
        self.backend.mkdir('/remote/dir/subdir')
        self.assertTrue(self.backend.hook.create_directory.called)

    def test_exists(self):
        self.backend.hook.path_exists.return_value = True
        self.assertTrue(self.backend.exists('/remote/file.txt'))
        self.backend.hook.path_exists.return_value = False
        self.assertFalse(self.backend.exists('/remote/file.txt'))

if __name__ == '__main__':
    unittest.main()

