# Issue tracker: GitHub (fork)

Issues and PRDs for this repo live as GitHub issues on the fork `cislunarspace/MinerU`.
Use the `gh` CLI for all operations, **always passing `--repo cislunarspace/MinerU`** because this repo has multiple remotes (`origin` → upstream `opendatalab/MinerU`, `myfork` → your fork).

## Conventions

- **Create an issue**: `gh issue create --repo cislunarspace/MinerU --title "..." --body "..."`. Use a heredoc for multi-line bodies.
- **Read an issue**: `gh issue view <number> --repo cislunarspace/MinerU --comments`, filtering comments by `jq` and also fetching labels.
- **List issues**: `gh issue list --repo cislunarspace/MinerU --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with appropriate `--label` and `--state` filters.
- **Comment on an issue**: `gh issue comment <number> --repo cislunarspace/MinerU --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --repo cislunarspace/MinerU --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --repo cislunarspace/MinerU --comment "..."`

## When a skill says "publish to the issue tracker"

Create a GitHub issue on `cislunarspace/MinerU`.

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number> --repo cislunarspace/MinerU --comments`.
