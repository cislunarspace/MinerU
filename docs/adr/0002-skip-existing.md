# Skip Existing: 重试时复用已有解析产物

GUI 重试文件夹处理时不应重新跑已经成功的文件。决定给 CLI 新增 `--skip-existing`：当对应 `<stem>.md` 解析产物已经存在于输出目录时，把该文档视为完成并跳过；GUI 工作流 1/3 默认传此参数。

## Status

Accepted.

## Considered Options

- **GUI 在调用前自己判输出文件、过滤出未完成子集传给 CLI**：CLI `-p` 当前只接单路径或单文件夹，要支持多文件得改 CLI 接口；扩展面比新增一个参数大。
- **CLI 默认开启跳过**：首次运行也会跳过，但用户首次本来就没有产物可跳，开启反而让人困惑为什么没跑。
- **`--resume` 断点续传**：暗示中断恢复，比我们要的“重试跳过”更重；本仓库没有持久化任务状态，不该假装有这个能力。

## Consequences

- CLI 多一个公开参数 `mineru --skip-existing`，外部脚本可独立启用。
- 跳过行为以 `<stem>.md` 解析产物存在为准；中间产物（`*_middle.json` 等）不参与判定。
- 跳过走 stderr 日志一行 `<stem>：输出已存在`；不进 Failure Report，状态走成功。
- GUI 工作流 1/3 在调用 MinerU 时始终传 `--skip-existing`；工作流 2 不调 MinerU，不变。
