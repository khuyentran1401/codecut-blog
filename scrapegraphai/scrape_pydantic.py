from pprint import pprint

from dotenv import load_dotenv
from scrapegraphai.graphs import SmartScraperGraph
from pydantic import BaseModel, Field
from typing import List
import os

load_dotenv()


class Book(BaseModel):
    title: str = Field(description="The title of the book")
    price: float = Field(description="Price in GBP as a number")
    rating: int = Field(description="Star rating from 1 to 5")


class BookCatalog(BaseModel):
    books: List[Book]


graph_config = {
    "llm": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "openai/gpt-4o-mini",
    },
    "verbose": False,
    "headless": True,
}

smart_scraper = SmartScraperGraph(
    prompt="Extract the first 3 books with their titles, prices, and star ratings",
    source="https://books.toscrape.com",
    schema=BookCatalog,
    config=graph_config,
)

result = smart_scraper.run()
pprint(result)
