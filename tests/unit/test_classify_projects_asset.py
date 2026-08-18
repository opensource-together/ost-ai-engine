import pytest
from unittest.mock import MagicMock, patch, call
import pandas as pd
from dagster import build_asset_context, AssetKey, Output

from src.linker.assets.classification.core_match__classify_projects import (
    _classify_one,
    core_match__classify_projects,
)
from src.linker.resources.llm_classifier_resource import (
    ClassificationResult,
    RateLimitError,
)


class TestClassifyOne:
    def test_classify_one_success(self) -> None:
        llm = MagicMock()
        llm.classify_project.return_value = ClassificationResult(
            category="Web",
            domain="Backend",
            model="test-model",
            prompt_version="v1",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
        )
        project = {"id": "1", "title": "test-project", "context": "some context"}
        cat_names = ["Web"]
        dom_names = ["Backend"]

        p, res, err, rate_limited = _classify_one(llm, project, cat_names, dom_names)

        assert p == project
        assert res.category == "Web"
        assert err is None
        assert rate_limited is False
        llm.classify_project.assert_called_once()

    @patch("time.sleep", return_value=None)
    def test_classify_one_retry_success(self, mock_sleep: MagicMock) -> None:
        llm = MagicMock()
        # First call raises RateLimitError, second succeeds
        llm.classify_project.side_effect = [
            RateLimitError("429 Too Many Requests"),
            ClassificationResult(
                category="Web",
                domain="Backend",
                model="test-model",
                prompt_version="v1",
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
            ),
        ]
        project = {"id": "1", "title": "test-project"}
        cat_names = ["Web"]
        dom_names = ["Backend"]

        p, res, err, rate_limited = _classify_one(llm, project, cat_names, dom_names)

        assert res.category == "Web"
        assert err is None
        assert rate_limited is True
        assert llm.classify_project.call_count == 2
        mock_sleep.assert_called_once()

    @patch("time.sleep", return_value=None)
    def test_classify_one_retry_failure(self, mock_sleep: MagicMock) -> None:
        llm = MagicMock()
        # Both calls fail
        llm.classify_project.side_effect = [
            RateLimitError("429 First"),
            RateLimitError("429 Second"),
        ]
        project = {"id": "1", "title": "test-project"}

        p, res, err, rate_limited = _classify_one(llm, project, ["Web"], ["Backend"])

        assert res is None
        assert isinstance(err, RateLimitError)
        assert "Second" in str(err)
        assert rate_limited is True
        assert llm.classify_project.call_count == 2

    def test_classify_one_generic_error(self) -> None:
        llm = MagicMock()
        llm.classify_project.side_effect = Exception("Generic Error")
        project = {"id": "1", "title": "test-project"}

        p, res, err, rate_limited = _classify_one(llm, project, ["Web"], ["Backend"])

        assert res is None
        assert str(err) == "Generic Error"
        assert rate_limited is False
        llm.classify_project.assert_called_once()


