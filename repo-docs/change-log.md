# repo-docs 变更记录

| Timestamp | Request | Actions | Verification | Result |
| --- | --- | --- | --- | --- |
| 2026-06-30 00:00 -04:00 | 项目向“企业团队本地 PR 风险门禁”方向收窄 | 增加 `custom_rules` 团队规则库说明、`rule_health` 反馈健康度说明、Docker 私有化运行命令；同步 README 和私有化部署文档 | `validate_repo_docs.py repo-docs --repo-root .`；`python -m unittest discover -s tests`；`python -m ai_pr_review_agent.evaluation --dataset examples/evaluation-set --format json` | guide 已同步新的团队规则和私有化方向。Synced through 58b9645f511393890f91e478d644ce42a3772dee |
| 2026-06-28 09:58 -04:00 | 使用 `repo-docs` 和 `repo-docs-zh` 为仓库创建中文 guide，并先运行 Understanding Sync check | 创建中文 `repo-docs/`，覆盖真实审查路径、规则引擎、策略门禁、评测/记忆闭环、命令和规则速查；更新本地 `AGENTS.md` 路由未来维护 | `validate_repo_docs.py repo-docs --repo-root .`；`python -m unittest discover -s tests`；`python -m ai_pr_review_agent.evaluation --dataset examples/evaluation-set --format json` | 初始构建。Synced through 58b9645f511393890f91e478d644ce42a3772dee |
| 2026-06-28 10:18 -04:00 | repo-docs 初始创建后的同步校验收尾 | 补齐中文 guide 的校验命令、术语表和同步锚点；降低开头代码名密度；在根 README 指向 `repo-docs/` | `validate_repo_docs.py repo-docs --repo-root .`；`python -m unittest discover -s tests`；`python -m ai_pr_review_agent.evaluation --dataset examples/evaluation-set --format json` | 初始 guide 可维护。Synced through 58b9645f511393890f91e478d644ce42a3772dee |
