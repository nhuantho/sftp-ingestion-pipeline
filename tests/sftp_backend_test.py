import unittest
from unittest.mock import patch, MagicMock
from modules.sftp_backend import SFTPBackend

class TestSFTPBackend(unittest.TestCase):
    def setUp(self):
        self.conn_id = 'test_sftp_conn_id'
        patcher = patch('modules.sftp_backend.SFTPHook', autospec=True)
        self.mock_sftp_hook_class = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_sftp_hook = self.mock_sftp_hook_class.return_value
        self.backend = SFTPBackend(self.conn_id)
        self.backend.hook = self.mock_sftp_hook
        self.backend.hook.walk = MagicMock()
        self.backend.hook.store_file = MagicMock()
        self.backend.hook.get_file = MagicMock()
        self.backend.hook.create_directory = MagicMock()
        self.backend.hook.path_exists = MagicMock()
        self.backend.hook.get_size = MagicMock()
        self.backend.hook.read_file = MagicMock()

    def test_list_files(self):
        self.backend.hook.walk.return_value = [
            ('/root', ['subdir'], ['file1.txt', 'file2.txt']),
            ('/root/subdir', [], ['file3.txt'])
        ]
        files = self.backend.list_files('/root')
        self.assertEqual(set(files), {'/root/file1.txt', '/root/file2.txt', '/root/subdir/file3.txt'})

    def test_upload_file_small(self):
        self.backend.hook.path_exists.return_value = True
        with patch('os.path.getsize', return_value=1024):
            self.backend.upload_file('local.txt', '/remote/file.txt')
            self.backend.hook.store_file.assert_called_with('/remote/file.txt', 'local.txt')

    def test_upload_file_large(self):
        self.backend.hook.path_exists.return_value = True
        with patch('os.path.getsize', return_value=1024 * 1024 * 20):
            with patch('builtins.open', unittest.mock.mock_open(read_data=b'x' * 1024 * 1024 * 20)) as mock_file:
                self.backend.upload_file('local.txt', '/remote/file.txt')
                self.backend.hook.store_file.assert_called()

    def test_download_file_small(self):
        self.backend.hook.get_size.return_value = 1024
        with patch('os.makedirs') as makedirs:
            self.backend.download_file('/remote/file.txt', '/local/file.txt')
            makedirs.assert_called()
            self.backend.hook.get_file.assert_called_with('/remote/file.txt', '/local/file.txt')

    def test_download_file_large(self):
        self.backend.hook.get_size.return_value = 1024 * 1024 * 20
        self.backend.hook.read_file.return_value = b'x' * 1024 * 1024 * 10
        with patch('os.makedirs') as makedirs:
            with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
                self.backend.download_file('/remote/file.txt', '/local/file.txt')
                makedirs.assert_called()
                self.backend.hook.read_file.assert_called()

    def test_mkdir(self):
        self.backend.hook.path_exists.side_effect = [False, False]
        self.backend.mkdir('/remote/dir/subdir')
        self.assertTrue(self.backend.hook.create_directory.called)

    def test_exists(self):
        self.backend.hook.path_exists.return_value = True
        self.assertTrue(self.backend.exists('/remote/file.txt'))
        self.backend.hook.path_exists.return_value = False
        self.assertFalse(self.backend.exists('/remote/file.txt'))

if __name__ == '__main__':
    unittest.main()
