# API Examples

## Basic Usage

### Get Recommendations for a User

```bash
curl "http://localhost:8080/recommendations?user_id={USER_ID}"
```

**Response:**
```json
{
  "user_id": "{USER_ID}",
  "username": "example_user",
  "recommendations": [
    {
      "project_id": "7fa66048-8fba-c6f9-2b58-1e9dfb0b34ed",
      "title": "OpenBB",
      "description": "Financial data platform for analysts, quants and AI agents.",
      "similarity_score": 0.839,
      "semantic_similarity": 0.552,
      "category_similarity": 0.333,
      "tech_similarity": 1.0,
      "popularity_score": 0.514,
      "stargazers_count": 51405,
      "primary_language": "Python",
      "categories": ["IA & Machine Learning"],
      "tech_stacks": ["Python"]
    }
  ],
  "total_count": 5,
  "generated_at": "2025-08-29T20:34:42Z"
}
```

### Format JSON Response

```bash
curl "http://localhost:8080/recommendations?user_id={USER_ID}" | jq
```

### Get Only Top 2 Recommendations

```bash
curl "http://localhost:8080/recommendations?user_id={USER_ID}" | jq '.recommendations[0:2]'
```

### Extract Specific Fields

```bash
# Get only project titles and similarity scores
curl "http://localhost:8080/recommendations?user_id={USER_ID}" | jq '.recommendations[] | {title: .title, score: .similarity_score}'

# Get projects with similarity score > 0.8
curl "http://localhost:8080/recommendations?user_id={USER_ID}" | jq '.recommendations[] | select(.similarity_score > 0.8)'
```

## Error Handling Examples

### Missing User ID

```bash
curl "http://localhost:8080/recommendations"
```

**Response:**
```json
{
  "error": "user_id parameter is required"
}
```

### Invalid User ID

```bash
curl "http://localhost:8080/recommendations?user_id=invalid-uuid"
```

**Response:**
```json
{
  "error": "Internal server error"
}
```

### User Not Found

```bash
curl "http://localhost:8080/recommendations?user_id=00000000-0000-0000-0000-000000000000"
```

**Response:**
```json
{
  "error": "Internal server error"
}
```

## Advanced Usage

### Using wget

```bash
wget -qO- "http://localhost:8080/recommendations?user_id={USER_ID}"
```

### Using Python

```python
import requests
import json

# Get recommendations
response = requests.get("http://localhost:8080/recommendations", 
                       params={"user_id": "{USER_ID}"})

if response.status_code == 200:
    data = response.json()
    print(f"Found {data['total_count']} recommendations for {data['username']}")
    
    for rec in data['recommendations']:
        print(f"- {rec['title']} (score: {rec['similarity_score']:.3f})")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### Using JavaScript/Node.js

```javascript
const fetch = require('node-fetch');

async function getRecommendations(userId) {
    try {
        const response = await fetch(`http://localhost:8080/recommendations?user_id=${userId}`);
        
        if (response.ok) {
            const data = await response.json();
            console.log(`Found ${data.total_count} recommendations for ${data.username}`);
            
            data.recommendations.forEach(rec => {
                console.log(`- ${rec.title} (score: ${rec.similarity_score.toFixed(3)})`);
            });
        } else {
            console.error(`Error: ${response.status} - ${response.statusText}`);
        }
    } catch (error) {
        console.error('Request failed:', error);
    }
}

getRecommendations('{USER_ID}');
```

### Using PowerShell

```powershell
$userId = "{USER_ID}"
$response = Invoke-RestMethod -Uri "http://localhost:8080/recommendations?user_id=$userId" -Method Get

Write-Host "Found $($response.total_count) recommendations for $($response.username)"

foreach ($rec in $response.recommendations) {
    Write-Host "- $($rec.title) (score: $([math]::Round($rec.similarity_score, 3)))"
}
```

## Testing Different Users

### Test with Different User Types

```bash
# Test with a Python developer
curl "http://localhost:8080/recommendations?user_id={PYTHON_USER_ID}" | jq '.recommendations[0:3]'

# Test with a JavaScript developer
curl "http://localhost:8080/recommendations?user_id={JS_USER_ID}" | jq '.recommendations[0:3]'

# Test with a data scientist
curl "http://localhost:8080/recommendations?user_id={DATA_SCIENCE_USER_ID}" | jq '.recommendations[0:3]'
```

### Compare Recommendations

```bash
# Compare recommendations between two users
echo "User 1 recommendations:"
curl -s "http://localhost:8080/recommendations?user_id={USER1_ID}" | jq '.recommendations[].title'

echo "User 2 recommendations:"
curl -s "http://localhost:8080/recommendations?user_id={USER2_ID}" | jq '.recommendations[].title'
```

## Performance Testing

### Load Testing

```bash
# Simple load test with Apache Bench
ab -n 100 -c 10 "http://localhost:8080/recommendations?user_id={USER_ID}"

# Using wrk for more detailed testing
wrk -t12 -c400 -d30s "http://localhost:8080/recommendations?user_id={USER_ID}"
```

### Response Time Testing

```bash
# Measure response time
time curl -s "http://localhost:8080/recommendations?user_id={USER_ID}" > /dev/null

# Multiple requests timing
for i in {1..10}; do
    echo "Request $i:"
    time curl -s "http://localhost:8080/recommendations?user_id={USER_ID}" > /dev/null
done
```

## Configuration Examples

### Different Recommendation Counts

```bash
# Set environment variable for different TOP_N values
export RECOMMENDATION_TOP_N=10
./recommendations-api

# Test with new setting
curl "http://localhost:8080/recommendations?user_id={USER_ID}" | jq '.total_count'
```

### Different Similarity Thresholds

```bash
# Set higher similarity threshold
export RECOMMENDATION_MIN_SIMILARITY=0.5
./recommendations-api

# Test with new threshold
curl "http://localhost:8080/recommendations?user_id={USER_ID}" | jq '.recommendations[].similarity_score'
```

## Troubleshooting Examples

### Check API Health

```bash
# Check if API is running
curl -I "http://localhost:8080/recommendations?user_id={USER_ID}"

# Check response headers
curl -v "http://localhost:8080/recommendations?user_id={USER_ID}"
```

### Debug Database Issues

```bash
# Test database connection
psql $DATABASE_URL -c "SELECT COUNT(*) FROM \"USER_PROJECT_SIMILARITY\";"

# Check if user exists
psql $DATABASE_URL -c "SELECT username FROM \"USER\" WHERE id = '{USER_ID}';"
```

### Monitor API Logs

```bash
# Follow API logs
tail -f logs/api.log

# Check for errors
grep "ERROR" logs/api.log
```
