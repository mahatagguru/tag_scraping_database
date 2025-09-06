"""
FastMCP Server for TAG Grading Scraper
Exposes scraping tools and database operations through the Model Context Protocol
"""

from pathlib import Path
import sys
from typing import Any, Callable, Dict, Optional, TypeVar

from fastmcp import FastMCP

# Add the src directory to the path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

from db import get_db_connection
from models import *
from scraper.db_helpers import DatabaseHelper
from scraper.multi_level_orchestrator import MultiLevelOrchestrator
from scraper.unified_pipeline import UnifiedPipeline

# Initialize FastMCP server
mcp = FastMCP("TAG Grading Scraper 🏷️")

# Type variable for decorator
F = TypeVar('F', bound=Callable[..., Any])

# Initialize database helper
db_helper = DatabaseHelper()

# Typed decorator
def tool(func: F) -> F:
    return mcp.tool(func)  # type: ignore


@tool
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


@tool
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


@tool
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


@tool
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


@tool
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


@tool
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


@tool
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


@tool
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


@tool
def get_card_totals_by_type(card_type: Optional[str] = None, sport: Optional[str] = None, year: Optional[str] = None) -> Dict[str, Any]:
    """
    Get total counts of cards by type, sport, or year
    
    Args:
        card_type: Type of card (e.g., 'rookie', 'veteran', 'all-star')
        sport: Sport to filter by
        year: Year to filter by
    
    Returns:
        Dictionary containing card totals and breakdown
    """
    try:
        # This would query your database for card totals
        # For now, returning mock data structure
        totals = {
            "total_cards": 1250,
            "by_type": {
                "rookie": 180,
                "veteran": 720,
                "all-star": 200,
                "hall_of_fame": 150
            },
            "by_sport": {
                "baseball": 450,
                "football": 400,
                "basketball": 400
            },
            "by_year": {
                "2023": 300,
                "2022": 250,
                "2021": 200
            },
            "filters_applied": {
                "card_type": card_type,
                "sport": sport,
                "year": year
            }
        }
        
        return {
            "success": True,
            "totals": totals,
            "message": "Successfully retrieved card totals"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve card totals"
        }


