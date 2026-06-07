# Project Memory

## 远期摘要

项目定位为 `Agentic HR`：以真实 HR 招聘评估工作流为外壳，以 LangGraph 多智能体/多节点状态编排为内核，目标是做成可写入简历、可面试讲解的 AI 工程项目，而不是单纯 Demo。

核心原则：

- 系统只做招聘辅助，不替代人类录用/淘汰决策。
- LangGraph 负责状态流转、条件路由、retry、自愈循环和后续 HITL。
- Harness 层负责测试、回放、trace、评估和可观测性。
- Agent、Skill、Tool、Node 分层设计：Agent 负责决策和开放式推理，确定性逻辑用普通 Node/Skill。
- 暂不自研完整 Agent 框架，使用 LangGraph 做底层编排，在其上封装业务 Harness。
- MCP 作为后期可选工具接入层，不放入 MVP 主线。
- 第一版不急着做 Redis、Docker、前后端分离、并发和数据库，先做可运行闭环。

重要架构讨论：

- 必须考虑 PDF 简历输入，加入 Document Ingestion 层。
- PDF 第一版只支持文本型 PDF；扫描件只标记 `needs_ocr=True`，暂不做 OCR。
- 评分不能简单依赖关键词重叠，必须考虑证据溯源和反关键词堆砌。
- 中国招聘场景需要区分校招、社招、实习，不能用同一套权重评估所有候选人。
- 校招更关注专业基础、项目/实习、学习能力和潜力证据。
- 社招更关注技能匹配、工作年限、项目复杂度、职责深度和业务成果。

## 已完成进度

已初始化 Git 仓库并分阶段提交。

当前提交历史核心节点：

- `d24a8cc Initial LangGraph walking skeleton`
- `6d61ec0 Add pydantic schemas and validation tests`
- `07068ba Add validation retry routing`
- `23f5bef Add track-aware scoring schemas`
- `65e7afc Add track-aware rubric selection`
- `9623bb7 Add PDF document parser`
- `fc43724 Add CLI evaluation inputs`
- `0cc88ce Add rule-based resume extraction`
- `edded28 Improve resume parsing with real PDF feedback`

当前系统能力：

- LangGraph walking skeleton 已跑通。
- 有 `core/state.py` 统一 WorkflowState。
- 有 Pydantic Schema：候选人、岗位、文档元信息、证据、评分 rubric、匹配 breakdown。
- Validator 使用 Pydantic 真实校验。
- Validator 失败后通过 conditional edge 回到 resume extractor，支持 retry，自愈上限由 `max_retries` 控制。
- 超过 retry 上限后会生成失败报告。
- PDF 解析使用 PyMuPDF，文件不存在时 fallback 到 mock resume。
- CLI 支持：

```powershell
D:\python\python.exe main.py --resume data\examples\candidate.pdf
D:\python\python.exe main.py --resume data\examples\candidate.pdf --jd "..."
```

- Resume extractor 已从固定 mock 改成规则版文本抽取。
- JD extractor 已从固定 mock 改成轻量规则抽取。
- Skills 统一在 `core/skills.py` 中维护。
- Rubric selector 能判断 campus / experienced / intern / unknown。
- Matcher 根据 selected rubric 加权评分，并输出证据说明。

## 真实 PDF 验证结果

用户已放入真实 PDF：

```text
data/examples/简历.pdf
```

注意：真实 PDF 含个人信息，已加入 `.gitignore`：

```text
data/examples/*.pdf
```

真实 PDF 验证结果：

- `Document parser: pymupdf`
- `Needs OCR: False`
- `text_length: 2465`
- 候选人识别为：苏鹏
- 使用数据科学 JD 后轨道识别为：`campus`
- 岗位标题修正为：校招数据科学工程师
- 匹配点包括：Computer Vision、Data Pipeline、Machine Learning、PyTorch、Python、Streamlit
- 匹配分：79.25

真实 PDF 暴露并已修正的问题：

- 原技能词表太窄，只识别 Python，已扩展 PyTorch、CNN、scikit-learn、Flask、Streamlit、Feature Engineering、Data Pipeline、ETL、Machine Learning、Computer Vision 等。
- 项目经历曾被误判成社招工作经历，已将校园项目、实习、正式工作经历分开。
- 在读硕士/项目/实习型简历应优先走 `campus`，已修正。
- JD 中“数据科学工程师”曾被错误标题化为后端工程师，已修正。

## 最近保留区

最近的工作重点是从真实 PDF 输入走完整端到端流程，并根据真实简历反馈修正规则抽取和分轨评分。

当前最新状态：

- 测试通过：`23 passed`
- 工作区在上一轮结束时干净。
- 最新提交：`edded28 Improve resume parsing with real PDF feedback`

下一步建议：

升级 `Report Writer`，从当前模板报告改为结构化 HR 评估报告，包含：

- 候选人摘要
- 岗位匹配亮点
- 风险点
- 证据引用
- 建议面试问题
- 人工审批建议

当前报告仍偏模板化，数据已更真实，但表达还不像正式 HR/面试官评估报告。
