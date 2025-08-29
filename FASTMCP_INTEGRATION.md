# FastMCP Integration for TAG Grading Scraper

This document explains how to use the FastMCP (Model Context Protocol) integration with your TAG Grading Scraper project.

## 🚀 What is FastMCP?

FastMCP is a Python framework for building MCP (Model Context Protocol) servers and clients. It allows you to expose your scraping tools and database operations as standardized services that LLMs and AI assistants can interact with directly.

**Key Benefits:**
- **LLM Integration**: Allow AI assistants to use your scraping tools
- **Standardized API**: Expose functionality through the MCP protocol
- **Tool Transformation**: Convert existing functions into LLM-friendly tools
- **Resource Exposure**: Let LLMs access your database and scraping results

## 📁 Files Added

- `src/fastmcp_server.py` - Main FastMCP server with scraping tools
- `src/fastmcp_config.py` - Configuration management for the server
- `src/fastmcp_client_example.py` - Example client usage
- `requirements_fastmcp.txt` - FastMCP-specific dependencies
- `docker-compose.fastmcp.yml` - Docker setup for FastMCP
- `Dockerfile.fastmcp` - Container configuration

## 🛠️ Installation

### Option 1: Install FastMCP from GitHub (Recommended)

```bash
# Install FastMCP directly from GitHub
pip install git+https://github.com/jlowin/fastmcp.git

# Or install from requirements
pip install -r requirements_fastmcp.txt
```

### Option 2: Use Official MCP SDK

```bash
# Install the official MCP Python SDK
pip install mcp

# Use the alternative server
python src/mcp_server_official.py
```

### 3. Verify Installation

```bash
# For FastMCP
python -c "import fastmcp; print('FastMCP installed successfully!')"

# For Official MCP SDK
python -c "import mcp; print('MCP SDK installed successfully!')"
```

## 🚀 Quick Start

### Start the FastMCP Server

```bash
cd src
python fastmcp_server.py
```

The server will start on `localhost:8000` and expose the following tools:

### Available Tools

#### 🔍 Scraping Tools
| Tool | Description | Parameters |
|------|-------------|------------|
| `scrape_sport_years` | Scrape available years for a sport | `sport` (string) |
| `scrape_sets_for_year` | Scrape sets for a sport/year | `sport`, `year` |
| `scrape_cards_for_set` | Scrape cards for a specific set | `set_name`, `limit` |
| `run_full_pipeline` | Run complete scraping pipeline | `sport`, `year`, `set_name` |

#### 📊 Analytics & Statistics
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_database_stats` | Get database statistics | None |
| `get_card_totals_by_type` | Get card totals by type/sport/year | `card_type`, `sport`, `year` |
| `get_card_scores_analysis` | Analyze card scores and grades | `min_score`, `max_score`, `sport` |
| `get_card_value_analysis` | Analyze card values and market data | `min_value`, `max_value`, `grade` |
| `get_set_completion_status` | Check set completion status | `set_name`, `sport`, `year` |
| `get_player_card_collection` | Get player's card collection | `player_name`, `sport`, `min_grade` |
| `get_market_trends_analysis` | Analyze market trends and prices | `days`, `sport`, `card_type` |

#### 🔍 Search & Query
| Tool | Description | Parameters |
|------|-------------|------------|
| `search_cards` | Search for cards in database | `query`, `limit` |
| `get_available_sports` | Get list of available sports | None |
| `get_pipeline_status` | Get pipeline status | None |

## 🔌 Using the Client

### Run the Example Client

```bash
cd src
python fastmcp_client_example.py
```

Choose between:
1. **Asynchronous client** (recommended)
2. **Synchronous client**

### Custom Client Usage

```python
from fastmcp import FastMCPClient
import asyncio

async def main():
    client = FastMCPClient("My Client")
    await client.connect("localhost:8000")
    
    # Call a tool
    result = await client.call_tool("get_available_sports", {})
    print(result)
    
    await client.close()

asyncio.run(main())
```

## 🐳 Docker Deployment

### Start FastMCP Services

```bash
docker-compose -f docker-compose.fastmcp.yml up -d
```

This will start:
- **FastMCP Server** on port 8000
- **Example Client** container

### View Logs

```bash
docker-compose -f docker-compose.fastmcp.yml logs -f fastmcp-server
```

### Stop Services

```bash
docker-compose -f docker-compose.fastmcp.yml down
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FASTMCP_HOST` | `localhost` | Server host address |
| `FASTMCP_PORT` | `8000` | Server port |
| `FASTMCP_DEBUG` | `false` | Enable debug mode |
| `DATABASE_PATH` | `tag_scraper_local.db` | Database file path |
| `MAX_CONCURRENT_SCRAPES` | `5` | Maximum concurrent scraping operations |
| `SCRAPE_TIMEOUT` | `300` | Scraping timeout in seconds |
| `RATE_LIMIT_DELAY` | `1.0` | Delay between requests in seconds |
| `REQUIRE_AUTH` | `false` | Require authentication |
| `LOG_LEVEL` | `INFO` | Logging level |

### Configuration Profiles

```python
from src.fastmcp_config import get_development_config, get_production_config

