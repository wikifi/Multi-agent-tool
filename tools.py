from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


@tool
def web_search(query: str) -> dict | str:
    """
    Perform a web search using Tavily API and return the top result.
    """
    if not query or not query.strip():
        return "No search query provided."

    try:
        results = tavily.search(query=query, max_results=5, timeout=15)
    except Exception as e:
        return f"Search failed: {e}"

    out = []

    for result in results.get("results", []):
        url = result.get("url")
        if not url:
            continue
        out.append(
            f"Title: {result.get('title', 'Untitled')}\n"
            f"URL: {url}\n"
            f"Snippet: {result.get('content', '')}\n"
        )

    return "\n----\n".join(out) if out else "No search results found."


@tool
def scrape(url: str) -> str:
    """
    Scrape the content of a webpage and return the text.
    """
    if not url or not str(url).strip():
        return "No URL was provided."

    try:
        resp = requests.get(
            url,
            timeout=12,
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
        )
        if resp.status_code >= 400:
            return f"Error fetching the URL: {resp.status_code} {resp.reason} for {url}"

        soup = BeautifulSoup(resp.text, 'html.parser')
        for tag in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
            tag.decompose()
        text = soup.get_text(separator='\n', strip=True)

        if not text:
            return f"No readable text found on: {url}"

        # Cap the returned text so a long article/docs page can't blow past
        # the model's context/output limits downstream in the writer chain.
        MAX_CHARS = 8000
        if len(text) > MAX_CHARS:
            return text[:MAX_CHARS] + "\n...[truncated]"
        return text
    except requests.RequestException as e:
        return f"Error fetching the URL: {e}"
    except Exception as e:
        return f"Error processing the URL: {e}"