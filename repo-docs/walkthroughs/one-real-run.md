# 一次真实审查怎么跑完

这条路径跟随一个有风险的 PR 变更：新增代码里同时出现密钥、SQL 拼接、动态执行和 Shell 执行。读完这条路径，你应该能用很朴素的话讲清楚：代码变更先被拆成新增行，本地规则先把确定性风险抓出来，策略层再决定哪些发现计入报告，最后 CI 把报告、评论和门禁串起来。示例文件是 examples/risky.diff。

这条路径跟随 examples/risky.diff。它模拟一次 PR 里新增了四行风险代码：一个 demo API key、一条 f-string SQL、一次 `eval`，以及一次 `shell=True` 命令执行。读完这条路径，你应该能解释：为什么这个项目不是单纯调用大模型，而是先用本地规则把确定性风险抓出来。

## Step 1: diff 文本先变成“新增代码清单”

命令入口可以来自 `--diff-file`、`--diff-text` 或 `--repo`。CLI 会先用[输入读取逻辑](../references/commands-and-artifacts.md#cli-入口)拿到统一 diff 文本，然后交给解析器。解析器不理解业务，它只做一件事：按文件、行号、新增行整理 diff。

在源码里，[diff 解析器](../../src/ai_pr_review_agent/diff_parser.py)会读取新增文件标记得到文件名，读取 hunk header 得到新文件起始行号，然后只收集以 `+` 开头但不是文件头的新增行。删除行不会增加新文件行号，上下文行会增加行号。这保证后面的风险项能落到具体文件和行号。

## Step 2: 规则引擎只扫新增行

解析完成后，[审查编排器](../../src/ai_pr_review_agent/reviewer.py)调用本地规则引擎。规则引擎不把整仓库交给 LLM，而是对新增行做确定性检查：变量名像 `api_key` 且值像字符串，就标成 `secret_literal`；SQL 里出现 f-string、`.format()`、`%` 或 JS/TS 模板字符串，就标成 `sql_interpolation`；`eval`、`exec`、`shell=True`、`child_process.exec` 等会分别成为动态执行或 Shell 执行风险。

这里有一个小的变量追踪：如果代码先写 `query = f"select ..."`，下一行再 `cursor.execute(query)`，规则引擎会记住 `query` 是拼出来的 SQL，再在执行处报风险。这个机制在[规则引擎和轻量数据流](../modules/rule-engine.md)里展开。

## Step 3: 风险等级和测试建议被汇总成报告对象

规则结果回来后，[审查编排器](../../src/ai_pr_review_agent/reviewer.py)会计算风险等级。它用最高严重级别做最终等级：有 `critical` 就是 `critical`，否则看 `high`、`medium`、`low`。examples/risky.diff 同时命中密钥、SQL、动态执行、Shell 执行和缺少测试，所以最终是 `critical`。

同一个报告对象还会带上测试建议、中文测试建议、上下文压缩计划、影响分析和结构化输出。这个设计让 Markdown、JSON、SARIF、Harness Manifest 都从同一份 `ReviewReport` 渲染，避免每个出口自己拼一套结果。

## Step 4: 策略配置过滤结果，门禁只在显式开启时失败

如果存在项目策略配置或 CLI 传入 `--config`，策略层会先过滤报告。例如默认配置忽略文档路径，这些路径里的发现不会参与最终风险评分。策略层还支持 `fail_on: high`，但普通报告命令不会因为这个配置自动失败；只有传入 `--enforce-policy` 或 `--fail-on-risk` 时，CLI 才会用风险阈值返回非零退出码。

这个分离很重要：生成报告时应该尽量成功产出文件；真正阻断 PR 的动作放在 CI 的最后一步。具体配置和边界在[策略门禁和 CI 集成](../modules/policy-ci.md)里。

## Step 5: 同一份报告被渲染成不同出口

人读的是 Markdown，自动化系统读的是 JSON，GitHub Code Scanning 读的是 SARIF。渲染器分别在[Markdown/JSON 渲染器](../../src/ai_pr_review_agent/renderers.py)和[SARIF 渲染器](../../src/ai_pr_review_agent/sarif_renderer.py)里。SARIF 会把规则 ID、严重程度、文件和行号转成 Code Scanning 可识别的结构。

本地可以这样验证：

```powershell
$env:PYTHONPATH='src'
$env:PYTHONIOENCODING='utf-8'
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --format json
```

输出里应看到 `risk_level` 为 `critical`，`findings` 里包含 `secret_literal`、`sql_interpolation`、`unsafe_eval`、`shell_execution` 和 `missing_tests`。

## Step 6: GitHub Actions 把本地审查放进 PR

在 GitHub 上，工作流会先生成 PR diff，再分别输出 Markdown、JSON 和 SARIF 报告。随后它把 Markdown 写入 Step Summary，创建或更新一条固定 PR 评论，上传审查产物，上传 SARIF，最后执行风险门禁。

这个顺序让高风险 PR 即使最终被门禁失败，也能留下报告、SARIF 和评论，开发者知道为什么失败。工作流细节见[策略门禁和 CI 集成](../modules/policy-ci.md)，命令和产物见[命令和产物速查](../references/commands-and-artifacts.md)。

验证命令：

```powershell
$env:PYTHONPATH='src'
$env:PYTHONIOENCODING='utf-8'
python -m unittest discover -s tests
python -m ai_pr_review_agent.evaluation --dataset examples/evaluation-set --format json
```

证据状态：除特别标注外，本页基于当前源码、配置、测试和评测产物确认。
