# TAG Grading Scraper - Cloud Launch Guide

## 🚀 Quick Start: Get Running in 30 Minutes

This guide will walk you through deploying the TAG Grading Scraper to the cloud and getting it fully operational. Choose your cloud platform and follow the step-by-step instructions.

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Cloud Account**: AWS, Google Cloud, or Azure account with billing enabled
- [ ] **Domain Name**: Optional but recommended for production
- [ ] **SSH Key Pair**: For secure server access
- [ ] **Git Access**: To clone the repository
- [ ] **Basic Terminal Skills**: Comfort with command line operations

## 🌐 Cloud Platform Options

### Option 1: AWS EC2 (Recommended for Beginners)
- **Pros**: Easy setup, comprehensive documentation, generous free tier
- **Cons**: Can be expensive for high-performance instances
- **Best For**: Learning, development, small to medium production loads

### Option 2: Google Cloud Platform
- **Pros**: Good performance, competitive pricing, excellent monitoring
- **Cons**: Slightly more complex setup
- **Best For**: Production workloads, cost optimization

### Option 3: Azure
- **Pros**: Good enterprise integration, Windows-friendly
- **Cons**: Can be more expensive
- **Best For**: Enterprise environments, Windows shops

---

## 🚀 AWS EC2 Launch (Step-by-Step)

### Step 1: Launch EC2 Instance

#### 1.1 Access AWS Console
```bash
# Open AWS Console in your browser
https://console.aws.amazon.com/
```

#### 1.2 Create EC2 Instance
```bash
# Navigate to EC2 Dashboard
# Click "Launch Instance"

# Instance Configuration:
Name: tag-scraper-production
AMI: Ubuntu Server 22.04 LTS (HVM)
Instance Type: t3.medium (2 vCPU, 4GB RAM)
Key Pair: Create new key pair (save the .pem file securely)
Security Group: Create new security group
```

#### 1.3 Configure Security Group
```bash
# Security Group Rules:
SSH (Port 22): Your IP address only
HTTP (Port 80): 0.0.0.0/0 (for web access)
HTTPS (Port 443): 0.0.0.0/0 (for secure web access)
Custom TCP (Port 8000): 0.0.0.0/0 (for Claude AI API)
```

#### 1.4 Launch and Connect
```bash
# Launch the instance
# Wait for status check to pass (green checkmark)

# Connect to your instance:
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

### Step 2: Server Setup

#### 2.1 Update System
```bash
# Update package lists and upgrade packages
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git unzip software-properties-common
```

#### 2.2 Install Docker
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# Logout and login again for group changes to take effect
exit
# SSH back in
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

#### 2.3 Install Additional Tools
```bash
# Install additional useful tools
sudo apt install -y htop tree nano vim

# Install AWS CLI (optional, for backup to S3)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### Step 3: Deploy Application

#### 3.1 Clone Repository
```bash
# Clone the repository
git clone <your-repository-url>
cd "New Scraping Tool"

# Verify files are present
ls -la
```

#### 3.2 Configure Environment
```bash
# Copy environment file
cp env.example .env

# Edit environment variables
nano .env
```

#### 3.3 Production Environment Configuration
```bash
# Database Configuration - USE STRONG PASSWORDS
POSTGRES_USER=tag_scraper_prod
POSTGRES_PASSWORD=YourSuperSecurePassword123!@#
POSTGRES_DB=tag_grading_prod
POSTGRES_PORT=5432

# Pipeline Configuration
PIPELINE_MAX_CONCURRENCY=5
PIPELINE_DELAY=2.0
# Use 'discover' to automatically find all available categories
# Or specify specific categories: Baseball,Hockey,Basketball,Football,Soccer,Golf,Racing,Wrestling,Gaming,Non-Sport
PIPELINE_CATEGORIES=discover

# Scheduling Configuration
PIPELINE_SCHEDULE=0 2 * * 0  # Sundays at 2 AM UTC
PIPELINE_TIMEZONE=UTC

# Logging Configuration
LOG_LEVEL=INFO

# Health Check Configuration
HEALTH_CHECK_INTERVAL=300
```

#### 3.4 Start Services
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

