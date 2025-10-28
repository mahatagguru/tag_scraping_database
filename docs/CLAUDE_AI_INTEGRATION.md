# TAG Grading Scraper - Claude AI Integration Guide

## Overview

This guide provides comprehensive instructions for integrating Claude AI with the TAG Grading Scraper database to enable intelligent querying, analysis, and insights generation for sports card population data.

## Integration Architecture

### System Components
```mermaid
graph TD
    A[Claude AI] --> B[API Gateway]
    B --> C[Query Parser]
    C --> D[Database Connector]
    D --> E[PostgreSQL Database]
    F[Natural Language Query] --> C
    G[Structured Response] --> A
    E --> H[Data Processing]
    H --> I[Insight Generation]
    I --> G
```

### Data Flow
1. **User Query**: Natural language question about sports card data
2. **Query Processing**: Claude AI parses and understands the intent
3. **Database Query**: SQL generation and execution
4. **Data Analysis**: Processing and analysis of results
5. **Insight Generation**: Contextual interpretation and recommendations
6. **Response**: Natural language answer with supporting data

## Prerequisites

### Required Components
- **Claude AI API Access**: Anthropic API key and access
- **Database Access**: PostgreSQL connection credentials
- **Python Environment**: Python 3.8+ with required packages
- **API Framework**: FastAPI or Flask for web service

### Required Python Packages
```bash
pip install anthropic
pip install psycopg2-binary
pip install sqlalchemy
pip install fastapi
pip install uvicorn
pip install python-dotenv
pip install pandas
pip install numpy
```

## Database Connection Setup

### 1. Environment Configuration
```bash
# .env file for Claude AI integration
ANTHROPIC_API_KEY=your_claude_api_key_here
DATABASE_URL=postgresql://username:password@host:port/database
CLAUDE_MODEL=claude-3-sonnet-20240229
MAX_TOKENS=4000
TEMPERATURE=0.1
```

### 2. Database Connection Class
```python
# database_connector.py
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import pandas as pd

class DatabaseConnector:
    def __init__(self, database_url):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    @contextmanager
    def get_session(self):
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def execute_query(self, query, params=None):
        """Execute SQL query and return results as DataFrame"""
        with self.get_session() as session:
            result = session.execute(text(query), params or {})
            if result.returns_rows:
                return pd.DataFrame(result.fetchall(), columns=result.keys())
            return None

    def get_table_schema(self, table_name=None):
        """Get database schema information"""
        if table_name:
            query = """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = :table_name
                ORDER BY ordinal_position
            """
            return self.execute_query(query, {'table_name': table_name})
        else:
            query = """
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """
            return self.execute_query(query)
```

## Claude AI Integration

### 1. Claude AI Client
```python
# claude_client.py
import anthropic
import os
from typing import Dict, Any

class ClaudeClient:
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def generate_response(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.1) -> str:
        """Generate response from Claude AI"""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return message.content[0].text
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def analyze_query(self, user_query: str, schema_info: str) -> Dict[str, Any]:
        """Analyze user query and generate SQL"""
        prompt = f"""
        You are a database expert analyzing sports card data. Given the following database schema and user query, generate appropriate SQL and analysis.

        Database Schema:
        {schema_info}

        User Query: {user_query}

        Please provide:
        1. SQL query to answer the question
        2. Explanation of what the query does
        3. Expected results format
        4. Any relevant insights or warnings

        Format your response as JSON with keys: sql_query, explanation, expected_results, insights
        """

        response = self.generate_response(prompt)
        # Parse JSON response and return structured data
        return self.parse_response(response)

    def interpret_results(self, query: str, results: pd.DataFrame, schema_info: str) -> str:
        """Interpret query results and provide insights"""
        prompt = f"""
        You are analyzing results from a sports card database query. Please provide insights and interpretation.

        Original Query: {query}

        Results (first 10 rows):
        {results.head(10).to_string()}

        Total Results: {len(results)} rows

        Database Schema Context:
        {schema_info}

        Please provide:
        1. Summary of the results
        2. Key insights and patterns
        3. Notable findings
        4. Recommendations or observations
        5. Any data quality issues noticed

        Provide a natural language response that would be helpful to someone asking about sports card data.
        """

        return self.generate_response(prompt)
```

