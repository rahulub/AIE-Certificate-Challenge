# AI Realtor — RAGAS Evaluation

RAGAS test set and evaluation utilities for the AI Realtor home inspection chatbot.

## Directory Structure

```
eval/
├── evaluate.py           # Run RAGAS evaluation (outputs data/eval_results.json)
├── evaluate_advanced.py  # RAGAS evaluation with advanced (Cohere) tools → data/eval_results_advanced.json
├── generate_testset.py    # Generate synthetic test set from backend/data/*.pdf or reference txt
├── json_to_pdf.py        # Export ragas_testset.json to PDF report
├── pyproject.toml        # Dependencies (ragas, langchain-openai, fpdf2)
├── uv.lock
└── data/
    ├── ragas_testset.json     # RAGAS test set (user_input, reference_contexts, reference)
    ├── ragas_testset.pdf      # Human-readable test set report
    ├── eval_results.json      # RAGAS scores (context precision, recall, faithfulness, etc.)
    └── home_inspection_reference.txt   # Fallback reference doc when no PDFs in backend/data
```

## Setup

```bash
cd eval
uv sync
```

Requires `OPENAI_API_KEY` (in `eval/.env`, `eval/.env.local`, or `backend/.env.local`).

## Pre-built Test Set

A curated RAGAS test set is already included in `data/`:

- **data/ragas_testset.json** — RAGAS-compatible format (user_input, reference_contexts, reference)
- **data/ragas_testset.pdf** — human-readable report

These cover home inspection red flags: foundation, roof, plumbing, electrical, HVAC, water damage, septic, and water heater.

## Workflow

### 1. Generate Synthetic Test Set (optional)

To regenerate the test set from documents:

```bash
cd eval
uv run python generate_testset.py
```

Loads documents from `backend/data/*.pdf` (or `eval/data/home_inspection_reference.txt`) and generates synthetic queries (single-hop, multihop direct, multihop abstract). Saves `ragas_testset.json` and `ragas_testset.pdf`.

Optional: `RAGAS_TESTSET_SIZE=15 uv run python generate_testset.py` (default: 10).

### 2. Run Evaluation

```bash
cd eval
uv run python evaluate.py
```

Requires `data/ragas_testset.json` (from pre-built set or step 1). Outputs RAGAS scores to `data/eval_results.json`.

**Agent mode** (evaluate the ReAct agent with base tools):

```bash
uv run python evaluate.py --agent
```

Uses the agent with `search_red_flag_guidelines`, `search_inspection_report`, and `web_search`. Requires Qdrant with `reference_guidelines` populated (run backend once). Output: `data/eval_results_agent.json`.

**Advanced agent** (evaluate the agent with Cohere reranked tools):

```bash
uv run python evaluate_advanced.py
```

Uses the agent with `search_red_flag_guidelines_advanced`, `search_inspection_report_advanced`, and `web_search`. Requires `COHERE_API_KEY` and Qdrant. Output: `data/eval_results_advanced.json`.

**Per-sample breakdown:**
```bash
uv run python evaluate.py --per-sample
uv run python evaluate.py --agent --per-sample
uv run python evaluate_advanced.py --per-sample
```

### 3. Regenerate PDF from JSON

```bash
uv run python json_to_pdf.py
```

Generates a PDF from `ragas_testset.json`. (Also: `generate_testset.py` outputs both JSON and PDF to `data/`.)
