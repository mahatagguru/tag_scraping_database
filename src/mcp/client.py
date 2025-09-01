"""
FastMCP Client Example for TAG Grading Scraper
Demonstrates how to connect to and use the FastMCP server
"""

import asyncio
import json
from typing import Any, Dict

from fastmcp import FastMCPClient


async def main():
    """Main client example function"""
    
    # Initialize FastMCP client
    client = FastMCPClient("TAG Scraper Client 🏷️")
    
    try:
        # Connect to the FastMCP server
        print("🔌 Connecting to TAG Grading Scraper FastMCP Server...")
        await client.connect("localhost:8000")
        
        print("✅ Connected successfully!")
        print(f"📋 Server: {client.server_info}")
        
        # Example 1: Get available sports
        print("\n🏈 Getting available sports...")
        sports_result = await client.call_tool("get_available_sports", {})
        print(f"Sports: {json.dumps(sports_result, indent=2)}")
        
        # Example 2: Get database statistics
        print("\n📊 Getting database statistics...")
        stats_result = await client.call_tool("get_database_stats", {})
        print(f"Database Stats: {json.dumps(stats_result, indent=2)}")
        
        # Example 3: Search for cards
        print("\n🔍 Searching for cards...")
        search_result = await client.call_tool("search_cards", {
            "query": "baseball",
            "limit": 10
        })
        print(f"Search Results: {json.dumps(search_result, indent=2)}")
        
        # Example 4: Get pipeline status
        print("\n📈 Getting pipeline status...")
        status_result = await client.call_tool("get_pipeline_status", {})
        print(f"Pipeline Status: {json.dumps(status_result, indent=2)}")
        
        # Example 5: Scrape sport years (if you want to test actual scraping)
        print("\n⚾ Scraping baseball years...")
        years_result = await client.call_tool("scrape_sport_years", {
            "sport": "baseball"
        })
        print(f"Baseball Years: {json.dumps(years_result, indent=2)}")
        
        # Example 6: Get card totals by type
        print("\n📊 Getting card totals by type...")
        totals_result = await client.call_tool("get_card_totals_by_type", {
            "card_type": "rookie",
            "sport": "baseball"
        })
        print(f"Card Totals: {json.dumps(totals_result, indent=2)}")
        
        # Example 7: Analyze card scores
        print("\n⭐ Analyzing card scores...")
        scores_result = await client.call_tool("get_card_scores_analysis", {
            "min_score": 9.0,
            "sport": "baseball"
        })
        print(f"Score Analysis: {json.dumps(scores_result, indent=2)}")
        
        # Example 8: Get player collection
        print("\n👤 Getting player collection...")
        player_result = await client.call_tool("get_player_card_collection", {
            "player_name": "Mike Trout",
            "sport": "baseball",
            "min_grade": 9.0
        })
        print(f"Player Collection: {json.dumps(player_result, indent=2)}")
        
        # Example 9: Market trends analysis
        print("\n📈 Analyzing market trends...")
        trends_result = await client.call_tool("get_market_trends_analysis", {
            "days": 30,
            "sport": "baseball",
            "card_type": "rookie"
        })
        print(f"Market Trends: {json.dumps(trends_result, indent=2)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Close the connection
        await client.close()
        print("\n🔌 Connection closed")

def run_sync_example():
    """Synchronous version of the client example"""
    
    # Initialize FastMCP client
    client = FastMCPClient("TAG Scraper Client 🏷️")
    
    try:
        # Connect to the FastMCP server
        print("🔌 Connecting to TAG Grading Scraper FastMCP Server...")
        client.connect_sync("localhost:8000")
        
        print("✅ Connected successfully!")
        print(f"📋 Server: {client.server_info}")
        
        # Example 1: Get available sports
        print("\n🏈 Getting available sports...")
        sports_result = client.call_tool_sync("get_available_sports", {})
        print(f"Sports: {json.dumps(sports_result, indent=2)}")
        
        # Example 2: Get database statistics
        print("\n📊 Getting database statistics...")
        stats_result = client.call_tool_sync("get_database_stats", {})
        print(f"Database Stats: {json.dumps(stats_result, indent=2)}")
        
        # Example 3: Search for cards
        print("\n🔍 Searching for cards...")
        search_result = client.call_tool_sync("search_cards", {
            "query": "baseball",
            "limit": 10
        })
        print(f"Search Results: {json.dumps(search_result, indent=2)}")
        
        # Example 4: Get pipeline status
        print("\n📈 Getting pipeline status...")
        status_result = client.call_tool_sync("get_pipeline_status", {})
        print(f"Pipeline Status: {json.dumps(status_result, indent=2)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Close the connection
        client.close_sync()
        print("\n🔌 Connection closed")

if __name__ == "__main__":
    print("🚀 FastMCP Client Example for TAG Grading Scraper")
    print("=" * 50)
    
    # Choose between async and sync examples
    print("\nChoose an example:")
    print("1. Asynchronous client (recommended)")
    print("2. Synchronous client")
    
    choice = input("Enter your choice (1 or 2): ").strip()
    
    if choice == "1":
        print("\n🔄 Running asynchronous example...")
        asyncio.run(main())
    elif choice == "2":
        print("\n⚡ Running synchronous example...")
        run_sync_example()
    else:
        print("❌ Invalid choice. Running asynchronous example by default...")
        asyncio.run(main())
