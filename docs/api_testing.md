# API Testing & Documentation

## FastAPI Swagger UI

### Accessing the API Documentation

Once the API server is running, you can access the interactive documentation:

```bash
# Start the API server
poetry run python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Access Swagger UI
http://localhost:8000/docs

# Access OpenAPI JSON schema
http://localhost:8000/openapi.json
```

### Available Endpoints

#### Health Check
- **URL**: `GET /health`
- **Purpose**: Verify API server is running
- **Response**: `{"status": "ok"}`

#### Project Recommendations
- **URL**: `GET /recommendations/{user_id}?top_n={number}`
- **Purpose**: Get personalized project recommendations for a user
- **Parameters**:
  - `user_id` (UUID): User identifier
  - `top_n` (int, optional): Number of recommendations (1-50, default: 10)
- **Response**: 
  ```json
  {
    "user_id": "uuid-string",
    "recommended_projects": ["project-id-1", "project-id-2"],
    "total_recommendations": 2
  }
  ```

## Integration Tests

### API Integration Tests (`test_api_recommendations.py`)

**Purpose**: Validate complete API functionality including HTTP behavior, request/response validation, and error handling.

#### Test Categories

1. **Health Endpoint Tests**
   - Verify health check returns 200 OK
   - Validate response format

2. **Recommendation Endpoint Tests**
   - **Success Cases**: Valid user IDs, different top_n values
   - **Validation**: UUID format, top_n range (1-50)
   - **Error Cases**: Invalid UUIDs, non-existent users
   - **Performance**: Response time validation (< 2 seconds)

3. **Model Loading Tests**
   - **No Models**: API behavior when ML models aren't loaded
   - **Empty Projects**: Handling when no projects are available
   - **Partial Models**: Behavior with incomplete model artifacts

4. **Response Format Tests**
   - **Schema Validation**: Required fields and data types
   - **UUID Validation**: Proper UUID format in responses
   - **Error Responses**: FastAPI validation error format

### Running API Tests

```bash
# Run all API integration tests
poetry run pytest tests/integration/test_api_recommendations.py -v

# Run specific test categories
poetry run pytest tests/integration/test_api_recommendations.py::TestHealthEndpoint -v
poetry run pytest tests/integration/test_api_recommendations.py::TestRecommendationEndpoint -v
poetry run pytest tests/integration/test_api_recommendations.py::TestModelLoadingErrors -v
```

## Manual Testing with Swagger UI

### Step 1: Start the API Server
```bash
# Ensure database is populated
poetry run python scripts/populate_db.py --mock

# Start API server
poetry run python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Test Health Endpoint
1. Open `http://localhost:8000/docs`
2. Find the `/health` endpoint
3. Click "Try it out" → "Execute"
4. Verify response: `{"status": "ok"}`

### Step 3: Test Recommendations Endpoint
1. Get a valid user ID from the database:
   ```bash
   poetry run python -c "
   from src.infrastructure.postgres.database import SessionLocal
   from src.domain.models.schema import User
   db = SessionLocal()
   user = db.query(User).first()
   print(f'User ID: {user.id}')
   db.close()
   "
   ```

2. In Swagger UI:
   - Find `/recommendations/{user_id}` endpoint
   - Click "Try it out"
   - Enter the user ID in the `user_id` field
   - Set `top_n` to 5 (optional)
   - Click "Execute"
   - Verify response format and data

### Step 4: Test Error Cases
1. **Invalid UUID**: Try `user_id = "invalid-uuid"`
   - Expected: 422 Validation Error
2. **Non-existent User**: Try a random UUID
   - Expected: 404 Not Found
3. **Invalid top_n**: Try `top_n = 0` or `top_n = 51`
   - Expected: 422 Validation Error

## API Testing Best Practices

### Test Data Setup
- Use `scripts/populate_db.py --mock` for consistent test data
- Create specific test users with known interaction patterns
- Ensure ML models are loaded before testing recommendations

### Error Testing
- Test all validation scenarios (invalid UUIDs, out-of-range values)
- Test edge cases (empty results, maximum limits)
- Verify error response formats match FastAPI standards

### Performance Testing
- Monitor response times for recommendation endpoints
- Test with different `top_n` values
- Validate concurrent request handling

### Security Testing
- Test input validation and sanitization
- Verify no sensitive data exposure in responses
- Test rate limiting (if implemented)

## Troubleshooting

### Common Issues

1. **Models Not Loaded**
   ```
   Error: "models not available"
   Solution: Ensure ML models are trained and saved in models/ directory
   ```

2. **Database Connection Issues**
   ```
   Error: Database connection failed
   Solution: Check DATABASE_URL in .env and ensure PostgreSQL is running
   ```

3. **No User Data**
   ```
   Error: "No interest profile found"
   Solution: Run populate_db.py and simulate_user_interactions.py
   ```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
poetry run python -m uvicorn src.api.main:app --reload --log-level debug
```

## API Documentation Standards

### OpenAPI Specification
- Auto-generated from FastAPI decorators
- Available at `/openapi.json`
- Includes request/response schemas
- Documents all validation rules

### Response Formats
- **Success**: JSON with data payload
- **Validation Error**: 422 with detailed error messages
- **Not Found**: 404 with descriptive message
- **Server Error**: 500 with error details

### Status Codes
- `200`: Success
- `404`: Resource not found
- `422`: Validation error
- `500`: Internal server error

---

**Current Status**: ✅ **API endpoints functional with Swagger UI**
**Test Coverage**: Comprehensive integration tests for all endpoints
**Documentation**: Auto-generated OpenAPI specification 