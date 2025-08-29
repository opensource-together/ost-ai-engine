# OST Data Engine - Documentation

## 🏗️ Architecture Overview

The OST Data Engine is a comprehensive recommendation system that combines machine learning pipelines with high-performance APIs to provide personalized project recommendations.

### **Core Components**

- **🤖 ML Pipeline** (Python/Dagster): Generates embeddings and calculates similarities
- **🚀 Go API**: High-performance REST API for recommendations
- **🗄️ PostgreSQL**: Vector storage with pgvector extension
- **⚡ Redis**: Optional caching layer for performance

### **Data Flow**

```
GitHub Data → ML Pipeline → Embeddings → Similarities → Go API → Recommendations
```

## 📚 Documentation Structure

### **Getting Started**
- [Quick Start Guide](deployment/quick-start.md)
- [Environment Configuration](deployment/environment.md)

### **API Documentation**
- [REST API Reference](api/rest-api.md)
- [Go API Implementation](api/go-api.md)
- [API Examples](api/examples.md)

### **ML Pipeline**
- [Pipeline Overview](ml-pipeline/overview.md)
- [Dagster Assets](ml-pipeline/dagster-assets.md)
- [Embedding Generation](ml-pipeline/embeddings.md)
- [Similarity Calculations](ml-pipeline/similarity.md)

### **Database**
- [Schema Documentation](database/schema.md)
- [Vector Operations](database/vector-operations.md)
- [Performance Optimization](database/performance.md)

### **Deployment**
- [Production Setup](deployment/production.md)
- [Monitoring](deployment/monitoring.md)
- [Troubleshooting](deployment/troubleshooting.md)

## 🚀 Quick Start

1. **Setup Environment**
   ```bash
   cp .env.example .env
   # Configure your environment variables
   ```

2. **Run ML Pipeline**
   ```bash
   dagster asset materialize --select user_project_similarities
   ```

3. **Start Go API**
   ```bash
   cd src/api/go
   go build -o recommendations-api recommendations.go
   ./recommendations-api
   ```

4. **Test API**
   ```bash
   curl "http://localhost:8080/recommendations?user_id={USER_ID}"
   ```

## 🔧 Configuration

All configuration is managed through environment variables. See [Environment Configuration](deployment/environment.md) for details.

## 📊 Performance

- **ML Pipeline**: ~30-60 seconds for full similarity calculation
- **API Response**: <10ms latency
- **Throughput**: 1000+ requests/second
- **Cache**: <1ms (Redis)

## 🤝 Contributing

1. Follow the existing code structure
2. Use environment variables for configuration
3. Add comprehensive logging
4. Update documentation for new features
