import unittest
from unittest.mock import MagicMock, patch, mock_open

from modules.sftp_backend import SFTPBackend


class TestSFTPBackend(unittest.TestCase):
    def setUp(self):
        self.conn_id = "test_sftp_conn"
        self.patcher = patch("modules.sftp_backend.SFTPHook", autospec=True)
        self.mock_hook_class = self.patcher.start()
        self.addCleanup(self.patcher.stop)

        # mock hook instance
        self.mock_hook = self.mock_hook_class.return_value

        # Create backend
        self.backend = SFTPBackend(self.conn_id)

        # Mock conn returned by get_conn()
        self.mock_conn = MagicMock()
        self.backend.hook.get_conn.return_value.__enter__.return_value = self.mock_conn
        self.backend.hook.get_conn.return_value.__exit__.return_value = None
        self.backend._conn = self.mock_conn  # so get_conn() returns this

    def test_list_files(self):
        # Mock SFTPAttributes
        def attr(filename, is_dir=False):
            obj = MagicMock()
            obj.filename = filename
            obj.st_mode = 0o040755 if is_dir else 0o100644
            return obj

        # Mock directory structure
        self.mock_conn.listdir_attr.side_effect = [
            [attr("subdir", True), attr("file1.txt"), attr("file2.txt")],
            [attr("file3.txt")]
        ]

        files = self.backend.list_files("/root")
        self.assertEqual(
            set(files),
            {
                "/root/subdir/file3.txt",
                "/root/file1.txt",
                "/root/file2.txt",
            },
        )

    def test_upload_file_small(self):
        with patch("os.path.getsize", return_value=1024):
            self.backend.upload_file("local.txt", "/remote/file.txt")
            self.mock_conn.put.assert_called_with("local.txt", "/remote/file.txt")

    def test_upload_file_large(self):
        large_size = 25 * 1024 * 1024
        with patch("os.path.getsize", return_value=large_size):
            m = mock_open(read_data=b"x" * large_size)
            with patch("builtins.open", m):
                mock_remote_file = MagicMock()
                self.mock_conn.open.return_value.__enter__.return_value = mock_remote_file

                self.backend.upload_file("local_big.txt", "/remote/big.txt")

                self.mock_conn.open.assert_called_with("/remote/big.txt", "wb")
                mock_remote_file.write.assert_called()

    def test_download_file_small(self):
        # Mock stat().st_size
        mock_stat = MagicMock()
        mock_stat.st_size = 1024
        self.mock_conn.stat.return_value = mock_stat

        with patch("os.makedirs") as makedirs:
            self.backend.download_file("/remote/file.txt", "/local/file.txt")
            makedirs.assert_called()
            self.mock_conn.get.assert_called_with("/remote/file.txt", "/local/file.txt")

    def test_download_file_large(self):
        mock_stat = MagicMock()
        mock_stat.st_size = 25 * 1024 * 1024
        self.mock_conn.stat.return_value = mock_stat

        mock_remote_f = MagicMock()
        mock_remote_f.read.side_effect = [
            b"x" * (10 * 1024 * 1024),
            b"x" * (10 * 1024 * 1024),
            b"",
        ]
        self.mock_conn.open.return_value.__enter__.return_value = mock_remote_f

        with patch("os.makedirs"):
            m = mock_open()
            with patch("builtins.open", m):
                self.backend.download_file("/r/big.bin", "/l/big.bin")

                mock_remote_f.read.assert_called()

    def test_mkdir(self):
        # conn.mkdir should be called many times, ignore failures
        self.backend.mkdir("/remote/dir/subdir")
        self.assertTrue(self.mock_conn.mkdir.called)

    def test_exists(self):
        # When stat works → exists
        self.mock_conn.stat.return_value = True
        self.assertTrue(self.backend.exists("/remote/x"))

        # When stat raises → not exists
        self.mock_conn.stat.side_effect = Exception("not found")
        self.assertFalse(self.backend.exists("/remote/x"))


if __name__ == "__main__":
    unittest.main()
