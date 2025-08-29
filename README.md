# TAG Grading Scraper

A comprehensive web scraping system for collecting sports card grading data from TAG Grading. This project features a multi-level pipeline architecture, Docker containerization, and robust data processing capabilities.

## 🚀 Features

- **Multi-Level Scraping Pipeline**: Efficiently scrapes sports cards, sets, years, and detailed information
- **Docker Support**: Full containerization with docker-compose for easy deployment
- **Database Integration**: PostgreSQL database with comprehensive schema for sports card data
- **Scheduling**: Configurable CRON-based scheduling for automated data collection
- **Audit System**: Comprehensive logging and audit trails for data integrity
- **Multi-Sport Support**: Baseball, Hockey, Basketball, Football, Soccer, Golf, Racing, Wrestling, Gaming, and Non-Sport categories

## 🏗️ Architecture

The system implements a sophisticated multi-level scraping architecture:

1. **Sport Years Scraper**: Discovers available sports and years
2. **Enhanced Sets Scraper**: Extracts card sets for each sport/year combination
3. **Card Crawler**: Processes individual cards within sets
4. **Card Detail Crawler**: Extracts detailed information for each card
5. **Multi-Level Orchestrator**: Coordinates the entire pipeline

## 🛠️ Technology Stack

- **Python 3.8+**: Core scraping logic
- **Playwright**: Modern web automation
- **PostgreSQL**: Data storage
- **Docker**: Containerization
- **SQLAlchemy**: Database ORM
- **asyncio**: Asynchronous processing

## 📋 Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose
- PostgreSQL (if running locally)

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd "New Scraping Tool"
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

### Local Development

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up database**
   ```bash
   python src/create_tables.py
   ```

3. **Run the pipeline**
   ```bash
   python src/scraper/pipeline.py
   ```

## ⚙️ Configuration

### Environment Variables

Key configuration options in `.env`:

- `PIPELINE_MAX_CONCURRENCY`: Maximum concurrent scraping operations
- `PIPELINE_DELAY`: Delay between requests (seconds)
- `PIPELINE_CATEGORIES`: Sports categories to scrape
- `PIPELINE_SCHEDULE`: CRON schedule for automated runs
- `LOG_LEVEL`: Logging verbosity

### Pipeline Categories

Available sports categories:
- Baseball
- Hockey
- Basketball
- Football
- Soccer
- Golf
- Racing
- Wrestling
- Gaming
- Non-Sport

Use `discover` to automatically find all available categories.

## 📊 Database Schema

The system creates comprehensive tables for:
- Sports and years
- Card sets
- Individual cards
- Card grades and details
- Audit logs

See `Documentation/DATABASE_SCHEMA.md` for detailed schema information.

## 🔧 Development

### Project Structure

```
src/
├── scraper/           # Core scraping modules
│   ├── pipeline.py    # Main pipeline orchestrator
│   ├── crawler.py     # Base crawler classes
│   ├── audit.py       # Audit and logging
│   └── ...
├── models.py          # Database models
├── db.py             # Database connection
└── create_tables.py  # Database initialization
```

### Running Tests

```bash
# Test the multi-level system
python src/test_multi_level_system.py

# Test specific pipeline levels
python src/test_four_level_pipeline.py
python src/test_five_level_pipeline.py
```

## 📈 Monitoring and Logs

- **Pipeline Logs**: `pipeline.log`
- **Docker Logs**: `docker-compose logs -f`
- **Health Checks**: Built-in health monitoring system

## 🐳 Docker Deployment

### Production Deployment

1. **Build and deploy**
   ```bash
   docker-compose -f docker-compose.yml up -d --build
   ```

2. **Monitor logs**
   ```bash
   docker-compose logs -f
   ```

3. **Scale if needed**
   ```bash
   docker-compose up -d --scale scraper=3
   ```

### Health Monitoring

The system includes built-in health checks and monitoring capabilities. See `Documentation/DOCKER_DEPLOYMENT.md` for detailed deployment information.

## 📚 Documentation

- [Project Overview](Documentation/PROJECT_OVERVIEW.md)
- [Database Schema](Documentation/DATABASE_SCHEMA.md)
- [Docker Deployment](Documentation/DOCKER_DEPLOYMENT.md)
- [Pipeline Implementation](Documentation/FIVE_LEVEL_PIPELINE_IMPLEMENTATION.md)
- [Cloud Launch Guide](Documentation/CLOUD_LAUNCH_GUIDE.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational and research purposes. Please respect the target website's terms of service and robots.txt file. Use responsibly and consider implementing appropriate delays between requests.

## 🆘 Support

For issues and questions:
1. Check the documentation
2. Review existing issues
3. Create a new issue with detailed information

---

**Built with ❤️ for the sports card collecting community**
