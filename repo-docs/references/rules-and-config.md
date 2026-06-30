# 规则与配置速查

这是查表材料。如果你还不了解审查路径，先读[一次真实审查怎么跑完](../walkthroughs/one-real-run.md)。

## 规则 ID 和严重级别

| 规则 ID | 严重级别 | 主要覆盖 |
| --- | --- | --- |
| `secret_literal` | `high` | Python、JS、TS 中形似 `api_key`、`apiKey`、`token`、`authToken`、`password` 的硬编码字符串 |
| `sql_interpolation` | `high` | Python f-string、`.format()`、`%` SQL；JS/TS 模板字符串 SQL 和字符串拼接 SQL |
| `unsafe_eval` | `critical` | Python `eval` / `exec`；JS/TS `eval` |
| `shell_execution` | `high` | Python `shell=True`、`os.system`；JS/TS `child_process.exec` / `execSync` |
| `broad_exception` | `low` | Python `except Exception` / `except BaseException` |
| `missing_tests` | `medium` | 非文档/配置的应用代码变更没有测试文件变更 |

## 策略配置键

默认配置文件是 `.ai-pr-review.yml`。

| 键 | 含义 | 示例 |
| --- | --- | --- |
| `fail_on` | `--enforce-policy` 时触发非零退出码的最低风险等级 | `high` |
| `ignore_rules` | 从最终报告和风险评分里移除的规则 ID | `["missing_tests"]` |
| `ignore_paths` | 从最终报告和风险评分里移除的路径 glob | `["docs/**", "*.md"]` |
| `custom_rules` | 团队自定义规则列表，在内置规则之前按新增行做字面匹配 | `team_no_pickle_loads` |

## 团队规则库

`custom_rules` 是这个项目向企业团队规则库靠拢的最小接口。它适合放团队明确禁止的简单模式，例如危险反序列化、内部禁用 API、敏感 SDK 调用。

```yaml
custom_rules:
  - id: team_no_pickle_loads
    pattern: "pickle.loads"
    severity: high
    message: "Team policy forbids unsafe pickle deserialization in PR changes."
```

命中后会生成对应 `rule_id` 的 finding，参与风险评分、JSON、SARIF 和 PR 评论。当前版本按字面匹配，不做复杂规则语言；复杂语义规则应进入内置规则引擎和评估集。

## 风险等级顺序

| 等级 | 排序值 | 说明 |
| --- | --- | --- |
| `low` | 0 | 没有发现项，或只有低风险发现 |
| `medium` | 1 | 命中测试缺口等中风险 |
| `high` | 2 | 命中密钥、SQL、Shell 等高风险 |
| `critical` | 3 | 命中动态代码执行等最高风险 |

风险等级由[审查编排器](../../src/ai_pr_review_agent/reviewer.py)按最高严重级别计算。
