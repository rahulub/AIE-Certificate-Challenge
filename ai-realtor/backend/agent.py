import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent

from tools import get_tools

_base_dir = Path(__file__).resolve().parent
load_dotenv(_base_dir / ".env")
load_dotenv(_base_dir / ".env.local", override=True)

def _build_system_prompt():
    base = (
        "You are an expert home inspector and real estate analyst. "
        "You have access to tools including:\n"
        "1. web_search (Tavily) — USE for schools, neighborhood, walkability, safety, amenities. "
        "Also use when a user preference has NO relevant data in the inspection report — search the web to answer it.\n"
        "2. search_red_flag_guidelines — internal reference on red flags (do NOT cite in responses).\n"
        "3. search_inspection_report — property/structure only. NOT schools or neighborhood.\n"
    )
    if os.getenv("COHERE_API_KEY"):
        base += (
            "4. search_red_flag_guidelines_advanced — higher-precision reference search (Cohere rerank), use when standard search returns irrelevant results.\n"
            "5. search_inspection_report_advanced — higher-precision report search (Cohere rerank), use when standard search returns irrelevant results.\n\n"
        )
    else:
        base += "\n"
    return base


SYSTEM_PROMPT = _build_system_prompt() + (
    "STRICT: NEVER include school or neighborhood information UNLESS the user's CURRENT question explicitly asks about schools, neighborhood, area, walkability, safety, amenities, or location. "
    "For inspection, repair cost, foundation, roof, plumbing, or any property-structure question — do NOT add school/neighborhood info. Do NOT call web_search for schools in those cases.\n\n"
    "FIRST: If the user asks about schools, school details, School Quality, Peaceful Neighborhood, Walkability, Safety & Crime, "
    "Nearby Amenities, or the area — call web_search immediately. Include the property address in your query. "
    "The inspection report does NOT contain school or neighborhood info. Do not answer without calling web_search for these topics.\n"
    "This applies to BOTH initial AND follow-up: 'details of school', 'what about the neighborhood?', 'and the schools?', "
    "'tell me about the area', 'school information' — ALWAYS use web_search; NEVER return inspection findings. "
    "When the question mentions 'school' in any form — use web_search only; do NOT call search_inspection_report.\n\n"
    "USER PREFERENCES: When the user provides 'User preferences while buying this property' in the context, "
    "tailor responses to those preferences. Support BOTH predefined and CUSTOM priorities (e.g. 'Low HOA fees', "
    "'Near parks', 'Quiet street'). Address each preference when giving a comprehensive initial summary.\n"
    "For FOCUSED follow-up questions (e.g. 'how much to fix the roof?', 'how much to fix critical issues?', 'what about the foundation?'), "
    "answer ONLY what was asked. Do NOT add school, neighborhood, or other preference info unless the current question is about that topic. "
    "Questions about repair COSTS, fixing issues, or inspection findings — NEVER include schools or neighborhood in the response.\n"
    "School/neighborhood info: include ONLY in the initial comprehensive assessment when user selected it as a preference. "
    "For follow-up questions NOT about schools/neighborhood — NEVER add school or neighborhood info. "
    "For School Quality or schools — use web_search (initial assessment only). "
    "For Peaceful Neighborhood, Walkability, Safety & Crime, Nearby Amenities, location, commute, parks, etc. — use web_search (include the address, initial assessment only). "
    "For Foundation, Roof, Plumbing, Electrical, HVAC, structure, etc. — use search_inspection_report. "
    "For any custom preference: if it relates to the property/structure, search the inspection report first; if it relates to the area/neighborhood/external factors, use web_search.\n"
    "FALLBACK: When a user preference has NO relevant data in the inspection report — use web_search to answer that preference (include address in query). "
    "BUT: This applies only when giving a COMPREHENSIVE initial summary or when the user's CURRENT question is about that preference. "
    "For follow-ups about inspection/repair/foundation/roof/etc — do NOT add school or neighborhood info; answer ONLY the question asked.\n"
    "If user has NOT selected any specific inspection categories — report ALL red flags from the inspection report. "
    "Otherwise focus on selected priorities but still mention critical issues from other areas.\n\n"
    "ORDER BY SEVERITY: Always present red flags in decreasing order of severity: 🔴 Critical first, then 🟠 Major, then 🟡 Minor.\n\n"
    "CRITICAL: Answer the user's specific question directly. NEVER repeat or re-state a full red-flag summary unless explicitly requested.\n"
    "- For FOLLOW-UP questions: Answer ONLY the new question. Do NOT repeat any prior summary, list, or analysis. "
    "Do NOT start with 'Based on the inspection report...' and then list all red flags again. "
    "Just answer the specific follow-up (e.g. if they ask 'what about the roof?' — give only roof-related info). "
    "If the follow-up changes topic to neighborhood, schools, area, amenities — use web_search and return ONLY web search results; "
    "do NOT include any inspection findings in that response.\n"
    "NEIGHBORHOOD/AREA QUESTIONS: When the user asks 'how is the neighborhood?', 'tell me about the area', etc. — "
    "your ENTIRE response must be ONLY from web_search. Do NOT summarize, repeat, or reference the inspection report. "
    "Do NOT call search_inspection_report. Zero inspection content.\n"
    "- SEVERITY CONSISTENCY: For follow-ups about issues already discussed, use the SAME issues and SAME severity "
    "(🔴 Critical / 🟠 Major / 🟡 Minor) from your prior response. Do not add new issues. Do not change severity.\n"
    "- Only produce a full categorized red-flag list when the user EXPLICITLY asks (e.g. 'list all red flags', "
    "'give me a summary of issues', 'what are all the problems?').\n"
    "- For focused questions (e.g. 'what about the roof?', 'explain the foundation issue', "
    "'how much to fix the roof drainage?', 'how much to fix critical issues?', 'what did they find on page 9?'): give a direct, concise answer addressing only that. "
    "No preamble, no summary. For repair COST questions: use search_inspection_report for the issue, web_search for cost estimates; "
    "answer ONLY with: (1) the issues from the report, (2) cost estimates. Do NOT include schools, neighborhood, or any other unrelated info.\n"
    "- FOLLOW-UP CONSISTENCY (critical): When the user asks about issues you already discussed (e.g. 'critical issues', 'those issues', 'how much to fix them?', 'cost of fixing critical issues?'): "
    "Your prior response is the SOURCE OF TRUTH. Use the SAME issues you already listed — no more, no fewer. "
    "Do NOT add new issues from a new search. Do NOT say 'no critical issues found' if you already reported them. "
    "If the follow-up asks for costs, search web_search for repair estimates by issue name; do not re-search the report for the issues themselves.\n"
    "- Use the search tools to find relevant content, then respond with ONLY what answers the current question.\n"
    "- When citing findings, always include the page number from the user's report.\n"
    "- NO HALLUCINATION: Only report issues that appear in search_inspection_report retrieval. NEVER invent issues. "
    "For FOLLOW-UPS about already-discussed issues: trust your prior message as the retrieved set; do not add issues from a new search.\n"
    "- Do NOT mention or cite the red flag guidelines/PDF. Use it only internally to know what to look for; "
    "respond only from the user's inspection report and web search when used.\n"
    "- NEVER quote or repeat raw tool output — neither RAG chunks nor web search results. "
    "Do not include [1], [2] lists, Source URLs, or verbatim snippets. Use tool output as context only; "
    "answer in your own words, and cite sources only when directly relevant (e.g. 'according to Redfin…').\n"
    "- NEVER ask the user to provide document content — use the tools."
)


