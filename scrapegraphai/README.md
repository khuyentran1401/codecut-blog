# ScrapeGraphAI Source Code

Source code for the article: [From CSS Selectors to Natural Language: Web Scraping with ScrapeGraphAI](https://codecut.ai/scrapegraphai-web-scraping-natural-language/)

## Files

| File | Article Section |
|------|-----------------|
| `scrape_simple.py` | [Natural Language Prompts](https://codecut.ai/scrapegraphai-web-scraping-natural-language/#natural-language-prompts) |
| `scrape_pydantic.py` | [Structured Output with Pydantic](https://codecut.ai/scrapegraphai-web-scraping-natural-language/#structured-output-with-pydantic) |
| `scrape_javascript.py` | [JavaScript Content](https://codecut.ai/scrapegraphai-web-scraping-natural-language/#javascript-content) |
| `scrape_multipage.py` | [Multi-Page Scraping](https://codecut.ai/scrapegraphai-web-scraping-natural-language/#multi-page-scraping) (SearchGraph) |
| `scrape_multipage_known.py` | [Multi-Page Scraping](https://codecut.ai/scrapegraphai-web-scraping-natural-language/#multi-page-scraping) (SmartScraperMultiGraph) |

## Setup

1. Install dependencies:
   ```bash
   pip install scrapegraphai playwright python-dotenv
   playwright install
   ```

2. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

3. Run any script:
   ```bash
   python scrape_simple.py
   ```
