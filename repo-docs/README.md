# AI PR Review Agent 项目理解文档

这个仓库做的是一个本地优先的 PR 风险审查工具。它接收 `git diff`，只看本次变更里的新增代码，找出硬编码密钥、SQL 拼接、动态执行、Shell 执行、缺少测试等风险，再把结果变成给人看的 Markdown、给 CI 用的 JSON、给 GitHub Code Scanning 用的 SARIF。

读这个项目时，先不要从文件树开始。更容易理解的入口是：一段有风险的 diff 进来，工具怎样一步步把它变成审查报告、PR 评论和风险门禁结果。这个完整路径在[一次真实审查怎么跑完](walkthroughs/one-real-run.md)里。

如果你已经知道代码审查工具的大概形态，可以直接看这些页面：

| 你想知道什么 | 从哪里开始 |
| --- | --- |
| 这个工具真实跑起来做了什么 | [一次真实审查怎么跑完](walkthroughs/one-real-run.md) |
| 为什么规则先于 LLM | [规则引擎和轻量数据流](modules/rule-engine.md) |
| `.ai-pr-review.yml`、PR 评论、风险门禁怎么连起来 | [策略门禁和 CI 集成](modules/policy-ci.md) |
| 25 个样本评测和 Review Memory 各自评什么 | [评测和反馈闭环](modules/evaluation-memory.md) |
| 常用命令、产物、配置字段 | [命令和产物速查](references/commands-and-artifacts.md) |
| 规则 ID、严重级别、配置键 | [规则与配置速查](references/rules-and-config.md) |
| 名词看不懂 | [术语表](glossary.md) |

当前 guide 覆盖本仓库的本地 CLI、规则检测、策略门禁、GitHub Actions、评测集和 Review Memory。DeepSeek 在这里作为可选增强层出现，但默认路径不依赖 API Key，也不需要外部模型才能跑通。

证据状态：除特别标注外，本页基于当前源码、配置、测试和评测产物确认。

