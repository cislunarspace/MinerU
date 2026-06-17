# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those roles to the actual label strings used in this repo's issue tracker.

| Label in skills | Label in our tracker | Meaning                                  |
| --------------- | -------------------- | ---------------------------------------- |
| `needs-triage`  | `needs-triage`       | Maintainer needs to evaluate this issue  |
| `needs-info`    | `needs-info`         | Waiting on reporter for more information |
| `ready-for-agent` | `ready-for-agent`  | Fully specified, ready for an AFK agent  |
| `ready-for-human` | `ready-for-human`  | Requires human implementation            |
| `wontfix`       | `wontfix`            | Will not be actioned (already exists on fork) |

## Create missing labels

Run once to create the four labels that don't exist yet on `cislunarspace/MinerU`:

```bash
gh label create needs-triage   --repo cislunarspace/MinerU --description "Maintainer needs to evaluate"   --color "ededed"
gh label create needs-info     --repo cislunarspace/MinerU --description "Waiting on reporter for info"    --color "c5def5"
gh label create ready-for-agent --repo cislunarspace/MinerU --description "Fully specified, ready for agent" --color "0e8a16"
gh label create ready-for-human --repo cislunarspace/MinerU --description "Needs human implementation"    --color "fbca04"
```

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use the corresponding label string from the table above.
