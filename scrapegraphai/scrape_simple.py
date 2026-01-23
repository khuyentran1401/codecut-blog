from pprint import pprint

from dotenv import load_dotenv
from scrapegraphai.graphs import SmartScraperGraph
import os

load_dotenv()

graph_config = {
    "llm": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "openai/gpt-4o-mini",
    },
    "verbose": False,
    "headless": True,
}

smart_scraper = SmartScraperGraph(
    prompt="Extract the first 5 book titles and their prices",
    source="https://books.toscrape.com",
    config=graph_config,
)

result = smart_scraper.run()
pprint(result)
