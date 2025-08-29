# TAG Grading Scraper - Docker Setup

This document explains how to run the TAG Grading Scraper in Docker with automated scheduling.

## Overview

The Docker setup provides:
- **Automatic startup**: Pipeline runs once when container starts
- **Scheduled execution**: Configurable weekly (or custom) runs
- **Health monitoring**: Database health checks and container monitoring
- **Persistent storage**: Logs and data volumes for persistence
- **Environment configuration**: All settings via environment variables

## Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd "New Scraping Tool"
```

### 2. Configure Environment
```bash
# Copy the example environment file
cp env.example .env

# Edit .env with your settings
nano .env
```

### 3. Start the Services
```bash
# Start everything
docker-compose up -d

# View logs
docker-compose logs -f scraper

# Stop services
docker-compose down
```

## Configuration

### Environment Variables

#### Database Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `myuser` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `mypassword` | PostgreSQL password |
| `POSTGRES_DB` | `mydatabase` | PostgreSQL database name |
| `POSTGRES_PORT` | `5432` | PostgreSQL port (host) |

#### Pipeline Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `PIPELINE_MAX_CONCURRENCY` | `3` | Maximum parallel requests |
| `PIPELINE_DELAY` | `1.0` | Delay between requests (seconds) |
| `PIPELINE_CATEGORIES` | `Baseball,Hockey,Basketball,Football` | Categories to scrape |

#### Scheduling Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `PIPELINE_SCHEDULE` | `0 2 * * 0` | CRON schedule (Sundays at 2 AM) |
| `PIPELINE_TIMEZONE` | `UTC` | Timezone for scheduling |

#### Logging Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### CRON Schedule Examples

| Schedule | Description |
|----------|-------------|
| `0 2 * * 0` | Sundays at 2:00 AM (default) |
| `0 3 * * 1` | Mondays at 3:00 AM |
| `0 */6 * * *` | Every 6 hours |
| `0 2 1 * *` | 1st of every month at 2:00 AM |
| `0 0 * * *` | Daily at midnight |
| `disabled` | No scheduling (run once on startup only) |

## Docker Services

### Database Service (`db`)
- **Image**: `postgres:15`
- **Health Check**: Automatic readiness detection
- **Persistence**: Data stored in `pgdata` volume
- **Port**: Configurable via `POSTGRES_PORT`

### Scraper Service (`scraper`)
- **Base**: Playwright Python image with supercronic
- **Startup**: Runs pipeline once, then starts scheduler
- **Scheduling**: Uses supercronic for lightweight cron functionality
- **Logs**: Persistent logging to `./logs` directory
- **Data**: Persistent data storage in `./data` directory

## File Structure

```
.
├── docker-compose.yml          # Main Docker orchestration
├── Dockerfile                  # Scraper container definition
├── env.example                 # Environment configuration template
├── bin/                        # Scripts directory
│   ├── run.sh                  # Main startup script
│   └── run_pipeline.sh         # Pipeline execution script
├── logs/                       # Log files (created automatically)
├── data/                       # Data files (created automatically)
└── src/                        # Source code
```

## Usage Examples

### Basic Setup
```bash
# Start with default settings
docker-compose up -d

# View real-time logs
docker-compose logs -f scraper
```

### Custom Configuration
```bash
# Set custom categories and schedule
export PIPELINE_CATEGORIES="Baseball,Hockey"
export PIPELINE_SCHEDULE="0 3 * * 1"  # Mondays at 3 AM
export PIPELINE_MAX_CONCURRENCY=5

# Start services
docker-compose up -d
```

### Environment File
```bash
# Create .env file
cat > .env << EOF
POSTGRES_USER=scraper_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=tag_grading
PIPELINE_CATEGORIES=Baseball
PIPELINE_SCHEDULE=0 2 * * 0
PIPELINE_MAX_CONCURRENCY=3
LOG_LEVEL=INFO
EOF

