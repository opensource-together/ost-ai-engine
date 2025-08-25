"""
Pipeline infrastructure layer - Prefect workflows for ML pipeline orchestration.

This module contains the Prefect flows and tasks that orchestrate our ML pipeline:
- Data collection (scraping)
- Feature engineering
- Model training
- Model deployment

Following our hexagonal architecture, this is an infrastructure adapter.
"""
