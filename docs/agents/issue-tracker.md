# Issue 追踪器：GitHub（fork）

本仓库的 Issue 和 PRD 以 GitHub issue 形式存放在 fork `cislunarspace/MinerU` 上。
所有操作均使用 `gh` CLI，**始终附加 `--repo cislunarspace/MinerU`**，因为本仓库有多个 remote（`origin` → 上游 `opendatalab/MinerU`，`myfork` → 你的 fork）。

## 常用操作

- **创建 issue**：`gh issue create --repo cislunarspace/MinerU --title "..." --body "..."`。多行内容用 heredoc。
- **查看 issue**：`gh issue view <number> --repo cislunarspace/MinerU --comments`，可用 `jq` 过滤评论并获取标签。
- **列出 issue**：`gh issue list --repo cislunarspace/MinerU --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'`，按需加 `--label` 和 `--state` 过滤。
- **评论**：`gh issue comment <number> --repo cislunarspace/MinerU --body "..."`
- **添加 / 移除标签**：`gh issue edit <number> --repo cislunarspace/MinerU --add-label "..."` / `--remove-label "..."`
- **关闭**：`gh issue close <number> --repo cislunarspace/MinerU --comment "..."`

## 技能中提到"发布到 issue 追踪器"时

在 `cislunarspace/MinerU` 上创建 GitHub issue。

## 技能中提到"获取相关工单"时

执行 `gh issue view <number> --repo cislunarspace/MinerU --comments`。
