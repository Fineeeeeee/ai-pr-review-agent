# 规则引擎和轻量数据流

这个项目先做规则检测，再考虑模型增强。原因很简单：很多 PR 风险不是开放式理解题，而是确定性模式题。危险函数、Shell 执行、硬编码密钥、SQL 字符串拼接这些风险，用规则更快、更稳定，也更容易在 CI 里复现。规则层的目标不是理解整个业务，而是先回答一个更小的问题：这次新增代码里有没有可以直接定位的风险。

## 白话模型

这个项目先做规则检测，再考虑 LLM 增强。原因很简单：很多 PR 风险不是开放式理解题，而是确定性模式题。动态执行、Shell 执行、硬编码密钥、SQL 字符串拼接这些风险，用规则更快、更稳定，也更容易在 CI 里复现。

规则引擎的输入不是完整仓库，而是 diff 解析器交出的新增行清单。这样它关注的是这次 PR 新增或修改的内容，而不是把旧代码全部重新审一遍。

## 代码模型

规则入口在[本地规则引擎](../../src/ai_pr_review_agent/checks.py)。`run_static_checks` 会逐个文件、逐条新增行调用 `check_line`。普通单行风险直接在 `check_line` 里判断；SQL 变量传播则多一步：先记住可疑 SQL 变量，再在后续执行调用里匹配这个变量。

一个典型例子是：

```python
query = f"select * from users where id = {user_id}"
cursor.execute(query)
```

第一行被识别成“拼出来的 SQL”，变量名 `query` 会暂存在当前文件的追踪表里。第二行看到 `execute(query)` 时，规则引擎就能在执行处报 `sql_interpolation`。Python 部分用 `ast.parse(...)` 辅助识别 f-string、`.format()` 和 `%` 格式化；JavaScript/TypeScript 部分用轻量规则识别模板字符串、字符串拼接、`eval(...)` 和 `child_process.exec(...)`。

当前规则 ID、严重级别和适用语言在[规则与配置速查](../references/rules-and-config.md#规则-id-和严重级别)里。

## 接下去阅读

回到[一次真实审查怎么跑完](../walkthroughs/one-real-run.md#step-2-规则引擎只扫新增行)看规则怎样进入报告；继续读[评测和反馈闭环](evaluation-memory.md)看这些规则怎样用标注 diff 样本做回归验证。

证据状态：除特别标注外，本页基于当前源码、配置、测试和评测产物确认。
