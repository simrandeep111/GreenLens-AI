# GreenLens AI — Backend Implementation README

> **Purpose:** This document explains the recommended backend implementation for GreenLens AI given the current state of the project: the frontend already exists, the data is limited and controlled for demo purposes, and the goal is to build the cleanest, most reliable, most impressive hackathon backend without unnecessary infrastructure.

---

## 1. What changed from the original idea

The original project direction leaned toward a more “AI-agent + RAG everywhere” architecture. That is useful during ideation, but for the actual hackathon build the backend should be **simpler, more deterministic, and easier to demo**.

### Current constraints
- The frontend is already defined and expects a clean API contract.
- The uploaded data will be **test/demo data**, not production-scale customer data.
- There is **no need for Supabase**, cloud object storage, or a database-backed file pipeline.
- The biggest technical risk is **correctly classifying CSV transactions into Scope 1 / Scope 2 / Scope 3**.
- The AI output must feel smart, but the core numbers must remain **auditable and explainable**.

### Final architecture principle
Use:
- **FastAPI** for the API layer
- **Local file storage** for uploads/results
- **Deterministic emissions/scoring logic** for all numeric outputs
- **Lightweight retrieval** for compliance/grants context
- **LLM only where it adds clear value**
- **No agent framework unless absolutely necessary**

This is the best fit for a hackathon because it minimizes failure points while still giving judges a credible AI story.

---

## 2. Recommended backend strategy in one sentence

**Build a deterministic ESG pipeline with a hybrid transaction-classification engine, local lightweight retrieval for compliance/grants, and an LLM only for narrative generation and ambiguous edge cases.**

---

## 3. What should and should not use AI

## Use AI for:
1. **Narrative report generation**
   - Executive summary
   - Compliance explanation
   - Funding/grants narrative
   - Recommended next actions

2. **Fallback classification of ambiguous CSV rows**
   - When keyword rules and vendor mappings are not confident
   - Only for a small subset of uncertain rows
   - Returned in strict JSON, not free text

3. **Optional explanation layer**
   - “Why is this mostly Scope 3?”
   - “Why is this compliance item marked warning?”
   - “Why is this grant relevant to this business?”

## Do **not** use AI for:
1. **Emission factor math**
2. **ESG score calculation**
3. **Revenue/intensity calculations**
4. **Status/progress logic**
5. **Primary classification of obvious transactions**

If judges ask how you prevent hallucinations, the answer is:
> “All scores, emissions, and benchmarks are computed deterministically in Python. The LLM only explains and summarizes the results.”

---

## 4. Core design decision: how Scope 1 / 2 / 3 classification should work

This is the single most important backend design choice.

## Do not use RAG for transaction classification
RAG is good at retrieving relevant text from documents. It is **not** the right primary mechanism for mapping accounting rows like:

- `Enbridge Gas - monthly utility`
- `Shell fleet fuel`
- `Uber for Business`
- `Sysco food supply`
- `Staples office supplies`

into Scope 1 / 2 / 3.

Why not:
- Scope classification is a **labeling problem**, not a knowledge retrieval problem.
- The input is short tabular/merchant text, not long natural-language queries.
- RAG adds complexity without improving reliability on this task.
- Judges will trust an explicit classification engine more than “the vector DB decided it”.

## Best approach: hybrid classifier
Use a **3-layer classification engine**:

### Layer 1 — deterministic merchant/category mapping
Maintain a small mapping table for known vendors and categories.

Examples:
- `enbridge`, `union gas`, `natural gas` → Scope 1
- `toronto hydro`, `hydro one`, `electricity` → Scope 2
- `air canada`, `uber`, `lyft`, `hotel`, `shipping`, `supplier`, `waste`, `packaging` → Scope 3

This should catch a large percentage of demo rows.

### Layer 2 — keyword/rule engine
If no exact merchant/category mapping matches, inspect:
- `category`
- `description`
- `vendor`

Then apply rules like:
- combustion / fleet / propane / diesel / natural gas → Scope 1
- hydro / electric / electricity / utility power → Scope 2
- everything else defaults to Scope 3 unless a stronger rule applies


---

## 5. Confidence-driven classification flow

Each row should produce:

- normalized text
- predicted scope
- confidence score
- classification reason
- source of classification

Example output per transaction:

```json
{
  "vendor": "Enbridge Gas",
  "category": "Utilities",
  "description": "January service",
  "amount": 842.17,
  "predicted_scope": "Scope 1",
  "confidence": 0.96,
  "reason": "Matched vendor dictionary: Enbridge Gas -> natural gas heating",
  "classification_source": "rule_engine"
}
```

For an ambiguous row:

```json
{
  "vendor": "ABC Facilities",
  "category": "Operations",
  "description": "Monthly site support",
  "amount": 620.00,
  "predicted_scope": "Scope 3",
  "confidence": 0.62,
  "reason": "LLM fallback inferred outsourced service spend rather than direct fuel or electricity",
  "classification_source": "llm_fallback"
}
```

This is useful because:
- it improves explainability
- it helps debugging during the demo
- it makes the backend feel intentional and trustworthy

---

## 6. How emissions should actually be calculated

Classification tells you **which scope** a row belongs to. It does not yet tell you **how much carbon** that row represents.

Use a separate emissions calculation layer.

## Recommended method for a hackathon

### Scope 1
Use spend-based or simplified factor logic for:
- natural gas
- propane
- diesel/gasoline fleet fuel

You can support two methods:
1. **Direct factor if usage quantity is available**
2. **Spend-to-activity estimate if only dollar spend is available**

For demo purposes, spend-based estimation is acceptable as long as it is consistent and disclosed.

### Scope 2
This is the cleanest category.
- infer electricity-related rows
- use a provincial grid factor table
- Ontario, Quebec, Alberta, BC should have different values

This is deterministic and easy to explain.

### Scope 3
Use spend-based factors by category:
- travel
- shipping/logistics
- purchased goods
- food supply
- waste
- packaging
- professional services

For a hackathon, you do **not** need a giant industrial-grade LCA engine.
You need:
- a compact factor table
- clear category mapping
- reproducible math

## Key principle
The backend should always preserve:
- raw amount
- mapped spend category
- factor used
- resulting CO2e
- scope assigned

That allows you to build both:
- the dashboard totals
- the detailed report tables

---

## 7. Should you use RAG?

## Yes, but only for the right parts
RAG should be used for:
1. **Compliance retrieval**
2. **Grant/program retrieval**
3. **Optionally citing guidance snippets inside the generated report**

## No, not for:
1. CSV transaction classification
2. Score calculation
3. Benchmark math
4. File storage
5. API orchestration

## Best RAG implementation for this hackathon
Because your corpus is small and static, use a **lightweight local retrieval layer**.

You have two viable options:

### Option A — simplest and most robust
Use a curated local knowledge base in the repo:
- `docs/compliance/*.md`
- `docs/grants/*.md`

Then run simple retrieval with:
- BM25 / keyword search
- or local embeddings + FAISS/Chroma
- or even hand-tagged JSON lookup for the demo

This is often the best hackathon choice because the document set is tiny.

### Option B — if you want the “RAG” story for judges
Use a small local vector store with pre-chunked docs:
- FAISS or Chroma persisted locally
- built at startup or precomputed before demo

This gives you a credible RAG architecture without requiring Supabase, Pinecone, or cloud infra.

## Recommendation
For this hackathon, the cleanest choice is:

- **local markdown/JSON knowledge corpus**
- **simple retrieval wrapper**
- **optional vector index only if you already have it working**

Do not build a complex external retrieval stack unless it is already stable.

---

## 8. Should you use LangChain or agents?

## Recommendation: avoid a freeform agent
A fully agentic LangChain setup sounds impressive in a README, but it is usually the wrong tradeoff for a hackathon demo.

Why:
- harder to debug
- more brittle
- more latency
- less predictable
- judges care more about a strong product flow than agent abstraction

## Better approach
Use an **explicit orchestration pipeline**:

1. parse upload
2. normalize rows
3. classify scope
4. calculate emissions
5. calculate ESG score
6. retrieve compliance context
7. retrieve grant context
8. generate structured report JSON
9. return results to frontend

This can still be implemented cleanly with service modules and helper classes. It does not need an agent runtime.

## When LangChain is acceptable
Only use LangChain if:
- one teammate already knows it well
- it saves time rather than adding ceremony
- you use it as a thin wrapper, not as the architecture itself

In other words:
> The pipeline should remain understandable even if LangChain is removed tomorrow.

---

## 9. Best architecture for your exact use case

## High-level system