class TestClassifyProjectsAsset:
    @pytest.fixture
    def mock_db_cursor(self) -> MagicMock:
        cursor = MagicMock()
        # Mock Category, Domain, Already Classified, and DLQ skip
        cursor.fetchall.side_effect = [
            [{"id": 1, "name": "Web"}],  # Categories
            [{"id": 1, "name": "Backend"}],  # Domains
            [{"projectId": "already-done"}],  # Classified IDs
            [],  # DLQ skip
        ]
        return cursor

    @patch(
        "src.linker.assets.classification.core_match__classify_projects.get_db_cursor"
    )
    @patch(
        "src.linker.assets.classification.core_match__classify_projects._persist_failures",
        return_value=0,
    )
    def test_asset_full_flow(
        self, mock_persist: MagicMock, mock_get_db: MagicMock, mock_db_cursor: MagicMock
    ) -> None:
        # Mock DB context manager
        cm = MagicMock()
        cm.__enter__.return_value = mock_db_cursor
        mock_get_db.return_value = cm

        # Mock LLM Resource
        llm = MagicMock()
        llm.model_id = "mistral-small"
        llm.prompt.fingerprint = "v1-fp"
        llm.classify_project.return_value = ClassificationResult(
            category="Web",
            domain="Backend",
            model="mistral-small",
            prompt_version="v1",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
        )

        # Asset input
        df = pd.DataFrame(
            [
                {"id": "new-1", "title": "Project 1", "context": "ctx1"},
                {"id": "already-done", "title": "Project 2"},  # Should be skipped
            ]
        )

        context = build_asset_context(resources={"llm_classifier": llm})

        output = core_match__classify_projects(context, df)

        assert isinstance(output, Output)
        assert len(output.value) == 1
        assert output.value[0]["project"]["id"] == "new-1"
        assert output.metadata["count"].value == 1
        assert output.metadata["prompt_tokens"].value == 10
        assert output.metadata["completion_tokens"].value == 5
        assert output.metadata["model_version"].value == "mistral-small"

        # Verify LLM was called only once for the new project
        llm.classify_project.assert_called_once()

    @patch(
        "src.linker.assets.classification.core_match__classify_projects.get_db_cursor"
    )
    @patch(
        "src.linker.assets.classification.core_match__classify_projects._persist_failures",
        return_value=1,
    )
    def test_asset_all_failures_raise(
        self, mock_persist: MagicMock, mock_get_db: MagicMock, mock_db_cursor: MagicMock
    ) -> None:
        cm = MagicMock()
        cm.__enter__.return_value = mock_db_cursor
        mock_get_db.return_value = cm

        llm = MagicMock()
        llm.model_id = "test-model"
        llm.prompt.fingerprint = "v1-fp"
        llm.classify_project.side_effect = RuntimeError(
            "Mistral API error: Status 402 insufficient_quota"
        )

        df = pd.DataFrame([{"id": "fail-1", "title": "Failed Project"}])
        context = build_asset_context(resources={"llm_classifier": llm})

        with pytest.raises(RuntimeError, match="all 1 project"):
            core_match__classify_projects(context, df)

        mock_persist.assert_called_once()

    @patch(
        "src.linker.assets.classification.core_match__classify_projects.get_db_cursor"
    )
    @patch(
        "src.linker.assets.classification.core_match__classify_projects._persist_failures",
        return_value=1,
    )
    def test_asset_partial_failures_still_succeed(
        self, mock_persist: MagicMock, mock_get_db: MagicMock, mock_db_cursor: MagicMock
    ) -> None:
        cm = MagicMock()
        cm.__enter__.return_value = mock_db_cursor
        mock_get_db.return_value = cm

        llm = MagicMock()
        llm.model_id = "test-model"
        llm.prompt.fingerprint = "v1-fp"
        llm.classify_project.side_effect = [
            ClassificationResult(
                category="Web",
                domain="Backend",
                model="test-model",
                prompt_version="v1",
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
            ),
            Exception("transient"),
        ]

        df = pd.DataFrame(
            [
                {"id": "ok-1", "title": "Ok Project"},
                {"id": "fail-1", "title": "Failed Project"},
            ]
        )
        context = build_asset_context(resources={"llm_classifier": llm})

        output = core_match__classify_projects(context, df)

        assert len(output.value) == 1
        assert output.metadata["failed"].value == 1
        mock_persist.assert_called_once()

    @patch(
        "src.linker.assets.classification.core_match__classify_projects.get_db_cursor"
    )
    @patch(
        "src.linker.assets.classification.core_match__classify_projects._persist_failures",
        return_value=1,
    )
    def test_asset_with_unknown_labels(
        self, mock_persist: MagicMock, mock_get_db: MagicMock, mock_db_cursor: MagicMock
    ) -> None:
        cm = MagicMock()
        cm.__enter__.return_value = mock_db_cursor
        mock_get_db.return_value = cm

        llm = MagicMock()
        llm.model_id = "test-model"
        llm.prompt.fingerprint = "v1-fp"
        # Return labels not in the mock DB
        llm.classify_project.return_value = ClassificationResult(
            category="UnknownCat",
            domain="UnknownDom",
            model="test-model",
            prompt_version="v1",
            prompt_tokens=5,
            completion_tokens=5,
            total_tokens=10,
        )

        df = pd.DataFrame([{"id": "unknown-1", "title": "Unknown Project"}])
        context = build_asset_context(resources={"llm_classifier": llm})

        with pytest.raises(RuntimeError, match="all 1 project"):
            core_match__classify_projects(context, df)

        mock_persist.assert_called_once()
