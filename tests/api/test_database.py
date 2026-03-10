from unittest.mock import MagicMock

from src.services.api.database import ConnectionPool


class TestConnectionPool:
    def test_get_cursor_yields_realdict_cursor(self) -> None:
        """get_cursor yields a RealDictCursor from the pool."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_pool = MagicMock()
        mock_pool.getconn.return_value = mock_conn

        pool = ConnectionPool.__new__(ConnectionPool)
        pool._pool = mock_pool

        with pool.get_cursor() as cur:
            assert cur is mock_cursor

        mock_conn.rollback.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_conn)