### 2. Query Processing Engine
```python
# query_processor.py
from typing import Dict, Any, Tuple
import pandas as pd
from claude_client import ClaudeClient
from database_connector import DatabaseConnector

class QueryProcessor:
    def __init__(self, claude_client: ClaudeClient, db_connector: DatabaseConnector):
        self.claude_client = claude_client
        self.db_connector = db_connector
        self.schema_info = self._get_schema_info()

    def _get_schema_info(self) -> str:
        """Get comprehensive database schema information"""
        schema_info = []

        # Get table list
        tables = self.db_connector.get_table_schema()

        for _, table in tables.iterrows():
            table_name = table['table_name']
            columns = self.db_connector.get_table_schema(table_name)

            table_info = f"Table: {table_name}\n"
            for _, col in columns.iterrows():
                table_info += f"  - {col['column_name']}: {col['data_type']}"
                if col['is_nullable'] == 'NO':
                    table_info += " (NOT NULL)"
                table_info += "\n"

            schema_info.append(table_info)

        return "\n".join(schema_info)

    def process_query(self, user_query: str) -> Dict[str, Any]:
        """Process natural language query and return results"""
        try:
            # Step 1: Analyze query and generate SQL
            analysis = self.claude_client.analyze_query(user_query, self.schema_info)

            if 'sql_query' not in analysis:
                return {
                    'error': 'Failed to generate SQL query',
                    'claude_response': analysis
                }

            # Step 2: Execute SQL query
            sql_query = analysis['sql_query']
            results = self.db_connector.execute_query(sql_query)

            if results is None:
                return {
                    'error': 'Query execution failed',
                    'sql_query': sql_query
                }

            # Step 3: Interpret results
            interpretation = self.claude_client.interpret_results(
                user_query, results, self.schema_info
            )

            # Step 4: Return comprehensive response
            return {
                'success': True,
                'user_query': user_query,
                'sql_query': sql_query,
                'results': results.to_dict('records'),
                'result_count': len(results),
                'explanation': analysis.get('explanation', ''),
                'insights': analysis.get('insights', ''),
                'interpretation': interpretation,
                'schema_context': self.schema_info[:500] + "..."  # Truncated for response
            }

        except Exception as e:
            return {
                'error': f'Processing error: {str(e)}',
                'user_query': user_query
            }
```

## Web API Service

### 1. FastAPI Application
```python
# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
from query_processor import QueryProcessor
from claude_client import ClaudeClient
from database_connector import DatabaseConnector
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="TAG Grading Scraper AI", version="1.0.0")

# Initialize components
claude_client = ClaudeClient(
    api_key=os.getenv('ANTHROPIC_API_KEY'),
    model=os.getenv('CLAUDE_MODEL', 'claude-3-sonnet-20240229')
)

db_connector = DatabaseConnector(os.getenv('DATABASE_URL'))
query_processor = QueryProcessor(claude_client, db_connector)

class QueryRequest(BaseModel):
    query: str
    max_tokens: Optional[int] = 4000
    temperature: Optional[float] = 0.1

class QueryResponse(BaseModel):
    success: bool
    user_query: str
    sql_query: Optional[str] = None
    results: Optional[list] = None
    result_count: Optional[int] = None
    explanation: Optional[str] = None
    insights: Optional[str] = None
    interpretation: Optional[str] = None
    error: Optional[str] = None

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process natural language query about sports card data"""
    try:
        result = query_processor.process_query(request.query)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schema")
async def get_schema():
    """Get database schema information"""
    try:
        return {
            "tables": db_connector.get_table_schema().to_dict('records'),
            "schema_info": query_processor.schema_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "TAG Grading Scraper AI"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2. Docker Configuration
```dockerfile
# Dockerfile for Claude AI integration
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]
```

```yaml
# docker-compose.yml addition for Claude AI service
services:
  claude-ai:
    build: .
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - CLAUDE_MODEL=${CLAUDE_MODEL}
    ports:
      - "8000:8000"
    depends_on:
      - db
    volumes:
      - ./logs:/app/logs
