# TAG Grading Scraper - Docker Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the TAG Grading Scraper in cloud environments using Docker and Docker Compose. The system is designed to be production-ready with proper security, monitoring, and scalability considerations.

## Prerequisites

### System Requirements
- **Operating System**: Linux (Ubuntu 20.04+ recommended) or macOS
- **Docker**: Version 20.10+ with Docker Compose
- **Memory**: Minimum 4GB RAM (8GB+ recommended)
- **Storage**: Minimum 20GB available disk space
- **Network**: Internet access for scraping operations

### Required Software
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

## Security Configuration

### 1. Environment Variables Setup

**IMPORTANT**: Never commit sensitive credentials to version control. Always use environment variables for production deployments.

Create a secure `.env` file:

```bash
# Copy the example environment file
cp env.example .env

# Edit with secure values
nano .env
```

#### Production Environment Variables

```bash
# Database Configuration - USE STRONG PASSWORDS IN PRODUCTION
POSTGRES_USER=tag_scraper_user
POSTGRES_PASSWORD=YourSuperSecurePassword123!
POSTGRES_DB=tag_grading_db
POSTGRES_PORT=5432

# Pipeline Configuration
PIPELINE_MAX_CONCURRENCY=5
PIPELINE_DELAY=2.0
# Use 'discover' to automatically find all available categories
# Or specify specific categories: Baseball,Hockey,Basketball,Football,Soccer,Golf,Racing,Wrestling,Gaming,Non-Sport
PIPELINE_CATEGORIES=discover

# Scheduling Configuration
PIPELINE_SCHEDULE=0 2 * * 0
PIPELINE_TIMEZONE=UTC

# Logging Configuration
LOG_LEVEL=INFO

# Health Check Configuration
HEALTH_CHECK_INTERVAL=300
```

### 2. Database Security Best Practices

#### Strong Password Requirements
- **Minimum 16 characters**
- **Mix of uppercase, lowercase, numbers, and special characters**
- **Avoid dictionary words and common patterns**
- **Use a password manager for secure generation**

#### Network Security
```bash
# Restrict database access to internal network only
# In production, consider using Docker networks or VPN
POSTGRES_HOST_AUTH_METHOD=scram-sha-256
```

#### SSL Configuration (Production)
```yaml
# Add to docker-compose.yml for production
services:
  db:
    environment:
      POSTGRES_SSL_MODE: require
      POSTGRES_SSL_CERT: /etc/ssl/certs/server.crt
      POSTGRES_SSL_KEY: /etc/ssl/private/server.key
```

### 3. File Permissions
```bash
# Secure file permissions
chmod 600 .env
chmod 600 docker-compose.yml
chmod 700 logs/
chmod 700 data/
```

## Cloud Deployment

### 1. AWS EC2 Deployment

#### Launch EC2 Instance
```bash
# Launch Ubuntu 20.04 LTS instance
# Instance Type: t3.medium (2 vCPU, 4GB RAM) minimum
# Storage: 30GB GP2 SSD
# Security Group: Allow SSH (port 22) from your IP only
```

#### Install Docker on EC2
```bash
# Connect to your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again for group changes to take effect
exit
```

#### Deploy Application
```bash
# Clone repository
git clone <your-repo-url>
cd "New Scraping Tool"

# Create secure environment file
cp env.example .env
nano .env  # Edit with secure values

# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
```

### 2. Google Cloud Platform (GCP) Deployment

#### Create GCP Instance
```bash
# Create Compute Engine instance
gcloud compute instances create tag-scraper \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=30GB \
  --tags=http-server,https-server

# Allow firewall rules
gcloud compute firewall-rules create allow-ssh \
  --allow tcp:22 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=allow-ssh
```

#### Deploy Application
```bash
# SSH to instance
gcloud compute ssh tag-scraper --zone=us-central1-a

# Follow same Docker installation steps as EC2
# Deploy application using docker-compose
```

### 3. Azure VM Deployment

#### Create Azure VM
```bash
# Create resource group
az group create --name tag-scraper-rg --location eastus

# Create VM
az vm create \
  --resource-group tag-scraper-rg \
  --name tag-scraper-vm \
  --image UbuntuLTS \
  --size Standard_D2s_v3 \
  --admin-username azureuser \
  --generate-ssh-keys

# Open port 22
az vm open-port --port 22 --resource-group tag-scraper-rg --name tag-scraper-vm
```

#### Deploy Application
```bash
# SSH to VM
ssh azureuser@<vm-public-ip>

# Follow Docker installation and deployment steps
```

## Production Deployment Checklist

### Security
- [ ] Strong database passwords configured
- [ ] Environment variables secured
- [ ] File permissions restricted
- [ ] Network access limited
- [ ] SSL certificates configured (if needed)
- [ ] Regular security updates enabled

### Monitoring
- [ ] Log aggregation configured
- [ ] Health checks enabled
- [ ] Resource monitoring setup
- [ ] Alert notifications configured
- [ ] Backup strategy implemented

