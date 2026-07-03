# 企业私有化部署说明

这个项目的私有化方向是“本地优先的 PR 风险门禁”，不是全量 SAST 平台。默认路径只依赖 Python 标准库，不需要外部 API，也不会把代码发送到第三方模型。

## 适合的部署形态

| 场景 | 推荐方式 |
| --- | --- |
| 开发者本地预检 | 直接运行 CLI |
| GitHub Enterprise / 私有仓库 PR 门禁 | 使用 GitHub Actions 或自托管 Runner |
| 内网环境离线审查 | 使用 Docker 镜像运行 CLI |
| 需要自然语言补充建议 | 在受控环境里配置 `DEEPSEEK_API_KEY`，默认不开启 |

## Docker 运行

镜像定位是“可复制的离线 CLI 审查环境”。它默认不启动常驻服务，不需要 API Key，也不会把代码发到外部模型。镜像内使用非 root 用户运行，构建上下文通过 `.dockerignore` 排除 `.env`、本地记忆数据、学习资料和生成产物。

构建镜像：

```powershell
docker build -t ai-pr-review-agent .
```

审查示例 diff：

```powershell
docker run --rm ai-pr-review-agent --diff-file examples/risky.diff --format json
```

审查挂载进来的私有 diff：

```powershell
docker run --rm -v ${PWD}:/workspace ai-pr-review-agent --diff-file /workspace/pr.diff --config /workspace/.ai-pr-review.yml --enforce-policy
```

在企业私有 Runner 中，可以把 PR diff 作为 artifact 或工作目录文件传入容器：

```powershell
docker run --rm `
  -v ${PWD}:/workspace `
  ai-pr-review-agent `
  --diff-file /workspace/pr.diff `
  --config /workspace/.ai-pr-review.yml `
  --format sarif `
  --enforce-policy
```

退出码约定：

| 退出码 | 含义 |
| --- | --- |
| `0` | 审查完成，未触发门禁 |
| `2` | 参数或配置错误 |
| `3` | 审查完成，但风险等级达到门禁阈值 |

## 团队规则库

团队规则写在 `.ai-pr-review.yml` 的 `custom_rules` 里。每条规则会按自己的 `type` 检查新增代码行，命中后进入普通 findings、风险评分、SARIF 和 PR 评论。

```yaml
custom_rules:
  - id: team_no_pickle_loads
    type: forbidden_call
    pattern: "pickle.loads"
    severity: high
    message: "Team policy forbids unsafe pickle deserialization in PR changes."
```

当前 `custom_rules` 适合放团队明确禁止的简单模式，例如危险反序列化、内部禁用 API、敏感 SDK 调用。规则类型包括：

| 类型 | 含义 |
| --- | --- |
| `literal` | 在新增行中做字面匹配，适合内部 SDK 名称、固定危险片段 |
| `forbidden_call` | 识别真实函数调用，适合禁用 API；Python 使用 AST，JS/TS 使用调用形态匹配 |

它不适合写复杂语义分析；复杂规则应该沉淀到内置规则引擎和评估集里。

## 反馈闭环

保存审查结果：

```powershell
python -m ai_pr_review_agent.cli --diff-file pr.diff --save-memory data/review-memory.jsonl
```

标注误报：

```powershell
python -m ai_pr_review_agent.memory_cli --memory-file data/review-memory.jsonl --file app.py --line 12 --status false_positive
```

查看规则健康度：

```powershell
python -m ai_pr_review_agent.memory_cli --memory-file data/review-memory.jsonl --summary --format json
```

`rule_health` 会给出每条规则的已复核数量、误报率、漏报数量和建议动作。当前版本只做提示，不自动关闭规则，避免因为少量反馈导致门禁策略漂移。

## 私有化边界

- 默认不需要密钥，不调用外部模型。
- DeepSeek 只在显式传入 `--deepseek` 且设置 `DEEPSEEK_API_KEY` 时启用。
- 规则配置、审查记忆和评估样本都可以保存在企业内网仓库。
- CI 门禁由 `--enforce-policy` 或 `--fail-on-risk` 显式开启。
- 本项目不内置数据库、后台管理系统或多租户权限模型。
