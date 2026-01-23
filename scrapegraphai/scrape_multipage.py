from scrapegraphai.graphs import SearchGraph
import os
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

graph_config = {
    "llm": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "openai/gpt-4o-mini",
    },
    "max_results": 3,
    "verbose": False,
}

search_graph = SearchGraph(
    prompt="Find the top 3 Python web scraping libraries and their GitHub stars",
    config=graph_config,
)

result = search_graph.run()
pprint(result)
