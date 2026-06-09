# Data Schema and Annotation Boundary

本项目的数据层分为三类：合成演示数据、人工标注数据、运行时产物。合成数据可以提交到仓库；真实简历、原始 PDF、人工标注结果和本地数据库默认不提交。

## Synthetic Candidate Dataset

Path: `data/datasets/synthetic_candidates.jsonl`

每行是一名候选人的结构化样本，用于训练“人工复核风险预测”演示模型。

```json
{
  "candidate_id": "cand-0001",
  "name": "候选人0001",
  "education": "本科",
  "major": "计算机科学与技术",
  "years_experience": 0,
  "skills": ["Python", "FastAPI", "SQL"],
  "expected_salary_k": 18,
  "candidate_track": "campus",
  "project_count": 2,
  "internship_count": 1,
  "evidence_strength_avg": 0.72,
  "parse_quality_score": 0.91
}
```

核心约束：

- `years_experience` 控制在 `0-10` 年，并提高 `0` 年候选人的比例以贴近校招/应届场景。
- `expected_salary_k` 控制在 `8-50`，并与学历形成正相关分布。
- `evidence_strength_avg` 表示技能是否有项目/经历证据支撑，而不是只看关键词堆砌。
- `parse_quality_score` 用于模拟 PDF 解析质量，低质量会提高人工复核风险。

## Synthetic Job Dataset

Path: `data/datasets/synthetic_jobs.jsonl`

每行是一个 JD 模板。

```json
{
  "job_id": "job-backend",
  "title": "后端开发工程师",
  "required_years": 0,
  "required_skills": ["Python", "FastAPI", "Redis"],
  "nice_to_have": ["Docker", "LLM 应用"],
  "salary_range_k": [18, 30],
  "recruitment_track": "campus"
}
```

## Synthetic Labels

Path: `data/datasets/synthetic_labels.jsonl`

当前 ML 目标是 `needs_human_review`，也就是“是否需要人工复核”，不是录用预测。

```json
{
  "candidate_id": "cand-0001",
  "job_id": "job-backend",
  "needs_human_review": true,
  "review_reasons": ["parse_quality_low", "salary_out_of_range"],
  "match_score": 73.4
}
```

## Manual Annotation

Path: `data/datasets/annotations.jsonl`

该文件被 `.gitignore` 忽略，适合存放你手工标注的真实或脱敏样本。推荐一行一个标注结果：

```json
{
  "annotation_id": "ann-20260609-001",
  "candidate_id": "private-redacted-001",
  "job_id": "job-backend",
  "needs_human_review": true,
  "review_reasons": ["missing_project_evidence"],
  "annotator": "human",
  "notes": "技能栏有 Redis，但项目经历没有对应证据。"
}
```

人工标注只回答流程风险问题：是否需要复核、复核原因是什么、哪些字段不可信。不标注“是否录用”，避免把演示模型包装成真实招聘决策模型。

## Runtime Persistence

FastAPI 服务和后续 Streamlit 分层会使用 SQLite 保存运行结果。

Default path: `data/hr_runs.sqlite3`

SQLite 保存：

- `workflow_runs`: request id、匹配分、风险分、人工复核状态、报告、完整 payload、trace。
- 完整 trace 以 JSON 保存，便于 replay、debug 和 demo 展示。

数据库文件默认忽略，不提交到仓库。
### Runtime Persistence Tables

FastAPI 服务使用 SQLite 保存运行结果，React 控制舱只通过 API 读取这些持久化数据。

Default path: `data/hr_runs.sqlite3`

SQLite 保存：
- `workflow_runs`: request id、匹配分、风险分、人工复核状态、报告、完整 payload、trace。
- `candidates`: 候选人姓名、学历、年限、分轨、期望薪资和完整候选人 profile。
- `jobs`: 岗位标题、要求年限、招聘分轨、技能要求和完整岗位 profile。
- `traces`: 节点级 trace 事件，支持排障、观测和 replay 展示。
- `reports`: Markdown 报告和报告质量检查结果。
- `reviews`: 人工复核结论、反馈、复核人和时间。
- `batches`: 批量评估批次摘要、候选人数、Top 候选人、批次报告和完整 batch payload。
- `batch_runs`: 批次与候选人运行记录的关联表，保留排名顺序、candidate id 和 rank score。

完整 payload 和 trace 仍以 JSON 保存，方便 replay、debug 和 demo 展示；规范化字段用于列表查询、筛选和控制舱渲染。
数据库文件默认忽略，不提交到仓库。
