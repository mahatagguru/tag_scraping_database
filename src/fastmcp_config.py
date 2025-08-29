"""
FastMCP Server Configuration for TAG Grading Scraper
"""

import os
from typing import Dict, Any
from pathlib import Path

class FastMCPConfig:
    """Configuration class for FastMCP server settings"""
    
    def __init__(self):
        self.server_name = "TAG Grading Scraper 🏷️"
        self.server_description = "MCP server for TAG grading data scraping and database operations"
        self.version = "1.0.0"
        
        # Server settings
        self.host = os.getenv("FASTMCP_HOST", "localhost")
        self.port = int(os.getenv("FASTMCP_PORT", "8000"))
        self.debug = os.getenv("FASTMCP_DEBUG", "false").lower() == "true"
        
        # Database settings
        self.db_path = os.getenv("DATABASE_PATH", "tag_scraper_local.db")
        self.max_connections = int(os.getenv("MAX_DB_CONNECTIONS", "10"))
        
        # Scraping settings
        self.max_concurrent_scrapes = int(os.getenv("MAX_CONCURRENT_SCRAPES", "5"))
        self.scrape_timeout = int(os.getenv("SCRAPE_TIMEOUT", "300"))  # 5 minutes
        self.rate_limit_delay = float(os.getenv("RATE_LIMIT_DELAY", "1.0"))  # 1 second
        
        # MCP Protocol settings
        self.mcp_version = "2024-11-05"
        self.supports_resources = True
        self.supports_tools = True
        self.supports_prompts = True
        
        # Authentication settings
        self.require_auth = os.getenv("REQUIRE_AUTH", "false").lower() == "true"
        self.auth_token = os.getenv("AUTH_TOKEN", "")
        
        # Logging settings
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "fastmcp_server.log")
        
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information for MCP protocol"""
        return {
            "name": self.server_name,
            "description": self.server_description,
            "version": self.version,
            "capabilities": {
                "tools": self.supports_tools,
                "resources": self.supports_resources,
                "prompts": self.supports_prompts
            }
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return {
            "path": self.db_path,
            "max_connections": self.max_connections,
            "type": "sqlite" if self.db_path.endswith('.db') else "postgresql"
        }
    
    def get_scraping_config(self) -> Dict[str, Any]:
        """Get scraping configuration"""
        return {
            "max_concurrent": self.max_concurrent_scrapes,
            "timeout": self.scrape_timeout,
            "rate_limit_delay": self.rate_limit_delay
        }
    
    def validate_config(self) -> bool:
        """Validate configuration settings"""
        errors = []
        
        if self.port < 1 or self.port > 65535:
            errors.append(f"Invalid port number: {self.port}")
        
        if self.max_concurrent_scrapes < 1:
            errors.append(f"Invalid max concurrent scrapes: {self.max_concurrent_scrapes}")
        
        if self.scrape_timeout < 1:
            errors.append(f"Invalid scrape timeout: {self.scrape_timeout}")
        
        if self.rate_limit_delay < 0:
            errors.append(f"Invalid rate limit delay: {self.rate_limit_delay}")
        
        if errors:
            print("Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True

# Global configuration instance
config = FastMCPConfig()

# Environment-specific configurations
def get_production_config() -> FastMCPConfig:
    """Get production configuration"""
    prod_config = FastMCPConfig()
    prod_config.host = "0.0.0.0"
    prod_config.port = 8000
    prod_config.debug = False
    prod_config.require_auth = True
    prod_config.log_level = "WARNING"
    return prod_config

def get_development_config() -> FastMCPConfig:
    """Get development configuration"""
    dev_config = FastMCPConfig()
    dev_config.host = "localhost"
    dev_config.port = 8001
    dev_config.debug = True
    dev_config.require_auth = False
    dev_config.log_level = "DEBUG"
    return dev_config
