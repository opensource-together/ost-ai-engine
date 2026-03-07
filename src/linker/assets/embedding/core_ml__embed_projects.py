import uuid

import pandas as pd
from dagster import AssetExecutionContext, AssetIn, AssetKey, asset
from sqlalchemy import create_engine, text

# Constant for the upsert query
UPSERT_EMBEDDING_QUERY = text("""
    INSERT INTO ml.embd_github_project ("id", "projectId", "vector", "createdAt")
    VALUES (:id, :projectId, :vector, NOW())
    ON CONFLICT ("projectId")
    DO UPDATE SET
        "vector" = EXCLUDED."vector",
        "createdAt" = NOW();
""")


@asset(
    compute_kind="python",
    group_name="project_ml",
    key=AssetKey(["ml", "embd_github_project"]),
    ins={
        "projects_df": AssetIn(key=AssetKey(["ml", "int_project_embedding_candidate"]))
    },
    required_resource_keys={"config", "sentence_transformer"},
)
def core_ml__embed_projects(
    context: AssetExecutionContext,
    projects_df: pd.DataFrame,
) -> None:
    """Compute embeddings from int_project_embedding_candidate.

    Results are stored in embd_github_project.
    """
    db_url = context.resources.config.db_url
    engine = create_engine(db_url)

    # 1. Fetch raw projects with context
    df = projects_df

    context.log.info(f"Fetched {len(df)} projects to embed.")

    if df.empty:
        return

    # 2. Compute embeddings (batch)
    valid_rows = df[df["rich_context_string"].astype(bool)]
    texts = valid_rows["rich_context_string"].tolist()
    project_ids = valid_rows["project_id"].tolist()

    sentence_transformer = context.resources.sentence_transformer
    vectors = sentence_transformer.encode_batch(texts) if texts else []
    context.log.info(f"Computed {len(vectors)} embeddings.")

    embeddings = [
        {"id": str(uuid.uuid4()), "projectId": pid, "vector": vec}
        for pid, vec in zip(project_ids, vectors, strict=False)
    ]

    context.log.info(f"Total embeddings computed: {len(embeddings)}")

    if not embeddings:
        return

    # 3. Store in DB (Upsert logic)
    context.log.info(f"Upserting {len(embeddings)} embeddings...")

    with engine.connect() as conn, conn.begin():
        for item in embeddings:
            # Convert list to string representation for postgres vector constraint
            vector_str = str(item["vector"])

            conn.execute(
                UPSERT_EMBEDDING_QUERY,
                {
                    "id": item["id"],
                    "projectId": item["projectId"],
                    "vector": vector_str,
                },
            )

    context.log.info("Successfully upserted embeddings to ml.embd_github_project.")
