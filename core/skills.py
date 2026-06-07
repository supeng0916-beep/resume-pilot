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
    "PyTorch": ["PyTorch", "Pytorch", "pytorch"],
    "CNN": ["CNN", "卷积神经网络"],
    "scikit-learn": ["SKLearn", "Scikit-learn", "sklearn", "NearestNeighbors"],
    "Pandas": ["Pandas", "pandas"],
    "NumPy": ["NumPy", "numpy"],
    "Flask": ["Flask", "flask"],
    "Streamlit": ["Streamlit", "streamlit"],
    "Feature Engineering": ["Feature Engineering", "特征工程"],
    "Data Pipeline": ["Data Pipeline", "数据流水线", "数据管道"],
    "ETL": ["ETL", "数据清洗"],
    "Machine Learning": ["机器学习", "Machine Learning", "ML"],
    "Computer Vision": ["计算机视觉", "Computer Vision", "图像分类", "图像去噪"],
}


def extract_known_skills(text: str) -> list[str]:
    matched: list[str] = []
    for canonical, aliases in SKILL_ALIASES.items():
        if any(alias.lower() in text.lower() for alias in aliases):
            matched.append(canonical)
    return matched
