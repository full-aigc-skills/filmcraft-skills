# FilmCraft 命令目录身份修复

[English](FilmCraft-Catalog-Identity.md)。对应插件 OpenSpec FC-RL-001-CURRENT-FACTS 与任务 9.4—9.6；正式行为仍由插件规范持有。

旧参考目录声明运行时 craft.4，却保留了较早二进制的摘要；原生快照与有效运行时锁已经指向实际 craft.4。不能直接修改摘要并把旧记录当作新采集。因此本次先从锁定 CLI 的实际空会话重新读取 command_list，再将版本、平台、二进制摘要、上游来源和原生参数绑定为同一来源。新旧 666 条命令行逐项比较一致；这仅证明目录，不证明每条命令执行成功。

生成器拒绝身份错配、重复/畸形命令行，以及同摘要下的参数或清单漂移。旧的 runtimePatchSourceCommit 未由当前锁证明，不继续继承。13 个独立技能按已有命令 ID 子集同步参数和元数据，不扩大或缩小已发布目录；没有跨技能运行依赖。资源同步之前执行只读目录一致性检查，不能把错误主目录传播为一致副本。

```bash
python3 -B scripts/build_command_coverage.py --capture-native
python3 -B scripts/sync_skill_suite.py
python3 -B scripts/build_command_coverage.py --check
python3 -B scripts/sync_skill_suite.py --check
python3 -B -m unittest discover -s tests -p test_catalog_identity.py -v
```

采集要求已授权且已安装的固定运行时，安装器继续核验其来源、回执和二进制。`--check` 不采集、不下载、不改文件。绑定证据见 [候选报告](evidence/filmcraft-catalog-identity-candidate-20261008.json)；源码回归与固定发行安装分别记录，旧发行保持原字节及原 MISMATCH 状态。
