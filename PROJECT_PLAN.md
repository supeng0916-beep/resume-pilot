# Agentic HR - 基于 LangGraph 的多智能体招聘评估系统

## 1. 项目定位

本项目定位为一个接近真实 HR 工作流的智能招聘评估系统，而不是单纯的 LangGraph 技术 Demo。

系统输入候选人简历、岗位 JD、招聘偏好等信息，通过多智能体工作流完成简历结构化、岗位需求解析、候选人匹配、风险评估、报告生成和人工审批。

核心原则：

- 系统只做招聘辅助，不直接替代人类做录用或淘汰决策。
- LLM 负责语义理解、信息抽取、报告生成。
- 传统 ML 模型负责可控的风险评分或匹配评分。
- Pydantic、规则节点和人工审批负责安全边界。
- LangGraph 负责状态流转、条件路由、错误恢复、人工中断和长期记忆。
- Harness 层负责运行、测试、评估、回放和观测整个 Agentic Workflow。

适合简历表述：

> 基于 LangGraph 构建 Hub-and-Spoke 多智能体招聘评估系统，将 LLM 信息抽取、Pydantic 强校验、传统 ML 风险模型、Human-in-the-Loop 审批和长期记忆机制整合为可追踪的端到端 HR 工作流。

### 1.1 框架选型判断

本项目选择 LangGraph 作为核心工作流编排框架，而不是从零自研完整 Agent 框架。

选择 LangGraph 的原因：

- 招聘评估流程天然是多步骤、有状态、有条件分支的工作流。
- 系统需要支持校验失败后的 retry、自愈循环和人工审批中断。
- LangGraph 的节点、边、条件边和 checkpoint 能较好表达该类流程。
- 使用主流框架有利于展示对 AI 应用工程生态的理解。

不从零自研完整框架的原因：

- 自研图执行引擎容易分散精力，短期内难以达到成熟框架的稳定性。
- 面试项目更应该展示业务建模、工程封装、评估体系和架构取舍，而不是重复实现底层调度。
- 本项目可以在 LangGraph 之上封装自己的 Harness、节点规范、日志追踪和评估体系，从而体现工程能力。

推荐表达：

```text
底层编排使用 LangGraph
业务节点自行设计
Harness 层自行封装
评估体系自行设计
控制舱自行实现
```

### 1.2 Harness 工程思想

本项目不仅实现 Agent 节点，还要实现一层 Agent Harness。

Harness 的目标是让系统可运行、可测试、可观测、可回放、可评估。

Harness 应体现以下能力：

- Scenario Harness：内置多组简历和 JD 测试样本，一键批量运行。
- Validation Harness：统一检查 LLM 结构化输出是否符合 Schema。
- Replay Harness：保存历史输入和节点输出，支持失败案例重放。
- Eval Harness：评估最终报告是否包含候选人摘要、匹配点、风险点、面试建议和审批建议。
- Observability Harness：记录节点耗时、retry 次数、错误原因、token 使用量和最终状态。
- Regression Harness：修改 prompt、schema 或节点逻辑后，使用旧样本回归测试，防止效果退化。

适合简历表述：

> 设计 Agent Harness 层，支持多场景批量运行、节点级 tracing、结构化校验、失败重放和评估回归，用于提升多智能体工作流的可测试性与可观测性。

### 1.3 Agent、Skill、Tool 与 Node 的边界

本项目不追求“所有模块都是 Agent”。更成熟的设计是按职责分层。

```text
Agent 负责决策和开放式推理
Skill 负责单一、可复用的能力
Tool 负责外部动作或外部系统调用
Node 负责工作流中的一个执行步骤
Harness 负责运行保障、测试、评估和观测
LangGraph 负责流程编排和状态流转
```

适合做 Skill 或普通 Node 的能力：

- Pydantic 校验
- 技能匹配计算
- 薪资范围解析
- 风险模型预测
- 报告格式检查
- 日志记录

适合做 Agent 的能力：

- Orchestrator：根据状态、错误和人工反馈决定下一步。
- Extraction Agent：处理非结构化简历或 JD，并在校验失败时自我修复。
- Report Agent：综合匹配分、风险分和历史偏好，生成解释性报告。
- Policy Agent：读取人工反馈，总结招聘偏好或风险规则。

