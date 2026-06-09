# 人工复核风险模型

## 用途

该模型预测候选人评估结果是否需要人工重点复核，不用于自动录用或淘汰候选人。

## 目标

- Target: `needs_human_review`
- Model type: `review_risk_logistic_v1`

## 训练数据

- Training rows: 400
- Validation rows: 100
- Data source: synthetic_or_annotated_jsonl

## 指标

- Accuracy: 0.92
- Precision: 0.9825
- Recall: 0.8889
- F1: 0.9333

## 特征权重

- `required_skill_coverage`: -1.826669
- `parse_quality_gap`: -0.185618
- `salary_pressure`: 7.802718
- `experience_gap`: 11.490862
- `evidence_gap`: 7.92004
- `track_unknown`: 7.612098
- `weak_match`: 7.37619

## 合规边界

该模型只用于排序人工复核优先级，最终招聘判断必须由人工完成。