# Development settings
dev_config = get_development_config()

# Production settings
prod_config = get_production_config()
```

## 🔧 Integration with Existing Code

The FastMCP server integrates seamlessly with your existing scraping pipeline:

- **UnifiedPipeline**: Used for scraping operations
- **MultiLevelOrchestrator**: Manages complex scraping workflows
- **DatabaseHelper**: Provides database operations
- **Models**: SQLAlchemy models for data structure

## 📊 Example Usage Scenarios

### 1. AI Assistant Integration

An AI assistant can now:
- Ask "What years of baseball cards are available?"
- Request "Scrape the 2023 Topps baseball set"
- Query "How many cards are in the database?"

### 2. Automated Workflows

```python
# Run complete pipeline through MCP
result = await client.call_tool("run_full_pipeline", {
    "sport": "baseball",
    "year": "2023",
    "set_name": "Topps"
})
```

### 3. Database Queries

```python
# Search for specific cards
results = await client.call_tool("search_cards", {
    "query": "Mike Trout",
    "limit": 20
})
```

### 4. Card Analytics

```python
# Get card totals by type
totals = await client.call_tool("get_card_totals_by_type", {
    "card_type": "rookie",
    "sport": "baseball",
    "year": "2023"
})

# Analyze card scores
scores = await client.call_tool("get_card_scores_analysis", {
    "min_score": 9.0,
    "sport": "baseball"
})

# Check set completion
completion = await client.call_tool("get_set_completion_status", {
    "set_name": "2023 Topps Baseball",
    "sport": "baseball"
})
```

### 5. Player Collections

```python
# Get player's card collection
collection = await client.call_tool("get_player_card_collection", {
    "player_name": "Mike Trout",
    "sport": "baseball",
    "min_grade": 9.0
})
```

### 6. Market Analysis

```python
# Analyze market trends
trends = await client.call_tool("get_market_trends_analysis", {
    "days": 30,
    "sport": "baseball",
    "card_type": "rookie"
})

# Get value analysis
values = await client.call_tool("get_card_value_analysis", {
    "min_value": 100.0,
    "grade": "9.5"
})
```

## 🧪 Testing

### Test Individual Tools

```bash
# Test database stats
curl -X POST http://localhost:8000/tools/get_database_stats \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Run Test Suite

```bash
python -m pytest tests/test_fastmcp.py -v
```

## 🔒 Security Considerations

- **Authentication**: Enable with `REQUIRE_AUTH=true`
- **Rate Limiting**: Configure with `RATE_LIMIT_DELAY`
- **Input Validation**: All tool parameters are validated
- **Error Handling**: Comprehensive error handling and logging

## 🚀 Production Deployment

### 1. Environment Setup

```bash
export FASTMCP_HOST=0.0.0.0
export FASTMCP_PORT=8000
export REQUIRE_AUTH=true
export AUTH_TOKEN=your-secure-token
export LOG_LEVEL=WARNING
```

### 2. Process Management

```bash
# Using systemd
sudo systemctl enable tag-scraper-fastmcp
sudo systemctl start tag-scraper-fastmcp

# Using supervisor
supervisorctl start tag-scraper-fastmcp
```

### 3. Load Balancing

```nginx
upstream fastmcp_servers {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    location / {
        proxy_pass http://fastmcp_servers;
    }
}
```

## 📚 Additional Resources

- [FastMCP Documentation](https://gofastmcp.com/getting-started/welcome)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [FastMCP GitHub Repository](https://github.com/jlowin/fastmcp)

## 🤝 Contributing

To add new tools to the FastMCP server:

1. Create your function in the appropriate module
2. Add the `@mcp.tool` decorator
3. Include comprehensive docstrings
4. Add error handling
5. Update this documentation

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `PYTHONPATH` includes `src/`
2. **Connection Refused**: Check if server is running on correct port
3. **Database Errors**: Verify database file exists and is accessible
4. **Permission Errors**: Check file permissions for logs and data directories

### Package Installation Issues

#### **FastMCP Not Found**
```bash
# Error: No matching distribution found for fastmcp
# Solution: Install from GitHub
pip install git+https://github.com/jlowin/fastmcp.git
```

#### **MCP SDK Not Found**
```bash
# Error: No module named 'mcp'
# Solution: Install official SDK
pip install mcp
```

#### **Alternative: Use Official MCP SDK**
If FastMCP installation fails, use the official MCP server:
```bash
pip install mcp
python src/mcp_server_official.py
```

### Debug Mode

```bash
export FASTMCP_DEBUG=true
export LOG_LEVEL=DEBUG
python src/fastmcp_server.py
```

---

**Happy Scraping with FastMCP! 🏷️🚀**
