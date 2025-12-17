"""Utilities shim: re-export prisma_client from the services package.

We moved the real implementation here. Keep the module small so
imports throughout the repo can import `prisma_client` from
`src.pipeline.utils`.
"""

from src.services.python.load_cfg import PipelineConfig

__all__ = ["PipelineConfig"]
