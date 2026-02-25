# PageIndex: Vectorless, Reasoning-Based RAG

## 📋 Overview

[PageIndex](https://github.com/VectifyAI/PageIndex) is an open-source RAG (Retrieval-Augmented Generation) system that replaces traditional vector databases and document chunking with LLM-powered reasoning over hierarchical tree indexes. Instead of computing embedding similarity scores, it builds a semantic tree structure from documents and uses an LLM (e.g., GPT-4o) to navigate that tree — mimicking how a human expert would locate information in a long document.

**Key claim:** 98.7% accuracy on [FinanceBench](https://huggingface.co/datasets/PatronusAI/financebench) (via Mafin 2.5, a PageIndex-powered financial RAG system), substantially outperforming vector-based alternatives on structured financial documents.

| Attribute | Detail |
|-----------|--------|
| **License** | MIT (permissive open-source) |
| **Repository** | [github.com/VectifyAI/PageIndex](https://github.com/VectifyAI/PageIndex) |
| **Supported docs** | PDF, Markdown |
| **Default LLM** | GPT-4o (`gpt-4o-2024-11-20`) |
| **Deployment** | Self-hosted, Cloud API, or Enterprise on-premises |
| **MCP Integration** | Available for Claude and other MCP-compatible tools |

---

## 🧠 How It Works

PageIndex follows a two-step retrieval process that fundamentally differs from traditional RAG:

### Step 1: Index Generation

Documents are transformed into semantic tree structures that resemble enriched tables of contents. Each node in the tree contains:

- **`title`** — Section heading
- **`node_id`** — Hierarchical identifier (e.g., `1.2.3`)
- **`start_index` / `end_index`** — Page ranges covered
- **`summary`** — LLM-generated section overview
- **`nodes`** — Nested child sections

This tree is built once per document and stored as structured JSON — no vector database required.

### Step 2: Tree Search (Retrieval)

When a query comes in, an LLM reasons through the tree hierarchy to locate the most relevant sections. It starts at the root, evaluates which branches are likely to contain the answer, and drills down — similar to how a human would use a table of contents to find information in a textbook.

**The core philosophy:** *"Similarity ≠ relevance — what we truly need in retrieval is relevance, and that requires reasoning."*

### Why This Matters: A Concrete Example

Consider the query: *"What were the debt trends in 2023?"*

- **Traditional vector RAG** returns chunks that *look semantically similar* to the query — but the actual answer might be buried in an Appendix, referenced on a different page, in a section that shares zero semantic overlap with the query text. Vector search would likely never find it.

- **PageIndex** doesn't ask *"What text looks similar to this query?"* — it asks *"Based on this document's structure, where would a human expert look for this answer?"* It follows the document's hierarchy, sees in-document references like "see Table 5.3", and navigates to the right section the way a domain expert would.

This is a fundamental shift: vector search treats every query as independent and flattens document structure into embeddings. PageIndex respects the structure — sections that reference other sections, context that builds across pages, appendices that contain the actual data.

---

## ⚖️ PageIndex vs Traditional Vector RAG

| Aspect | PageIndex | Traditional Vector RAG |
|--------|-----------|------------------------|
| **Infrastructure** | No vector DB needed (tree stored as JSON) | Requires vector database (pgvector, Pinecone, Weaviate, etc.) |
| **Chunking** | Preserves natural document sections | Splits documents into artificial fixed-size chunks |
| **Retrieval method** | LLM reasoning over tree hierarchy | Cosine/dot-product similarity on embeddings |
| **Explainability** | Traceable reasoning path with section/page references | Opaque similarity scores |
| **Cost per query** | ~$0.05–0.15 (LLM inference) | ~$0.00002 (embedding lookup) |
| **Latency** | 3–10 seconds | ~100–300ms |
| **Best document type** | Long, structured docs (100–500+ pages) | Short snippets, FAQs, knowledge bases |
| **Accuracy on structured docs** | 98.7% (FinanceBench) | Lower on complex multi-page reasoning |
| **Scaling cost** | Grows with query volume (LLM calls) | Grows with data volume (storage + indexing) |

---

## ✅ When to Use PageIndex

PageIndex is a strong fit when your use case matches these criteria:

### Ideal Use Cases

- **Long, structured documents** — Financial reports, regulatory filings, legal contracts, technical manuals, academic papers (100+ pages with hierarchical structure)
- **Complex multi-hop questions** — Queries that require synthesizing information across multiple sections of a document
- **Accuracy over speed** — Applications where getting the right answer matters more than sub-second latency (e.g., compliance, legal research, financial analysis)
- **Explainability requirements** — When you need to cite exact pages/sections and show the reasoning path to an answer
- **Document analysis workflows** — Analyzing a small number of high-value documents deeply rather than searching across thousands of short snippets

### Example Scenarios

- Querying a 300-page annual financial report for specific revenue figures across subsidiaries
- Searching regulatory handbooks (e.g., CFR Title 38, benefits guides) for eligibility criteria
- Extracting clauses from long legal agreements
- Navigating technical specifications or API documentation spanning hundreds of pages

---

## ❌ When NOT to Use PageIndex

PageIndex is **not** the right choice for every RAG application. Avoid it when:

### Poor Fit Scenarios

- **Short knowledge snippets** — If your knowledge base is a collection of short FAQ-style entries, cosine similarity already performs well and costs almost nothing
- **High query volume with low latency requirements** — At 3–10s per retrieval and ~$0.05–0.15/query, PageIndex becomes expensive at scale (e.g., 15k queries/month = ~$750–2,250 vs ~$0.30 for embeddings)
- **Real-time chat applications** — User-facing chatbots expecting sub-second responses will feel sluggish
- **Simple factual lookups** — If queries are straightforward keyword matches, vector search or even full-text search is faster and cheaper
- **Large corpus of small documents** — PageIndex shines on individual large documents, not on searching across thousands of small ones

### Cost Comparison at Scale

| Monthly Queries | Vector RAG (embeddings) | PageIndex (LLM reasoning) |
|----------------|------------------------|--------------------------|
| 1,000 | ~$0.02 | ~$50–150 |
| 5,000 | ~$0.10 | ~$250–750 |
| 15,000 | ~$0.30 | ~$750–2,250 |
| 50,000 | ~$1.00 | ~$2,500–7,500 |

> **Note:** PageIndex costs depend on the LLM used. Using GPT-4o-mini or open-source models (e.g., via Ollama) can significantly reduce per-query cost, though accuracy may vary.

---

## 🏗️ Architecture Decision: Hybrid Approach

For most production systems, the best approach is a **hybrid architecture** that routes queries to the appropriate retrieval system:

```text
User Query
    │
    ▼
┌─────────────┐
│   Router     │  ← Classifies query complexity
│  (LLM/rules) │
└──────┬──────┘
       │
  ┌────┴────┐
  │         │
  ▼         ▼
┌──────┐  ┌──────────┐
│Vector│  │PageIndex │
│  RAG │  │(Deep     │
│(Fast)│  │ Search)  │
└──────┘  └──────────┘
  ~200ms    ~3-10s
  ~$0.00002  ~$0.05-0.15
```

### Routing Strategy

| Query Type | Route To | Reasoning |
|-----------|----------|-----------|
| Simple factual (e.g., "What is the refund policy?") | Vector RAG | Fast, cheap, sufficient accuracy |
| Complex multi-part (e.g., "Compare Q3 revenue across all subsidiaries and explain variances") | PageIndex | Requires cross-section reasoning |
| Regulatory/legal (e.g., "Am I eligible under Section 3.2.1(b)?") | PageIndex | Needs hierarchical document navigation |

### Integration Effort

Estimated effort to add PageIndex as a complementary retrieval layer:

| Phase | Effort | Description |
|-------|--------|-------------|
| Proof of concept | 8–12 hours | Index 2–3 target documents, test retrieval accuracy |
| Query router | 5–8 hours | Build classification logic to route queries |
| Production integration | 12–15 hours | Error handling, caching, monitoring, fallbacks |
| **Total** | **25–35 hours** | Full hybrid integration |

---

## 🚀 Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/VectifyAI/PageIndex.git
cd PageIndex

# Install dependencies
pip3 install --upgrade -r requirements.txt
```

### Configuration

Create a `.env` file with your OpenAI API key:

```bash
CHATGPT_API_KEY=sk-your-api-key-here
```

### Build an Index

```bash
python3 run_pageindex.py --pdf_path /path/to/document.pdf
```

### Configuration Options

| Flag | Default | Description |
|------|---------|-------------|
| `--model` | `gpt-4o-2024-11-20` | OpenAI model for index building and search |
| `--max-pages-per-node` | `10` | Maximum pages per tree node |
| `--max-tokens-per-node` | `20,000` | Token limit per node |
| `--toc-check-pages` | `20` | Pages scanned for table of contents detection |
| `--if-add-node-id` | — | Include hierarchical node IDs in the tree |
| `--if-add-node-summary` | — | Include LLM-generated summaries per node |
| `--if-add-doc-description` | — | Include overall document description |

### Alternative Access Methods

| Method | URL / Info | Best For |
|--------|-----------|----------|
| **Chat Platform** | [chat.pageindex.ai](https://chat.pageindex.ai) | Quick document analysis without setup |
| **API** | Available via PageIndex cloud service | Programmatic integration |
| **MCP Server** | MCP integration for Claude and compatible tools | AI assistant workflows |

---

## 📊 Advantages Summary

1. **No vector infrastructure** — Eliminates the need for pgvector, Pinecone, Weaviate, or any vector database. The tree index is a plain JSON structure.

2. **Superior accuracy on structured documents** — 98.7% on FinanceBench, where traditional RAG systems struggle with multi-page reasoning and cross-section references.

3. **Explainable retrieval** — Every answer traces back through a clear reasoning path with specific page and section references, unlike opaque similarity scores.

4. **No chunking artifacts** — Documents are split along natural section boundaries, avoiding the common RAG problem of splitting context across chunk boundaries.

5. **Handles documents beyond LLM context windows** — The tree structure allows navigation of 500+ page documents without needing to fit them entirely in context.

6. **MIT licensed** — Fully open-source with permissive licensing for commercial use.

7. **Multiple deployment options** — Self-hosted, cloud API, or enterprise on-premises deployment.

---

## ⚠️ Disadvantages Summary

1. **High per-query cost** — Each retrieval requires LLM inference (~$0.05–0.15/query with GPT-4o), making it 2,500–7,500x more expensive than embedding lookups per query.

2. **High latency** — 3–10 seconds per retrieval vs ~200ms for vector search. Not suitable for real-time applications requiring sub-second response.

3. **Benchmark specificity** — The 98.7% accuracy was measured on 200+ page structured financial filings. Performance on short, unstructured, or FAQ-style content has not been benchmarked and likely offers less advantage over traditional RAG.

4. **LLM dependency** — Quality is tied to the underlying LLM. Cheaper models may degrade accuracy; using GPT-4o means reliance on OpenAI's API availability and pricing.

5. **Index generation cost** — Building the tree index also requires LLM calls, adding upfront cost per document. This is a one-time cost but can be significant for large document collections.

6. **Not designed for large corpus search** — Optimized for deep analysis of individual documents, not for searching across thousands of documents simultaneously.

7. **Newer technology** — Less battle-tested in production compared to mature vector database solutions like pgvector or Pinecone.

---

## 🔗 Resources

- **GitHub:** [github.com/VectifyAI/PageIndex](https://github.com/VectifyAI/PageIndex)
- **Chat Platform:** [chat.pageindex.ai](https://chat.pageindex.ai)
- **Cookbooks:** Runnable examples including vectorless and vision-based RAG (in the repo)
- **FinanceBench Results:** Via [Mafin 2.5](https://github.com/VectifyAI/PageIndex) — PageIndex-powered financial RAG
- **Citation:** Zhang, M., Tang, Y. and PageIndex Team, "PageIndex: Next-Generation Vectorless, Reasoning-based RAG", PageIndex Blog, Sep 2025.

---

## 📝 Decision Checklist

Use this checklist to determine if PageIndex is right for your project:

- [ ] Are you working with long, structured documents (100+ pages)?
- [ ] Do queries require multi-section or multi-page reasoning?
- [ ] Is accuracy more important than latency for your use case?
- [ ] Do you need explainable retrieval with page/section citations?
- [ ] Can your budget support ~$0.05–0.15 per retrieval query?
- [ ] Is your query volume manageable (< 5,000/month) or can you use a hybrid approach?

**If you checked 4+ boxes:** PageIndex is likely a good fit — start with a proof of concept on 2–3 target documents.

**If you checked 2–3 boxes:** Consider a hybrid approach with vector RAG for simple queries and PageIndex for complex ones.

**If you checked 0–1 boxes:** Stick with traditional vector RAG (pgvector, Pinecone, etc.) — it's faster, cheaper, and sufficient for your use case.
