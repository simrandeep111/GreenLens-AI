# GreenLens AI

## Devpost README

GreenLens AI is a full-stack ESG intelligence platform built for Canadian SMBs. It turns operational and financial records into a structured ESG assessment, including emissions across Scope 1, Scope 2, and Scope 3, a deterministic ESG score, compliance guidance, matched funding programs, supporting-document assurance, fraud-signal detection, and a generated executive report.

This repository is intentionally designed as a practical hackathon system rather than an overbuilt enterprise platform. The numbers are deterministic and auditable, the knowledge layer is local and lightweight, and the LLM is used only where it adds real value: narrative generation and grounded report chat.

## What the project does

GreenLens AI helps a company answer a difficult but common question:

How do we go from messy transaction exports and optional supporting documents to a credible ESG snapshot that is useful for decision-making, compliance, and funding conversations?

The application accepts:

- A transaction CSV
- Company metadata such as province, industry, employee count, and revenue
- A short governance self-assessment
- Optional supporting PDFs such as invoices, statements, fuel receipts, and utility bills

From that input, GreenLens produces:

- An ESG score with Environmental, Social, and Governance sub-scores
- A full emissions breakdown by scope and category
- Compliance readiness against Canadian-relevant frameworks
- Matched grant and funding programs
- Recommended next actions
- Supporting-document review and fraud/evidence risk flags
- A narrative report suitable for a management-style readout
- A grounded report copilot for follow-up questions

## Why this architecture exists

The project was built around a few core principles:

- Deterministic calculations for anything numeric or score-related
- Lightweight local retrieval instead of external vector infrastructure
- File-based storage instead of a database, because the demo flow is controlled and small-scale
- Simple FastAPI + Next.js architecture for reliability and speed
- Limited LLM scope to reduce hallucination risk

In practice, that means:

- Emissions are calculated in Python, not invented by an LLM
- ESG scores are rule-based, not probabilistic
- Compliance and grant context come from curated local JSON knowledge files
- The LLM writes the report narrative, but it is grounded in structured inputs
- The report copilot answers questions from the generated report plus local retrieved context

## Core capabilities

- CSV-driven ESG analysis for SMB transaction data
- Hybrid classification engine for Scope 1 / 2 / 3 mapping
- Province-aware emissions calculation using simplified Canadian factors
- Deterministic ESG score generation
- Local retrieval for compliance and grants
- Supporting-document parsing for uploaded PDFs
- Document-to-ledger matching
- Fraud detection using both document checks and forensic ledger tests
- LLM-generated report narrative with deterministic fallback
- Report chat endpoint for grounded Q&A over the completed analysis

## End-to-end user journey

1. The user lands on the intake page and enters company details.
2. The user uploads a CSV and optionally uploads supporting PDFs.
3. The frontend calls the upload endpoint and then starts the analysis job.
4. The backend runs the pipeline in a background thread and updates progress.
5. The frontend polls the status endpoint and shows each processing stage.
6. Once complete, the dashboard and full report become available.
7. The user can review emissions, compliance, funding matches, recommendations, and supporting-document findings.
8. The user can ask follow-up questions in the report copilot, which answers from the saved report and retrieved context.

## High-level architecture

### Frontend

- Framework: Next.js 16 with React 19
- Purpose: intake flow, processing screen, dashboard, full report, report copilot
- State model: browser session persisted in `localStorage`
- Default backend target: `http://127.0.0.1:8000`

### Backend

- Framework: FastAPI
- Processing model: background thread per analysis job
- Storage model: local filesystem only
- API model: upload -> analyze -> poll status -> fetch report
- LLM model path: Moorcheh API using Sonnet 4 directly by default

### Storage

- Uploaded files are stored under `greenlens-backend/data/uploads/<upload_id>`
- Completed report artifacts are stored under `greenlens-backend/data/processed/<job_id>`
- The frontend persists current-session context in browser storage

### Knowledge layer

- Compliance knowledge is stored locally in JSON files
- Grant knowledge is stored locally in JSON files
- Retrieval is metadata-based scoring, not external vector search

## Repository structure

