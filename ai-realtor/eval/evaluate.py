#!/usr/bin/env python3
"""
Run RAGAS evaluation for AI Realtor. Use as standalone script to avoid
Python 3.14 + Jupyter asyncio timeout issues.

Usage:
  python evaluate.py              # RAG chain (in-memory retriever, no tools)
  python evaluate.py --agent      # Agent with tools: search_red_flag_guidelines,
                                  # search_inspection_report, web_search

Prerequisites for --agent:
  - Qdrant running with reference_guidelines populated (run backend once)
  - TAVILY_API_KEY for web_search (optional; agent may skip if not needed)
Output: eval/data/eval_results.json (or eval_results_agent.json with --agent)
"""

import argparse
import asyncio
import json
import os
import sys
import warnings
from pathlib import Path

# Suppress deprecation warnings for ragas.metrics (use ragas.metrics.collections in v1.0)
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*ragas.metrics.*")

from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DATA = PROJECT_ROOT / "backend" / "data"
EVAL_DATA = SCRIPT_DIR / "data"

load_dotenv(SCRIPT_DIR / ".env")
load_dotenv(SCRIPT_DIR / ".env.local", override=True)
load_dotenv(PROJECT_ROOT / "backend" / ".env")
load_dotenv(PROJECT_ROOT / "backend" / ".env.local", override=True)


def main():
    parser = argparse.ArgumentParser(description="RAGAS evaluation for AI Realtor")
    parser.add_argument(
        "--agent",
        action="store_true",
        help="Use agent with tools (search_red_flag_guidelines, search_inspection_report, web_search)",
    )
    parser.add_argument("--per-sample", action="store_true", help="Print per-sample breakdown")
    args = parser.parse_args()

    import numpy as np
    from langchain_community.document_loaders import TextLoader, PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough

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

    eval_samples = []

    if args.agent:
        # Agent with tools: search_red_flag_guidelines, search_inspection_report, web_search
        # Eval-specific prompt mandates tool use (no impact on production agent.py)
        sys.path.insert(0, str(PROJECT_ROOT / "backend"))
        from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
        from langgraph.prebuilt import create_react_agent

        from agent import SYSTEM_PROMPT
        from tools import get_tools_for_eval

        # Eval-only: mandate tool use so RAGAS metrics reflect retrieval quality.
        # Production agent.py is unchanged.
        SYSTEM_PROMPT_EVAL = SYSTEM_PROMPT + (
            "\n\n[EVAL] MANDATORY — ALWAYS USE TOOLS FIRST: "
            "For ANY question about property inspection, red flags, defects, inspection concepts, "
            "or what to look for — you MUST call at least one search tool BEFORE answering. "
            "Do NOT answer from memory. Use search_red_flag_guidelines for general inspection knowledge; "
            "use search_inspection_report for property-specific findings (may be empty). "
            "Only after retrieving and reading tool results may you formulate your answer."
        )

        model = ChatOpenAI(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0,
        )
        agent = create_react_agent(model, get_tools_for_eval(), prompt=SYSTEM_PROMPT_EVAL)

        async def run_agent_eval():
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

        print("Running agent with tools (search_red_flag_guidelines, search_inspection_report, web_search)...")
        eval_samples = asyncio.run(run_agent_eval())

    else:
        # RAG chain: in-memory retriever, no tools
        docs = []
        if BACKEND_DATA.exists():
            for p in BACKEND_DATA.glob("*.pdf"):
                docs.extend(PyPDFLoader(str(p)).load())
        if not docs:
            ref_file = EVAL_DATA / "home_inspection_reference.txt"
            if ref_file.exists():
                docs = TextLoader(str(ref_file)).load()
        if not docs:
            print("Error: No documents for RAG.")
            sys.exit(1)

        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        chunks = splitter.split_documents(docs)
        embeddings = OpenAIEmbeddings()
        chunk_vectors = np.array(embeddings.embed_documents([c.page_content for c in chunks]))

        def retrieve(query: str, k: int = 4):
            qv = np.array(embeddings.embed_query(query)).reshape(1, -1)
            sims = np.dot(chunk_vectors, qv.T).flatten() / (
                np.linalg.norm(chunk_vectors, axis=1) * np.linalg.norm(qv)
            )
            idx = np.argsort(sims)[::-1][:k]
            return [chunks[i] for i in idx]

        def format_docs(docs_list):
            return "\n\n".join(d.page_content for d in docs_list)

        RAG_PROMPT = """Answer the question based only on the following context. Be concise.

Context:
{context}

Question: {question}

Answer:"""

        prompt = ChatPromptTemplate.from_template(RAG_PROMPT)
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        rag_chain = (
            {"context": lambda q: format_docs(retrieve(q)), "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        for rec in test_records:
            question = rec.get("user_input", "")
            if isinstance(question, list):
                question = question[-1] if question else ""
            if isinstance(question, dict) and "content" in question:
                question = question["content"]
            question = str(question)

            retrieved_docs = retrieve(question)
            retrieved_contexts = [d.page_content for d in retrieved_docs]
            response = rag_chain.invoke(question)

            eval_samples.append({
                "user_input": question,
                "retrieved_contexts": retrieved_contexts,
                "reference_contexts": rec.get("reference_contexts") or [],
                "response": response,
                "reference": rec.get("reference", ""),
            })

    # Build dataset and evaluate
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

    # Use LangchainEmbeddingsWrapper to satisfy RAGAS metrics that call embed_query
    ragas_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())
    result = evaluate(dataset, metrics=metrics, embeddings=ragas_embeddings)

    # Save results
    out = {
        "mode": "agent" if args.agent else "rag",
        "scores": {k: float(v) if not (isinstance(v, float) and np.isnan(v)) else None
                  for k, v in result._repr_dict.items()},
        "scores_per_row": result.to_pandas().to_dict(orient="records"),
    }
    out_name = "eval_results_agent.json" if args.agent else "eval_results.json"
    out_path = EVAL_DATA / out_name
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Mode: {'agent' if args.agent else 'rag'}")
    print(f"Saved: {out_path}")
    print("Scores:", result._repr_dict)

    # Optionally print per-sample breakdown (like the notebook's DataFrame display)
    if args.per_sample:
        import pandas as pd
        df = pd.DataFrame(out.get("scores_per_row", []))
        if not df.empty:
            # Show key columns for readability
            cols = [c for c in ["user_input", "response", "reference"] if c in df.columns]
            if cols:
                print("\nPer-sample (excerpt):")
                print(df[cols].to_string(max_colwidth=60))


if __name__ == "__main__":
    main()