因此，本项目更准确的定位是 Agentic Workflow System，而不是所有节点都由 Agent 实现的系统。

## 2. 第一版核心场景

第一版只聚焦一个完整闭环：

```text
输入：候选人简历 PDF + 岗位 JD
    ↓
PDF 文档解析与文本清洗
    ↓
简历信息抽取
    ↓
岗位要求抽取
    ↓
结构化校验
    ↓
岗位匹配度计算
    ↓
候选人风险评估
    ↓
生成招聘评估报告
    ↓
人工审批
    ↓
记录反馈与偏好
```

第一版不追求复杂 HR 系统功能，例如排班、薪酬系统、ATS 集成、邮件发送、Offer 审批链、多租户权限等。

## 3. 文档摄取层：PDF 简历解析

真实招聘流程中，候选人信息通常来自 PDF 简历，而不是已经清洗好的纯文本。

因此，本项目需要在 LLM 抽取之前加入 Document Ingestion 层。

目标：

- 接收 PDF 简历文件。
- 判断 PDF 类型：文本型 PDF 或扫描型 PDF。
- 从文本型 PDF 中提取正文、表格和基础布局信息。
- 对扫描型 PDF 预留 OCR 能力。
- 清洗页眉、页脚、重复空白、分页符和乱码。
- 输出稳定的 `resume_text`，供 Resume Extraction Agent 使用。

建议第一版先支持文本型 PDF，扫描件 OCR 作为后续增强。

推荐处理流程：

```text
PDF 文件
    ↓
Document Loader
    ↓
PDF 类型检测
    ↓
文本型 PDF：PyMuPDF / pdfplumber 提取文本
扫描型 PDF：OCR 预留接口
    ↓
文本清洗与分段
    ↓
resume_text
    ↓
Resume Extraction Agent
```

### 3.1 PDF 解析节点设计

新增 `Document Parser Node`。

职责：

- 接收 PDF 文件路径或上传文件对象。
- 提取原始文本。
- 保留必要的段落结构。
- 记录解析方式和解析质量。
- 如果解析文本过短或为空，标记为 `needs_ocr = True`。

输出示例：

```python
{
    "resume_text": "...",
    "document_meta": {
        "file_name": "candidate_resume.pdf",
        "page_count": 2,
        "parser": "pymupdf",
        "needs_ocr": False,
        "text_length": 3250
    }
}
```

### 3.2 PDF 解析技术取舍

第一版建议：

- 优先使用 PyMuPDF 或 pdfplumber 解析文本型 PDF。
- 如果简历中表格很多，可以优先尝试 pdfplumber。
- 如果追求速度和基础文本提取，可以优先尝试 PyMuPDF。
- OCR 不作为 MVP 必需项，但需要预留接口。

后续增强：

- 使用 OCR 处理扫描型 PDF。
- 支持 DOCX 简历。
- 支持多文件上传。
- 支持简历原文与抽取字段的引用定位。
- 支持解析质量评分，低质量解析自动提示人工检查。

## 4. 系统边界与安全原则

HR 场景涉及敏感决策，因此系统必须明确边界：

- 不输出“必须录用”或“必须淘汰”的结论。
- 输出应为“建议进入下一轮”“建议补充信息”“建议人工重点关注”等辅助性意见。
- 对年龄、性别、婚育、民族、健康状况等敏感信息保持谨慎，默认不作为评分依据。
- 最终报告必须经过 Human-in-the-Loop 人工审批。
- 所有关键判断应给出可解释理由。
- 人工拒绝或修改系统建议时，应记录原因，方便后续改进。

### 4.1 校招与社招分轨评分

中国招聘场景中，候选人通常至少分为校招、社招和实习三类。

系统不能用同一套权重评价所有候选人。

原因：

- 应届生通常没有正式工作经历，不应因为工作年限为 0 被直接扣低分。
- 社招生可能学历普通但经验丰富，不应被学历权重过度压制。
- 实习生更应关注基础能力、学习能力、项目潜力和岗位匹配度。

因此，系统需要引入 `candidate_track` 和 `scoring_rubric`。

候选人轨道：

```text
campus       校招 / 应届生
experienced  社招 / 有经验候选人
intern       实习生
unknown      无法判断
```

