import typing as _t
from dagster import asset, Output, MetadataValue, AssetIn
from src.services.python.prisma_client import prisma_client
from src.pipeline.assets.scraper.core.utils import _find_model

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

@asset(
    kinds={"python"},
    owners=DEFAULT_OWNERS,
    group_name="projects_embedding",
    description="Format project data from enriched metadata into a context string for embedding.",
    ins={"core_github__enrich_project_data": AssetIn()},
)
def raw_project_data(context, core_github__enrich_project_data: _t.List[_t.Dict]):
    """
    Formats the data into a single context string for each project.
    Uses enriched input data and resolves tech stack names from the DB.
    """
    context.log.info(f"raw_project_data: Starting with {len(core_github__enrich_project_data) if core_github__enrich_project_data else 0} items...")

    with prisma_client() as prisma:
        if prisma is None:
            context.log.error("Failed to connect to Prisma.")
            # We can't resolve tech stacks without DB, but maybe we can still proceed with empty stacks?
            # Or just fail/return empty. Let's return empty to be safe.
            return Output(value=[], metadata={"error": MetadataValue.text("Prisma client unavailable")})

        # Fetch all TechStacks to map IDs to Names
        ts_map = {}
        model_ts = _find_model(prisma, ["tech_stack", "TechStack", "techStack", "techstack"])
        if model_ts:
            try:
                all_ts = model_ts.find_many()
                for ts in all_ts:
                    ts_map[ts.id] = ts.name
            except Exception as e:
                context.log.warning(f"Failed to fetch TechStacks: {e}")

    results = []
    for item in core_github__enrich_project_data or []:
        project = item.get("project") or {}
        repo_url = item.get("repoUrl")
        
        if not repo_url:
            continue

        # Resolve Tech Stack names
        tech_stack_ids = item.get("tech_stack_ids") or []
        tech_stack_names = []
        for ts_id in tech_stack_ids:
            name = ts_map.get(ts_id)
            if name:
                tech_stack_names.append(name)
        
        tech_stacks_str = ", ".join(tech_stack_names)
        
        description = project.get("description") or ""
        title = project.get("title") or project.get("name") or "" # Fallback to name if title missing
        readme = item.get("readme") or ""
        topics = item.get("topics") or []
        topics_str = ", ".join(topics)
        
        context_str = f"""
Title: {title}
Description: {description}
Tech Stacks: {tech_stacks_str}
Topics: {topics_str}
Readme: {readme}
""".strip()

        results.append({
            "repoUrl": repo_url,
            "context": context_str
        })

    context.log.info(f"raw_project_data: Formatted {len(results)} project contexts.")

    return Output(
        value=results,
        metadata={
            "project_count": MetadataValue.int(len(results)),
            "status": MetadataValue.text("success"),
            "sample_output": MetadataValue.json(results[0]) if results else MetadataValue.null(),
        }
    )
