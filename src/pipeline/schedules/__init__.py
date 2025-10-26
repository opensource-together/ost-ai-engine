"""Schedules package for src.pipeline.

This module exposes schedule factory functions so callers can import
from `src.pipeline.schedules` directly. Keeping a small __init__ helps
tools and improves import ergonomics.
"""

from .github import make_github_scraper_schedule

__all__ = ["make_github_scraper_schedule"]