#### 3.5 Verify Deployment
```bash
# Check if services are running
docker-compose ps

# Check database connectivity
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT version();"

# Check scraper logs
docker-compose logs scraper --tail=50
```

### Step 4: Initial Data Collection

#### 4.1 Run Initial Pipeline
```bash
# The system should automatically run on startup
# Monitor the logs to see progress
docker-compose logs -f scraper

# If you want to run manually:
docker-compose exec scraper /app/bin/run_pipeline.sh
```

#### 4.2 Verify Data Collection
```bash
# Check database tables
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "\dt"

# Check data in tables
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT COUNT(*) FROM categories;"
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT COUNT(*) FROM years;"

# Verify all categories were discovered
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT name FROM categories ORDER BY name;"

# Check total data collected
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT COUNT(*) as total_cards FROM cards;"
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT COUNT(*) as total_sets FROM sets;"
```

---

## ☁️ Google Cloud Platform Launch

### Step 1: Create GCP Instance

#### 1.1 Access GCP Console
```bash
# Open GCP Console
https://console.cloud.google.com/
```

#### 1.2 Create Compute Engine Instance
```bash
# Navigate to Compute Engine > VM instances
# Click "Create Instance"

# Instance Configuration:
Name: tag-scraper-gcp
Machine type: e2-medium (2 vCPU, 4GB RAM)
Boot disk: Ubuntu 22.04 LTS
Size: 30GB
Firewall: Allow HTTP/HTTPS traffic
```

#### 1.3 Configure Firewall Rules
```bash
# Create firewall rule for SSH
gcloud compute firewall-rules create allow-ssh \
  --allow tcp:22 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=allow-ssh

# Create firewall rule for web traffic
gcloud compute firewall-rules create allow-web \
  --allow tcp:80,tcp:443,tcp:8000 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=allow-web
```

#### 1.4 Connect to Instance
```bash
# SSH to your instance
gcloud compute ssh tag-scraper-gcp --zone=us-central1-a
```

### Step 2: Follow Server Setup (Same as AWS)
```bash
# Follow steps 2.1 through 3.5 from AWS section above
# The setup process is identical
```

---

## 🔵 Azure Launch

### Step 1: Create Azure VM

#### 1.1 Access Azure Portal
```bash
# Open Azure Portal
https://portal.azure.com/
```

#### 1.2 Create Virtual Machine
```bash
# Navigate to Virtual Machines
# Click "Create" > "Virtual Machine"

# VM Configuration:
Resource group: Create new (tag-scraper-rg)
VM name: tag-scraper-azure
Region: East US
Image: Ubuntu Server 22.04 LTS
Size: Standard_D2s_v3 (2 vCPU, 8GB RAM)
Authentication type: SSH public key
```

#### 1.3 Configure Networking
```bash
# Networking tab:
Virtual network: Create new
Subnet: Default
Public IP: Create new
NIC network security group: Advanced
NSG rules: Allow SSH, HTTP, HTTPS, Custom port 8000
```

#### 1.4 Connect to VM
```bash
# Use Azure Cloud Shell or local terminal
ssh azureuser@<vm-public-ip>
```

### Step 2: Follow Server Setup (Same as AWS)
```bash
# Follow steps 2.1 through 3.5 from AWS section above
# The setup process is identical
```

---

## 🔧 Post-Deployment Configuration

### Step 1: Set Up Monitoring

#### 1.1 Create Monitoring Script
```bash
# Create monitoring script
nano monitor.sh

#!/bin/bash
echo "=== TAG Grading Scraper Status ==="
echo "Date: $(date)"
echo ""

# Check Docker services
echo "Docker Services:"
docker-compose ps
echo ""

# Check resource usage
echo "System Resources:"
free -h
df -h /
echo ""

# Check database size
echo "Database Size:"
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT pg_size_pretty(pg_database_size(current_database()));"
echo ""

# Check recent logs
echo "Recent Scraper Logs:"
docker-compose logs scraper --tail=10
echo ""

# Make executable
chmod +x monitor.sh
```

#### 1.2 Set Up Log Rotation
```bash
# Configure logrotate
sudo nano /etc/logrotate.d/tag-scraper

# Add configuration
/home/ubuntu/New\ Scraping\ Tool/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
}
```

### Step 2: Set Up Automated Backups

