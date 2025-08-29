"""
FastMCP Server for TAG Grading Scraper
Exposes scraping tools and database operations through the Model Context Protocol
"""

from fastmcp import FastMCP
from typing import List, Dict, Optional, Any
import asyncio
from pathlib import Path
import sys

# Add the src directory to the path to import our modules
sys.path.append(str(Path(__file__).parent))

from models import *
from scraper.unified_pipeline import UnifiedPipeline
from scraper.multi_level_orchestrator import MultiLevelOrchestrator
from scraper.db_helpers import DatabaseHelper
from db import get_db_connection

# Initialize FastMCP server
mcp = FastMCP("TAG Grading Scraper 🏷️")

# Initialize database helper
db_helper = DatabaseHelper()

@mcp.tool
def scrape_sport_years(sport: str) -> Dict[str, Any]:
    """
    Scrape available years for a specific sport
    
    Args:
        sport: The sport to scrape years for (e.g., 'baseball', 'football', 'basketball')
    
    Returns:
        Dictionary containing scraped years and status
    """
    try:
        pipeline = UnifiedPipeline()
        years = pipeline.scrape_sport_years(sport)
        return {
            "success": True,
            "sport": sport,
            "years_found": len(years),
            "years": years,
            "message": f"Successfully scraped {len(years)} years for {sport}"
        }
    except Exception as e:
        return {
            "success": False,
            "sport": sport,
            "error": str(e),
            "message": f"Failed to scrape years for {sport}"
        }

@mcp.tool
def scrape_sets_for_year(sport: str, year: str) -> Dict[str, Any]:
    """
    Scrape available sets for a specific sport and year
    
    Args:
        sport: The sport to scrape sets for
        year: The year to scrape sets for
    
    Returns:
        Dictionary containing scraped sets and status
    """
    try:
        pipeline = UnifiedPipeline()
        sets = pipeline.scrape_sets_for_year(sport, year)
        return {
            "success": True,
            "sport": sport,
            "year": year,
            "sets_found": len(sets),
            "sets": sets,
            "message": f"Successfully scraped {len(sets)} sets for {sport} {year}"
        }
    except Exception as e:
        return {
            "success": False,
            "sport": sport,
            "year": year,
            "error": str(e),
            "message": f"Failed to scrape sets for {sport} {year}"
        }

@mcp.tool
def scrape_cards_for_set(set_name: str, limit: Optional[int] = 100) -> Dict[str, Any]:
    """
    Scrape cards for a specific set
    
    Args:
        set_name: The name of the set to scrape cards for
        limit: Maximum number of cards to scrape (default: 100)
    
    Returns:
        Dictionary containing scraped cards and status
    """
    try:
        pipeline = UnifiedPipeline()
        cards = pipeline.scrape_cards_for_set(set_name, limit=limit)
        return {
            "success": True,
            "set_name": set_name,
            "cards_found": len(cards),
            "cards": cards[:limit] if limit else cards,
            "message": f"Successfully scraped {len(cards)} cards for set {set_name}"
        }
    except Exception as e:
        return {
            "success": False,
            "set_name": set_name,
            "error": str(e),
            "message": f"Failed to scrape cards for set {set_name}"
        }

@mcp.tool
def get_database_stats() -> Dict[str, Any]:
    """
    Get statistics about the scraped data in the database
    
    Returns:
        Dictionary containing database statistics
    """
    try:
        stats = db_helper.get_database_stats()
        return {
            "success": True,
            "stats": stats,
            "message": "Successfully retrieved database statistics"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve database statistics"
        }

@mcp.tool
def search_cards(query: str, limit: Optional[int] = 50) -> Dict[str, Any]:
    """
    Search for cards in the database
    
    Args:
        query: Search query (searches card names, set names, etc.)
        limit: Maximum number of results to return (default: 50)
    
    Returns:
        Dictionary containing search results
    """
    try:
        results = db_helper.search_cards(query, limit=limit)
        return {
            "success": True,
            "query": query,
            "results_found": len(results),
            "results": results,
            "message": f"Found {len(results)} cards matching '{query}'"
        }
    except Exception as e:
        return {
            "success": False,
            "query": query,
            "error": str(e),
            "message": f"Failed to search for cards with query '{query}'"
        }

@mcp.tool
def run_full_pipeline(sport: str, year: str, set_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the full scraping pipeline for a sport, year, and optionally a specific set
    
    Args:
        sport: The sport to scrape
        year: The year to scrape
        set_name: Optional specific set to scrape (if None, scrapes all sets)
    
    Returns:
        Dictionary containing pipeline execution results
    """
    try:
        orchestrator = MultiLevelOrchestrator()
        results = orchestrator.run_full_pipeline(sport, year, set_name)
        return {
            "success": True,
            "sport": sport,
            "year": year,
            "set_name": set_name,
            "results": results,
            "message": f"Successfully completed full pipeline for {sport} {year}"
        }
    except Exception as e:
        return {
            "success": False,
            "sport": sport,
            "year": year,
            "set_name": set_name,
            "error": str(e),
            "message": f"Failed to run full pipeline for {sport} {year}"
        }

@mcp.tool
def get_available_sports() -> Dict[str, Any]:
    """
    Get list of available sports that can be scraped
    
    Returns:
        Dictionary containing available sports
    """
    try:
        # This would typically come from your configuration or database
        sports = ["baseball", "football", "basketball", "hockey", "soccer"]
        return {
            "success": True,
            "sports": sports,
            "count": len(sports),
            "message": f"Found {len(sports)} available sports"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve available sports"
        }

@mcp.tool
def get_pipeline_status() -> Dict[str, Any]:
    """
    Get the current status of the scraping pipeline
    
    Returns:
        Dictionary containing pipeline status information
    """
    try:
        # This would check the actual pipeline status
        status = {
            "pipeline_running": False,
            "last_run": "2024-01-01T00:00:00Z",
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0
        }
        return {
            "success": True,
            "status": status,
            "message": "Successfully retrieved pipeline status"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve pipeline status"
        }

if __name__ == "__main__":
    print("🚀 Starting TAG Grading Scraper FastMCP Server...")
    print("📚 Available tools:")
    print("  - scrape_sport_years: Scrape available years for a sport")
    print("  - scrape_sets_for_year: Scrape sets for a sport/year")
    print("  - scrape_cards_for_set: Scrape cards for a specific set")
    print("  - get_database_stats: Get database statistics")
    print("  - search_cards: Search for cards in the database")
    print("  - run_full_pipeline: Run the complete scraping pipeline")
    print("  - get_available_sports: Get list of available sports")
    print("  - get_pipeline_status: Get pipeline status")
    print("\n🔌 Server ready to accept MCP connections!")
    
    # Run the FastMCP server
    mcp.run()
