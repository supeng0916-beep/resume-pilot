from __future__ import annotations


SKILL_ALIASES: dict[str, list[str]] = {
    "Python": ["Python", "python"],
    "FastAPI": ["FastAPI", "fastapi"],
    "PostgreSQL": ["PostgreSQL", "postgres"],
    "Redis": ["Redis", "redis"],
    "MySQL": ["MySQL", "mysql"],
    "Docker": ["Docker", "docker"],
    "Kubernetes": ["Kubernetes", "K8s", "k8s"],
    "LangGraph": ["LangGraph", "langgraph"],
    "LLM": ["LLM", "大模型", "大语言模型", "LLM 应用"],
}


def extract_known_skills(text: str) -> list[str]:
    matched: list[str] = []
    for canonical, aliases in SKILL_ALIASES.items():
        if any(alias.lower() in text.lower() for alias in aliases):
            matched.append(canonical)
    return matched
