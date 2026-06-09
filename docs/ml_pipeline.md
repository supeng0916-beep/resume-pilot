# ML Pipeline: Human Review Risk

本项目的 ML 部分只预测 `needs_human_review`，即一个候选人评估结果是否需要人工复核。它不预测录用概率，不替代 HR 决策。

## Data Sources

- 合成候选人：`data/datasets/synthetic_candidates.jsonl`
- 合成 JD：`data/datasets/synthetic_jobs.jsonl`
- 合成标签：`data/datasets/synthetic_labels.jsonl`
- 人工标注：`data/datasets/annotations.jsonl`，默认不提交

## Training

```powershell
D:\python\python.exe scripts\train_review_risk_model.py --dataset-dir data\datasets --output models\review_risk_model.json --model-card models\model_card_review_risk.md --epochs 80 --learning-rate 0.06 --validation-ratio 0.2 --seed 42
```

当前提交的 demo 模型保存在 `models/review_risk_model.json`，模型卡片在 `models/model_card_review_risk.md`。

## Feature Groups

- 候选人基础信息：学历、年限、候选人类型、期望薪资。
- 岗位匹配信息：技能重合、年限差距、薪资区间差距。
- 解析与证据信息：PDF 解析质量、技能证据强度、项目数量、实习数量。
- 流程风险信息：是否缺字段、是否需要 OCR、是否存在异常状态。

## Evaluation Boundary

指标用于说明工程流程是否能跑通，包括 accuracy、precision、recall、F1。由于数据主要为合成数据，指标不能解释为真实招聘预测能力。

## Runtime Usage

CLI:

```powershell
D:\python\python.exe main.py --risk-model-path models\review_risk_model.json
```

FastAPI:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_api.ps1
```

请求：

```json
{
  "request_id": "api-demo-001",
  "resume_text": "Candidate Alice. Python FastAPI Redis project.",
  "jd_text": "Backend engineer requires Python, FastAPI and Redis.",
  "risk_model_path": "models/review_risk_model.json"
}
```
