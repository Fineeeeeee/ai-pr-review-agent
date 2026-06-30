# 策略门禁和 CI 集成

## 白话模型

策略层回答两个问题：哪些发现不应该计入本次报告，以及风险到什么程度要让 CI 失败。报告生成和门禁失败被故意分开：先尽量生成 Markdown、JSON、SARIF 和 PR 评论，再在最后一步决定是否阻断。

这样做的好处是，高风险 PR 不会只留下一个红叉。开发者仍然能在 PR 评论、Actions Summary、artifact 和 Code Scanning 里看到具体风险。

## 代码模型

策略配置默认读取 `.ai-pr-review.yml`。配置键包括 `fail_on`、`ignore_rules` 和 `ignore_paths`，解析和应用逻辑在[策略模块](../../src/ai_pr_review_agent/review_policy.py)。`apply_policy(...)` 会过滤掉被忽略的规则或路径，然后重新计算风险等级、测试计划、上下文压缩计划和结构化输出。

CLI 在[命令入口](../../src/ai_pr_review_agent/cli.py)里加载策略。普通报告命令会应用忽略规则和忽略路径，但不会因为 `fail_on` 自动失败；`--enforce-policy` 才会读取配置里的 `fail_on`，`--fail-on-risk high` 则是一次性覆盖门禁阈值。命中门禁时，CLI 返回 `3`。

GitHub Actions 工作流在[PR 审查工作流](../../.github/workflows/ai-pr-review.yml)里。它的顺序是：跑测试、生成 diff、生成三种报告、写 Step Summary、创建或更新 PR 评论、上传 artifact、上传 SARIF、执行风险门禁。PR 评论用 `<!-- ai-pr-review-agent -->` 作为 marker，所以后续运行会更新旧评论，不会刷屏。

本地可以用同一份配置复现门禁判断：

```powershell
$env:PYTHONPATH='src'
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --config .ai-pr-review.yml --enforce-policy
```

## 接下去阅读

配置字段见[规则与配置速查](../references/rules-and-config.md#策略配置键)。要复现 CI 的本地门禁，可看[命令和产物速查](../references/commands-and-artifacts.md#本地复现命令)。

证据状态：除特别标注外，本页基于当前源码、配置、测试和评测产物确认。
