from pprint import pprint
from scrapegraphai.graphs import SmartScraperGraph
import os

from dotenv import load_dotenv

load_dotenv()

graph_config = {
    "llm": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "openai/gpt-4o-mini",
    },
    "verbose": False,
    "headless": True,  # Browser runs in background
}

# quotes.toscrape.com/js loads content via JavaScript
smart_scraper = SmartScraperGraph(
    prompt="Extract the first 3 quotes with their text and authors",
    source="https://quotes.toscrape.com/js/",
    config=graph_config,
)

result = smart_scraper.run()
pprint(result)