```text
greenlens-ai/
  app/
    page.tsx              # intake flow
    processing/page.tsx   # progress UI while backend pipeline runs
    dashboard/page.tsx    # dashboard view of completed analysis
    report/page.tsx       # full narrative report + report copilot
  components/
    intake/               # company form, upload UI, governance questions
    processing/           # progress bar and step display
    dashboard/            # dashboard cards and charts
    report/               # report sections, sidebars, fraud/supporting-doc views
  lib/
    api.ts                # frontend API client
    report.ts             # report normalization helpers
    session.ts            # local session persistence
    types.ts              # shared frontend types

greenlens-backend/
  api/
    upload.py             # file upload endpoint
    analyze.py            # starts analysis job
    status.py             # pipeline progress endpoint
    report.py             # completed report endpoint
    report_chat.py        # report copilot endpoint
  core/
    config.py             # paths, env, emission factors, model config
    job_store.py          # in-memory job tracking
  services/
    pipeline.py                   # orchestrates the full analysis
    csv_parser.py                 # validates and parses uploaded CSVs
    normalizer.py                 # text cleaning and vendor canonicalization
    scope_classifier.py           # hybrid scope classification logic
    emissions_calculator.py       # emissions math and aggregation
    scoring_engine.py             # deterministic ESG scoring
    retrieval_service.py          # local compliance and grant retrieval
    supporting_document_service.py# PDF extraction and document parsing
    fraud_detection_service.py    # document assurance + forensic checks
    report_generator.py           # narrative report generation
    report_chat_service.py        # grounded report Q&A
    moorcheh_client.py            # shared LLM client
    report_store.py               # final report loading/normalization
  knowledge/
    compliance/           # local compliance corpus
    grants/               # local grants corpus
  demo_data/
    *.csv                 # sample ledgers
    support_docs/         # sample PDF evidence files
  scripts/
    smoke_test_demo.py    # end-to-end backend smoke test

DEVPOST_README.md         # this file
README.md                 # minimal root README
```

## Detailed backend pipeline

The central orchestrator is `greenlens-backend/services/pipeline.py`.

### Step 1: Upload and file persistence

The backend receives:

- One required CSV file
- Zero or more optional PDF files

Files are stored locally under a generated upload folder. Filenames are sanitized before saving.

Key endpoint:

- `POST /api/upload`

Relevant file:

- `greenlens-backend/api/upload.py`

### Step 2: Analysis job creation

After upload, the frontend sends:

- `uploadId`
- Company info
- Governance answers

The backend creates a job record and launches the pipeline in a background thread.

Key endpoint:

- `POST /api/analyze`

Relevant files:

- `greenlens-backend/api/analyze.py`
- `greenlens-backend/core/job_store.py`

### Step 3: CSV parsing

The CSV parser expects these required columns:

- `date`
- `category`
- `description`
- `amount`
- `vendor`

The parser:

- normalizes column names
- cleans amount strings
- converts amounts to positive floats
- removes zero-value rows

Relevant file:

- `greenlens-backend/services/csv_parser.py`

### Step 4: Text normalization

The normalizer standardizes vendor, category, and description text and attempts to map vendors to canonical names.

Examples:

- `Enbridge Gas` -> `enbridge_gas`
- `Toronto Hydro` -> `toronto_hydro`
- `Sysco` -> `sysco_food`

Relevant file:

- `greenlens-backend/services/normalizer.py`

### Step 5: Scope classification

The scope classifier uses a three-layer hybrid approach:

1. Vendor dictionary mapping
2. Keyword rules
3. Default Scope 3 fallback with subcategory detection

This design makes the core emissions workflow explainable and consistent. It avoids using an LLM as the primary classifier for ledger rows.

Relevant file:

- `greenlens-backend/services/scope_classifier.py`

### Step 6: Emissions calculation

Once rows are classified, the backend calculates emissions using simplified spend-based factors and province-aware electricity factors.

Outputs include:

- total emissions
- scope-level totals
- category breakdown
- percent of total
- emissions intensity

Relevant files:

- `greenlens-backend/services/emissions_calculator.py`
- `greenlens-backend/core/config.py`

### Step 7: ESG score and benchmark generation

The scoring engine calculates:

- total ESG score
- environmental score
- social score
- governance score
- grade
- benchmark intensity comparison

This is deterministic logic, not LLM output.

Relevant file:

- `greenlens-backend/services/scoring_engine.py`

### Step 8: Compliance and grant retrieval

The retrieval layer reads local JSON corpora and ranks documents based on:

- province relevance
- industry relevance
- SMB size fit for grants

This avoids the operational overhead of an external vector database while still giving the project a grounded knowledge layer.

Relevant file:

- `greenlens-backend/services/retrieval_service.py`

### Step 9: Supporting-document assurance

If the user uploads PDFs, GreenLens extracts text from digital PDFs without relying on an OCR service. It then parses fields such as:

- issuer
- issue date
- due date
- billing period
- reference ID
- total amount
- subtotal and tax

The backend attempts document-to-ledger matching based on:

- canonical vendor match
- date proximity
- amount similarity

