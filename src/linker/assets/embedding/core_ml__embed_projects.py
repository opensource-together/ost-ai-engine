import uuid
from collections.abc import Iterator
from typing import Any

import pandas as pd
from dagster import AssetExecutionContext, AssetIn, AssetKey, asset
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

UPSERT_EMBEDDING_QUERY = text("""
    INSERT INTO ml.embd_github_project ("id", "projectId", "vector", "createdAt")
    VALUES (:id, :projectId, :vector, NOW())
    ON CONFLICT ("projectId")
    DO UPDATE SET
        "vector" = EXCLUDED."vector",
        "createdAt" = NOW();
""")


def _embed_stream(
    projects_df: Iterator[pd.DataFrame],
    sentence_transformer: Any,
    engine: Engine,
    log: Any,
) -> int:
    """Embed an iterator of DataFrames chunk-by-chunk and upsert each chunk.

    Extracted from the asset so it can be unit-tested without the Dagster
    invocation layer rebinding `context.resources`.
    """
    total_embedded = 0
    for chunk_idx, chunk in enumerate(projects_df):
        if chunk.empty:
            continue

        valid_rows = chunk[chunk["rich_context_string"].astype(bool)]
        texts = valid_rows["rich_context_string"].tolist()
        project_ids = valid_rows["project_id"].tolist()

        if not texts:
            log.info(f"Chunk {chunk_idx}: {len(chunk)} rows, 0 with context — skipped")
            continue

        vectors = sentence_transformer.encode_batch(texts)
        log.info(f"Chunk {chunk_idx}: embedded {len(vectors)}/{len(chunk)} rows")

        with engine.connect() as conn, conn.begin():
            for pid, vec in zip(project_ids, vectors, strict=False):
                conn.execute(
                    UPSERT_EMBEDDING_QUERY,
                    {
                        "id": str(uuid.uuid4()),
                        "projectId": pid,
                        "vector": str(vec),
                    },
                )

        total_embedded += len(vectors)

    return total_embedded


@asset(
    compute_kind="python",
    group_name="project_ml",
    key=AssetKey(["ml", "embd_github_project"]),
    ins={
        "projects_df": AssetIn(
            key=AssetKey(["ml", "int_project_embedding_candidate"]),
            input_manager_key="streaming_io_manager",
        )
    },
    required_resource_keys={"config", "sentence_transformer"},
)
def core_ml__embed_projects(
    context: AssetExecutionContext,
    projects_df: Any,
) -> None:
    """Stream embeddings chunk-by-chunk from int_project_embedding_candidate.

    `projects_df` is an iterator of DataFrames (streaming_io_manager), so the
    full embedding candidate table never materializes in memory.
    """
    engine = create_engine(context.resources.config.db_url)
    total = _embed_stream(
        projects_df=projects_df,
        sentence_transformer=context.resources.sentence_transformer,
        engine=engine,
        log=context.log,
    )
    context.log.info(f"Finished streaming embed: {total} total embeddings upserted.")
