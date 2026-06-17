# 分流标签

技能中提到的五个标准分流角色，对应本仓库 issue 追踪器中的实际标签。

| 技能中的角色 | 追踪器中的标签 | 含义 |
| ------------ | -------------- | ---- |
| `needs-triage` | `needs-triage` | 需要维护者评估此 issue |
| `needs-info` | `needs-info` | 等待提交者补充信息 |
| `ready-for-agent` | `ready-for-agent` | 已充分定义，可交由 agent 处理 |
| `ready-for-human` | `ready-for-human` | 需要人工实现 |
| `wontfix` | `wontfix` | 不予处理（已在 fork 上存在） |

## 创建缺失的标签

在 `cislunarspace/MinerU` 上执行一次，创建尚不存在的四个标签：

```bash
gh label create needs-triage   --repo cislunarspace/MinerU --description "需要维护者评估"   --color "ededed"
gh label create needs-info     --repo cislunarspace/MinerU --description "等待提交者补充信息" --color "c5def5"
gh label create ready-for-agent --repo cislunarspace/MinerU --description "已充分定义，可交由 agent 处理" --color "0e8a16"
gh label create ready-for-human --repo cislunarspace/MinerU --description "需要人工实现"    --color "fbca04"
```

当技能中提到某个角色（例如"应用 AFK-ready 分流标签"）时，使用上表中对应的标签字符串。