#### 2.1 Create Backup Script
```bash
# Create backup script
nano backup.sh

#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="tag_scraper_backup_$DATE"

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
docker-compose exec -T db pg_dump -U $POSTGRES_USER $POSTGRES_DB > $BACKUP_DIR/${BACKUP_NAME}.sql

# Application backup
tar -czf $BACKUP_DIR/${BACKUP_NAME}.tar.gz \
    --exclude=logs/*.log \
    --exclude=data/temp/* \
    .

# Clean old backups (keep 7 days)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_NAME"

# Make executable
chmod +x backup.sh
```

#### 2.2 Set Up Cron Jobs
```bash
# Edit crontab
crontab -e

# Add these lines:
# Daily backup at 1 AM
0 1 * * * /home/ubuntu/New\ Scraping\ Tool/backup.sh

# Daily monitoring report at 9 AM
0 9 * * * /home/ubuntu/New\ Scraping\ Tool/monitor.sh > /home/ubuntu/monitoring_report.txt
```

### Step 3: Performance Optimization

#### 3.1 Database Optimization
```bash
# Connect to database
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB

# Run optimization commands
VACUUM ANALYZE;
REINDEX DATABASE tag_grading_prod;

# Exit database
\q
```

#### 3.2 Docker Optimization
```bash
# Create docker-compose.override.yml for production
nano docker-compose.override.yml

version: '3.8'
services:
  db:
    environment:
      POSTGRES_SHARED_BUFFERS: 1GB
      POSTGRES_EFFECTIVE_CACHE_SIZE: 3GB
      POSTGRES_WORK_MEM: 16MB
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  scraper:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
```

---

## 🔍 Troubleshooting Common Issues

### Issue 1: Services Won't Start

#### Symptoms
```bash
# Services show as "Exit" status
docker-compose ps
# Shows: scraper Exit (1) or db Exit (1)
```

#### Solutions
```bash
# Check logs for specific errors
docker-compose logs scraper
docker-compose logs db

# Common fixes:
# 1. Check environment variables
cat .env

# 2. Verify file permissions
ls -la

# 3. Restart services
docker-compose down
docker-compose up -d
```

### Issue 2: Database Connection Failed

#### Symptoms
```bash
# Scraper can't connect to database
# Error: "connection refused" or "authentication failed"
```

#### Solutions
```bash
# 1. Check if database is running
docker-compose ps db

# 2. Check database logs
docker-compose logs db

# 3. Test database connection
docker-compose exec db pg_isready -U $POSTGRES_USER

# 4. Verify credentials in .env file
grep POSTGRES .env
```

### Issue 3: Scraping Not Working

#### Symptoms
```bash
# No data being collected
# Empty tables in database
```

#### Solutions
```bash
# 1. Check scraper logs
docker-compose logs scraper --tail=100

# 2. Verify internet connectivity
curl -I https://my.taggrading.com

# 3. Check Playwright installation
docker-compose exec scraper playwright --version

# 4. Run manual test
docker-compose exec scraper python -m scraper.new_pipeline --sport Baseball --dry-run
```

### Issue 4: High Memory Usage

#### Symptoms
```bash
# System running out of memory
# Docker containers being killed
```

#### Solutions
```bash
# 1. Check memory usage
free -h
docker stats

# 2. Reduce concurrency in .env
PIPELINE_MAX_CONCURRENCY=2  # Reduce from 5 to 2

# 3. Increase swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 4. Restart services
docker-compose restart
```

---

## 📊 Verification Checklist

### ✅ Basic System Check
- [ ] Docker services running (`docker-compose ps`)
- [ ] Database accessible (`docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1;"`)
- [ ] Scraper container healthy (`docker-compose logs scraper --tail=10`)

### ✅ Data Collection Check
- [ ] Initial pipeline completed successfully
- [ ] Categories table populated (`SELECT COUNT(*) FROM categories;`)
- [ ] Years table populated (`SELECT COUNT(*) FROM years;`)
- [ ] Sets table populated (`SELECT COUNT(*) FROM sets;`)

### ✅ Scheduling Check
- [ ] Cron file created (`docker-compose exec scraper cat /app/bin/cron.txt`)
- [ ] supercronic running (`docker-compose exec scraper ps aux | grep supercronic`)
- [ ] Scheduled runs executing (check logs for scheduled execution)