判断来源优先级：

1. 岗位 JD 明确指定招聘类型。
2. 候选人简历中的毕业时间、工作经历、实习经历和项目类型。
3. 如果无法确定，则标记为 `unknown`，并在报告中提示人工确认。

校招评分更关注：

- 专业/学历匹配
- 校园项目
- 实习经历
- 技能基础
- 学习能力证据
- 竞赛、科研、作品集或开源项目

社招评分更关注：

- 岗位技能匹配
- 相关工作年限
- 项目复杂度
- 职责深度
- 业务成果
- 行业或领域匹配

实习评分更关注：

- 基础技能
- 项目实践
- 学习能力
- 沟通与执行潜力
- 时间匹配度

示例权重：

```text
校招：
专业/学历匹配 20%
项目/实习经历 25%
技能基础 20%
学习能力证据 15%
竞赛/科研/作品 10%
岗位动机与稳定性 10%

社招：
岗位技能匹配 30%
相关工作年限 15%
项目复杂度/职责深度 25%
业务成果 15%
行业/领域匹配 10%
薪资与稳定性 5%
```

评分报告必须说明当前使用的是哪一套 rubric。

示例：

```text
该候选人按校招规则评估，因此未因缺少正式工作年限扣分；主要评分依据为校园项目、技能基础和实习经历。
```

```text
该候选人按社招规则评估，学历权重较低，主要依据其 5 年后端经验、项目复杂度和技能证据给出较高匹配分。
```

### 4.2 证据溯源与反关键词堆砌

评分不能只依赖关键词命中。

如果候选人只在技能栏堆砌大量技术词，但项目经历和工作经历没有支撑，系统应降低置信度，并提示人工核实。

设计原则：

- 技能栏出现某技术，只作为弱证据。
- 项目经历中出现具体使用场景，作为中证据。
- 描述了职责、技术方案、业务成果或复杂问题处理，作为强证据。
- 同一关键词重复出现不重复加分。
- 报告必须引用证据片段，而不是只给结论。

示例：

```text
JD 要求：Redis

弱证据：技能栏列出 Redis
中证据：项目中使用 Redis 做缓存
强证据：说明 Redis 用于热点数据缓存、TTL 策略和缓存击穿处理
```

系统需要引入证据结构：

```python
EvidenceSpan:
    source
    section
    text
    page
    confidence

SkillEvidence:
    skill
    evidence_strength
    evidence
```

后续 Matcher 应基于证据强度计算技能分，而不是简单统计关键词重叠。

## 5. Agent 与节点架构

采用 Hub-and-Spoke 架构，但不是所有节点都设计成 LLM Agent。

Hub 负责任务编排和状态路由；Spoke 负责专门能力。

### 5.1 Hub

#### Orchestrator Agent

职责：

- 判断当前工作流阶段。
- 根据 State 决定下一步节点。
- 根据错误信息决定是否重试。
- 决定是否进入人工审批。
- 读取长期记忆或招聘偏好。

### 5.2 Spokes

#### Resume Extraction Agent

职责：

- 从简历文本中抽取候选人结构化信息。
- 输出候选人姓名、学历、工作年限、技能、项目经历、期望薪资、最近工作经历等字段。

#### Document Parser Node

职责：

- 从 PDF 简历中提取文本。
- 判断是否需要 OCR。
- 输出清洗后的 `resume_text` 和 `document_meta`。

该节点属于确定性文档处理节点，不需要设计成 Agent。

#### JD Extraction Agent

职责：

- 从岗位 JD 中抽取岗位要求。
- 输出岗位名称、必备技能、加分技能、经验年限、学历要求、薪资范围、岗位级别等字段。

#### Validation Node

职责：

- 使用 Pydantic 校验 LLM 输出。
- 如果字段缺失、类型错误、格式错误，则返回结构化错误。
- 触发自愈循环，让 Extractor 根据错误重写。

该节点应优先使用普通 Python 函数，不必使用 LLM。

#### Matching Node

职责：

- 计算候选人与岗位之间的匹配度。
- 可以先用规则实现，再逐步加入 embedding 或 ML 方法。

示例维度：

