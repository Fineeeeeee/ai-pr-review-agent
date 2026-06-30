# 评测和反馈闭环

## 白话模型

这个项目的评测主要评“规则有没有扫准”，不是评 LLM 文案质量。评测集由一批模拟 PR diff 组成，每个样本在 `manifest.json` 里标注应该命中的规则。跑评测时，工具把实际命中的规则和预期规则对比，算出召回率、精确率、漏检数、误报数和平均耗时。

Review Memory 是另一条闭环。它把每次审查发现存成 JSONL 事件，后续可以人工标注 `accepted`、`false_positive`、`false_negative` 等状态，再按规则统计哪些规则可靠、哪些规则容易误报。

现在摘要里还会输出 `rule_health`。它按规则统计已复核数量、误报率、漏报数量和建议动作，用来辅助团队调优规则。它只给提示，不自动关闭或降权规则，避免少量反馈把 CI 门禁带偏。

## 代码模型

评测逻辑在[评测入口](../../src/ai_pr_review_agent/evaluation.py)。它读取 `examples/evaluation-set/manifest.json`，逐个 diff 调用 `review_diff(...)`，再比较 `expected_rules` 和实际 `finding.rule_id`。当前评测报告在[评测报告](../../docs/evaluation-report.md)，覆盖 25 个样本，包含 Python、JavaScript、TypeScript 的密钥、SQL、动态执行、Shell 执行、测试缺口和低风险变更。

Review Memory 的写入在[记忆模块](../../src/ai_pr_review_agent/review_memory.py)。`append_review_events(...)` 会把每条 finding 写成 JSONL；`summarize_review_events(...)` 会按状态和规则聚合。命令行标注和汇总在[记忆 CLI](../../src/ai_pr_review_agent/memory_cli.py)。

本地评估命令：

```powershell
$env:PYTHONPATH='src'
python -m ai_pr_review_agent.evaluation --dataset examples/evaluation-set --format json
```

## 接下去阅读

先看[一次真实审查怎么跑完](../walkthroughs/one-real-run.md#step-2-规则引擎只扫新增行)理解 finding 从哪里来；再看[命令和产物速查](../references/commands-and-artifacts.md#评测和记忆命令)复现评测和记忆统计。

证据状态：除特别标注外，本页基于当前源码、配置、测试和评测产物确认。
