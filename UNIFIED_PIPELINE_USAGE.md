# Unified TAG Grading Pipeline - Usage Guide

## 🚀 Overview

The Unified TAG Grading Pipeline consolidates all scraping functionality into a single, optimized command with comprehensive error handling, audit logging, and multi-runner support. This replaces the previous scattered pipeline implementations with a unified, production-ready solution.

## ✨ Key Features

- **🔍 Dynamic Discovery**: Automatically discovers all categories, years, sets, and cards
- **🛡️ Error Handling**: Comprehensive retry logic with exponential backoff and jitter
- **📊 Audit Logging**: Database audit trail for all operations with runner identification
- **🔄 Multi-Runner Support**: Coordinate multiple pipeline instances for high throughput
- **📈 Progress Tracking**: Real-time statistics and comprehensive reporting
- **⚡ Performance**: Optimized concurrency and rate limiting
- **🐳 Docker Ready**: Full Docker support with environment-based configuration

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Unified Pipeline                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Runner 1  │  │   Runner 2  │  │   Runner N  │        │
│  │ (Concurrency│  │ (Concurrency│  │ (Concurrency│        │
│  │   Control)  │  │   Control)  │  │   Control)  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│              Multi-Level Orchestrator                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Years     │  │    Sets     │  │    Cards    │        │
│  │ Discovery   │  │ Discovery   │  │ Discovery   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│              Audit Logger + Database                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Operations │  │    Errors   │  │   Results   │        │
│  │    Log      │  │     Log     │  │     Log     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. **Single Pipeline Run**

```bash
# Basic run with default settings
python src/scraper/unified_pipeline.py

# Run with custom configuration
python src/scraper/unified_pipeline.py \
  --concurrency 5 \
  --delay 2.0 \
  --max-retries 3 \
  --retry-backoff 2.0 \
  --log-level DEBUG
```

### 2. **Multi-Runner Orchestration**

```bash
# Run with 3 concurrent runners
python src/scraper/multi_runner_orchestrator.py \
  --num-runners 3 \
  --concurrency 2 \
  --delay 1.0

# High-throughput configuration
python src/scraper/multi_runner_orchestrator.py \
  --num-runners 5 \
  --concurrency 4 \
  --delay 0.5 \
  --max-retries 2
```

### 3. **Docker Deployment**

```bash
# Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f scraper

# Stop services
docker-compose down
```

## ⚙️ Configuration Options

### **Pipeline Configuration**

| Option | Default | Description |
|--------|---------|-------------|
| `--concurrency` | 3 | Number of concurrent workers per runner |
| `--delay` | 1.0 | Delay between requests in seconds |
| `--max-retries` | 3 | Maximum retry attempts for failed operations |
| `--retry-backoff` | 2.0 | Exponential backoff multiplier |
| `--dry-run` | False | Run without database writes (testing mode) |
| `--log-level` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

### **Execution Options**

| Option | Default | Description |
|--------|---------|-------------|
| `--start-from` | category | Start scraping from this level |
| `--year-filter` | None | Filter to specific years |
| `--set-filter` | None | Filter to specific sets |
| `--card-filter` | None | Filter to specific cards |
| `--runner-id` | Auto | Unique identifier for this runner |

### **Multi-Runner Configuration**

| Option | Default | Description |
|--------|---------|-------------|
| `--num-runners` | 3 | Number of concurrent pipeline runners |
| `--check-interval` | 10.0 | Status check interval in seconds |
| `--working-directory` | . | Working directory for runners |
| `--python-path` | python | Python executable path |

## 📊 Usage Examples

### **Example 1: Development Testing**

```bash
# Quick test with minimal load
python src/scraper/unified_pipeline.py \
  --dry-run \
  --concurrency 1 \
  --delay 5.0 \
  --log-level DEBUG
```

**Use Case**: Testing pipeline functionality without affecting production data

### **Example 2: Production Scraping**

```bash
# Production configuration with balanced performance
python src/scraper/unified_pipeline.py \
  --concurrency 3 \
  --delay 2.0 \
  --max-retries 3 \
  --retry-backoff 2.0 \
  --log-level INFO
```

**Use Case**: Regular production data collection with error handling

### **Example 3: High-Throughput Processing**

```bash
# Multi-runner high-throughput configuration
python src/scraper/multi_runner_orchestrator.py \
  --num-runners 5 \
  --concurrency 4 \
  --delay 1.0 \
  --max-retries 2 \
  --check-interval 5.0
```

**Use Case**: Large-scale data collection with multiple coordinated runners

### **Example 4: Targeted Scraping**

```bash
# Focus on specific sports or years
python src/scraper/unified_pipeline.py \
  --categories Baseball,Hockey \
  --concurrency 2 \
  --delay 1.5
```

**Use Case**: Targeted data collection for specific analysis needs

## 🔧 Environment Configuration

### **Basic Configuration (.env)**