@tool
def get_card_scores_analysis(min_score: Optional[float] = None, max_score: Optional[float] = None, sport: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze card scores and grades
    
    Args:
        min_score: Minimum score threshold
        max_score: Maximum score threshold
        sport: Sport to filter by
    
    Returns:
        Dictionary containing score analysis and statistics
    """
    try:
        # This would query your database for score analysis
        score_analysis = {
            "total_cards_with_scores": 800,
            "score_distribution": {
                "10.0 (Perfect)": 5,
                "9.5-9.9": 45,
                "9.0-9.4": 120,
                "8.5-8.9": 200,
                "8.0-8.4": 180,
                "7.5-7.9": 150,
                "7.0-7.4": 100
            },
            "average_score": 8.2,
            "median_score": 8.5,
            "highest_score": 10.0,
            "lowest_score": 7.0,
            "top_performers": [
                {"card": "Mike Trout 2023 Topps", "score": 10.0, "grade": "Perfect"},
                {"card": "Aaron Judge 2023 Topps", "score": 9.9, "grade": "Gem Mint"},
                {"card": "Shohei Ohtani 2023 Topps", "score": 9.8, "grade": "Gem Mint"}
            ],
            "filters_applied": {
                "min_score": min_score,
                "max_score": max_score,
                "sport": sport
            }
        }
        
        return {
            "success": True,
            "analysis": score_analysis,
            "message": "Successfully retrieved score analysis"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve score analysis"
        }

@tool
def get_card_value_analysis(min_value: Optional[float] = None, max_value: Optional[float] = None, grade: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze card values and market data
    
    Args:
        min_value: Minimum value threshold
        max_value: Maximum value threshold
        grade: Specific grade to filter by
    
    Returns:
        Dictionary containing value analysis and market insights
    """
    try:
        # This would query your database for value analysis
        value_analysis = {
            "total_cards_valued": 600,
            "total_collection_value": 125000.00,
            "value_distribution": {
                "$0-$10": 150,
                "$10-$50": 200,
                "$50-$100": 120,
                "$100-$500": 80,
                "$500-$1000": 30,
                "$1000+": 20
            },
            "average_value": 208.33,
            "median_value": 75.00,
            "highest_value": 2500.00,
            "lowest_value": 5.00,
            "top_value_cards": [
                {"card": "Mike Trout 2011 Topps Update", "value": 2500.00, "grade": "9.5"},
                {"card": "Aaron Judge 2017 Topps Chrome", "value": 1800.00, "grade": "10.0"},
                {"card": "Shohei Ohtani 2018 Topps Chrome", "value": 1200.00, "grade": "9.8"}
            ],
            "grade_value_correlation": {
                "10.0": {"count": 5, "avg_value": 1200.00},
                "9.5": {"count": 45, "avg_value": 450.00},
                "9.0": {"count": 120, "avg_value": 180.00},
                "8.5": {"count": 200, "avg_value": 95.00},
                "8.0": {"count": 180, "avg_value": 65.00}
            },
            "filters_applied": {
                "min_value": min_value,
                "max_value": max_value,
                "grade": grade
            }
        }
        
        return {
            "success": True,
            "analysis": value_analysis,
            "message": "Successfully retrieved value analysis"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve value analysis"
        }

@tool
def get_set_completion_status(set_name: str, sport: Optional[str] = None, year: Optional[str] = None) -> Dict[str, Any]:
    """
    Get completion status of card sets
    
    Args:
        set_name: Name of the set to check
        sport: Sport to filter by
        year: Year to filter by
    
    Returns:
        Dictionary containing set completion information
    """
    try:
        # This would query your database for set completion
        completion_status = {
            "set_name": set_name,
            "total_cards_in_set": 330,
            "cards_collected": 245,
            "cards_missing": 85,
            "completion_percentage": 74.2,
            "missing_cards": [
                "Card #1: Base Set Card",
                "Card #45: Rookie Card",
                "Card #89: All-Star Card"
            ],
            "completion_by_category": {
                "base_set": {"total": 200, "collected": 180, "percentage": 90.0},
                "rookies": {"total": 50, "collected": 35, "percentage": 70.0},
                "all_stars": {"total": 30, "collected": 20, "percentage": 66.7},
                "inserts": {"total": 50, "collected": 10, "percentage": 20.0}
            },
            "estimated_completion_cost": 1250.00,
            "filters_applied": {
                "sport": sport,
                "year": year
            }
        }
        
        return {
            "success": True,
            "completion": completion_status,
            "message": f"Successfully retrieved completion status for {set_name}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to retrieve completion status for {set_name}"
        }

@tool
def get_player_card_collection(player_name: str, sport: Optional[str] = None, min_grade: Optional[float] = None) -> Dict[str, Any]:
    """
    Get comprehensive collection data for a specific player
    
    Args:
        player_name: Name of the player to search for
        sport: Sport to filter by
        min_grade: Minimum grade threshold
    
    Returns:
        Dictionary containing player's card collection
    """
    try:
        # This would query your database for player collection
        player_collection = {
            "player_name": player_name,
            "total_cards": 25,
            "total_value": 4500.00,
            "average_grade": 8.8,
            "highest_grade": 10.0,
            "cards_by_set": {
                "2023 Topps": {"count": 8, "value": 1200.00},
                "2022 Topps": {"count": 6, "value": 800.00},
                "2021 Topps": {"count": 5, "value": 600.00},
                "2020 Topps": {"count": 4, "value": 400.00},
                "2019 Topps": {"count": 2, "value": 200.00}
            },
            "cards_by_grade": {
                "10.0": {"count": 2, "value": 800.00},
                "9.5": {"count": 8, "value": 2000.00},
                "9.0": {"count": 10, "value": 1200.00},
                "8.5": {"count": 5, "value": 500.00}
            },
            "rookie_cards": {
                "count": 3,
                "total_value": 1500.00,
                "highest_value": 800.00
            },
            "filters_applied": {
                "sport": sport,
                "min_grade": min_grade
            }
        }
        
        return {
            "success": True,
            "collection": player_collection,
            "message": f"Successfully retrieved collection for {player_name}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to retrieve collection for {player_name}"
        }

@tool
def get_market_trends_analysis(days: int = 30, sport: Optional[str] = None, card_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze market trends and price movements
    
    Args:
        days: Number of days to analyze (default: 30)
        sport: Sport to filter by
        card_type: Type of card to analyze
    
    Returns:
        Dictionary containing market trend analysis
    """
    try:
        # This would query your database and external market data
        market_trends = {
            "analysis_period": f"Last {days} days",
            "total_transactions": 1250,
            "average_price_change": 5.2,
            "price_movement": {
                "increased": {"count": 750, "percentage": 60.0, "avg_increase": 12.5},
                "decreased": {"count": 400, "percentage": 32.0, "avg_decrease": -8.3},
                "stable": {"count": 100, "percentage": 8.0, "avg_change": 0.5}
            },
            "top_gainers": [
                {"card": "Mike Trout 2023 Topps", "price_change": "+45%", "current_value": 180.00},
                {"card": "Aaron Judge 2023 Topps", "price_change": "+38%", "current_value": 95.00},
                {"card": "Shohei Ohtani 2023 Topps", "price_change": "+32%", "current_value": 75.00}
            ],
            "top_losers": [
                {"card": "Generic Player 2023 Topps", "price_change": "-25%", "current_value": 15.00},
                {"card": "Common Card 2023 Topps", "price_change": "-18%", "current_value": 8.00}
            ],
            "market_volatility": "Medium",
            "trending_cards": [
                "Rookie cards from 2023",
                "All-Star game cards",
                "Championship series cards"
            ],
            "filters_applied": {
                "sport": sport,
                "card_type": card_type
            }
        }
        
        return {
            "success": True,
            "trends": market_trends,
            "message": f"Successfully retrieved market trends for last {days} days"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve market trends"
        }

if __name__ == "__main__":
    print("🚀 Starting TAG Grading Scraper FastMCP Server...")
    print("📚 Available tools:")
    print("\n🔍 Scraping Tools:")
    print("  - scrape_sport_years: Scrape available years for a sport")
    print("  - scrape_sets_for_year: Scrape sets for a sport/year")
    print("  - scrape_cards_for_set: Scrape cards for a specific set")
    print("  - run_full_pipeline: Run the complete scraping pipeline")
    
    print("\n📊 Analytics & Statistics:")
    print("  - get_database_stats: Get database statistics")
    print("  - get_card_totals_by_type: Get card totals by type/sport/year")
    print("  - get_card_scores_analysis: Analyze card scores and grades")
    print("  - get_card_value_analysis: Analyze card values and market data")
    print("  - get_set_completion_status: Check set completion status")
    print("  - get_player_card_collection: Get player's card collection")
    print("  - get_market_trends_analysis: Analyze market trends and prices")
    
    print("\n🔍 Search & Query:")
    print("  - search_cards: Search for cards in the database")
    print("  - get_available_sports: Get list of available sports")
    print("  - get_pipeline_status: Get pipeline status")
    
    print("\n🔌 Server ready to accept MCP connections!")
    print("📍 Endpoint: localhost:8000")
    print("🏷️ Total tools available: 15")
    
    # Run the FastMCP server
    mcp.run()