Relevant file:

- `greenlens-backend/services/supporting_document_service.py`

### Step 10: Fraud and evidence-risk analysis

The fraud detector performs two kinds of checks.

Document-level checks:

- duplicate supporting-document references
- internal math mismatch
- parser gaps
- unmatched documents
- partial amount mismatches
- thin supporting-document coverage for recurring vendors

Ledger-level forensic checks:

- Benford's Law
- Round-Number Bias
- Temporal Patterns

The service returns:

- overall risk
- risk score
- summary
- matched / partial / unmatched document counts
- duplicate document count
- verified spend amount
- verified spend percentage
- top flags
- transaction anomalies

Relevant file:

- `greenlens-backend/services/fraud_detection_service.py`

### Step 11: Report generation

The report generator builds a narrative prompt from structured deterministic inputs, then asks the LLM for a JSON response containing:

- `executiveSummary`
- `emissionsNarrative`
- `complianceNarrative`
- `fraudNarrative`
- `fundingNarrative`
- `actionsNarrative`

If the LLM fails or returns unusable output, the backend falls back to a deterministic template report.

Relevant files:

- `greenlens-backend/services/report_generator.py`
- `greenlens-backend/services/moorcheh_client.py`

### Step 12: Result persistence

When the job completes, GreenLens writes:

- `document_assurance.json`
- `final_report.json`

to:

- `greenlens-backend/data/processed/<job_id>/`

These files make it easy to inspect the final payload outside the UI.

## How AI is used in this project

GreenLens AI is intentionally selective about where AI is involved.

### AI is used for

- turning verified analysis outputs into polished narrative sections
- answering grounded follow-up questions about the completed report

### AI is not used for

- emissions math
- ESG score calculation
- primary transaction classification for obvious cases
- compliance readiness scoring
- progress/status logic

This separation is one of the most important design choices in the project. It keeps the system credible while still delivering an "AI product" experience.

## Frontend experience

### Intake page

Route:

- `/`

The intake screen collects:

- company profile
- CSV file
- optional PDF files
- governance self-assessment answers

Relevant file:

- `greenlens-ai/app/page.tsx`

### Processing page

Route:

- `/processing`

This page:

- loads the current session from browser storage
- polls `GET /api/status/{job_id}`
- shows pipeline progress
- shows an early fraud/risk alert if available

Relevant file:

- `greenlens-ai/app/processing/page.tsx`

### Dashboard

Route:

- `/dashboard`

The dashboard presents:

- score and benchmark summary
- emissions cards and charts
- compliance readiness
- company profile snapshot
- recommendations
- matched funding programs

Relevant file:

- `greenlens-ai/app/dashboard/page.tsx`

### Full report

Route:

- `/report`

The report view shows:

- executive summary
- emissions narrative and table
- compliance narrative
- funding narrative
- actions
- fraud / supporting-document analysis
- report copilot

Relevant file:

- `greenlens-ai/app/report/page.tsx`

### Session handling

The frontend stores the current analysis session in `localStorage` and ties it to the backend boot ID. That prevents stale browser data from surviving a backend restart and accidentally attaching to the wrong analysis state.

Relevant file:

- `greenlens-ai/lib/session.ts`

## Report copilot

The report copilot is a grounded chat layer over the completed analysis.

How it works:

1. The backend loads the saved report.
2. It converts report sections, emissions breakdowns, flags, documents, compliance items, grants, and recommendations into retrieval chunks.
3. It optionally augments with compliance and grant retrieval.
4. It answers the question using those chunks as context.
5. If the LLM call fails, it falls back to a deterministic grounded answer.

This keeps the chat useful without turning it into an open-ended, hallucination-prone assistant.

Relevant files:

- `greenlens-backend/api/report_chat.py`
- `greenlens-backend/services/report_chat_service.py`

## API surface

### `GET /`

Health and backend metadata endpoint.

Returns:

- service name
- status
- boot ID
- startup timestamp

### `POST /api/upload`

Accepts:

- one CSV file
- optional PDF files

Returns:

- `uploadId`

### `POST /api/analyze`

Accepts:

- `uploadId`
- `company`
- `governance_answers`

Returns:

- `jobId`

### `GET /api/status/{job_id}`

Returns job progress including:

- status
- current step
- label
- progress percentage
- optional error
- optional fraud alert summary

### `GET /api/report/{job_id}`

Returns the completed report payload.

If the job is not finished yet, it responds with HTTP 202 so the frontend can keep polling.

### `POST /api/report-chat/{job_id}`

Accepts:

- a question
- short chat history

Returns:

- answer text
- answer source
- citations

## Local setup

### Prerequisites

- Python 3
- Node.js
- npm

### 1. Clone the repository

```bash
git clone <repo-url>
cd GreenLens-AI
```

### 2. Create the Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install backend dependencies

```bash
pip install -r greenlens-backend/requirements.txt
```

### 4. Configure backend environment variables

Create `greenlens-backend/.env` with:

```env
MOORCHEH_API_KEY=your_key_here
MOORCHEH_MODEL=anthropic.claude-sonnet-4-20250514-v1:0
```

Notes:

- `MOORCHEH_API_KEY` is required for live narrative generation and live report chat
- `MOORCHEH_MODEL` defaults to Sonnet 4 directly in the current codebase

### 5. Install frontend dependencies

```bash
cd greenlens-ai
npm install
cd ..
```

### 6. Run the backend

```bash
cd greenlens-backend
source ../.venv/bin/activate
uvicorn main:app --reload
```

The backend runs at:

- `http://127.0.0.1:8000`

### 7. Run the frontend

In a separate terminal:

```bash
cd greenlens-ai
npm run dev
```

The frontend runs at:

- `http://localhost:3000`

### Optional frontend environment variable

The frontend already defaults to `http://127.0.0.1:8000`, but you can set:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

if you want to point it somewhere else.

## Running the smoke test

The repository includes an end-to-end backend smoke test that covers:

- CSV + supporting documents flow
- CSV-only flow
- report payload shape
- report-chat fallback behavior

Run it with:

```bash
source .venv/bin/activate
python greenlens-backend/scripts/smoke_test_demo.py
```

This is the fastest way to verify the backend is wired correctly before opening the frontend.

## Demo data

Sample ledger files and sample supporting documents are included in:

- `greenlens-backend/demo_data/`

This includes:

- demo CSVs for multiple businesses
- example utility bills
- fuel receipts
- invoices
- intentionally duplicated documents for assurance testing

## Expected input format

### CSV

The uploaded CSV should contain at least these columns:

- `date`
- `category`
- `description`
- `amount`
- `vendor`

The parser normalizes column naming, so standard CSV exports with slightly different spacing still work as long as those core fields are present.

### PDFs

Supporting documents work best when they are:

- text-based digital PDFs
- invoices, utility statements, or receipts
- reasonably structured documents with identifiable totals and dates

The current implementation does not rely on external OCR, so image-only scans may require manual review.

## Output files and artifacts

For each completed analysis, GreenLens saves:

- uploaded source files under `greenlens-backend/data/uploads/<upload_id>/`
- `document_assurance.json` under `greenlens-backend/data/processed/<job_id>/`
- `final_report.json` under `greenlens-backend/data/processed/<job_id>/`

These artifacts are useful for:

- debugging
- auditability
- demos
- post-run inspection without opening the UI

## Important implementation decisions

### Why there is no database

This project is optimized for hackathon reliability. File-based storage was enough for the expected scope and removes unnecessary infrastructure.

### Why there is no vector database

The knowledge corpus is small, static, and curated. Simple local ranking on JSON metadata is sufficient and easier to explain.

### Why the LLM is not used for calculations

The most important numbers in this project need to be defendable. Deterministic Python logic provides that.

### Why the fraud module matters

Most ESG demos stop at a pretty dashboard. GreenLens adds an evidence-quality layer, which makes the output feel much closer to a real reporting workflow.

## Limitations

- The supporting-document parser is optimized for digital PDFs, not full OCR-heavy workflows
- The scope classifier is strong for the included demo patterns but not yet a production-grade universal ledger classifier
- Knowledge retrieval is intentionally simple and works best with the current curated corpus
- Local file storage and in-memory jobs are ideal for demo scale, not distributed production scale
- The ESG scoring system is simplified for a hackathon prototype and not a substitute for a formal external audit

## Future improvements

- add OCR for scanned receipts and image-heavy invoices
- expand the vendor and category mapping dictionary
- support more provinces, sectors, and emission factor detail
- introduce persistent job storage and multi-user auth
- add downloadable PDF export
- support richer compliance corpora and citations in the final report
- expose more audit traces for row-level classification review

## Why this project is submission-ready

This repository already demonstrates:

- a clear user problem
- a complete full-stack workflow
- deterministic analytical depth
- an AI narrative layer with bounded scope
- a tangible fraud/evidence-assurance differentiator
- local demo data and a runnable smoke test

It is not just a concept deck or a single-screen prototype. It is a working application with a defined pipeline, inspectable outputs, and a clear separation between analytics, retrieval, and language generation.