```bash
# Pipeline Configuration
PIPELINE_MAX_CONCURRENCY=3
PIPELINE_DELAY=2.0
PIPELINE_CATEGORIES=discover
PIPELINE_MAX_RETRIES=3
PIPELINE_RETRY_BACKOFF=2.0

# Scheduling Configuration
PIPELINE_SCHEDULE=0 2 * * 0
PIPELINE_TIMEZONE=UTC

# Logging Configuration
LOG_LEVEL=INFO
```

### **Advanced Configuration**

```bash
# High-performance configuration
PIPELINE_MAX_CONCURRENCY=5
PIPELINE_DELAY=1.0
PIPELINE_MAX_RETRIES=2
PIPELINE_RETRY_BACKOFF=1.5

# Conservative configuration
PIPELINE_MAX_CONCURRENCY=2
PIPELINE_DELAY=3.0
PIPELINE_MAX_RETRIES=5
PIPELINE_RETRY_BACKOFF=3.0
```

## 📈 Performance Tuning

### **Concurrency Guidelines**

| Server Resources | Recommended Concurrency | Notes |
|------------------|------------------------|-------|
| 2 vCPU, 4GB RAM | 2-3 | Conservative, stable |
| 4 vCPU, 8GB RAM | 4-6 | Balanced performance |
| 8 vCPU, 16GB RAM | 8-12 | High throughput |
| 16+ vCPU, 32GB+ RAM | 12-20 | Maximum throughput |

### **Rate Limiting Guidelines**

| Target Website | Recommended Delay | Notes |
|----------------|-------------------|-------|
| TAG Grading | 1.0-2.0s | Respectful scraping |
| High-traffic sites | 0.5-1.0s | Aggressive but safe |
| Rate-limited sites | 2.0-5.0s | Conservative approach |

### **Retry Configuration**

| Network Quality | Max Retries | Backoff | Notes |
|----------------|-------------|---------|-------|
| Excellent | 2 | 1.5 | Fast recovery |
| Good | 3 | 2.0 | Balanced approach |
| Poor | 5 | 3.0 | Conservative recovery |

## 🐳 Docker Deployment

### **Basic Docker Setup**

```bash
# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f scraper

# Stop services
docker-compose down
```

### **Custom Docker Configuration**

```bash
# Override environment variables
export PIPELINE_MAX_CONCURRENCY=5
export PIPELINE_DELAY=1.0
export PIPELINE_MAX_RETRIES=3

# Start with custom settings
docker-compose up -d
```

### **Docker Health Monitoring**

```bash
# Check container health
docker-compose ps

# Monitor resource usage
docker stats

# Check logs for errors
docker-compose logs scraper | grep ERROR
```

## 🔍 Monitoring and Debugging

### **Real-Time Monitoring**

```bash
# Follow pipeline logs
docker-compose logs -f scraper

# Check specific runner logs
docker-compose logs scraper | grep "runner_1"

# Monitor audit logs
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB \
  -c "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10;"
```

### **Performance Metrics**

```bash
# Check pipeline statistics
docker-compose exec scraper python -c "
from scraper.unified_pipeline import UnifiedPipeline, PipelineConfig
config = PipelineConfig()
pipeline = UnifiedPipeline(config)
print(f'Pipeline initialized: {config}')
"

# Monitor database performance
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB \
  -c "SELECT COUNT(*) FROM audit_logs WHERE created_at > NOW() - INTERVAL '1 hour';"
```

### **Error Investigation**

```bash
# Check for recent errors
docker-compose logs scraper | grep -i error | tail -20

# View audit log errors
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB \
  -c "SELECT * FROM audit_logs WHERE level = 'ERROR' ORDER BY created_at DESC LIMIT 10;"

# Check runner status
docker-compose exec scraper ps aux | grep python
```

## 🧪 Testing

### **Run Test Suite**

```bash
# Run comprehensive tests
python src/test_unified_pipeline.py

# Test specific functionality
python src/test_unified_pipeline.py --help

# Run with verbose output
python src/test_unified_pipeline.py --verbose
```

### **Dry Run Testing**

```bash
# Test pipeline without database writes
python src/scraper/unified_pipeline.py \
  --dry-run \
  --concurrency 1 \
  --delay 0.1

# Test multi-runner orchestration
python src/scraper/multi_runner_orchestrator.py \
  --num-runners 2 \
  --concurrency 1 \
  --delay 0.1 \
  --check-interval 5.0
```

## 🚨 Troubleshooting

### **Common Issues**

#### **Pipeline Won't Start**

```bash
# Check dependencies
pip install -r requirements.txt

# Verify database connection
python -c "from src.db import SessionLocal; print('DB OK')"

# Check file permissions
ls -la src/scraper/unified_pipeline.py
```

#### **Database Connection Errors**

