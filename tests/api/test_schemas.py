from src.services.api.schemas import CategoryOut, ProjectOut, TechStackOut


class TestSchemas:
    def test_project_out_from_dict(self) -> None:
        """ProjectOut can be constructed from a DB row dict."""
        data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "My Project",
            "description": "A cool project",
            "repo_url": "https://github.com/org/repo",
            "published": True,
            "trending": False,
            "categories": [],
            "domains": [],
            "tech_stacks": [],
        }
        project = ProjectOut(**data)
        assert project.title == "My Project"
        assert project.categories == []

    def test_category_out(self) -> None:
        """CategoryOut holds id and name."""
        cat = CategoryOut(id="abc-123", name="Web Development")
        assert cat.name == "Web Development"

    def test_techstack_out_with_type(self) -> None:
        """TechStackOut includes type field."""
        ts = TechStackOut(id="x", name="Python", icon_url="http://img", type="LANGUAGE")
        assert ts.type == "LANGUAGE"
