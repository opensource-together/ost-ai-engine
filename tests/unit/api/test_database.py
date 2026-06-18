from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from src.api.database import build_engine_and_session_factory


class TestDatabase:
    def test_build_engine_and_session_factory_returns_both(self) -> None:
        """The helper returns an engine and a Session-producing factory."""
        mock_engine = MagicMock()

        with patch("src.api.database.create_engine", return_value=mock_engine):
            engine, session_factory = build_engine_and_session_factory(
                "postgresql://u:p@localhost/db"
            )

        assert engine is mock_engine
        session = session_factory()
        assert isinstance(session, Session)
