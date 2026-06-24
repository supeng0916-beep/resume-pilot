# Benchmark Usage

The benchmark harness measures operational behavior across many resumes. It is designed for interview and engineering questions about schema pass rate, latency, token usage, retry behavior, and estimated cost.

## Smoke Benchmark

```powershell
D:\python\python.exe scripts\run_benchmark.py --limit 3 --request-id smoke-benchmark --output data\test_outputs\benchmark_smoke.json
```

## 50 Resume Benchmark

```powershell
D:\python\python.exe scripts\run_benchmark.py --limit 50 --request-id benchmark-50 --output data\test_outputs\benchmark_50.json
```

## With Local LLM Extraction

Start an OpenAI-compatible local model server, then configure:

```env
HR_LLM_ENABLED=true
HR_LLM_PROVIDER=ollama
HR_LLM_MODEL=qwen2.5:7b
HR_LLM_BASE_URL=http://localhost:11434/v1
```

For a 16 GB RAM / 2 GB VRAM laptop, use the lighter model:

```env
HR_LLM_ENABLED=true
HR_LLM_PROVIDER=ollama
HR_LLM_API_KEY=local
HR_LLM_MODEL=qwen3:1.7b
HR_LLM_BASE_URL=http://localhost:11434/v1
HR_LLM_TIMEOUT_SECONDS=120
HR_LLM_STRUCTURED_EXTRACTION_ENABLED=false
```

Check the local model:

```powershell
D:\python\python.exe scripts\check_local_llm.py
```

Run:

```powershell
D:\python\python.exe scripts\run_benchmark.py --limit 50 --enable-llm-structured-extraction --price-per-1k-tokens 0 --output data\test_outputs\benchmark_50_local_llm.json
```

## Output Summary

The JSON report contains:

```json
{
  "candidate_count": 50,
  "completed_count": 50,
  "schema_pass_rate": 1.0,
  "total_duration_ms": 12345,
  "average_duration_ms": 246.9,
  "total_retry_count": 0,
  "token_usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  },
  "estimated_cost": 0.0
}
```

When LLM-backed agents report token usage through `agent_metrics`, the benchmark aggregates it automatically.

Each run also includes:

```json
{
  "specialist_execution": {
    "mode": "parallel",
    "agents": ["candidate_analyst", "job_analyst", "memory_agent"],
    "duration_ms": 12
  }
}
```
