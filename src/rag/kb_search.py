"""
Knowledge Base Search Module

Provides functionality to search an activities knowledge base and retrieve
the top matching entries based on keyword and semantic scoring.
"""

import json
import re
from pathlib import Path
from typing import Any


def search_kb(query: str, top_k: int = 3) -> list[dict]:
    """
    Search the activities knowledge base and return the top_k matching entries.

    This function performs keyword and semantic scoring:
    - Filters out stop words for more meaningful matching
    - Weights title matches higher than description matches
    - Handles semantic queries (e.g., "most participants" → sorts by max_participants)
    - Returns top_k entries ranked by relevance

    Args:
        query: The search query string (e.g., "chess tournament" or "most participants")
        top_k: Maximum number of results to return (default: 3)

    Returns:
        List of top_k knowledge base entries (dicts) ranked by keyword overlap score.
        Each entry preserves all fields from the knowledge base (id, title, description, etc.).

    Example:
        >>> results = search_kb("chess", top_k=2)
        >>> len(results) <= 2
        True
        >>> results[0]["title"]
        'Chess Club'
    """
    # Load the knowledge base JSON file
    kb_path = Path(__file__).parent / "activities_kb.json"
    
    if not kb_path.exists():
        return []
    
    with open(kb_path, "r", encoding="utf-8") as f:
        knowledge_base: list[dict] = json.load(f)
    
    # Stop words to filter out from scoring
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'which', 'that',
        'there', 'be', 'this', 'an', 'all', 'there', 'does', 'do'
    }
    
    query_lower = query.lower().strip()
    query_words = [w for w in query_lower.split() if w not in stop_words]
    
    # Detect semantic queries
    is_max_query = any(word in query_lower for word in ['most', 'maximum', 'max', 'highest', 'largest'])
    is_daily_query = 'daily' in query_lower
    
    # Score each entry
    scored_entries: list[tuple[dict, float]] = []
    
    for entry in knowledge_base:
        title = entry.get("title", "").lower()
        description = entry.get("description", "").lower()
        schedule = entry.get("schedule", "").lower()
        
        # Score title matches (higher weight: 3x)
        title_matches = sum(1 for word in query_words if word in title)
        
        # Score description matches (normal weight: 1x)
        description_matches = sum(1 for word in query_words if word in description)
        
        # Score schedule matches (2x weight for schedule-specific queries)
        schedule_matches = sum(1 for word in query_words if word in schedule)
        
        # Combined score
        base_score = (title_matches * 3) + description_matches + (schedule_matches * 2)
        
        # Semantic boosting
        if is_max_query:
            # Boost entries with high max_participants
            base_score += entry.get("max_participants", 0) / 10
        
        if is_daily_query:
            # Boost daily activities
            if 'daily' in schedule:
                base_score += 5
        
        if base_score > 0:
            scored_entries.append((entry, base_score))
    
    # Sort by score (descending)
    scored_entries.sort(key=lambda x: x[1], reverse=True)
    
    # Return top_k entries
    return [entry for entry, _ in scored_entries[:top_k]]



if __name__ == "__main__":
    # Sample queries
    sample_queries = [
        "chess",
        "basketball tournament",
        "art painting"
    ]
    
    print("Knowledge Base Search - Sample Queries\n")
    print("=" * 60)
    
    for query in sample_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 60)
        results = search_kb(query, top_k=3)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']}")
                print(f"   {result['description']}")
                print()
        else:
            print("No matching activities found.\n")
    
    print("=" * 60)
