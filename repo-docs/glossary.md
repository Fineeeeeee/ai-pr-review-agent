# 术语表

| 术语 | 项目里的意思 | 延伸阅读 |
| --- | --- | --- |
| PR 风险审查 | 只看本次 diff 的新增代码，找出可能阻断合并的风险 | [一次真实审查怎么跑完](walkthroughs/one-real-run.md) |
| 规则引擎 | 不依赖 LLM 的本地判断逻辑，用来识别确定性风险 | [规则引擎和轻量数据流](modules/rule-engine.md) |
| 轻量数据流 | 在同一个文件的新增行里记住可疑变量，再在后续调用里识别它 | [规则引擎和轻量数据流](modules/rule-engine.md) |
| 策略门禁 | 按 `.ai-pr-review.yml` 的阈值决定 CI 是否失败 | [策略门禁和 CI 集成](modules/policy-ci.md) |
| SARIF | GitHub Code Scanning 能读取的结构化扫描结果格式 | [命令和产物速查](references/commands-and-artifacts.md) |
| Review Memory | 把发现项保存为 JSONL，并允许后续标注误报、漏报、采纳状态 | [评测和反馈闭环](modules/evaluation-memory.md) |
| 评测集 | 一组带预期规则标签的模拟 diff，用来检查规则有没有漏报或误报 | [评测和反馈闭环](modules/evaluation-memory.md) |
| `eval(...)` | 动态执行字符串或输入内容的调用，本项目把它视为最高风险之一 | [规则与配置速查](references/rules-and-config.md) |
| `shell=True` | Python subprocess 的 Shell 执行开关，本项目把它归为 Shell 执行风险 | [规则与配置速查](references/rules-and-config.md) |
| `.format()` | Python 字符串格式化方法；当它参与 SQL 拼接时会触发 SQL 风险 | [规则引擎和轻量数据流](modules/rule-engine.md) |
| `check_line(...)` | 规则引擎中处理单条新增行的函数 | [规则引擎和轻量数据流](modules/rule-engine.md) |
| `--enforce-policy` | CLI 参数；显式启用 `.ai-pr-review.yml` 里的 `fail_on` 风险门禁 | [策略门禁和 CI 集成](modules/policy-ci.md) |
