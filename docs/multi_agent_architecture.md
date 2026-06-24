# Multi-Agent Architecture

AgenticHR is now positioned as a supervisor-centered multi-agent evaluation system, not a single prompt wrapper. The design keeps LangGraph as the orchestration backbone and uses a central Supervisor to plan and route work, while specialist agents produce independent, typed results that can be audited, criticized, and merged.

## Why Multi-Agent

A single chat model can produce a plausible hiring report, but it does not naturally provide separable accountability for:

- candidate-side interpretation
- job-side requirement analysis
- evidence grounding
- historical feedback retrieval
- risk review
- cross-agent consistency checking
- final consensus and arbitration

AgenticHR separates these concerns so that each agent emits a structured `AgentResult`. The system can then inspect which agent made which claim, which claims lack evidence, and which conflicts require human review.

## Runtime Shape

Current LangGraph path:

```text
Supervisor
 -> DocumentParser
 -> ResumeExtractor
 -> JDExtractor
 -> Validator
 -> ParallelSpecialists(Supervisor-selected specialists)
 -> RubricSelector
 -> Matcher
 -> RiskEvaluator
 -> SupervisorReviewRouter
 -> EvidenceAuditor? / CriticAgent?
 -> ConsensusAgent
 -> ReportWriter
 -> HumanReview
```

The graph now uses a real fan-out/fan-in specialist stage. `ParallelSpecialists` dispatches only the spokes selected by Supervisor, merges their `AgentResult` outputs, preserves their child trace entries, and records `specialist_execution.mode = "parallel"`.

CandidateAnalyst and JobAnalyst run by default for candidate evaluation. MemoryAgent runs only when a feedback memory source is configured. After match/risk scoring, Supervisor creates a second review route:

- EvidenceAuditor runs only when there are matched skills to ground against resume evidence.
- CriticAgent runs when risk/threshold ambiguity exists or EvidenceAuditor finds weak/unsupported evidence.
- ConsensusAgent always arbitrates the final recommendation.

ConsensusAgent owns the final recommendation; the old ReportingAgent role has been folded into consensus arbitration.

## Agent vs Deterministic Node Boundary

AgenticHR deliberately does not call every node an agent.

Core agents:

- `SupervisorAgent`: central planning, dynamic routing policy, activation list, and skipped-agent reasons
- `CandidateAnalyst`: candidate-side interpretation and information gaps
- `JobAnalyst`: job-side priorities and requirement focus
- `MemoryAgent`: historical human feedback retrieval, executed only when memory is configured
- `EvidenceAuditor`: evidence grounding for matched skills
- `CriticAgent`: cross-agent consistency and risk-trigger review
- `ConsensusAgent`: final arbitration and recommendation

Deterministic nodes and tools:

- `DocumentParser`: PyMuPDF, OCR, and optional vision text extraction
- `ResumeExtractor` / `JDExtractor`: structured extraction with rule fallback and optional LLM assistance
- `Validator`: Pydantic schema gate
- `RubricSelector`: scoring-track selection
- `Matcher`: score calculation
- `RiskEvaluator`: manual-review risk scoring
- `ReportWriter`: deterministic report rendering

This boundary is intentional: stable, cheap, testable work stays deterministic; ambiguous interpretation, evidence review, conflict checking, and final arbitration are handled by agents.

CandidateAnalyst and JobAnalyst are hybrid agents. Each first invokes an embedded deterministic skill from `core/agent_skills.py`, then optionally calls the local/OpenAI-compatible model gateway when `HR_AGENT_LLM_ENABLED=true`. The LLM layer is constrained to evidence-bound interpretation, interview probes, and concerns; if it fails, the deterministic skill output remains the source of truth.

## Agent Contracts

`core/agent_contracts.py` defines the common output contract:

```text
agent_name
role
status
findings
evidence_refs
confidence
concerns
token_usage
duration_ms
model_name
provider
```

This is the key production boundary. Downstream consumers do not need to know whether a result came from rules, a local model, a remote model, or a hybrid agent.

## Critic and Consensus

`EvidenceAuditor` checks whether matched skills are supported by resume evidence.

`CriticAgent` checks contradictions such as high match score with weak evidence, high risk score, or score/risk inconsistency.

`ConsensusAgent` merges specialist outputs into the final recommendation and records:

- recommendation
- rationale
- consensus confidence
- conflicts
- unsupported skills
- open concerns

This is the part that makes the system meaningfully different from a single chat completion: the final answer is an arbitration over independently produced agent outputs, not only a generated paragraph.

## Local Model Gateway

`core/model_gateway.py` introduces an OpenAI-compatible model gateway. It supports:

- `openai`
- `openai_compatible`
- `ollama`
- `lmstudio`

Example `.env` for Ollama:

```env
HR_LLM_ENABLED=true
HR_LLM_PROVIDER=ollama
HR_LLM_API_KEY=local
HR_LLM_MODEL=qwen3:1.7b
HR_LLM_BASE_URL=http://localhost:11434/v1
HR_LLM_TIMEOUT_SECONDS=60
HR_LLM_STRUCTURED_EXTRACTION_ENABLED=false
HR_AGENT_LLM_ENABLED=true
```

For local providers, the gateway uses `local` as the API key by default and normalizes the URL to `/chat/completions`.

`qwen3:1.7b` is used for text reasoning inside selected agents. It is not a vision/OCR model. Image-style PDFs should use the parser's OCR-first path:

```env
HR_IMAGE_PDF_PARSE_STRATEGY=ocr_first
HR_ENABLE_LOCAL_OCR=true
```

## Benchmark Command

Run a 50-candidate benchmark:

```powershell
D:\python\python.exe scripts\run_benchmark.py --limit 50 --request-id benchmark-50 --output data\test_outputs\benchmark_50.json
```

The benchmark records:

- candidate count
- schema pass rate
- total and average duration
- retry count
- token usage
- estimated model cost
- per-candidate score/risk/validation status
- specialist execution mode and duration

This directly answers the production question: "What happens when we run 50 resumes through the system?"
