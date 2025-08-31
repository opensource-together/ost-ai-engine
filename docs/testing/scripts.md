# Test Scripts Documentation

## Overview

The OST Data Engine includes several scripts to support testing and development workflows.

## Scripts Directory

```
scripts/
├── setup_test_data_fallback.py     # Fallback for test data creation
└── database/                       # Database setup scripts
    ├── create_test_users.py        # Create test users
    ├── populate_reference_tables.py # Populate reference data
    └── recreate_schema.sql         # Database schema recreation
```

## Test Scripts



### setup_test_data_fallback.py

**Purpose**: Create test data directly in SQL when dbt is unavailable.

**Usage**:
```bash
python scripts/setup_test_data_fallback.py
```

**Features**:
- Creates test users, projects, and similarities
- Uses direct SQL instead of dbt
- Provides fallback for CI environments
- Maintains data consistency with dbt models

**Example Output**:
```
🔧 Setting up test data using fallback method...
  ✅ Verifying setup...
  📊 Test data created:
     Users: 3
     Projects: 5
     Similarities: 15
✅ Test data setup completed using fallback method!
```

## Database Scripts

### create_test_users.py

**Purpose**: Create test users in the database for development.

**Usage**:
```bash
python scripts/database/create_test_users.py
```

**Features**:
- Creates sample users with different profiles
- Populates user data for testing
- Uses environment variables for configuration

### populate_reference_tables.py

**Purpose**: Populate reference tables with sample data.

**Usage**:
```bash
python scripts/database/populate_reference_tables.py
```

**Features**:
- Creates categories and tech stacks
- Populates association tables
- Provides realistic test data

### recreate_schema.sql

**Purpose**: Recreate the complete database schema.

**Usage**:
```bash
psql -d OST_PROD -f scripts/database/recreate_schema.sql
```

**Features**:
- Creates all tables and indexes
- Sets up extensions (vector, uuid-ossp)
- Establishes foreign key relationships

## Integration with Testing

### pytest Integration

The test scripts integrate with pytest through fixtures:

```python
# conftest.py
@pytest.fixture(scope="session")
def setup_test_database():
    """Setup test database with minimal schema and test data using dbt."""
    # ... setup code
    
    # Run dbt models for test data
    dbt_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'dbt')
    
    try:
        # Use fallback script for test data
        fallback_script = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'setup_test_data_fallback.py')
        subprocess.run([sys.executable, fallback_script], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to setup test data: {e}")
        raise
```

### CI/CD Integration

The scripts are used in the CI pipeline:

```yaml
# .github/workflows/ci.yml
- name: Setup database schema
  run: |
    # Use fallback script for test data
    cd $GITHUB_WORKSPACE
    poetry run python scripts/setup_test_data_fallback.py
```

## Environment Configuration

### Required Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5434/OST_PROD
POSTGRES_HOST=localhost
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_PORT=5434
POSTGRES_DB=OST_PROD

# dbt
DBT_PROJECT_DIR=src/dbt
```

### Script-Specific Variables

```env
# For local development
LOG_LEVEL=INFO
ENVIRONMENT=development

# For database scripts
DB_SCHEMA=public
DB_THREADS=4
```

## Error Handling

### Common Error Scenarios

1. **Database Connection Failed**
   ```python
   # Scripts check connection before proceeding
   engine = create_engine(settings.DATABASE_URL)
   with engine.connect() as conn:
       conn.execute(text("SELECT 1"))
   ```

2. **dbt Not Available**
   ```python
   # Fallback to direct SQL
   try:
       subprocess.run(['poetry', 'run', 'dbt', 'run'], check=True)
   except subprocess.CalledProcessError:
       # Use fallback script
       subprocess.run([sys.executable, 'scripts/setup_test_data_fallback.py'])
   ```

3. **Environment Variables Missing**
   ```python
   # Scripts validate required variables
   required_vars = ['DATABASE_URL', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
   for var in required_vars:
       if not os.getenv(var):
           raise ValueError(f"Missing required environment variable: {var}")
   ```

## Best Practices

### 1. Error Handling
- All scripts include comprehensive error handling
- Graceful fallbacks when primary methods fail
- Clear error messages for debugging

### 2. Logging
- Structured logging with different levels
- Progress indicators for long-running operations
- Detailed output for troubleshooting

### 3. Configuration
- Environment-based configuration
- Validation of required variables
- Flexible settings for different environments

### 4. Testing
- Scripts are tested as part of the CI pipeline
- Integration tests verify script functionality
- Unit tests for individual script components

## Troubleshooting

### Debug Mode

Enable debug logging for scripts:

```bash
# Set debug level
export LOG_LEVEL=DEBUG

# Run script with debug output
python scripts/setup_test_data_fallback.py
```

### Common Issues

1. **Permission Denied**
   ```bash
   # Make script executable
   chmod +x scripts/setup_test_data_fallback.py
   ```

2. **Module Not Found**
   ```bash
   # Add project root to Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

3. **Database Lock**
   ```bash
   # Check for active connections
   psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity;"
   ```

### Performance Optimization

1. **Parallel Execution**
   ```python
   # Use multiple threads for database operations
   import concurrent.futures
   
   with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
       futures = [executor.submit(operation) for operation in operations]
   ```

2. **Batch Processing**
   ```python
   # Process data in batches
   batch_size = 1000
   for i in range(0, len(data), batch_size):
       batch = data[i:i + batch_size]
       process_batch(batch)
   ```

## Future Enhancements

1. **Configuration Management**
   - YAML configuration files
   - Environment-specific settings
   - Validation schemas

2. **Monitoring**
   - Performance metrics
   - Execution time tracking
   - Success/failure rates

3. **Automation**
   - Scheduled test data refresh
   - Automatic cleanup
   - Health checks