- 技能匹配度
- 工作年限匹配度
- 学历匹配度
- 薪资匹配度
- 项目经验相关性

#### ML Risk Node

职责：

- 使用 LightGBM 或 XGBoost 预测候选人风险。
- 风险可以先定义为 offer 接受风险、稳定性风险或岗位适配风险。
- 第一版使用合成数据训练模型，不宣称真实业务准确率。

#### Report Agent

职责：

- 生成面向招聘官的评估报告。
- 报告包括候选人摘要、匹配点、风险点、建议面试问题、是否建议进入下一轮。

#### Human Review Node

职责：

- 在最终报告生成后暂停流程。
- 等待人工选择：通过、拒绝、要求重写、补充信息。
- 记录人工反馈。

#### Memory Node

职责：

- 保存人工反馈和招聘偏好。
- 让后续 Orchestrator 或 Report Agent 读取历史偏好。
- 第一版可用本地 Markdown 或 JSON 文件，后续再迁移到数据库。

## 6. WorkflowState 初步设计

建议在 `core/state.py` 中定义统一状态。

```python
class WorkflowState(TypedDict):
    request_id: str
    resume_file_path: str | None
    resume_text: str
    jd_text: str
    document_meta: dict | None

    candidate_profile: dict | None
    job_profile: dict | None
    scoring_rubric: dict | None

    validation_errors: list[str]
    retry_count: int
    max_retries: int

    match_score: float | None
    match_breakdown: dict | None

    risk_score: float | None
    risk_factors: list[str]

    report: str | None
    human_decision: str | None
    human_feedback: str | None

    current_step: str
    errors: list[str]
```

后续可以根据 Pydantic Schema 进一步拆分为更强类型的数据结构。

## 7. 分阶段开发路线

### 阶段一：Walking Skeleton

目标：不接入真实 LLM，不接入真实数据库，先跑通 LangGraph 状态流转。

任务：

- 初始化 Python 项目结构。
- 安装 `langgraph`、`langchain-core`、`pydantic`、`python-dotenv` 等基础依赖。
- 定义 `WorkflowState`。
- 编写 Mock 节点：
  - Orchestrator
  - Document Parser
  - Resume Extractor
  - JD Extractor
  - Validator
  - Matcher
  - Risk Evaluator
  - Report Writer
- 编译 LangGraph。
- 编写最小 Harness：
  - 统一运行入口 `harness/runner.py`
  - 内置样本 `harness/test_cases.py`
  - 节点执行日志 `harness/trace.py`
- 跑通完整流程：

```text
Start -> Orchestrator -> Document Parser -> Resume Extractor -> JD Extractor -> Validator -> Matcher -> Risk Evaluator -> Report Writer -> End
```

验收标准：

- 命令行运行一次完整流程。
- 每个节点能打印输入、输出和当前状态。
- 最终生成一份 Mock 招聘评估报告。
- Document Parser 能接收一个示例 PDF 或 Mock PDF 输入，并输出 `resume_text`。
- Harness 能使用固定样本一键运行完整工作流。
- Harness 能记录每个节点的执行顺序、输入摘要、输出摘要和错误信息。

### 阶段二：PDF 解析、LLM 抽取与自愈循环

目标：接入真实 PDF 解析能力，将简历和 JD 抽取节点替换为真实 LLM 调用，并加入强校验与 retry。

任务：

- 使用 PyMuPDF 或 pdfplumber 实现文本型 PDF 解析。
- 对解析结果进行清洗和分段。
- 如果解析文本过短，标记为 `needs_ocr = True`。
- 接入 LLM API。
- 编写候选人信息 Schema。
- 编写岗位信息 Schema。
- 用 Pydantic 校验 LLM 输出。
- 如果校验失败，将错误信息反馈给 LLM，要求其重写 JSON。
- 使用 conditional edge 实现最多 3 次重试。
- 在 Harness 中统计校验失败率、自动修复成功率和最终失败样本。

验收标准：

- 输入一段自然语言简历，能抽取结构化候选人信息。
- 输入一个文本型 PDF 简历，能解析出可用于抽取的 `resume_text`。
- 输入一段岗位 JD，能抽取结构化岗位要求。
- LLM 输出格式错误时，系统能自动修复或优雅失败。
- 能用多组测试样本批量验证抽取稳定性。

