# AI PR Review Agent

一个本地优先的智能代码审查与 PR 风险分析工具。项目接收 `git diff` 或 patch 文件，自动解析变更文件、新增代码行和行号，识别常见安全风险与测试缺口，并输出 Markdown、JSON、SARIF 和 Agent Harness 等结构化结果。

项目默认路径仅依赖 Python 标准库，不需要 API Key 即可完成离线审查；如配置 `DEEPSEEK_API_KEY`，可选调用 DeepSeek 生成更自然的中英文补充审查意见。

## 项目特点

- 本地优先：默认不依赖外部模型或付费服务，适合离线演示和本地 CI。
- 风险检测：覆盖密钥泄露、SQL 字符串插值、动态代码执行、Shell 执行、宽泛异常捕获和缺少测试变更。
- AST 增强：对 SQL 插值场景加入 AST 辅助识别和轻量变量追踪，支持 `query = f"..."; cursor.execute(query)`、`.format()` 和 `%` 格式化等写法。
- 多语言检测：支持 Python、JavaScript、TypeScript 的增量风险扫描，覆盖 JS/TS 模板字符串 SQL、字符串拼接 SQL、`eval`、`child_process.exec` 和前端密钥硬编码等场景。
- 结构化输出：支持 Markdown、JSON、SARIF 和 Agent Harness Manifest。
- PR 自动化：内置 GitHub Actions 工作流，可在 Pull Request 中运行测试、生成审查报告、上传 SARIF、更新 PR 评论，并按风险阈值阻断高风险 PR。
- 策略配置：支持 `.ai-pr-review.yml`，可配置风险门禁阈值、忽略规则和忽略路径。
- 上下文压缩：根据风险信号将文件分为 `full`、`focused`、`summary`、`skip`，优先分析高风险文件。
- 影响分析：在提供仓库路径时，基于 Python AST 识别变更函数及其直接调用方。
- 评审记忆：支持将审查发现保存为 JSONL 事件，便于后续标注误报、漏报和采纳状态。
- 可选 LLM 增强：DeepSeek 作为增强层，基于本地规则结果生成补充审查建议。
- 可量化评测：内置 25 个模拟 PR diff 样本，用于统计召回率、精确率、误报数和分析耗时。

## 技术栈

- Python 3.10+
- Python Standard Library
- Git Diff Parser
- Static Rule Engine
- AST Impact Analysis
- JavaScript / TypeScript Rule Detection
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

使用策略配置：

```powershell
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --config .ai-pr-review.yml
```

启用风险门禁：

```powershell
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --config .ai-pr-review.yml --enforce-policy
```

也可以临时指定门禁阈值：

```powershell
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --fail-on-risk high
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

## 策略配置

默认配置文件：

```text
.ai-pr-review.yml
```

示例：

```yaml
fail_on: high

ignore_rules: []

ignore_paths:
  - "docs/**"
  - "*.md"
```

字段说明：

- `fail_on`：CI 风险门禁阈值，可选 `low`、`medium`、`high`、`critical`。
- `ignore_rules`：从最终报告和风险评分中忽略的规则 ID，例如 `missing_tests`。
- `ignore_paths`：从最终报告和风险评分中忽略的路径 glob，例如 `docs/**`。

普通报告命令会应用 `ignore_rules` 和 `ignore_paths`，但不会因为 `fail_on` 自动失败。只有显式传入 `--enforce-policy` 或 `--fail-on-risk` 时，CLI 才会返回非零退出码。

## GitHub Actions

项目内置工作流：

```text
.github/workflows/ai-pr-review.yml
```

Pull Request 触发后会执行：

1. 拉取完整 Git 历史。
2. 设置 Python 运行环境。
3. 运行单元测试。
4. 生成 PR diff。
5. 输出 Markdown、JSON 和 SARIF 审查结果。
6. 将 Markdown 写入 GitHub Step Summary。
7. 创建或更新 Pull Request 固定评论。
8. 上传审查产物。
9. 上传 SARIF 到 GitHub Code Scanning。
10. 根据 `.ai-pr-review.yml` 的 `fail_on` 阈值执行风险门禁。

工作流默认不调用 DeepSeek，也不需要任何 API Key。DeepSeek 增强审查建议保留在本地或受控 CI 环境中按需启用。

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

查看反馈统计：

```powershell
python -m ai_pr_review_agent.memory_cli --memory-file data/review-memory.jsonl --summary --format json
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
- AST 辅助 SQL 插值检测
- JavaScript / TypeScript 风险检测
- CLI 参数处理
- 策略配置和风险门禁
- Web API
- Markdown / JSON 渲染
- SARIF 输出
- Agent Harness 输出
- 上下文压缩
- AST 影响分析
- DeepSeek 请求构造
- 评审记忆读写
- 评审记忆反馈统计
- 评测集统计

## 评测结果

项目内置 25 个模拟 PR diff 样本，覆盖密钥泄露、SQL 插值、SQL 变量传播、JS/TS 模板字符串 SQL、JS/TS 字符串拼接 SQL、动态执行、Shell 执行、宽泛异常、测试缺口和低风险变更等场景。

当前可复现结果：

- 样本数：25
- 召回率：100.0%
- 精确率：100.0%
- 误报数：0
- 平均分析耗时：低于 1 ms
- 全量分析占比：75.0%
- 跳过低风险上下文占比：25.0%

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

- 增强 AST 和轻量数据流分析，减少正则规则的误报和漏报。
- 扩展 Java 等更多语言支持。
- 基于评审记忆中的反馈状态优化规则优先级。
- 支持更完整的多 Agent 审查流程编排。

## Repo docs

项目理解文档在 `repo-docs/`。新读者从 `repo-docs/README.md` 开始；后续回答架构、上手或“这个子系统怎么工作”问题前，应先检查相关 guide 页面和当前源码。代码、配置、测试或行为变化后，运行 Understanding Sync check，并把有意义的 guide 更新记录到 `repo-docs/change-log.md`。

## 企业团队 PR 风险门禁方向

当前项目更靠近“企业团队的本地优先 PR 风险门禁”，不是全能代码审查平台。核心路径是：团队把明确禁止的模式写进 `.ai-pr-review.yml`，PR 触发后工具只审查新增代码行，输出 Markdown、JSON、SARIF 和 PR 评论，并通过 `fail_on` 阈值阻断高风险变更。

团队规则示例：

```yaml
custom_rules:
  - id: team_no_pickle_loads
    type: forbidden_call
    pattern: "pickle.loads"
    severity: high
    message: "Team policy forbids unsafe pickle deserialization in PR changes."
```

`custom_rules` 会在内置规则之前检查新增行，适合承载团队禁用 API、危险 SDK 调用、内部安全约定等明确规则。当前支持 `literal` 和 `forbidden_call` 两类：前者做字面匹配，后者识别真实函数调用，避免字符串和注释误命中。复杂语义判断仍应进入内置规则和评估集，避免把配置文件变成不可维护的小型规则语言。

Review Memory 支持把审查发现保存成 JSONL，并标注 `accepted`、`false_positive`、`false_negative`。摘要输出里的 `rule_health` 会按规则给出已复核数量、误报率、漏报数量和建议动作，用来辅助团队调优规则；当前版本只提示，不自动关闭规则。

私有化部署说明见 [docs/private-deployment.md](docs/private-deployment.md)。项目提供 `Dockerfile`，默认离线运行，不需要 API Key；DeepSeek 只作为显式开启的增强层。