```

## Usage Examples

### 1. Basic Query Examples

#### Sports Overview
```python
# Query: "How many baseball cards do we have from the 1990s?"
{
    "query": "How many baseball cards do we have from the 1990s?"
}

# Expected SQL:
"""
SELECT COUNT(DISTINCT c.id) as card_count
FROM cards c
JOIN sets s ON c.set_id = s.id
JOIN years y ON s.year_id = y.id
JOIN categories cat ON y.category_id = cat.id
WHERE cat.name = 'Baseball'
  AND y.year BETWEEN 1990 AND 1999
"""
```

#### Population Analysis
```python
# Query: "What are the most common grades for hockey cards?"
{
    "query": "What are the most common grades for hockey cards?"
}

# Expected SQL:
"""
SELECT g.grade_label, SUM(p.count) as total_population
FROM grades g
JOIN populations p ON g.id = p.grade_id
JOIN cards c ON p.card_uid = c.card_uid
JOIN sets s ON c.set_id = s.id
JOIN years y ON s.year_id = y.id
JOIN categories cat ON y.category_id = cat.id
WHERE cat.name = 'Hockey'
GROUP BY g.grade_label
ORDER BY total_population DESC
"""
```

#### Player Analysis
```python
# Query: "Show me all Michael Jordan cards and their population data"
{
    "query": "Show me all Michael Jordan cards and their population data"
}

# Expected SQL:
"""
SELECT
    c.player,
    c.card_number,
    s.set_name,
    y.year,
    g.grade_label,
    p.count as population_count
FROM cards c
JOIN sets s ON c.set_id = s.id
JOIN years y ON s.year_id = y.id
JOIN populations p ON c.card_uid = p.card_uid
JOIN grades g ON p.grade_id = g.id
WHERE c.player ILIKE '%Michael Jordan%'
ORDER BY y.year, s.set_name, c.card_number
"""
```

### 2. Advanced Query Examples

#### Trend Analysis
```python
# Query: "How has the population of 1989 Upper Deck Ken Griffey Jr. cards changed over time?"
{
    "query": "How has the population of 1989 Upper Deck Ken Griffey Jr. cards changed over time?"
}

# Expected SQL:
"""
SELECT
    s.captured_at,
    g.grade_label,
    p.count as population_count
FROM snapshots s
JOIN populations p ON s.id = p.snapshot_id
JOIN cards c ON p.card_uid = c.card_uid
JOIN sets set ON c.set_id = set.id
JOIN years y ON set.year_id = y.id
JOIN grades g ON p.grade_id = g.id
WHERE c.player = 'Ken Griffey Jr.'
  AND set.set_name = 'Upper Deck'
  AND y.year = 1989
ORDER BY s.captured_at, g.grade_label
"""
```

#### Comparative Analysis
```python
# Query: "Compare the population distribution between 1987 Topps and 1987 Donruss baseball sets"
{
    "query": "Compare the population distribution between 1987 Topps and 1987 Donruss baseball sets"
}

# Expected SQL:
"""
SELECT
    set.set_name,
    g.grade_label,
    COUNT(DISTINCT c.id) as card_count,
    AVG(p.count) as avg_population,
    SUM(p.count) as total_population
FROM sets set
JOIN years y ON set.year_id = y.id
JOIN categories cat ON y.category_id = cat.id
JOIN cards c ON set.id = c.set_id
JOIN populations p ON c.card_uid = p.card_uid
JOIN grades g ON p.grade_id = g.id
JOIN snapshots s ON p.snapshot_id = s.id
WHERE cat.name = 'Baseball'
  AND y.year = 1987
  AND set.set_name IN ('Topps', 'Donruss')
  AND s.captured_at = (SELECT MAX(captured_at) FROM snapshots)
GROUP BY set.set_name, g.grade_label
ORDER BY set.set_name, g.grade_label
"""
```

## Integration with Existing Systems

### 1. Slack Integration
```python
# slack_integration.py
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from query_processor import QueryProcessor

