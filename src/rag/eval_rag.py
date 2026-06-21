"""
Faithfulness Evaluation Harness for KB Search

Evaluates the faithfulness of LLM-generated answers grounded in knowledge base context
retrieved by the search_kb function.
"""

import os
import sys
from pathlib import Path

from langchain_openai import ChatOpenAI


def get_llm_client():
    """
    Initialize LLM client from environment variables.
    
    Prefers GITHUB_TOKEN with Azure endpoint, falls back to OPENAI_API_KEY.
    
    Returns:
        ChatOpenAI: Configured LLM client
        
    Raises:
        ValueError: If neither GITHUB_TOKEN nor OPENAI_API_KEY is set
    """
    github_token = os.getenv("GITHUB_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if github_token:
        # Use GitHub token with Azure endpoint
        client = ChatOpenAI(
            api_key=github_token,
            model="gpt-4o-mini",
            base_url="https://models.inference.ai.azure.com",
        )
        return client
    elif openai_key:
        # Use OpenAI API key
        client = ChatOpenAI(
            api_key=openai_key,
            model="gpt-3.5-turbo",
        )
        return client
    else:
        raise ValueError(
            "No API key found. Set GITHUB_TOKEN or OPENAI_API_KEY environment variable."
        )


def generate_answer(query: str, context: str, llm) -> str:
    """
    Generate an answer using the LLM based on query and context.
    
    Args:
        query: The user query
        context: The retrieved context from knowledge base
        llm: Configured LLM client
        
    Returns:
        str: Generated answer
    """
    prompt = f"""Based on the following context, answer the query concisely.
You must ground your answer in the context provided.
If the context contains specific facts (numbers, dates, names), include them in your answer.

Context:
{context}

Query: {query}

Answer (grounded in context):"""
    
    response = llm.invoke(prompt)
    return response.content


def compute_faithfulness_score(context: str, answer: str) -> float:
    """
    Compute faithfulness score based on context-answer alignment.
    
    Improved scoring considers:
    - Exact phrase/fact matching (numbers, dates, names)
    - Key keyword presence (weighted by importance)
    - Stop word filtering
    Range: 0.0 to 1.0 (higher is more faithful).
    
    Args:
        context: Retrieved context from knowledge base
        answer: LLM-generated answer
        
    Returns:
        float: Faithfulness score (0.0 to 1.0)
    """
    context_lower = context.lower()
    answer_lower = answer.lower()
    
    # Common stop words to ignore
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
        'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which',
        'who', 'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both',
        'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
        'only', 'same', 'so', 'than', 'too', 'very', 'as', 'if', 'just'
    }
    
    # Extract meaningful words (length > 3, not stop words)
    context_words = set(
        word.strip('.,!?;:""\'') 
        for word in context_lower.split() 
        if len(word.strip('.,!?;:""\'')) > 3 and word.lower() not in stop_words
    )
    
    # If no meaningful context words, trivially faithful
    if not context_words:
        return 1.0
    
    # Extract words from answer
    answer_words = set(
        word.strip('.,!?;:""\'') 
        for word in answer_lower.split()
    )
    
    # Score 1: Keyword matching (40% weight)
    # Only count meaningful words
    answer_meaningful = {
        w for w in answer_words 
        if len(w) > 3 and w not in stop_words
    }
    matching_words = len(context_words & answer_meaningful)
    keyword_score = min(1.0, matching_words / max(len(context_words), 1))
    
    # Score 2: Exact phrase/fact matching (60% weight)
    # Look for critical facts: numbers, proper nouns from context
    facts_score = 1.0
    context_sentences = [s.strip() for s in context.split('.') if s.strip()]
    
    # Extract numerical facts and proper nouns (capitalized)
    critical_facts = []
    for sentence in context_sentences:
        # Extract numbers
        import re
        numbers = re.findall(r'\b\d+\b', sentence)
        critical_facts.extend(numbers)
        
        # Extract capitalized terms (proper nouns/activity names)
        proper_nouns = [word for word in sentence.split() 
                       if word and word[0].isupper() and len(word) > 3]
        critical_facts.extend(proper_nouns)
    
    # Check if critical facts appear in answer
    facts_found = sum(1 for fact in critical_facts if fact.lower() in answer_lower)
    if critical_facts:
        facts_score = facts_found / len(critical_facts)
    else:
        facts_score = 1.0
    
    # Combined score: 40% keyword matching + 60% fact matching
    combined_score = (0.4 * keyword_score) + (0.6 * facts_score)
    
    return min(1.0, combined_score)


def run_ragas_eval():
    """
    Run faithfulness evaluation on test cases.
    
    Returns:
        int: Exit code (0 if passed, 1 if failed)
    """
    # Import search_kb
    from kb_search import search_kb
    
    # Define test cases
    test_cases = [
        {
            "query": "how many people can join chess club",
            "expected_context": "12",
            "description": "Max participants for Chess Club"
        },
        {
            "query": "when does basketball practice run",
            "expected_context": "Monday",
            "description": "Basketball schedule"
        },
        {
            "query": "which activity allows most participants",
            "expected_context": "30",
            "description": "Highest participant capacity"
        },
        {
            "query": "is there a daily activity",
            "expected_context": "Daily",
            "description": "Daily activities"
        }
    ]
    
    # Initialize LLM
    llm = get_llm_client()
    
    # Store results
    results = []
    
    print("\n" + "=" * 70)
    print("Faithfulness Evaluation for KB Search")
    print("=" * 70)
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        expected = test_case["expected_context"]
        
        print(f"\nTest Case {i}: {test_case['description']}")
        print(f"  Query: {query}")
        
        # Retrieve context using search_kb
        search_results = search_kb(query, top_k=3)
        
        if not search_results:
            print("  ERROR: No results retrieved from knowledge base")
            context = "No context available"
            answer = "No answer available"
            faithfulness = 0.0
        else:
            # Format context from retrieved results
            context_parts = []
            for result in search_results:
                context_parts.append(
                    f"Title: {result['title']}\n"
                    f"Description: {result['description']}"
                )
            context = "\n\n".join(context_parts)
            
            # Check if expected context is present
            context_found = expected.lower() in context.lower()
            print(f"  Expected content: '{expected}'")
            print(f"  Content found in results: {context_found}")
            
            # Generate answer
            answer = generate_answer(query, context, llm)
            print(f"  Answer: {answer[:100]}..." if len(answer) > 100 else f"  Answer: {answer}")
            
            # Compute faithfulness
            faithfulness = compute_faithfulness_score(context, answer)
        
        print(f"  Faithfulness Score: {faithfulness:.4f}")
        results.append(faithfulness)
    
    # Compute overall score
    print("\n" + "-" * 70)
    overall_score = sum(results) / len(results) if results else 0.0
    
    print(f"\nFaithfulness Scores by Test Case:")
    for i, score in enumerate(results, 1):
        print(f"  Test Case {i}: {score:.4f}")
    
    print(f"\nOverall Faithfulness Score: {overall_score:.4f}")
    
    # Determine pass/fail
    threshold = 0.85
    if overall_score >= threshold:
        print(f"✓ PASSED: Faithfulness score ({overall_score:.4f}) >= {threshold}")
        return 0
    else:
        print(f"✗ FAILED: Faithfulness score ({overall_score:.4f}) < {threshold}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = run_ragas_eval()
        sys.exit(exit_code)
    except Exception as e:
        print(f"Error running evaluation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
