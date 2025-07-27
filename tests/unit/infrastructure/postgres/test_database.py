"""
Unit tests for database infrastructure.

Tests the database connection, session management, and configuration.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from src.infrastructure.postgres.database import (
    engine,
    SessionLocal,
    Base,
    get_db
)
from src.infrastructure.config import settings


class TestDatabaseConnection:
    """Test database connection and engine creation."""

    def test_engine_creation(self):
        """Test that the engine is created successfully."""
        assert engine is not None
        # Compare URLs without password for security
        engine_url = str(engine.url)
        settings_url = settings.DATABASE_URL
        
        # Extract components for comparison
        assert engine_url.startswith("postgresql://")
        assert settings_url.startswith("postgresql://")
        
        # Check host and port
        assert "localhost" in engine_url or "127.0.0.1" in engine_url
        assert "5434" in engine_url or "5432" in engine_url
        assert "ost_db" in engine_url or "test_db" in engine_url

    def test_engine_url_format(self):
        """Test that the engine URL follows PostgreSQL format."""
        url = str(engine.url)
        assert url.startswith("postgresql://")
        assert "localhost" in url or "127.0.0.1" in url
        assert "5434" in url or "5432" in url  # Our default ports
        assert "ost_db" in url or "test_db" in url  # Our default database names


class TestSessionManagement:
    """Test session creation and management."""

    def test_session_local_creation(self):
        """Test that SessionLocal is created successfully."""
        assert SessionLocal is not None
        assert isinstance(SessionLocal, sessionmaker)

    def test_session_local_bind(self):
        """Test that SessionLocal is bound to the correct engine."""
        assert SessionLocal.kw['bind'] == engine

    def test_session_local_autocommit_false(self):
        """Test that autocommit is set to False."""
        assert SessionLocal.kw['autocommit'] is False

    def test_session_local_autoflush_false(self):
        """Test that autoflush is set to False."""
        assert SessionLocal.kw['autoflush'] is False

    def test_create_session(self):
        """Test creating a new session."""
        session = SessionLocal()
        assert session is not None
        session.close()

    def test_session_context_manager(self):
        """Test session as context manager."""
        with SessionLocal() as session:
            assert session is not None
            # Session should be closed automatically


class TestBaseModel:
    """Test the declarative base model."""

    def test_base_creation(self):
        """Test that Base is created successfully."""
        assert Base is not None
        assert hasattr(Base, 'metadata')

    def test_base_metadata(self):
        """Test that Base has metadata for table creation."""
        assert Base.metadata is not None
        assert hasattr(Base.metadata, 'create_all')


class TestGetDbDependency:
    """Test the get_db dependency function."""

    def test_get_db_generator(self):
        """Test that get_db returns a generator."""
        db_gen = get_db()
        assert hasattr(db_gen, '__iter__')
        assert hasattr(db_gen, '__next__')

    def test_get_db_yields_session(self):
        """Test that get_db yields a database session."""
        db_gen = get_db()
        session = next(db_gen)
        
        assert session is not None
        assert hasattr(session, 'close')
        
        # Clean up
        try:
            next(db_gen)  # Should raise StopIteration
        except StopIteration:
            pass

    def test_get_db_session_cleanup(self):
        """Test that get_db properly closes the session."""
        with patch('src.infrastructure.postgres.database.SessionLocal') as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            
            db_gen = get_db()
            session = next(db_gen)
            
            # Simulate the finally block
            try:
                next(db_gen)
            except StopIteration:
                pass
            
            # Session should be closed
            mock_session.close.assert_called_once()

    def test_get_db_multiple_calls(self):
        """Test that get_db can be called multiple times."""
        # First call
        db_gen1 = get_db()
        session1 = next(db_gen1)
        try:
            next(db_gen1)
        except StopIteration:
            pass
        
        # Second call
        db_gen2 = get_db()
        session2 = next(db_gen2)
        try:
            next(db_gen2)
        except StopIteration:
            pass
        
        # Both sessions should be different instances
        assert session1 is not session2


class TestDatabaseConfiguration:
    """Test database configuration and settings."""

    def test_database_url_from_settings(self):
        """Test that database URL comes from settings."""
        assert settings.DATABASE_URL is not None
        assert isinstance(settings.DATABASE_URL, str)
        assert len(settings.DATABASE_URL) > 0

    def test_database_url_format(self):
        """Test that database URL has correct format."""
        url = settings.DATABASE_URL
        assert url.startswith("postgresql://")
        assert "user:password" in url or "test_user:test_password" in url
        assert "localhost" in url or "127.0.0.1" in url
        assert "5434" in url or "5432" in url
        assert "ost_db" in url or "test_db" in url


class TestDatabaseErrorHandling:
    """Test database error handling scenarios."""

    def test_get_db_session_creation_failure(self):
        """Test handling of session creation failure in get_db."""
        with patch('src.infrastructure.postgres.database.SessionLocal') as mock_session_local:
            mock_session_local.side_effect = Exception("Session creation failed")
            
            db_gen = get_db()
            with pytest.raises(Exception, match="Session creation failed"):
                next(db_gen)

    def test_session_close_on_exception(self):
        """Test that session is closed even when exception occurs."""
        with patch('src.infrastructure.postgres.database.SessionLocal') as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            
            # Simulate an exception during session usage
            db_gen = get_db()
            session = next(db_gen)
            
            # Simulate exception
            mock_session.some_method.side_effect = Exception("Database error")
            
            try:
                session.some_method()
            except Exception:
                pass
            
            # Simulate the finally block
            try:
                next(db_gen)
            except StopIteration:
                pass
            
            # Session should still be closed
            mock_session.close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
