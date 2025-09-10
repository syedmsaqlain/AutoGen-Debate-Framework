import os
from dotenv import load_dotenv
from autogen import AssistantAgent, UserProxyAgent, config_list_from_json

# Load environment variables
load_dotenv()

# Load LLM configuration
config_list = config_list_from_json(
    "OAI_CONFIG_LIST.json",
    file_location=".",
    filter_dict={
        "model": ["gemini-2.5-flash-lite"],
    },
)

llm_config = {
    "config_list": config_list,
    "timeout": 120,
    "temperature": 0.7,
}




def get_web_search_urls(query: str, max_results: int = 5) -> str:
    """Perform web searches and return formatted results for AI agents"""
    try:
        # Try both old and new package names
        try:
            from ddgs import DDGS  # New package name
        except ImportError:
            from duckduckgo_search import DDGS  # Old package name
            
        print(f"🔍 Searching for: {query}")
        
        with DDGS() as ddgs:
            results = []
            for result in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": result.get("title", "No title"),
                    "url": result.get("href", "No URL"), 
                    "summary": result.get("body", "No content")[:150] + "..."
                })
            
            print(f"✅ Found {len(results)} results")
            
            # Format for AI consumption (not too verbose)
            if not results:
                return "No relevant search results found for this topic."
            
            formatted = f"Search results for '{query}':\n\n"
            for i, result in enumerate(results, 1):
                formatted += f"{i}. {result['title']}\n"
                formatted += f"   URL: {result['url']}\n"
                formatted += f"   Summary: {result['summary']}\n\n"
            
            return formatted
            
    except Exception as e:
        print(f"❌ Search error: {e}")
        return f"Web search failed due to technical error: {str(e)}"


