# Agentic HR 标注规范

本项目的数据策略分两层：

1. 合成结构化数据用于训练、回归测试和端到端工程验证。
2. 少量脱敏真实简历用于人工标注，评估 LLM 抽取和匹配逻辑。

系统不直接预测“是否录用”。当前标签目标是识别候选人与岗位的匹配强度，以及是否需要人工重点复核。

## 文件格式

合成数据默认写入 `data/datasets/`：

- `synthetic_candidates.jsonl`
- `synthetic_jobs.jsonl`
- `synthetic_labels.jsonl`
- `annotations.jsonl`

每行是一个独立 JSON 对象，便于追加、抽样、上传到 Colab 和做增量评估。

## 匹配标签

`strong_match`：
候选人大部分必备技能命中，并且核心技能至少有项目、实习或工作经历证据支撑。

`partial_match`：
候选人具备一部分岗位要求，但核心技能缺失、年限不足，或证据不够完整。

`weak_match`：
候选人与岗位核心要求差距明显，或技能主要停留在关键词列表，没有项目/经历证据。

## 人工复核标签

`needs_human_review = true` 适用于以下情况：

- PDF/OCR/视觉解析质量低。
- 候选人类型无法判断。
- 核心技能只有关键词，没有项目或工作经历证据。
- 期望薪资接近或超过岗位预算。
- 工作年限低于 JD 要求。
- LLM 抽取失败、字段矛盾或 schema 校验多次失败。
- 涉及敏感或不应由系统自动判断的信息。

## 风险标签

`salary_pressure`：
期望薪资接近或超过岗位预算上限。

`evidence_gap`：
技能只出现在技能栏，缺少项目、实习或工作经历证据。

`experience_gap`：
候选人相关年限低于 JD 要求。

`parse_low_quality`：
PDF 解析、OCR 或 Vision LLM 转写质量较低。

`track_unknown`：
无法可靠判断校招、社招或实习轨道。

## 证据质量

`strong`：
候选人在项目/工作经历中说明了技能使用场景、职责或结果。

`medium`：
候选人在项目或经历中提到技能，但上下文较少。

`weak`：
技能主要出现在技能栏，项目支撑较弱。

`unsupported`：
系统命中技能，但简历中没有可核验片段。

## 标注流程

1. 运行 `scripts/generate_dataset.py` 生成合成数据。
2. 打开标注舱检查样本、修正候选人画像和岗位画像。
3. 选择匹配标签、风险标签、证据质量，并填写备注。
4. 保存到 `annotations.jsonl`。
5. 后续训练或评估优先使用人工标注记录，合成标签用于冷启动和回归测试。

## Colab 训练交接

上传以下文件到 Colab 即可训练：

- `synthetic_candidates.jsonl`
- `synthetic_jobs.jsonl`
- `synthetic_labels.jsonl`
- `annotations.jsonl`，如果已经有人工标注

训练产物建议保存为：

- `models/review_risk_model.json`
- `models/model_card_review_risk.md`

模型目标建议是预测 `needs_human_review`，而不是预测候选人是否应被录用。

本地训练命令：

```powershell
D:\python\python.exe scripts\train_review_risk_model.py --dataset-dir data\datasets --output models\review_risk_model.json --model-card models\model_card_review_risk.md
```

如果使用 Colab，可上传 `data/datasets/*.jsonl`，训练后把 `review_risk_model.json` 和 `model_card_review_risk.md` 放回项目的 `models/` 目录。`models/*.json` 默认不提交到 git，避免把临时模型或真实训练产物误提交。
