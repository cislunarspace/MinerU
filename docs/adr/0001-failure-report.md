# Failure Report: CLI 产出结构化失败报告，GUI 展示

GUI 与 MinerU CLI 之间出现失败信息缺口：CLI 内部已经有 `TaskFailure`，但只在 stderr 写一段人读文本，外部只拿到退出码。决定新增 `Failure Report`：由 CLI 在收到 `--failure-report-path` 时把任务级失败写成 JSON，GUI 读取后在状态栏/通知给短摘要、在日志区给完整列表。

## Status

Accepted.

## Considered Options

- **GUI 解析 stderr 文本**：短期最快，stderr 格式一改就坏，工作流 1/2/3 各自都得写解析。
- **只扩展任务运行时日志，状态栏继续只显示退出码**：保留现有行为，不解决"看不到哪个文件为什么失败"的问题。
- **Failure Report 写到用户输出目录**：污染输出目录，留下包含文件路径和错误细节的运行元数据。

## Consequences

- CLI 多一个公开参数 `mineru --failure-report-path <path>`，外部脚本可能开始依赖；后续改名要带 deprecation 过渡。
- `Failure Report` 只承载用户级失败摘要，不含 traceback、环境变量、token。开发诊断仍走日志。
- 只有任务级失败（`TaskFailure`）写入报告；启动失败、参数错误、API 不可用不写报告，保留现有错误消息。
- `WorkflowWorker` 不识别 `Failure Report`；报告读写放在 GUI 工作流层。