# Start services
docker-compose up -d
```

### Manual Execution
```bash
# Run pipeline manually (inside container)
docker-compose exec scraper python -m scraper.pipeline --categories Baseball

# Run with custom options
docker-compose exec scraper python -m scraper.pipeline \
  --categories Baseball Hockey \
  --concurrency 5 \
  --delay 0.5
```

## Monitoring and Logs

### View Logs
```bash
# All services
docker-compose logs

# Just scraper
docker-compose logs scraper

# Follow logs in real-time
docker-compose logs -f scraper

# Last 100 lines
docker-compose logs --tail=100 scraper
```

### Health Checks
```bash
# Check service status
docker-compose ps

# Check database health
docker-compose exec db pg_isready -U myuser -d mydatabase

# Check scraper health
docker-compose exec scraper ps aux | grep supercronic
```

### Log Files
- **Container logs**: `docker-compose logs scraper`
- **Pipeline logs**: `./logs/pipeline.log`
- **Cron logs**: `./logs/cron.log`
- **Application logs**: `./logs/` directory

## Troubleshooting

### Common Issues

#### Database Connection Failed
```bash
# Check if database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Verify environment variables
docker-compose exec scraper env | grep POSTGRES
```

#### Pipeline Execution Failed
```bash
# Check pipeline logs
docker-compose logs scraper

# Run pipeline manually to debug
docker-compose exec scraper python -m scraper.pipeline --categories Baseball --verbose

# Check Python dependencies
docker-compose exec scraper pip list
```

#### Scheduling Not Working
```bash
# Check if supercronic is running
docker-compose exec scraper ps aux | grep supercronic

# Verify cron file
docker-compose exec scraper cat /app/bin/cron.txt

# Check cron logs
docker-compose exec scraper tail -f /app/logs/cron.log
```

### Debug Mode
```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG

# Restart services
docker-compose restart scraper

# Follow logs
docker-compose logs -f scraper
```

### Reset Everything
```bash
# Stop and remove everything
docker-compose down -v

# Remove all images
docker-compose down --rmi all

# Start fresh
docker-compose up -d
```

## Production Considerations

### Security
- Use strong passwords for database
- Consider using Docker secrets for sensitive data
- Restrict network access to database port
- Use non-root user in container (already implemented)

### Performance
- Adjust `PIPELINE_MAX_CONCURRENCY` based on server resources
- Monitor memory usage during scraping
- Consider using `PIPELINE_DELAY` to avoid overwhelming target site
- Use appropriate `PIPELINE_SCHEDULE` for your use case

### Monitoring
- Set up log aggregation (ELK stack, etc.)
- Monitor container resource usage
- Set up alerts for pipeline failures
- Track database growth and performance

### Backup
- Regular database backups
- Log rotation and archival
- Volume backup for persistent data
- Consider using Docker volumes for easier backup

## Advanced Configuration

### Custom Schedules
```bash
# Run every 4 hours
export PIPELINE_SCHEDULE="0 */4 * * *"

# Run on specific days
export PIPELINE_SCHEDULE="0 2 * * 1,3,5"  # Mon, Wed, Fri at 2 AM

# Run multiple times per day
export PIPELINE_SCHEDULE="0 2,14 * * *"   # 2 AM and 2 PM daily
```

### Multiple Categories
```bash
# Scrape specific categories
export PIPELINE_CATEGORIES="Baseball,Hockey"

# Scrape all discovered categories
export PIPELINE_CATEGORIES="discover"
```

### Resource Limits
```yaml
# In docker-compose.yml
services:
  scraper:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
```

## Support

For issues and questions:
1. Check the logs: `docker-compose logs scraper`
2. Verify configuration: `docker-compose exec scraper env`
3. Test manually: `docker-compose exec scraper python -m scraper.pipeline --help`
4. Check this documentation for common solutions

The Docker setup is designed to be production-ready with proper error handling, logging, and monitoring capabilities.
