# AI PR Review Agent

一个本地优先的智能代码审查与 PR 风险分析工具。项目接收 `git diff` 或 patch 文件，自动解析变更文件、新增代码行和行号，识别常见安全风险与测试缺口，并输出 Markdown、JSON、SARIF 和 Agent Harness 等结构化结果。

项目默认路径仅依赖 Python 标准库，不需要 API Key 即可完成离线审查；如配置 `DEEPSEEK_API_KEY`，可选调用 DeepSeek 生成更自然的中英文补充审查意见。

## 项目特点

- 本地优先：默认不依赖外部模型或付费服务，适合离线演示和本地 CI。
- 风险检测：覆盖密钥泄露、SQL 字符串插值、动态代码执行、Shell 执行、宽泛异常捕获和缺少测试变更。
- 结构化输出：支持 Markdown、JSON、SARIF 和 Agent Harness Manifest。
- 上下文压缩：根据风险信号将文件分为 `full`、`focused`、`summary`、`skip`，优先分析高风险文件。
- 影响分析：在提供仓库路径时，基于 Python AST 识别变更函数及其直接调用方。
- 评审记忆：支持将审查发现保存为 JSONL 事件，便于后续标注误报、漏报和采纳状态。
- 可选 LLM 增强：DeepSeek 作为增强层，基于本地规则结果生成补充审查建议。
- 可量化评测：内置 20 个模拟 PR diff 样本，用于统计召回率、精确率、误报数和分析耗时。

## 技术栈

- Python 3.10+
- Python Standard Library
- Git Diff Parser
- Static Rule Engine
- AST Impact Analysis
- JSON / SARIF / JSONL
- HTTP Server
- DeepSeek API
- unittest

## 快速开始

克隆项目后进入目录：

```powershell
cd ai-pr-review-agent
$env:PYTHONPATH='src'
$env:PYTHONIOENCODING='utf-8'
```

运行示例审查：

```powershell
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff
```

输出 JSON：

```powershell
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --format json
```

输出 SARIF：

```powershell
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --format sarif
```

输出 Agent Harness Manifest：

```powershell
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --format harness
```

审查当前仓库变更：

```powershell
python -m ai_pr_review_agent.cli --repo .
```

审查 staged 变更：

```powershell
python -m ai_pr_review_agent.cli --repo . --staged
```

## Web UI

启动本地 Web 服务：

```powershell
$env:PYTHONPATH='src'
python -m ai_pr_review_agent.server
```

浏览器打开：

```text
http://127.0.0.1:8765
```

Web UI 支持粘贴 diff、加载示例、查看风险等级、Markdown 报告和结构化 JSON。

## DeepSeek 增强审查

默认审查流程不需要 API Key。需要启用 DeepSeek 增强审查时，设置环境变量：

```powershell
$env:DEEPSEEK_API_KEY='your-api-key'
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --deepseek
```

也可以指定模型：

```powershell
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --deepseek --model deepseek-v4-pro
```

## 评审记忆

保存审查发现：

```powershell
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --save-memory data/review-memory.jsonl
```

标注审查事件：

```powershell
python -m ai_pr_review_agent.memory_cli --memory-file data/review-memory.jsonl --file app.py --line 4 --status false_positive
```

支持状态：

- `pending`
- `accepted`
- `false_positive`
- `false_negative`
- `ignored`

## 运行测试

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests
```

当前测试覆盖：

- Diff 解析
- 风险规则检测
- CLI 参数处理
- Web API
- Markdown / JSON 渲染
- SARIF 输出
- Agent Harness 输出
- 上下文压缩
- AST 影响分析
- DeepSeek 请求构造
- 评审记忆读写
- 评测集统计

## 评测结果

项目内置 20 个模拟 PR diff 样本，覆盖密钥泄露、SQL 插值、动态执行、Shell 执行、宽泛异常、测试缺口和低风险变更等场景。

当前可复现结果：

- 样本数：20
- 召回率：100.0%
- 精确率：100.0%
- 误报数：0
- 平均分析耗时：约 0.1 ms
- 全量分析占比：66.67%
- 跳过低风险上下文占比：33.33%

详细结果见 [docs/evaluation-report.md](docs/evaluation-report.md)。

## 系统架构

```text
git diff / diff file
        |
        v
diff_parser.py        -> 解析文件、行号和新增代码
        |
        v
checks.py             -> 本地规则引擎识别风险
        |
        v
reviewer.py           -> 汇总风险等级和测试建议
        |
        +--> context_compressor.py -> 上下文压缩策略
        +--> impact_analysis.py    -> 变更函数与直接调用方分析
        +--> structured_output.py  -> CI-ready JSON schema
        +--> review_memory.py      -> JSONL 反馈事件
        +--> agent_harness.py      -> Agent 工程画像
        |
        v
renderers.py          -> Markdown / JSON 输出
sarif_renderer.py     -> SARIF 输出
harness_renderer.py   -> Agent Harness Manifest
        |
        +--> cli.py
        +--> server.py
        +--> memory_cli.py
        +--> deepseek_client.py
```

## 目录结构

```text
ai-pr-review-agent/
  src/ai_pr_review_agent/
    cli.py
    server.py
    diff_parser.py
    checks.py
    reviewer.py
    context_compressor.py
    impact_analysis.py
    structured_output.py
    renderers.py
    sarif_renderer.py
    agent_harness.py
    harness_renderer.py
    review_memory.py
    memory_cli.py
    deepseek_client.py
    evaluation.py
    models.py
  tests/
  examples/
  docs/
  pyproject.toml
  README.md
```

## 适用场景

- 本地 PR 风险预审
- 代码审查辅助工具
- CI 中的增量代码风险检测
- 安全规则演示与扩展
- AI Agent 工程化实践

## 后续计划

- 接入 GitHub Actions，在 PR 中自动评论审查结果。
- 增强 AST 和轻量数据流分析，减少正则规则的误报和漏报。
- 扩展 JavaScript、TypeScript、Java 等语言支持。
- 基于评审记忆中的反馈状态优化规则优先级。
- 支持更完整的多 Agent 审查流程编排。