### 阶段三：匹配评分与规则解释

目标：先用规则实现可解释匹配评分，并引入校招/社招分轨评分思路。

任务：

- 判断候选人轨道：校招、社招、实习或 unknown。
- 根据轨道选择不同 scoring rubric。
- 计算技能匹配度。
- 计算工作年限匹配度。
- 计算学历匹配度。
- 计算薪资匹配度。
- 记录技能证据强度，避免单纯关键词堆砌。
- 生成 `match_breakdown`，说明每项分数来源。
- 在 Harness 中加入报告质量检查，确认报告引用了匹配依据。

验收标准：

- 输出总匹配分。
- 输出分项解释。
- 输出当前使用的 scoring rubric。
- 校招候选人不会因为没有正式工作年限被直接扣低分。
- 社招候选人的经验与项目证据权重大于学历。
- 报告能引用至少一条技能或项目证据。
- Report Agent 能引用匹配结果生成报告。
- Harness 能检查每份报告是否包含匹配点、风险点和建议面试问题。

### 阶段四：合成数据与传统 ML 风险模型

目标：训练一个可挂载到 LangGraph 节点中的 ML 模型。

任务：

- 编写 `scripts/data_generator.py`。
- 使用 Faker 和 numpy 生成候选人样本。
- 特征包括：
  - 学历权重
  - 技能匹配度
  - 跳槽频率
  - 期望薪资涨幅
  - 工作年限
  - 行业匹配度
- 生成合成标签，例如 `offer_acceptance_risk` 或 `stability_risk`。
- 编写 `scripts/train_model.py`。
- 使用 LightGBM 或 XGBoost 训练模型。
- 保存模型到 `models/risk_model.pkl`。
- 在 Risk Node 中加载模型并预测风险。

注意：

- 合成数据只用于项目演示和系统验证。
- 不宣称模型具备真实招聘预测能力。

验收标准：

- 能生成训练数据。
- 能训练并保存模型。
- LangGraph 工作流能调用模型输出风险分数。
- 报告中能解释主要风险因素。

### 阶段五：Human-in-the-Loop 与记忆机制

目标：让系统在关键决策前暂停，并沉淀人工反馈。

任务：

- 使用 LangGraph interrupt 机制或自定义审批节点。
- 在最终报告生成后等待人工审批。
- 支持操作：
  - approve
  - reject
  - revise
  - need_more_info
- 将人工反馈保存到 `MEMORY.md` 或 `memory/rules.json`。
- Orchestrator 启动时读取历史规则。
- Harness 支持 replay 人工拒绝案例，验证记忆规则是否影响后续报告。

验收标准：

- 系统能在报告生成后暂停。
- 人工输入决定后续流程。
- 反馈能被保存，并在下一次运行中被读取。
- 被拒绝案例可以被重放，并能看到系统如何调整后续建议。

### 阶段六：最小控制舱

目标：提供一个可演示的简单界面。

建议优先选择 Streamlit，而不是一开始就做复杂前后端分离。

原因：

- 开发成本低。
- 适合展示 AI 工作流。
- 适合面试演示。
- 可以快速做出输入区、流程状态、报告区、审批按钮。

任务：

- 简历输入框。
- JD 输入框。
- 运行按钮。
- 节点执行状态展示。
- 匹配分与风险分展示。
- 最终报告展示。
- 人工审批按钮。

验收标准：

- 可以通过网页完成一次候选人评估。
- 可以看到主要节点状态。
- 可以完成审批操作。

### 阶段七：工程化增强

目标：在核心闭环稳定后，再补充真实项目常见工程能力。

这一阶段不是 MVP 必需项，但适合让项目更像真实生产系统。

可选能力：

- FastAPI 后端
- React / Vue 前端
- PostgreSQL 数据库
- Redis 缓存
- Docker 容器化
- Celery / RQ 异步任务队列
- API 鉴权
- 日志与 tracing
- 单元测试和集成测试
- Harness 回归测试
- GitHub Actions CI

建议优先级：

