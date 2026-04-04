Conduct deep market research for a client project using the `what-to-build.md` file (or equivalent product vision document) in the current working directory as your primary input. Cross-reference with any available meeting transcripts and summaries.

Use web search extensively to research every competitor, tool, and market trend mentioned in the source documents — and discover ones that weren't mentioned.

Generate a markdown file called `research-primer.md` in the current working directory with the following sections:

---

## 1. Market Landscape

- What is the broader market category this product falls into?
- How large is this market? (TAM/SAM/SOM with sources)
- What are the key trends shaping this space right now?
- Is the market growing, consolidating, or being disrupted? By what forces?
- What recent funding rounds, acquisitions, or exits signal market direction?

## 2. Competitor Deep Dive

For **every** competitor or existing solution mentioned in the source documents, plus any you discover through research, create a detailed profile:

### [Competitor Name]
- **What they do:** One-paragraph summary
- **Pricing:** Pricing model and price points (cite sources)
- **Target users:** Who they sell to and how they position themselves
- **Strengths:** What they do well — be specific, reference reviews and case studies
- **Weaknesses:** Where they fall short — reference user complaints, review sites, forum posts
- **Relevant to this project because:** How they relate to what the client wants to build
- **Key differentiator from our project:** What makes our proposed solution different

Organize competitors into tiers:
1. **Direct competitors** — solve the same problem for the same users
2. **Adjacent competitors** — solve a related problem or serve adjacent users
3. **DIY / status quo** — how people solve this today without a dedicated tool

## 3. Competitive Gap Analysis

- Create a feature comparison matrix: rows = key features from the what-to-build doc, columns = competitors
- Use ✅ (has it), ⚠️ (partial/weak), ❌ (missing) for each cell
- Identify the **white space** — what combination of features does no competitor offer?
- What is the proposed product's unfair advantage? (proprietary data, unique workflow, domain expertise, etc.)

## 4. User & Buyer Research

- What do real users say about existing solutions? (Search G2, Capterra, Reddit, Hacker News, Twitter/X, LinkedIn, industry forums)
- What are the top 3–5 complaints about current tools in this space?
- What do users wish existed but doesn't?
- Are there relevant case studies or success stories from competitors that validate market demand?

## 5. Technical Feasibility Assessment

- What are the core technical challenges in building this?
- Are there existing APIs, models, libraries, or services that accelerate development?
- What has changed recently (new AI models, new APIs, regulatory shifts) that makes this more feasible now than 2 years ago?
- What are the biggest technical risks? (accuracy requirements, data quality, integration complexity, etc.)

## 6. Pricing & Business Model Intelligence

- How do competitors price? (per seat, per transaction, flat rate, usage-based)
- What pricing signals did the client give in meetings?
- What is the likely willingness-to-pay based on the problem's cost? (Reference the "cost of not solving" from the what-to-build doc)
- Recommended pricing model with reasoning

## 7. Strategic Positioning

- Based on all research, where should this product position itself?
- What is the one-sentence pitch that captures the differentiation?
- What are the 3 strongest selling points backed by research?
- What competitive responses should be anticipated? (incumbents adding features, new entrants, etc.)

## 8. Risks & Red Flags

- Market risks: Is the market too small, too crowded, or shifting away?
- Competitor risks: Is a well-funded competitor about to ship something similar?
- Regulatory risks: Are there compliance or legal barriers?
- Adoption risks: Are there switching costs or behavioral barriers that make adoption hard?

## 9. Sources & References

- List every source consulted with URLs
- Distinguish between: meeting transcripts (primary), competitor websites (secondary), review sites (secondary), news articles (tertiary)
- Flag any claims that could not be independently verified

---

**Research guidelines:**
- Use direct quotes from meeting transcripts to ground the research in the client's actual words and perspective
- Every competitor claim should have a source — don't speculate about pricing or features without evidence
- When web search returns conflicting information, note the conflict and present both sides
- Prioritize recency — a 2024+ source beats a 2022 source
- If a competitor was mentioned negatively by the client, verify those claims independently — the client's perception may be outdated or incomplete

After the research document is complete, use the /presentation-maker skill to create a presentation version of the research primer suitable for sharing with the client or team. The presentation should emphasize the competitive gap analysis, positioning recommendations, and key market insights — not raw data dumps.
