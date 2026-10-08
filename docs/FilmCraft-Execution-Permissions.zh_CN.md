# Execution permissions / 执行权限

公开工作流、完整命令执行和所属桌面执行要求独立提供真实读写根；原生子进程使用macOS系统沙箱，保护输入、技能代码与运行时缓存，所属桌面桥仅开放分配的本地端口。桌面与MCP共用授权临时目录以生成渲染帧。实际候选原生和签名桌面检查通过；完整FC-RL-002、固定宿主验收及八项V1任务仍开放。

The trusted maintenance installer remains outside the native sandbox and requires an explicit runtime-home write grant. Unsupported systems refuse public execution; no sandbox bypass fallback is used. Low-level Python APIs are internal trusted interfaces. Native parameter registries, secret-reference contracts and maintenance separation still require full acceptance.

```mermaid
flowchart LR
  Host[Trusted host roots] --> Guard[Canonical path checks]
  Guard --> Sandbox[macOS system sandbox]
  Sandbox --> CLI[Native CLI]
  Sandbox --> Desktop[Owned signed desktop]
  Desktop <--> Bridge[Assigned loopback port]
  CLI --> Output[Authorized output and temporary files]
```