1. Docker：方便面试官或自己复现项目。
2. 数据库：保存候选人、岗位、报告、审批记录。
3. FastAPI：把 LangGraph 工作流包装成服务。
4. Redis：在有异步任务、缓存或会话状态需求后再引入。
5. 前后端分离：如果时间充足再做，不建议第一版就上。
6. 并发：先设计为单用户演示，后续再支持多请求并发。
7. CI 回归：用 Harness 样本做基础自动化检查，防止改动破坏主流程。

## 8. 关于真实落地问题的取舍

### 并发

第一版不需要复杂并发。

原因：

- 项目主要用于简历和面试展示。
- LangGraph 工作流本身先跑通更重要。
- LLM 调用和人工审批天然是慢流程。

后续如果要支持多用户，可以引入：

- request_id
- thread_id
- LangGraph checkpoint
- 后端任务队列
- 数据库状态表

### Redis

第一版不必使用 Redis。

适合引入 Redis 的场景：

- 缓存 LLM 抽取结果。
- 存储短期会话状态。
- 配合 Celery/RQ 做异步任务队列。
- 防止重复提交。

如果只是本地演示，Redis 会增加复杂度。

### Docker

建议后期加入 Docker。

Docker 的价值：

- 简历项目更完整。
- 方便部署和演示。
- 避免环境依赖混乱。

但不建议阶段一就做 Docker，先让项目本身跑通。

### 前后端分离

第一版不建议前后端分离。

建议路线：

1. CLI 跑通核心流程。
2. Streamlit 做最小控制舱。
3. FastAPI 暴露工作流接口。
4. React/Vue 做正式前端。

这样学习曲线更平滑，也更容易阶段性交付。

### 数据库

第一版可以不用数据库，先用 JSON / Markdown / SQLite。

推荐演进：

```text
本地 JSON / Markdown
    ↓
SQLite
    ↓
PostgreSQL
```

适合入库的数据：

- 候选人结构化信息
- 岗位信息
- 每次评估任务
- 节点运行日志
- 报告
- 人工审批记录
- 记忆规则

### 后端服务

第一版不必做后端服务。

当 Streamlit 演示稳定后，再引入 FastAPI：

- `POST /evaluations`
- `GET /evaluations/{id}`
- `POST /evaluations/{id}/approve`
- `POST /evaluations/{id}/revise`

### MCP

MCP 可以作为后续增强能力，但不建议放入 MVP。

MCP 的价值是把外部系统能力以标准化方式暴露给 Agent，例如文件系统、数据库、内部 HR 系统、邮件、日历或知识库。

适合引入 MCP 的场景：

- Agent 需要读取候选人附件、历史评估记录或岗位库。
- Agent 需要查询数据库、文件系统或知识库。
- Agent 需要和外部 HR 工具集成，例如 ATS、日历、邮件系统。
- 希望将工具调用能力从业务代码中解耦，形成更标准的 Tool 接入层。

不建议 MVP 阶段引入 MCP 的原因：

- 当前第一目标是跑通招聘评估工作流。
- 早期外部工具较少，直接用 Python 函数或内部 Tool 封装即可。
- MCP 会增加协议、服务启动、权限和调试复杂度。

推荐路线：

```text
MVP：Python 函数 / 内部 Tool
    ↓
工程化增强：FastAPI + 数据库
    ↓
高级集成：MCP Server 暴露文件、数据库、岗位库、候选人库等工具
```

可选 MCP 设计：

```text
mcp_server/
├── server.py
├── tools/
│   ├── candidate_store.py
│   ├── job_store.py
│   ├── resume_files.py
│   └── approval_records.py
└── README.md
```

在本项目中的合理定位：

> MCP 不是核心工作流框架，而是外部工具和企业系统的标准化接入层。LangGraph 负责编排，Harness 负责测试与观测，MCP 负责工具能力暴露。

## 9. 推荐最终技术路线

MVP 技术栈：

- Python
- LangGraph
- LangChain Core
- Pydantic
- python-dotenv
- PyMuPDF 或 pdfplumber
- LightGBM 或 XGBoost
- scikit-learn
- pandas
- numpy
- Streamlit

工程化增强技术栈：

- FastAPI
- SQLite / PostgreSQL
- Redis
- Docker
- MCP
- pytest
- GitHub Actions

## 10. 项目目录建议

