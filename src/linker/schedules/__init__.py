"""Schedules package for src.linker.

This module exposes schedule factory functions so callers can import
from `src.linker.schedules` directly. Keeping a small __init__ helps
tools and improves import ergonomics.
"""

# Prefer the new module name; keep this file minimal so importing the package
# doesn't eagerly try to import heavy modules or outdated names.
from .github_scraper_schedule import make_github_scraper_schedule

__all__ = ["make_github_scraper_schedule"]
