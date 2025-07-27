"""
Unit tests for data loader infrastructure.

Tests critical production functionality: session management, data formatting,
error handling, and DataFrame structure for ML pipeline.
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from src.infrastructure.postgres.data_loader import load_projects_to_dataframe


class TestDataLoaderSessionManagement:
    """Test critical session management for production."""

    @patch('src.infrastructure.postgres.data_loader.SessionLocal')
    def test_session_is_always_closed(self, mock_session_local):
        """Test that database session is always closed, even on errors."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        # Simulate successful load
        mock_df = pd.DataFrame({'id': [1, 2], 'title': ['A', 'B'], 'description': ['Desc1', 'Desc2']})
        mock_session.query.return_value.statement = "SELECT * FROM projects"
        mock_session.bind = MagicMock()
        
        with patch('pandas.read_sql', return_value=mock_df):
            load_projects_to_dataframe()
        
        # Session should be closed
        mock_session.close.assert_called_once()

    @patch('src.infrastructure.postgres.data_loader.SessionLocal')
    def test_session_closed_on_exception(self, mock_session_local):
        """Test that session is closed even when exception occurs."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(SQLAlchemyError):
            load_projects_to_dataframe()
        
        # Session should still be closed
        mock_session.close.assert_called_once()


class TestDataLoaderDataFormatting:
    """Test critical data formatting for ML pipeline."""

    @patch('src.infrastructure.postgres.data_loader.SessionLocal')
    def test_id_column_converted_to_string(self, mock_session_local):
        """Test that id column is converted to string for ML consistency."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        # Create test data with integer IDs
        test_data = pd.DataFrame({
            'id': [1, 2, 3],
            'title': ['Project A', 'Project B', 'Project C'],
            'description': ['Desc A', 'Desc B', 'Desc C']
        })
        
        mock_session.query.return_value.statement = "SELECT * FROM projects"
        mock_session.bind = MagicMock()
        
        with patch('pandas.read_sql', return_value=test_data):
            result_df = load_projects_to_dataframe()
        
        # ID column should be string type
        assert result_df['id'].dtype == 'object'  # pandas string type
        assert all(isinstance(id_val, str) for id_val in result_df['id'])

    @patch('src.infrastructure.postgres.data_loader.SessionLocal')
    def test_required_columns_present(self, mock_session_local):
        """Test that required columns for ML pipeline are present."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        test_data = pd.DataFrame({
            'id': [1, 2],
            'title': ['Project A', 'Project B'],
            'description': ['Desc A', 'Desc B']
        })
        
        mock_session.query.return_value.statement = "SELECT * FROM projects"
        mock_session.bind = MagicMock()
        
        with patch('pandas.read_sql', return_value=test_data):
            result_df = load_projects_to_dataframe()
        
        # Required columns for ML pipeline
        required_columns = ['id', 'title', 'description']
        for col in required_columns:
            assert col in result_df.columns, f"Required column '{col}' missing"

    @patch('src.infrastructure.postgres.data_loader.SessionLocal')
    def test_returns_dataframe(self, mock_session_local):
        """Test that function returns a pandas DataFrame."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        test_data = pd.DataFrame({
            'id': [1],
            'title': ['Project A'],
            'description': ['Desc A']
        })
        
        mock_session.query.return_value.statement = "SELECT * FROM projects"
        mock_session.bind = MagicMock()
        
        with patch('pandas.read_sql', return_value=test_data):
            result = load_projects_to_dataframe()
        
        # Should return DataFrame
        assert isinstance(result, pd.DataFrame)
        assert not result.empty


class TestDataLoaderErrorHandling:
    """Test critical error handling for production."""

    @patch('src.infrastructure.postgres.data_loader.SessionLocal')
    def test_database_connection_error(self, mock_session_local):
        """Test handling of database connection errors."""
        mock_session_local.side_effect = SQLAlchemyError("Connection failed")
        
        with pytest.raises(SQLAlchemyError, match="Connection failed"):
            load_projects_to_dataframe()

    @patch('src.infrastructure.postgres.data_loader.SessionLocal')
    def test_query_execution_error(self, mock_session_local):
        """Test handling of query execution errors."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.side_effect = SQLAlchemyError("Query failed")
        
        with pytest.raises(SQLAlchemyError, match="Query failed"):
            load_projects_to_dataframe()

    @patch('src.infrastructure.postgres.data_loader.SessionLocal')
    def test_pandas_read_sql_error(self, mock_session_local):
        """Test handling of pandas read_sql errors."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.statement = "SELECT * FROM projects"
        mock_session.bind = MagicMock()
        
        with patch('pandas.read_sql', side_effect=Exception("Pandas error")):
            with pytest.raises(Exception, match="Pandas error"):
                load_projects_to_dataframe()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