```text
Next.js Frontend
   |
   |  POST /api/upload
   |  POST /api/analyze
   |  GET  /api/status/{jobId}
   |  GET  /api/report/{jobId}
   v
FastAPI Backend
   |
   +-- Upload Service (local file save)
   +-- Job Orchestrator
   +-- CSV Parser + Normalizer
   +-- Scope Classifier
   +-- Emissions Calculator
   +-- ESG Scoring Engine
   +-- Retrieval Service (compliance + grants)
   +-- Report Generator (LLM)
   +-- Local Result Store
```

## Why this is the right architecture
- fits the frontend you already built
- no unnecessary external infra
- easy to explain
- easy to debug live
- deterministic where it matters
- still includes real AI
- works well with limited demo data

---

## 10. File storage strategy

Since you do **not** want Supabase or similar storage, use local filesystem storage.

## Recommended local directories

```text
greenlens-backend/
├── app/
├── data/
│   ├── uploads/
│   │   ├── <uploadId>/
│   │   │   ├── input.csv
│   │   │   └── support_1.pdf
│   ├── processed/
│   │   ├── <jobId>/
│   │   │   ├── normalized_rows.json
│   │   │   ├── classified_rows.json
│   │   │   ├── emissions_summary.json
│   │   │   └── final_report.json
│   └── knowledge/
│       ├── compliance/
│       └── grants/
```

## Why this is enough
For a hackathon:
- one backend instance
- limited test files
- no persistent multi-user production requirement
- easier setup and fewer credentials

## Important note
This is acceptable because the app is demo-only.
If the product later becomes real, then storage can migrate to:
- S3 / GCS / Azure Blob
- Postgres for metadata
- durable job queue
- persistent vector store

But none of that is needed now.

---

## 11. Recommended backend folder structure

```text
greenlens-backend/
├── main.py
├── api/
│   ├── upload.py
│   ├── analyze.py
│   ├── status.py
│   └── report.py
├── core/
│   ├── config.py
│   ├── job_store.py
│   └── logger.py
├── services/
│   ├── upload_service.py
│   ├── csv_parser.py
│   ├── normalizer.py
│   ├── scope_classifier.py
│   ├── emissions_calculator.py
│   ├── scoring_engine.py
│   ├── retrieval_service.py
│   ├── report_generator.py
│   └── pipeline.py
├── models/
│   ├── request_models.py
│   ├── response_models.py
│   └── domain_models.py
├── knowledge/
│   ├── compliance/
│   └── grants/
├── data/
│   ├── uploads/
│   └── processed/
├── tests/
│   ├── test_scope_classifier.py
│   ├── test_scoring.py
│   └── test_pipeline.py
└── requirements.txt
```

## Why this structure is better than an “agent-first” structure
It separates:
- API routes
- business logic
- retrieval
- scoring
- persistence
- report generation

That makes it easier for the team to work in parallel.

---

## 12. End-to-end backend flow

## Step 1 — upload
Frontend sends:
- CSV file
- optional PDF files

Backend:
- creates `uploadId`
- saves files locally
- validates CSV columns
- returns `uploadId`

## Step 2 — analyze
Frontend sends:
- `uploadId`
- company metadata
- governance/self-assessment answers

Backend:
- creates `jobId`
- sets job status to `queued`
- launches background pipeline
- returns `jobId`

## Step 3 — processing pipeline
The pipeline updates status as it goes:

1. `Parsing uploaded data`
2. `Normalizing merchants and categories`
3. `Classifying Scope 1 / 2 / 3`
4. `Calculating emissions and benchmarks`
5. `Retrieving compliance and grant context`
6. `Generating ESG report`
7. `Saving final result`

## Step 4 — status polling
Frontend hits `GET /api/status/{jobId}` every 1–2 seconds.

## Step 5 — report fetch
When status is `complete`, frontend calls `GET /api/report/{jobId}` and renders:
- dashboard
- report page

---

## 13. Detailed decision on the LLM role

The LLM should be used as a **controlled generation service**, not the system brain.

## Best LLM tasks

### A. Report generation
Inputs:
- company info
- ESG scores
- emissions totals and breakdown
- benchmark metrics
- compliance retrieval snippets
- grants retrieval snippets
- recommendations

Output:
- structured JSON only

### B. Ambiguous row classification
Inputs:
- vendor
- category
- description
- allowed labels
- short rules

Output:
- strict JSON with:
  - scope
  - confidence
  - rationale

### C. Recommendation phrasing
The recommendation itself can be generated from deterministic facts.