class SlackIntegration:
    def __init__(self, slack_token: str, query_processor: QueryProcessor):
        self.client = WebClient(token=slack_token)
        self.query_processor = query_processor

    def handle_slack_query(self, channel: str, user_query: str):
        """Handle Slack query and post response"""
        try:
            # Process query
            result = self.query_processor.process_query(user_query)

            if result['success']:
                # Format response for Slack
                response = self._format_slack_response(result)
                self.client.chat_postMessage(
                    channel=channel,
                    text=response,
                    unfurl_links=False
                )
            else:
                self.client.chat_postMessage(
                    channel=channel,
                    text=f"Error processing query: {result.get('error', 'Unknown error')}"
                )

        except SlackApiError as e:
            print(f"Slack API error: {e.response['error']}")

    def _format_slack_response(self, result: dict) -> str:
        """Format query result for Slack"""
        response = f"*Query:* {result['user_query']}\n\n"

        if result['explanation']:
            response += f"*Explanation:* {result['explanation']}\n\n"

        if result['result_count']:
            response += f"*Results:* {result['result_count']} records found\n\n"

        if result['insights']:
            response += f"*Insights:* {result['insights']}\n\n"

        if result['interpretation']:
            response += f"*Analysis:* {result['interpretation']}\n\n"

        return response
```

### 2. Discord Bot Integration
```python
# discord_integration.py
import discord
from discord.ext import commands
from query_processor import QueryProcessor

class DiscordBot(commands.Bot):
    def __init__(self, query_processor: QueryProcessor):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        self.query_processor = query_processor

    async def setup_hook(self):
        await self.add_cog(QueryCog(self.query_processor))

class QueryCog(commands.Cog):
    def __init__(self, query_processor: QueryProcessor):
        self.query_processor = query_processor

    @commands.command(name='query')
    async def query_command(self, ctx, *, question: str):
        """Query the sports card database using natural language"""
        async with ctx.typing():
            result = self.query_processor.process_query(question)

            if result['success']:
                embed = self._create_embed(result)
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"Error: {result.get('error', 'Unknown error')}")

    def _create_embed(self, result: dict) -> discord.Embed:
        """Create Discord embed from query result"""
        embed = discord.Embed(
            title="Sports Card Query Results",
            description=result['user_query'],
            color=0x00ff00
        )

        if result['explanation']:
            embed.add_field(name="Explanation", value=result['explanation'], inline=False)

        if result['result_count']:
            embed.add_field(name="Results", value=f"{result['result_count']} records found", inline=True)

        if result['insights']:
            embed.add_field(name="Insights", value=result['insights'], inline=False)

        if result['interpretation']:
            embed.add_field(name="Analysis", value=result['interpretation'][:1024], inline=False)

        return embed
```

## Security and Best Practices

### 1. API Security
```python
# security.py
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