### ✅ Performance Check
- [ ] Memory usage reasonable (`free -h`)
- [ ] Disk space adequate (`df -h`)
- [ ] Database performance good (no slow queries in logs)

---

## 🚀 Next Steps After Launch

### 1. Connect PowerBI
```bash
# Follow the PowerBI Connection Guide
# Use your server's public IP as the database host
# Database: tag_grading_prod
# Username: tag_scraper_prod
# Password: YourSuperSecurePassword123!@#
```

### 2. Set Up Claude AI Integration
```bash
# Follow the Claude AI Integration Guide
# Deploy the AI service container
# Configure API keys and database connection
```

### 3. Set Up Monitoring and Alerts
```bash
# Configure CloudWatch (AWS), Cloud Monitoring (GCP), or Application Insights (Azure)
# Set up email/SMS alerts for system issues
# Monitor resource usage and costs
```

### 4. Scale and Optimize
```bash
# Monitor performance metrics
# Adjust concurrency settings based on performance
# Consider horizontal scaling for high loads
# Optimize database queries and indexes
```

---

## 💰 Cost Optimization

### AWS Cost Optimization
```bash
# Use Spot Instances for development/testing
# Set up billing alerts
# Use reserved instances for production
# Monitor and terminate unused resources
```

### GCP Cost Optimization
```bash
# Use preemptible instances for development
# Set up budget alerts
# Use committed use discounts
# Monitor and optimize resource usage
```

### Azure Cost Optimization
```bash
# Use Azure Hybrid Benefit if applicable
# Set up spending limits
# Use reserved instances
# Monitor and optimize resource usage
```

---

## 🔒 Security Hardening

### 1. Network Security
```bash
# Restrict SSH access to your IP only
# Use key-based authentication only
# Disable password authentication
# Set up fail2ban for intrusion prevention
```

### 2. Application Security
```bash
# Use strong passwords for database
# Regularly update system packages
# Monitor for security vulnerabilities
# Use HTTPS for web access
```

### 3. Data Security
```bash
# Encrypt data at rest
# Use secure database connections
# Regular security audits
# Monitor access logs
```

---

## 📞 Support and Maintenance

### Daily Operations
```bash
# Check system status
./monitor.sh

# Review logs for errors
docker-compose logs scraper --tail=100

# Verify scheduled runs
docker-compose logs scraper | grep "cron"
```

### Weekly Maintenance
```bash
# Run database maintenance
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "VACUUM ANALYZE;"

# Check disk space
df -h

# Review performance metrics
docker stats --no-stream
```

### Monthly Maintenance
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose pull
docker-compose up -d

# Review and rotate logs
# Check backup integrity
# Review security settings
```

---

## 🎯 Success Metrics

### System Health
- **Uptime**: >99.5%
- **Response Time**: <2 seconds for database queries
- **Error Rate**: <1% of scraping attempts

### Data Quality
- **Completeness**: >95% of expected data collected
- **Accuracy**: >99% data accuracy
- **Timeliness**: Data updated within 24 hours

### Performance
- **Resource Usage**: <80% CPU, <80% memory
- **Database Performance**: <5 second query response time
- **Scraping Speed**: >1000 cards per hour

---

## 🚀 Launch Complete!

Congratulations! You now have a fully functional TAG Grading Scraper running in the cloud. The system will:

- ✅ **Automatically discover** new sports, years, sets, and cards
- ✅ **Collect population data** on a scheduled basis
- ✅ **Store data securely** in a PostgreSQL database
- ✅ **Provide real-time access** for PowerBI and other BI tools
- ✅ **Scale automatically** based on your needs
- ✅ **Monitor and maintain** itself with minimal intervention

### Quick Commands for Daily Use
```bash
# Check system status
./monitor.sh

# View recent logs
docker-compose logs scraper --tail=50

# Run manual pipeline
docker-compose exec scraper /app/bin/run_pipeline.sh

# Access database
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB

# Restart services
docker-compose restart

# Update system
docker-compose pull && docker-compose up -d
```

Your TAG Grading Scraper is now ready for production use! 🎉
