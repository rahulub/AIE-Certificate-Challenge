# PropertyLens — Presentation Slides (9 slides)

---

## Slide 1: Title

# **PropertyLens**

*AI-Powered Home Inspection Analysis*

---

## Slide 2: The Problem

**Home buyers and agents struggle to quickly extract critical issues from lengthy, technical inspection reports—leading to missed red flags and costly surprises.**

Reports are often 30–80 pages of dense text. Buyers skip sections or lack expertise to judge severity. Agents spend hours walking clients through the same questions. Result: decisions on incomplete info, buyer's remorse, and unexpected repair bills.

---

## Slide 3: Our Solution

**PropertyLens** turns lengthy inspection PDFs into clear, actionable insights through a chat-based interface.

- **Upload** — Property address + inspection report (PDF)
- **Choose priorities** — Foundation, Roof, Systems, Neighborhood, or custom
- **Chat** — Natural-language questions with streaming answers (🔴 Critical / 🟠 Major / 🟡 Minor + page citations)
- **Follow up** — Conversation history so context carries over

---

## Slide 4: How It Works

1. **Landing** — Enter Property → Upload Report → Get Analysis
2. **Form** — Address, PDF upload, priority checkboxes
3. **Submit** — Report indexed, chat panel opens
4. **Ask** — "What are the critical issues?" "How much to fix the roof?" "Tell me about the foundation"
5. **Stream** — Real-time answers with severity labels and page numbers

---

## Slide 5: Key Features

- **PDF ingestion** — Semantic search over inspection reports
- **Severity labeling** — Critical, Major, Minor with page citations
- **Streaming chat** — Real-time responses, no waiting
- **Conversation history** — Follow-ups retain context
- **Focus priorities** — User chooses structure, systems, neighborhood
- **Web search** — Neighborhood, schools, repair costs (Tavily)

---

## Slide 6: Technology

| Layer | Tech |
|-------|------|
| **Frontend** | Next.js, React, Tailwind, shadcn/ui |
| **Backend** | FastAPI, Python |
| **Agent** | LangGraph ReAct, GPT-4o-mini |
| **RAG** | Qdrant, OpenAI embeddings |
| **Tools** | search_inspection_report, search_red_flag_guidelines, web_search |
| **Persistence** | Redis (chat), Qdrant (vectors) |

---

## Slide 7: Architecture

```
User → Next.js → FastAPI → LangGraph Agent (GPT-4o-mini)
                                  ↓
              RAG (Qdrant) │ Web Search (Tavily)
                                  ↓
                    Streaming response → User
```

---

## Slide 8: Impact & Benefits

- **Buyers** — Informed decisions without reading 50-page PDFs
- **Agents** — Save time, consistent report-backed answers
- **Transparency** — Severity + page citations for verification
- **Flexibility** — Custom priorities, natural-language questions
- **Actionability** — Repair cost estimates where relevant

---

## Slide 9: Thank You

# **PropertyLens**

*AI-Powered Home Inspection Analysis*

**Questions?**
