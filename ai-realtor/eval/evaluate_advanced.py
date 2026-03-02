#!/usr/bin/env python3
"""
RAGAS evaluation for AI Realtor agent with ADVANCED (Cohere reranked) tools.

Uses agent with:
  - search_red_flag_guidelines_advanced (Cohere rerank)
  - search_inspection_report_advanced (Cohere rerank)
  - web_search

Prerequisites:
  - Qdrant with reference_guidelines populated (run backend once)
  - COHERE_API_KEY (required for advanced tools)
  - TAVILY_API_KEY for web_search (optional)

Usage: python evaluate_advanced.py
Output: eval/data/eval_results_advanced.json
"""

import argparse
import asyncio
import json
import os
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*ragas.metrics.*")

from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
EVAL_DATA = SCRIPT_DIR / "data"

load_dotenv(SCRIPT_DIR / ".env")
load_dotenv(SCRIPT_DIR / ".env.local", override=True)
load_dotenv(PROJECT_ROOT / "backend" / ".env")
load_dotenv(PROJECT_ROOT / "backend" / ".env.local", override=True)


def main():
    parser = argparse.ArgumentParser(description="RAGAS evaluation for AI Realtor (advanced tools)")
    parser.add_argument("--per-sample", action="store_true", help="Print per-sample breakdown")
    args = parser.parse_args()

    if not os.getenv("COHERE_API_KEY"):
        print("Error: COHERE_API_KEY required for advanced tools. Set it in backend/.env.local")
        sys.exit(1)

    import numpy as np
    from langchain_openai import OpenAIEmbeddings

    from ragas import EvaluationDataset, SingleTurnSample, evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.metrics import (
        context_precision,
        context_recall,
        faithfulness,
        answer_relevancy,
        answer_correctness,
    )

    EVAL_DATA.mkdir(parents=True, exist_ok=True)
    testset_path = EVAL_DATA / "ragas_testset.json"
    if not testset_path.exists():
        print(f"Error: {testset_path} not found. Run generate_testset.py first.")
        sys.exit(1)

    with open(testset_path) as f:
        test_records = json.load(f)

    sys.path.insert(0, str(PROJECT_ROOT / "backend"))
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
    from langgraph.prebuilt import create_react_agent

    from agent import SYSTEM_PROMPT
    from tools import get_tools_for_advanced_eval

    # Eval-only: mandate tool use so RAGAS metrics reflect retrieval quality.
    # Advanced tools use Cohere rerank for higher-precision retrieval.
    SYSTEM_PROMPT_EVAL = SYSTEM_PROMPT + (
        "\n\n[EVAL] MANDATORY — ALWAYS USE TOOLS FIRST: "
        "For ANY question about property inspection, red flags, defects, inspection concepts, "
        "or what to look for — you MUST call at least one search tool BEFORE answering. "
        "Do NOT answer from memory. Use search_red_flag_guidelines_advanced for general inspection knowledge; "
        "use search_inspection_report_advanced for property-specific findings (may be empty). "
        "Only after retrieving and reading tool results may you formulate your answer."
    )

    model = ChatOpenAI(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0,
    )
    agent = create_react_agent(
        model, get_tools_for_advanced_eval(), prompt=SYSTEM_PROMPT_EVAL
    )

    async def run_advanced_eval():
        samples = []
        for rec in test_records:
            question = rec.get("user_input", "")
            if isinstance(question, list):
                question = question[-1] if question else ""
            if isinstance(question, dict) and "content" in question:
                question = question["content"]
            question = str(question)

            inputs = {"messages": [HumanMessage(content=question)]}
            result = await agent.ainvoke(inputs)
            messages = result.get("messages", [])

            tool_outputs = []
            for msg in messages:
                if isinstance(msg, ToolMessage) and msg.content:
                    tool_outputs.append(msg.content)

            final_response = ""
            for msg in reversed(messages):
                if isinstance(msg, AIMessage) and msg.content:
                    final_response = msg.content
                    break

            samples.append({
                "user_input": question,
                "retrieved_contexts": tool_outputs if tool_outputs else ["(no tool calls)"],
                "reference_contexts": rec.get("reference_contexts") or [],
                "response": final_response or "(empty response)",
                "reference": rec.get("reference", ""),
            })
        return samples

    print(
        "Running agent with advanced tools "
        "(search_red_flag_guidelines_advanced, search_inspection_report_advanced, web_search)..."
    )
    eval_samples = asyncio.run(run_advanced_eval())

    samples = [
        SingleTurnSample(
            user_input=s["user_input"],
            retrieved_contexts=s["retrieved_contexts"],
            reference_contexts=s["reference_contexts"],
            response=s["response"],
            reference=s["reference"],
        )
        for s in eval_samples
    ]
    dataset = EvaluationDataset(samples=samples)
    metrics = [
        context_precision,
        context_recall,
        faithfulness,
        answer_relevancy,
        answer_correctness,
    ]

    ragas_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())
    result = evaluate(dataset, metrics=metrics, embeddings=ragas_embeddings)

    out = {
        "mode": "agent_advanced",
        "tools": [
            "search_red_flag_guidelines_advanced",
            "search_inspection_report_advanced",
            "web_search",
        ],
        "scores": {
            k: float(v) if not (isinstance(v, float) and np.isnan(v)) else None
            for k, v in result._repr_dict.items()
        },
        "scores_per_row": result.to_pandas().to_dict(orient="records"),
    }
    out_path = EVAL_DATA / "eval_results_advanced.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Mode: agent_advanced")
    print(f"Saved: {out_path}")
    print("Scores:", result._repr_dict)

    if args.per_sample:
        import pandas as pd

        df = pd.DataFrame(out.get("scores_per_row", []))
        if not df.empty:
            cols = [c for c in ["user_input", "response", "reference"] if c in df.columns]
            if cols:
                print("\nPer-sample (excerpt):")
                print(df[cols].to_string(max_colwidth=60))


if __name__ == "__main__":
    main()