```text
agentic-hr/
├── app/
│   └── streamlit_app.py
├── core/
│   ├── state.py
│   ├── schemas.py
│   └── config.py
├── graph/
│   ├── workflow.py
│   └── routing.py
├── harness/
│   ├── runner.py
│   ├── test_cases.py
│   ├── trace.py
│   ├── evaluator.py
│   ├── replay.py
│   └── metrics.py
├── nodes/
│   ├── orchestrator.py
│   ├── document_parser.py
│   ├── resume_extractor.py
│   ├── jd_extractor.py
│   ├── validator.py
│   ├── matcher.py
│   ├── risk_evaluator.py
│   ├── report_writer.py
│   └── human_review.py
├── memory/
│   ├── MEMORY.md
│   └── rules.json
├── mcp_server/
│   ├── server.py
│   └── tools/
│       ├── candidate_store.py
│       ├── job_store.py
│       ├── resume_files.py
│       └── approval_records.py
├── models/
│   └── risk_model.pkl
├── scripts/
│   ├── data_generator.py
│   └── train_model.py
├── data/
│   ├── synthetic_candidates.csv
│   └── examples/
├── tests/
│   ├── test_schemas.py
│   ├── test_matcher.py
│   └── test_workflow.py
├── main.py
├── requirements.txt
├── .env.example
└── README.md
```

## 11. 简历亮点设计

后续 README 和简历中可以突出：

- 使用 LangGraph 实现多智能体状态机编排，支持条件路由、失败重试和人工中断。
- 在 LangGraph 之上设计 Agent Harness 层，支持批量样本运行、节点级 tracing、失败 replay 和回归评估。
- 设计 PDF 文档摄取层，将候选人简历解析、文本清洗、解析质量检测与 LLM 结构化抽取解耦。
- 使用 Pydantic 对 LLM 结构化输出进行强校验，构建自动修复循环。
- 区分 Agent、Skill、Tool 和普通 Node，将开放式推理、确定性校验、外部动作和流程节点解耦。
- 设计校招/社招分轨评分机制，避免用单一权重评价不同类型候选人。
- 引入证据溯源与反关键词堆砌机制，使匹配分数基于项目和经历证据，而不是简单关键词命中。
- 将 LLM 与 LightGBM/XGBoost 结合，实现语义抽取 + 传统 ML 风险评分的混合评估架构。
- 设计 Human-in-the-Loop 审批流程，避免 AI 直接参与高风险 HR 决策。
- 构建可解释招聘评估报告，展示匹配依据、风险因素和建议面试问题。
- 使用 Streamlit/FastAPI/Docker 完成可演示、可部署的 AI 应用闭环。
- 将 MCP 作为可选工具接入层，预留与文件系统、数据库、岗位库和候选人库的标准化集成能力。

## 12. 当前最重要的下一步

先不要急着做 Redis、Docker、前后端分离。

当前 MVP 闭环已经基本完成：

```text
CLI 可运行 LangGraph 工作流
    ↓
PDF 简历能解析为干净文本，图片型 PDF 可走 OCR fallback
    ↓
规则/工具层能结构化抽取简历和 JD
    ↓
Pydantic 能校验并触发 retry
    ↓
规则匹配能输出解释性分数
    ↓
报告 Agent 能生成招聘评估报告
    ↓
人工审批能暂停和记录反馈
    ↓
Streamlit 控制舱能演示完整流程
    ↓
Tools 层封装 PDF 解析、结构化抽取、批量评估、报告保存和邮件发送
    ↓
可选 LLM 报告增强层生成辅助摘要和面试追问
    ↓
图片型 PDF 支持 OCR 超时、解析质量评分、Vision LLM 辅助解析和控制舱进度条
```

LLM 接入原则：不要一上来让 LLM 直接决定最终分数。更稳妥的顺序是：

1. 已将 LLM 接到报告增强/面试问题生成节点，默认关闭，失败不影响确定性报告。
2. 已将 Vision LLM 作为图片型 PDF 解析的可选 fallback，OCR 低质量或超时时仍保留人工复核标记。
3. 下一步再将 LLM 接到简历和 JD 结构化抽取节点，并继续保留 Pydantic 校验与 retry。
4. 最后再考虑数据库、Docker、FastAPI、Redis 和并发能力。