```bash
# Verify database is running
docker-compose ps db

# Check environment variables
docker-compose exec scraper env | grep POSTGRES

# Test database connectivity
docker-compose exec scraper python -c "
from src.db import SessionLocal
session = SessionLocal()
print('Database connection successful')
session.close()
"
```

#### **Performance Issues**

```bash
# Reduce concurrency
export PIPELINE_MAX_CONCURRENCY=2

# Increase delays
export PIPELINE_DELAY=3.0

# Check system resources
docker stats
```

#### **Audit Logging Issues**

```bash
# Verify audit table exists
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB \
  -c "\dt audit_logs"

# Check table permissions
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB \
  -c "SELECT * FROM audit_logs LIMIT 1;"
```

## 📚 Advanced Usage

### **Custom Runner Configuration**

```python
from scraper.multi_runner_orchestrator import MultiRunnerOrchestrator, RunnerConfig

# Create custom configuration
config = RunnerConfig(
    runner_id="custom_runner",
    concurrency=5,
    delay=1.0,
    max_retries=3,
    retry_backoff=2.0
)

# Run orchestration
orchestrator = MultiRunnerOrchestrator(config, num_runners=3)
results = orchestrator.run_orchestration()
```

### **Programmatic Pipeline Usage**

```python
from scraper.unified_pipeline import UnifiedPipeline, PipelineConfig

# Create configuration
config = PipelineConfig(
    concurrency=3,
    delay=2.0,
    max_retries=3,
    retry_backoff=2.0,
    dry_run=False
)

# Run pipeline
pipeline = UnifiedPipeline(config)
with pipeline.get_session():
    results = pipeline.run_pipeline()
    print(f"Pipeline completed: {results}")
```

### **Custom Audit Logging**

```python
from scraper.unified_pipeline import AuditLogger

# Create audit logger
audit_logger = AuditLogger(session, runner_id="custom_runner")

# Log custom operations
audit_logger.log_operation("INFO", "Custom operation started", {
    'operation_type': 'custom',
    'parameters': {'param1': 'value1'}
})

# Log errors with context
audit_logger.log_error("custom_operation", "Operation failed", {
    'operation_type': 'custom',
    'error_details': 'Detailed error information'
})
```

## 🎯 Best Practices

### **Production Deployment**

1. **Start Conservative**: Begin with low concurrency and increase gradually
2. **Monitor Resources**: Watch CPU, memory, and database performance
3. **Use Retry Logic**: Configure appropriate retry settings for your network
4. **Audit Everything**: Ensure all operations are logged for debugging
5. **Test Thoroughly**: Use dry-run mode for testing new configurations

### **Performance Optimization**

1. **Balance Concurrency**: Find the sweet spot between speed and stability
2. **Respect Rate Limits**: Don't overwhelm target websites
3. **Use Multi-Runners**: Distribute load across multiple instances
4. **Monitor Bottlenecks**: Identify and resolve performance bottlenecks
5. **Optimize Database**: Use appropriate indexes and connection pooling

### **Error Handling**

1. **Configure Retries**: Set appropriate retry counts and backoff
2. **Log Everything**: Ensure all errors are captured in audit logs
3. **Graceful Degradation**: Handle failures without stopping the entire pipeline
4. **Monitor Alerts**: Set up alerts for critical failures
5. **Regular Testing**: Test error scenarios regularly

## 🔮 Future Enhancements

### **Planned Features**

- **Real-time Dashboard**: Web-based monitoring interface
- **Advanced Scheduling**: More sophisticated scheduling options
- **Machine Learning**: ML-powered error prediction and optimization
- **API Endpoints**: REST API for pipeline control and monitoring
- **Advanced Analytics**: Detailed performance analytics and reporting

### **Extension Points**

- **Custom Scrapers**: Plugin system for custom scraping logic
- **Data Exporters**: Multiple export format support
- **Notification System**: Email, Slack, and webhook notifications
- **Backup Integration**: Automated backup and recovery
- **Cloud Integration**: Native cloud platform support

## 📞 Support

### **Getting Help**

1. **Check Documentation**: Review this guide and related documentation
2. **Run Tests**: Use the test suite to identify issues
3. **Check Logs**: Review pipeline and audit logs for error details
4. **Verify Configuration**: Ensure environment variables are set correctly
5. **Test Incrementally**: Start with simple configurations and build up

### **Reporting Issues**

When reporting issues, please include:

- **Configuration**: Environment variables and command-line options
- **Error Messages**: Complete error output and stack traces
- **Logs**: Relevant log entries from pipeline and audit logs
- **Environment**: Docker version, Python version, and system details
- **Steps to Reproduce**: Clear steps to reproduce the issue

---

## 🎉 Conclusion

The Unified TAG Grading Pipeline provides a robust, scalable, and maintainable solution for sports card data collection. With comprehensive error handling, audit logging, and multi-runner support, it's ready for production use at any scale.

**Happy Scraping! 🚀📊**