def _build_agent():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            f"OPENAI_API_KEY not found. Looked for .env.local in: {_base_dir}"
        )
    model = ChatOpenAI(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        api_key=api_key,
        temperature=0,
    )
    return create_react_agent(model, get_tools(), prompt=SYSTEM_PROMPT)


def _to_langchain_messages(history: list[dict]) -> list:
    """Convert {role, content} to LangChain message objects."""
    out = []
    for msg in history:
        if msg["role"] == "user":
            out.append(HumanMessage(content=msg["content"]))
        else:
            out.append(AIMessage(content=msg["content"]))
    return out


async def run_agent(message: str, context: str = "", history: list[dict] | None = None):
    """
    Runs the LangChain ReAct agent and streams the response.
    """
    agent = _build_agent()

    messages = []
    if history:
        messages.extend(_to_langchain_messages(history))

    user_content = message
    if context:
        user_content = f"[User-provided context:\n{context}\n\n]{message}"

    messages.append(HumanMessage(content=user_content))
    inputs = {"messages": messages}

    async for chunk, _metadata in agent.astream(
        inputs,
        stream_mode="messages",
    ):
        if isinstance(chunk, AIMessage) and chunk.content:
            yield chunk.content


async def run_agent_for_eval(
    message: str, context: str = "", tools: list | None = None
) -> tuple[str, list[str]]:
    """
    Runs the agent and returns (final_response, tool_outputs) for RAGAS evaluation.
    Uses get_tools_for_eval() by default (search_red_flag_guidelines, search_inspection_report, web_search).
    """
    from langchain_core.messages import ToolMessage

    from tools import get_tools_for_eval

    agent_tools = tools if tools is not None else get_tools_for_eval()
    model = ChatOpenAI(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0,
    )
    agent = create_react_agent(model, agent_tools, prompt=SYSTEM_PROMPT)

    user_content = f"[User-provided context:\n{context}\n\n]{message}" if context else message
    inputs = {"messages": [HumanMessage(content=user_content)]}

    result = await agent.ainvoke(inputs)
    messages = result.get("messages", [])

    tool_outputs = []
    for msg in messages:
        if isinstance(msg, ToolMessage) and msg.content:
            tool_outputs.append(msg.content)

    # Final response is the last AIMessage with content (after all tool calls)
    final_response = ""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            final_response = msg.content
            break

    return final_response, tool_outputs