Example:
- if Scope 3 > 50% of total → recommend supplier engagement
- if governance score < 12 → recommend disclosure/policy improvements
- if Alberta electricity is large share → recommend power efficiency/renewables

The LLM can phrase these elegantly, but the trigger logic should be deterministic.

## Do not let the LLM invent:
- grant amounts
- compliance statuses
- numeric score changes
- emission totals
- benchmark values

---

## 14. Suggested retrieval architecture

## Compliance retrieval
Create a small document set covering:
- GHG Protocol summary
- OSFI B-15 overview
- GRI / ESG reporting summary
- relevant Canadian disclosure notes
- province-aware environmental guidance where relevant

Each chunk should be:
- short
- clean
- tagged
- not overly redundant

Example metadata:
```json
{
  "doc_type": "compliance",
  "framework": "OSFI B-15",
  "industry": "general",
  "province": "Canada",
  "topic": "climate disclosure"
}
```

## Grants retrieval
Create a separate corpus for:
- federal programs
- Ontario programs
- sector-specific incentives
- SME eligibility notes

Example metadata:
```json
{
  "doc_type": "grant",
  "program_name": "Ontario SMB Green Fund",
  "province": "Ontario",
  "industry": "general",
  "company_size": "SMB"
}
```

## Why separate corpora matter
If you keep grants and compliance in one undifferentiated knowledge base, retrieval quality drops. The query for “available funding” may accidentally pull disclosure standards. Separate retrieval flows are cleaner and more explainable.

---

## 15. API design aligned to your frontend

The frontend contract you already defined is good. The backend should keep it almost unchanged.

## Endpoints

### `POST /api/upload`
Purpose:
- save files
- validate input format
- create `uploadId`

### `POST /api/analyze`
Purpose:
- create job
- attach company + questionnaire inputs
- trigger background processing

### `GET /api/status/{jobId}`
Purpose:
- processing step
- progress percentage
- human-readable label
- error message if failed

### `GET /api/report/{jobId}`
Purpose:
- return complete structured result for dashboard + report

## Optional extra endpoint
### `GET /api/debug/{jobId}`
For hackathon debugging only.
Could return:
- classified rows
- factors used
- confidence breakdown
- retrieved snippets

This is extremely useful during development, even if you hide it in the demo.

---

## 16. How to make the classification feel robust in the demo

Judges will likely ask:
- “How do you know the emissions classification is correct?”
- “What happens when the CSV is messy?”
- “Where does the AI actually help?”

Your answer should be:

1. **We normalize messy accounting data first**
   - lowercase
   - strip punctuation
   - unify vendor aliases
   - standardize categories

2. **We classify most rows with deterministic vendor/category rules**
   - faster
   - more explainable
   - more consistent

3. **We only call the LLM on ambiguous rows**
   - reduces hallucination risk
   - preserves reliability
   - gives flexibility on real-world messy data

4. **All carbon math and ESG scoring remain deterministic**
   - the LLM never touches the numbers

That is a very strong story.

---

## 17. Recommendation engine design

Recommendations should not be purely freeform LLM outputs.

## Better design
Create a deterministic recommendation rules layer.

Examples:
- if `scope3 / total > 0.5` → add supplier engagement recommendation
- if `scope2` high and province carbon intensity high → add electricity efficiency recommendation
- if governance score low → add formal disclosure/policy recommendation
- if no sustainability reporting → add annual ESG report recommendation
- if grant matches exist → add “apply to X program” recommendation

Then let the LLM convert the selected recommendations into polished narrative text.

This ensures:
- consistent output
- easy debugging
- clear product logic

---

## 18. How to benchmark ESG performance

The environmental score should rely on **emission intensity**, not only absolute emissions.

Why:
- a larger business naturally emits more
- judges will expect a relative benchmark
- it is more fair across industries

Recommended benchmark:
- `kgCO2e per $1,000 revenue`

Then compare against:
- industry average
- optional “top quartile” value

This gives you:
- a clean dashboard chart
- an explainable scoring model
- a better business story

---

## 19. Processing/status architecture

Because your frontend already includes a processing screen, the backend should expose real pipeline progress.

## Minimal job store
Use an in-memory dictionary or lightweight local JSON store:

```python
jobs[job_id] = {
    "status": "running",
    "current_step": 3,
    "step_label": "Classifying Scope 1 / 2 / 3",
    "progress": 48,
    "error": None
}
```

This is enough for demo conditions.

