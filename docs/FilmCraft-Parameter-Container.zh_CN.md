# FilmCraft 解析后参数对象校验

[English](FilmCraft-Parameter-Container.md)。对应插件 OpenSpec 的 FC-CM-001-RESOLVED-TICK 与任务 9.3；插件仓持有正式规格。

旧入口在结构预检时允许整体 `params` 使用 `$ref`，解析后却未复验对象类型。引用返回字符串可能绕过 tick 字段检查，返回布尔、数字或数组可能产生未捕获的 TypeError。新增共享参数检查要求解析后仍为 JSON 对象，在依赖原生请求前返回 `invalid_command_parameters`。已有字面参数、对象引用、精确整数及错误回执合同保持兼容；workflow-native 继续使用自身的 `invalid_native_operation` 结构错误。

8 项入口专项测试通过。新增用例遍历 7 种整体参数引用结果，修复前出现 2 个错误通过及 5 个未结构化异常；修复后均保存 FAIL 回执且只调用前置只读命令，依赖编辑未提交。资源同步器将同一实现同步至 13 个独立技能，不直接编辑插件内快照。

此文档记录源码行为；固定安装、真实原生引用、逐命令分维矩阵和完整 V1 按各自证据验收。证据见 [源码回归报告](evidence/filmcraft-params-container-source-20261008.json)。
