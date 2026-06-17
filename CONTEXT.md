# MinerU

本上下文说明 GUI 与 CLI 处理文档时使用的项目语言。它只记录领域词汇，不记录实现方案。

## Language

**Failure Report**:
A machine-readable summary of failed document processing tasks, including the affected document and the reason shown to the user. It is a user-facing failure summary, not a developer diagnostic dump.
_Avoid_: Error log, stderr output, exit code, traceback

**Task Failure**:
A failed unit of document processing within a batch run. It identifies the document or documents that failed and the failure reason.
_Avoid_: Crash, failed process
