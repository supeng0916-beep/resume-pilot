from __future__ import annotations

import json
import sys
from pathlib import Path
from time import perf_counter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.model_gateway import chat_with_config, load_model_gateway_config_from_env


def main() -> None:
    config = load_model_gateway_config_from_env()
    if config is None:
        raise SystemExit("LLM config is disabled or incomplete. Check HR_LLM_* settings in .env.")

    started = perf_counter()
    response = chat_with_config(
        messages=[
            {
                "role": "system",
                "content": "You are a concise local model health checker. Return JSON only.",
            },
            {
                "role": "user",
                "content": "Return {\"status\":\"ok\",\"model\":\"your model name\"}.",
            },
        ],
        config=config,
    )
    duration_ms = int((perf_counter() - started) * 1000)
    if response is None:
        raise SystemExit("No response from model gateway.")

    print(
        json.dumps(
            {
                "provider": response.provider,
                "model": response.model,
                "duration_ms": duration_ms,
                "token_usage": response.token_usage.model_dump(),
                "content_preview": response.content[:300],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