## Why not Celery/Redis?
Because that is unnecessary infrastructure for:
- one backend instance
- limited concurrency
- hackathon timescales

Use:
- FastAPI background tasks
- or asyncio task orchestration
- or a simple thread-based worker

The priority is stability, not enterprise job architecture.

---

## 20. PDF handling

PDFs are optional support documents.

Use them for:
- utility bills
- fuel receipts
- optional evidence extraction

## Recommendation
Do not make PDF parsing a core requirement for the main demo path.

Instead:
- CSV should drive the core analysis
- PDF parsing should be additive, not blocking

Why:
- PDFs are messy
- OCR/parsing adds edge cases
- demo reliability matters more

Best implementation:
- if PDF exists, parse text lightly
- extract supporting clues such as utility type/vendor
- enrich confidence or attach evidence notes
- do not make the report depend on perfect PDF extraction

---

## 21. Hackathon-friendly implementation choice summary

## Best final stack
- **Frontend:** Next.js (already built)
- **Backend:** FastAPI
- **Storage:** local filesystem
- **Job state:** in-memory dict
- **CSV handling:** pandas
- **Retrieval:** local corpus + simple retrieval
- **LLM:** one model for report generation + fallback row classification
- **Scoring:** deterministic Python functions
- **Charts/report data:** structured JSON returned to frontend

## Avoid for now
- Supabase
- Postgres
- Celery + Redis
- freeform multi-tool agent
- cloud object storage
- production auth
- complicated vector infrastructure
- over-generalized ML classifier training pipeline

---

## 22. Most important architectural recommendation

If you only remember one thing, it should be this:

> **Do not build GreenLens AI as a general-purpose AI agent. Build it as a deterministic ESG engine with carefully placed AI.**

That is what makes it:
- faster to implement
- easier to debug
- more trustworthy in front of judges
- better aligned with your current frontend

---

## 23. Final recommended system blueprint

```text
INPUTS
- company form
- CSV export
- optional PDFs
- governance/self-assessment answers

PIPELINE
1. Save files locally
2. Parse CSV
3. Normalize text fields
4. Classify each row with:
   a) vendor/category dictionary
   b) keyword rules
   c) LLM fallback for uncertain rows
5. Map each row to an emission factor
6. Calculate Scope 1/2/3 totals and intensity benchmark
7. Calculate deterministic ESG score
8. Retrieve compliance snippets from local knowledge base
9. Retrieve grant snippets from local knowledge base
10. Select deterministic recommendations
11. Use LLM to generate structured report JSON
12. Save final result locally
13. Return dashboard/report payload to frontend

OUTPUTS
- progress/status updates
- ESG score
- emissions breakdown
- benchmark comparison
- compliance statuses
- grant matches
- recommendations
- narrative report sections
```

---

## 24. Recommended build order

### Phase 1 — must work first
- file upload
- CSV validation
- row normalization
- deterministic scope classification
- emissions calculation
- score calculation

### Phase 2 — make it look intelligent
- retrieval for compliance
- retrieval for grants
- structured report generation

### Phase 3 — polish
- status polling
- better explanations
- debug endpoint
- second mock company
- cleaner prompt outputs

This order matters because your demo still works even if the most advanced AI layer is imperfect.

---

## 25. What to say in the pitch about the backend

A strong explanation would be:

> “We intentionally designed the backend so the numbers are deterministic and auditable, while AI is used only where it creates real product value. Transaction classification is handled by a hybrid engine: known vendors and categories are classified by rules, while ambiguous rows use a constrained LLM fallback. We then compute emissions and ESG scores in Python, retrieve relevant compliance and grant context from a lightweight local knowledge base, and generate a structured ESG report for the frontend. Because this is a hackathon demo with controlled data, we use local storage and a simple job pipeline instead of overengineering cloud infrastructure.”

That answer sounds disciplined, product-minded, and technically credible.

---

## 26. Final recommendation

For GreenLens AI, the best backend architecture is:

- **FastAPI + local storage**
- **explicit service pipeline, not a freeform agent**
- **deterministic scope/emissions/score logic**
- **hybrid scope classifier with LLM fallback**
- **lightweight local retrieval for compliance and grants**
- **LLM-generated narrative only after the facts are computed**

That architecture is the most cohesive choice for:
- your existing frontend
- your hackathon timeline
- your controlled demo data
- your need to impress judges without introducing unnecessary fragility

---

*End of backend implementation README.*
