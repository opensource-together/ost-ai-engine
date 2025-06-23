import pandas as pd
from sqlalchemy.orm import Session
from src.domain.models.schema import Project
from src.infrastructure.postgres.database import SessionLocal


def load_projects_to_dataframe() -> pd.DataFrame:
    """
    Fetches all projects from the database and loads them into a pandas DataFrame.

    This function is the first step in our ML training pipeline. It retrieves the
    raw data needed for feature engineering.

    Returns:
        pd.DataFrame: A DataFrame where each row is a project, containing at
                      least the project's id, title, and description.
    """
    db: Session = SessionLocal()
    try:
        # Create a SQLAlchemy query object to select the necessary columns.
        # For now, we focus on the core textual data.
        query = db.query(Project.id, Project.title, Project.description)

        # Use pandas' read_sql function for efficient loading.
        # This function directly executes the SQL query and returns a DataFrame.
        df = pd.read_sql(query.statement, query.session.bind)

        # Ensure the id column is of type string for consistency
        if "id" in df.columns:
            df["id"] = df["id"].astype(str)

        return df

    finally:
        db.close()


if __name__ == "__main__":
    # This is a simple test script to verify the function works.
    # To run it, execute `python -m src.infrastructure.postgres.data_loader`
    print("Attempting to load projects into a DataFrame...")
    projects_df = load_projects_to_dataframe()

    if not projects_df.empty:
        print("Successfully loaded projects!")
        print(f"Loaded {len(projects_df)} projects.")
        print("First 5 rows:")
        print(projects_df.head())
        print("\nDataFrame Info:")
        projects_df.info()
    else:
        print("No projects found or an error occurred.")
