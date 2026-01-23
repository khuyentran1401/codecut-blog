from scrapegraphai.graphs import SmartScraperMultiGraph
import os
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

graph_config = {
    "llm": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "openai/gpt-4o-mini",
    },
    "verbose": False,
    "headless": True,
}

multi_scraper = SmartScraperMultiGraph(
    prompt="Extract the page title and main heading",
    source=[
        "https://books.toscrape.com",
        "https://quotes.toscrape.com",
    ],
    config=graph_config,
)

result = multi_scraper.run()
pprint(result)