### Performance
- [ ] Resource limits configured
- [ ] Database connection pooling
- [ ] Caching strategy implemented
- [ ] Load balancing configured (if needed)

## Maintenance and Operations

### 1. Regular Maintenance Tasks

#### Database Maintenance
```bash
# Connect to database container
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB

# Run maintenance commands
VACUUM ANALYZE;
REINDEX DATABASE tag_grading_db;
```

#### Log Rotation
```bash
# Configure logrotate for production
sudo nano /etc/logrotate.d/tag-scraper

# Add configuration
/app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
}
```

#### Backup Strategy
```bash
# Create backup script
nano backup.sh

#!/bin/bash
BACKUP_DIR="/backups/tag-scraper"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
docker-compose exec -T db pg_dump -U $POSTGRES_USER $POSTGRES_DB > $BACKUP_DIR/db_backup_$DATE.sql

# Application data backup
tar -czf $BACKUP_DIR/app_data_$DATE.tar.gz data/ logs/

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

# Make executable
chmod +x backup.sh

# Add to crontab for daily backups
crontab -e
# Add: 0 1 * * * /path/to/backup.sh
```

### 2. Scaling Considerations

#### Horizontal Scaling
```yaml
# docker-compose.yml with multiple scraper instances
services:
  scraper:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
```

#### Load Balancing
```yaml
# Add nginx load balancer
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - scraper
```

### 3. Troubleshooting

#### Common Issues

**Database Connection Issues**
```bash
# Check database status
docker-compose exec db pg_isready -U $POSTGRES_USER

# Check logs
docker-compose logs db

# Restart database
docker-compose restart db
```

**Scraper Performance Issues**
```bash
# Check resource usage
docker stats

# Check scraper logs
docker-compose logs -f scraper

# Adjust concurrency settings
# Edit .env file and restart
docker-compose restart scraper
```

**Memory Issues**
```bash
# Check memory usage
free -h

# Adjust Docker memory limits
# Edit docker-compose.yml
docker-compose down
docker-compose up -d
```

## Monitoring and Alerting

### 1. Health Checks
```bash
# Built-in health checks
docker-compose ps

# Custom health check script
nano health_check.sh

#!/bin/bash
# Check if services are responding
if curl -f http://localhost:8080/health; then
    echo "Service healthy"
    exit 0
else
    echo "Service unhealthy"
    exit 1
fi
```

### 2. Log Monitoring
```bash
# Real-time log monitoring
docker-compose logs -f --tail=100

# Log aggregation with ELK stack
# Add to docker-compose.yml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.17.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"
  
  logstash:
    image: docker.elastic.co/logstash/logstash:7.17.0
    volumes:
      - ./logs:/var/log/tag-scraper
    ports:
      - "5044:5044"
  
  kibana:
    image: docker.elastic.co/kibana/kibana:7.17.0
    ports:
      - "5601:5601"
```

## Backup and Recovery

### 1. Automated Backups
```bash
# Create comprehensive backup script
nano full_backup.sh

#!/bin/bash
BACKUP_DIR="/backups/tag-scraper"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="tag_scraper_full_$DATE"

mkdir -p $BACKUP_DIR

# Stop services
docker-compose down

# Database backup
docker-compose run --rm db pg_dump -h db -U $POSTGRES_USER $POSTGRES_DB > $BACKUP_DIR/${BACKUP_NAME}.sql

# Application backup
tar -czf $BACKUP_DIR/${BACKUP_NAME}.tar.gz \
    --exclude=logs/*.log \
    --exclude=data/temp/* \
    .

# Restart services
docker-compose up -d

# Upload to cloud storage (AWS S3 example)
aws s3 cp $BACKUP_DIR/${BACKUP_NAME}.sql s3://your-backup-bucket/
aws s3 cp $BACKUP_DIR/${BACKUP_NAME}.tar.gz s3://your-backup-bucket/

# Clean local backups older than 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

### 2. Recovery Procedures
```bash
# Database recovery
docker-compose down
docker-compose up -d db

# Wait for database to be ready
sleep 30

# Restore database
docker-compose exec -T db psql -U $POSTGRES_USER -d $POSTGRES_DB < backup_file.sql

# Restart all services
docker-compose up -d
```

## Security Hardening

### 1. Network Security
```bash
# Configure firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow from 10.0.0.0/8 to any port 5432  # Internal DB access only
sudo ufw deny 5432  # Block external DB access

# Check firewall status
sudo ufw status
```

### 2. Container Security
```yaml
# Enhanced docker-compose.yml with security
services:
  db:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /var/run/postgresql
  
  scraper:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /app/temp
```

### 3. Regular Security Updates
```bash
# Update base images regularly
docker-compose pull
docker-compose up -d

# Scan for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image tag-scraper:latest
```

This deployment guide provides a comprehensive approach to securely deploying and maintaining the TAG Grading Scraper in production cloud environments.
