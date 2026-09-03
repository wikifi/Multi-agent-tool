from langchain.agents import create_agent
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from tools import web_search, scrape
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# MODEL SETUP
# ============================================================

primary_llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    temperature=0.2,
    max_output_tokens=1024,
    max_retries=6,
    timeout=120,
)

fallback_llm = ChatGoogleGenerativeAI(
    model="gemini-3.7-flash",
    temperature=0.2,
    max_output_tokens=1024,
    max_retries=3,
    timeout=60,
)


# Used for normal chains
llm = primary_llm.with_fallbacks(
    [fallback_llm]
)


# ============================================================
# AGENT BUILDER
# ============================================================

def _build_agent(model_, tools, system_prompt):
    return create_agent(
        model=model_,
        tools=tools,
        system_prompt=system_prompt,
    )


def _invoke_agent_with_fallback(
    tools,
    payload,
    system_prompt
):
    """
    Try primary model first.
    If primary fails, retry using fallback model.
    """

    try:

        agent = _build_agent(
            primary_llm,
            tools,
            system_prompt
        )

        return agent.invoke(payload)

    except Exception as exc:

        print(
            f"\n[fallback] Primary model failed: "
            f"{exc.__class__.__name__}: {exc}"
        )

        print(
            "[fallback] Retrying with fallback model..."
        )

        agent = _build_agent(
            fallback_llm,
            tools,
            system_prompt
        )

        return agent.invoke(payload)


# ============================================================
# SEARCH AGENT
# ============================================================

SEARCH_AGENT_PROMPT = """
You are an expert web search agent.

Your ONLY responsibility is to search the web and find the
best and most recent sources for the user's research topic.

DO NOT write a full research report.

DO NOT provide a long explanation about the topic.

Use the web_search tool to search the internet.

After searching, return the results in this format:

SEARCH RESULTS

1. Title:
URL:
Why Relevant:

2. Title:
URL:
Why Relevant:

3. Title:
URL:
Why Relevant:

4. Title:
URL:
Why Relevant:

5. Title:
URL:
Why Relevant:

Rules:

- Find 3 to 5 highly relevant sources.
- Prefer recent information.
- Prefer authoritative sources.
- Prefer government, universities, research organizations,
  official organizations and reputable news sources.
- Always include the actual URL returned by the search tool.
- Do not invent URLs.
- Keep each explanation short.
- Do not write the final research report.
- Do not perform deep analysis.
"""


def build_search_agent():

    return create_agent(
        model=primary_llm,
        tools=[web_search],
        system_prompt=SEARCH_AGENT_PROMPT,
    )


def invoke_search_agent(payload):

    return _invoke_agent_with_fallback(
        tools=[web_search],
        payload=payload,
        system_prompt=SEARCH_AGENT_PROMPT,
    )


# ============================================================
# SCRAPE AGENT
# ============================================================

SCRAPE_AGENT_PROMPT = """
You are an expert web scraping research agent.

Your responsibility is to:

1. Read the search results provided by the user.
2. Identify the SINGLE most relevant URL.
3. Use the scrape tool to scrape that URL.
4. Extract useful factual information from the page.

Prefer:

- Official sources
- Government websites
- Universities
- Research organizations
- Reputable news organizations
- High-quality technical sources

Do NOT write the final research report.

Return the result in this format:

SELECTED SOURCE

Title:
URL:
Reason for Selection:

SCRAPED CONTENT

[Detailed useful content from the webpage]

IMPORTANT FACTS

- Fact 1
- Fact 2
- Fact 3

Rules:

- Do not invent information.
- Do not invent URLs.
- Preserve important dates.
- Preserve important statistics and numbers.
- Preserve important names and facts.
- Mention the URL that was actually scraped.
"""


def build_scrape_agent():

    return create_agent(
        model=primary_llm,
        tools=[scrape],
        system_prompt=SCRAPE_AGENT_PROMPT,
    )


def invoke_scrape_agent(payload):

    return _invoke_agent_with_fallback(
        tools=[scrape],
        payload=payload,
        system_prompt=SCRAPE_AGENT_PROMPT,
    )


# ============================================================
# WRITER CHAIN
# ============================================================

writer_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an expert research writer.

Create a professional, factual and well-structured
research report using ONLY the research information
provided to you.
"""
    ),

    (
        "user",
        """
Create a comprehensive research report.

Topic:
{topic}

Research Gathered:
{research}

Use the following structure:

# {topic}

## Introduction

Provide a concise introduction.

## Key Findings

Provide at least 3 important findings.

## Detailed Analysis

Explain the important information in detail.

## Conclusion

Summarize the major findings.

## Sources

List the URLs and sources used.

Important rules:

- Do not invent facts.
- Do not invent sources.
- Do not add unsupported information.
- Maintain a professional tone.
- Use Markdown formatting.
"""
    ),
])


writer_chain = (
    writer_prompt
    | llm
    | StrOutputParser()
)


# ============================================================
# CRITIC CHAIN
# ============================================================

critic_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an expert research critic.

Your job is to critically evaluate the quality,
accuracy, structure and completeness of the research report.
"""
    ),

    (
        "user",
        """
Analyze the following research report.

REPORT:

{report}

Respond using exactly this structure:

# Research Review

## Score

Score: X/10

## Strengths

- ...
- ...
- ...

## Areas to Improve

- ...
- ...
- ...

## Accuracy Check

- ...
- ...

## One Line Verdict

...
"""
    ),
])


critic_chain = (
    critic_prompt
    | llm
    | StrOutputParser()
)