security = HTTPBearer()

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key for protected endpoints"""
    if credentials.credentials != os.getenv('API_SECRET_KEY'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return credentials.credentials

# Apply to protected endpoints
@app.post("/query", dependencies=[Depends(verify_api_key)])
async def process_query(request: QueryRequest):
    # ... existing code
```

### 2. Rate Limiting
```python
# rate_limiter.py
from fastapi import HTTPException
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    def check_rate_limit(self, client_id: str):
        """Check if client has exceeded rate limit"""
        now = time.time()
        client_requests = self.requests[client_id]

        # Remove old requests outside window
        client_requests[:] = [req_time for req_time in client_requests
                            if now - req_time < self.window_seconds]

        if len(client_requests) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded"
            )

        client_requests.append(now)
```

### 3. Query Validation
```python
# query_validator.py
import re
from typing import List

class QueryValidator:
    def __init__(self):
        self.forbidden_patterns = [
            r'\bDROP\b',
            r'\bDELETE\b',
            r'\bUPDATE\b',
            r'\bINSERT\b',
            r'\bALTER\b',
            r'\bCREATE\b',
            r'\bTRUNCATE\b'
        ]

    def validate_query(self, query: str) -> List[str]:
        """Validate query for security and safety"""
        errors = []

        # Check for forbidden SQL operations
        for pattern in self.forbidden_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                errors.append(f"Forbidden SQL operation detected: {pattern}")

        # Check query length
        if len(query) > 1000:
            errors.append("Query too long (max 1000 characters)")

        # Check for suspicious patterns
        if ';' in query:
            errors.append("Multiple SQL statements not allowed")

        return errors
```

## Monitoring and Analytics

### 1. Query Analytics
```python
# analytics.py
import time
from datetime import datetime
from typing import Dict, Any

class QueryAnalytics:
    def __init__(self):
        self.query_log = []

    def log_query(self, user_query: str, processing_time: float,
                  success: bool, result_count: int = 0):
        """Log query for analytics"""
        log_entry = {
            'timestamp': datetime.utcnow(),
            'query': user_query,
            'processing_time': processing_time,
            'success': success,
            'result_count': result_count
        }
        self.query_log.append(log_entry)

    def get_analytics(self) -> Dict[str, Any]:
        """Get query analytics"""
        if not self.query_log:
            return {}

        total_queries = len(self.query_log)
        successful_queries = sum(1 for log in self.query_log if log['success'])
        avg_processing_time = sum(log['processing_time'] for log in self.query_log) / total_queries

        return {
            'total_queries': total_queries,
            'success_rate': successful_queries / total_queries,
            'avg_processing_time': avg_processing_time,
            'recent_queries': self.query_log[-10:]  # Last 10 queries
        }
```

### 2. Performance Monitoring
```python
# performance_monitor.py
import psutil
import time
from typing import Dict, Any

class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'uptime': time.time() - self.start_time
        }

    def get_database_metrics(self, db_connector) -> Dict[str, Any]:
        """Get database performance metrics"""
        try:
            # Get active connections
            result = db_connector.execute_query(
                "SELECT count(*) as active_connections FROM pg_stat_activity"
            )
            active_connections = result.iloc[0]['active_connections'] if result is not None else 0

            # Get database size
            result = db_connector.execute_query(
                "SELECT pg_size_pretty(pg_database_size(current_database())) as db_size"
            )
            db_size = result.iloc[0]['db_size'] if result is not None else 'Unknown'

            return {
                'active_connections': active_connections,
                'database_size': db_size
            }
        except Exception as e:
            return {'error': str(e)}
```

## Deployment and Scaling

### 1. Production Deployment
```bash
# Production deployment script
#!/bin/bash

# Build and deploy Claude AI service
docker-compose -f docker-compose.prod.yml build claude-ai
docker-compose -f docker-compose.prod.yml up -d claude-ai

# Verify deployment
docker-compose -f docker-compose.prod.yml ps claude-ai

# Check logs
docker-compose -f docker-compose.prod.yml logs -f claude-ai

# Health check
curl http://localhost:8000/health
```

### 2. Load Balancing
```yaml
# nginx.conf for load balancing
upstream claude_ai_backend {
    server claude-ai-1:8000;
    server claude-ai-2:8000;
    server claude-ai-3:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://claude_ai_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Auto-scaling
```yaml
# docker-compose.scale.yml
services:
  claude-ai:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
```

This Claude AI integration guide provides comprehensive coverage of integrating intelligent querying and analysis capabilities with the TAG Grading Scraper database.
