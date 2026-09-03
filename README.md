# Multi-Agent Research Pipeline

A sophisticated multi-agent system for automated research, web scraping, and content generation using LangChain, Google Gemini, and Streamlit.

## Overview

This system orchestrates multiple AI agents to perform comprehensive research tasks:
- **Search Agent**: Performs intelligent web searches using Tavily API
- **Scraper Agent**: Extracts and processes content from webpages
- **Writer Agent**: Generates well-structured research content
- **Critic Agent**: Reviews and refines generated content

## Features

- **Web Search**: Intelligent search powered by Tavily API
- **Web Scraping**: Extract content from webpages using BeautifulSoup
- **Multi-Agent Orchestration**: Coordinated agent pipeline for complex tasks
- **Streamlit UI**: Beautiful, interactive web interface
- **Fallback LLM Support**: Automatic failover between Gemini models
- **Streaming Support**: Real-time response streaming

## Installation

1. **Clone or download the project**
   ```bash
   cd multi\ agent\ sys
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   \.venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```
   GOOGLE_API_KEY=your_google_gemini_api_key
   TAVILY_API_KEY=your_tavily_api_key
   ```

## Usage

Run the Streamlit application:
```bash
streamlit run app.py
```

The application will launch at `http://localhost:8501` in your default browser.

## Project Structure

```
├── app.py              # Streamlit UI and main application
├── pipeline.py         # Research pipeline orchestration
├── agents.py           # LangChain agent definitions
├── tools.py            # Web search and scraping tools
├── requirements.txt    # Project dependencies
└── README.md          # This file
```

## Key Components

### app.py
Streamlit application providing an interactive interface for the research pipeline. Features custom styling and real-time response streaming.

### pipeline.py
Orchestrates the multi-agent workflow:
- `run_research_pipeline()` - Standard synchronous pipeline execution
- `run_research_pipeline_stream()` - Streaming pipeline for real-time feedback

### agents.py
Defines and manages AI agents:
- **Search Agent**: Queries web using Tavily API
- **Scrape Agent**: Extracts webpage content
- **Writer Chain**: Generates comprehensive research content
- **Critic Chain**: Refines and validates output

Uses fallback LLM strategy with:
- Primary: `gemini-3.5-flash-lite` (fast, cost-effective)
- Fallback: `gemini-3.7-flash` (more capable)

### tools.py
Implements LangChain tools:
- `web_search(query)` - Search the web and return top results
- `scrape(url)` - Extract and clean webpage content

## Dependencies

- **LLM & Agents**: LangChain, Google Generative AI
- **Web Tools**: Tavily API, BeautifulSoup, requests
- **UI**: Streamlit, Rich
- **Utilities**: python-dotenv

See `requirements.txt` for complete list and versions.

## API Keys Required

1. **Google Gemini API**: For LLM capabilities
   - Get it from: https://makersuite.google.com/app/apikey

2. **Tavily API**: For web search
   - Get it from: https://app.tavily.com

## Error Handling

The system includes robust error handling:
- LLM fallback mechanism for model failures
- Graceful timeout handling (120s primary, 60s fallback)
- Retry logic with exponential backoff
- Input validation for search queries and URLs

## Performance Features

- **Max Output Tokens**: 1024 tokens per response
- **Temperature**: 0.2 (lower = more consistent, less creative)
- **Max Retries**: 6 for primary, 3 for fallback
- **Timeout**: 120s primary, 60s fallback

## Development

To extend the system:

1. Add new tools in `tools.py` using the `@tool` decorator
2. Create new agents in `agents.py` using `_build_agent()`
3. Update the pipeline in `pipeline.py` with new agent calls
4. Add UI controls in `app.py` for new functionality

## License

Specify your license here (e.g., MIT, Apache 2.0)

## Support

For issues or questions, please create an issue in the repository or contact the development team.
