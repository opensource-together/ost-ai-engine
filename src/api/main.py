from fastapi import FastAPI

app = FastAPI(
    title="Data Engine API",
    description="API for the recommendation engine.",
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to ensure the API is running.
    """
    return {"status": "ok"} 