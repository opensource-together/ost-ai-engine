"""Utilities shim: re-export prisma_client from the services package.

We moved the real implementation here. Keep the module small so
imports throughout the repo can import `prisma_client` from
`src.pipeline.utils`.
"""

from src.services.python.prisma_client import prisma_client

# Ré-exporter PipelineConfig pour y accéder via src.pipeline.utils
try:
	from src.services.python.load_cfg import PipelineConfig
except Exception:  # pragma: no cover - defensive: keep utils import-safe
	PipelineConfig = None

__all__ = ["prisma_client", "PipelineConfig"]
