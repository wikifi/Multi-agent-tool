import ast

from langchain_core.messages import HumanMessage

from agents import (
    invoke_search_agent,
    invoke_scrape_agent,
    writer_chain,
    critic_chain,
)


# ============================================================
# CLEAN AGENT OUTPUT
# ============================================================

def clean_agent_output(content):
    """
    Convert structured Gemini/LangChain output into
    clean human-readable text.
    """

    # --------------------------------------------------------
    # STRING
    # --------------------------------------------------------

    if isinstance(content, str):

        text = content.strip()

        # Handle strings that contain representations such as:
        #
        # [{'type': 'text', 'text': 'SEARCH RESULTS...'}]

        try:

            parsed = ast.literal_eval(text)

            if isinstance(parsed, (list, dict)):
                return clean_agent_output(parsed)

        except (ValueError, SyntaxError):
            pass

        return text


    # --------------------------------------------------------
    # LIST
    # --------------------------------------------------------

    if isinstance(content, list):

        parts = []

        for item in content:

            if isinstance(item, dict):

                if "text" in item:

                    parts.append(
                        clean_agent_output(
                            item["text"]
                        )
                    )

                elif "content" in item:

                    parts.append(
                        clean_agent_output(
                            item["content"]
                        )
                    )

            elif isinstance(item, str):

                parts.append(item)


        return "\n\n".join(
            part.strip()
            for part in parts
            if part and part.strip()
        )


    # --------------------------------------------------------
    # DICTIONARY
    # --------------------------------------------------------

    if isinstance(content, dict):

        if "text" in content:

            return clean_agent_output(
                content["text"]
            )

        if "content" in content:

            return clean_agent_output(
                content["content"]
            )


    return str(content).strip()


# ============================================================
# STREAMING PIPELINE
# ============================================================

def run_research_pipeline_stream(topic: str, on_step=None):

    state = {}


    def notify(step_number, label):

        if on_step is not None:
            on_step(
                step_number,
                label
            )


    try:

        # ====================================================
        # STEP 1 — SEARCH
        # ====================================================

        notify(
            1,
            "Searching the web"
        )

        yield {
            "step": 1,
            "status": "running",
            "label": "Searching the web",
        }


        search_response = invoke_search_agent({

            "messages": [

                HumanMessage(
                    content=(
                        f"Find recent and detailed "
                        f"information about {topic}."
                    )
                )

            ]

        })


        raw_search = (
            search_response[
                "messages"
            ][-1].content
        )


        # CLEAN OUTPUT
        state["search_results"] = (
            clean_agent_output(
                raw_search
            )
        )


        print(
            "\nSearch Result:\n",
            state["search_results"]
        )


        yield {
            "step": 1,
            "status": "done",
            "label": "Searching the web",
            "notice": "Search complete.",
        }


        # ====================================================
        # STEP 2 — SCRAPE
        # ====================================================

        notify(
            2,
            "Scraping top resources"
        )

        yield {
            "step": 2,
            "status": "running",
            "label": "Scraping top resources",
        }


        scraped_response = invoke_scrape_agent({

            "messages": [

                HumanMessage(
    content=f"""
    Research the following topic:

    {topic}

    Use the web search tool to find the 5 most relevant
    and recent sources.

    Return ONLY clean human-readable search results.

    For each result provide:

    1. Title
    2. URL
    3. Short summary explaining why the source is relevant

    Do NOT return:
    - JSON
    - Python dictionaries
    - metadata
    - signatures
    - tool arguments
    - internal tool information
    """
                )

            ]

        })


        raw_scraped = (
            scraped_response[
                "messages"
            ][-1].content
        )


        # CLEAN OUTPUT
        state["scraped_content"] = (
            clean_agent_output(
                raw_scraped
            )
        )


        print(
            "\nScraped Content:\n",
            state["scraped_content"]
        )


        yield {
            "step": 2,
            "status": "done",
            "label": "Scraping top resources",
            "notice": "Scrape complete.",
        }


        # ====================================================
        # STEP 3 — WRITER
        # ====================================================

        notify(
            3,
            "Writing the report"
        )

        yield {
            "step": 3,
            "status": "running",
            "label": "Writing the report",
        }


        research_combined = (

            f"SEARCH RESULTS:\n"
            f"{state['search_results']}\n\n"

            f"DETAILED SCRAPED CONTENT:\n"
            f"{state['scraped_content']}"

        )


        state["report"] = writer_chain.invoke({

            "topic": topic,

            "research": research_combined,

        })


        print(
            "\nGenerated Report:\n",
            state["report"]
        )


        yield {
            "step": 3,
            "status": "done",
            "label": "Writing the report",
            "notice": "Report generated.",
        }


        # ====================================================
        # STEP 4 — CRITIC
        # ====================================================

        notify(
            4,
            "Reviewing the report"
        )

        yield {
            "step": 4,
            "status": "running",
            "label": "Reviewing the report",
        }


        state["critic_feedback"] = (
            critic_chain.invoke({

                "report": state["report"]

            })
        )


        print(
            "\nCritic Feedback:\n",
            state["critic_feedback"]
        )


        yield {
            "step": 4,
            "status": "done",
            "label": "Reviewing the report",
            "notice": "Review complete.",
        }


        # ====================================================
        # FINAL
        # ====================================================

        yield {
            "step": "final",
            "status": "done",
            "state": state,
        }


    except Exception as exc:

        yield {
            "step": "error",
            "status": "error",
            "error": str(exc),
        }