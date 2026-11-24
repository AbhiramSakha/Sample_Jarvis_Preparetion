from tools.registry import registry

try:
    from ddgs import DDGS
except ImportError:  # older package name
    from duckduckgo_search import DDGS


@registry.register(
    "web_search",
    "Search the web for current information, news or facts. Returns top results.",
    {"query": {"type": "string", "description": "Search query"}},
    ["query"],
)
def web_search(query: str):
    results = DDGS().text(query, max_results=5)
    if not results:
        return "No results found."
    return "\n".join(f"- {r['title']}: {r['body']}" for r in results)