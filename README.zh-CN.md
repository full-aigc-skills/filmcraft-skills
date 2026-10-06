# FilmCraft 独立技能

当前正在实现，尚未完成插件发布验收。

`filmcraft-use` 自带 Python 3.11+ 安装器，固定官方 macOS arm64 CLI 制品，校验压缩包和二进制，保留许可证，原子安装新版本，复用完整的已有版本。技能目录可独立复制，不依赖兄弟技能或插件私有路径。

运行测试：`python3 -m unittest discover -s tests -v`。完整创作流程和宿主验收仍待完成。

规范和任务：[FilmCraft 插件 OpenSpec](https://github.com/full-aigc-plugins/filmcraft-plugin/tree/main/openspec/changes/establish-v1-plugin)。

[English](README.md)

原生剪辑入口支持素材导入与收集、整数 ticks 编排、独立音频、字幕样式、工程重开、H.264 导出，以及移动交付包后的摘要核对和局部修订。参见[工作流说明](skills/filmcraft-use/references/workflow.md)。入口只依赖 Python 标准库与自动安装的 CLI；真实验收测试额外需要 ffmpeg、ffprobe 和 Pillow。

开发版本 `0.1.0-dev.1` 修复并行首次安装/复用时的安装锁竞争：等待最多 120 秒，再核验复用；超时不覆盖安装或重放编辑任务。

开发版本 dev.2 的原生交付包含摘要绑定的 exchange-loss.json，区分格式损失、结构观察与未验证字体/效果保真；导出派生物不替代原生工程。

## CLI 与场景技能体系

[FilmCraft Skill Suite Architecture](docs/FilmCraft-Skill-Suite-Architecture.zh_CN.md)

| 技能 | 用途 |
| :--- | :--- |
| `filmcraft-use` | 组合多个本工具能力并保留可编辑原生交付 |
| `filmcraft-cli` | 查询实际命令参数和能力，调用公开 CLI、MCP 与诊断 |
| `filmcraft-cli-setup` | 首次安装、摘要校验、版本检查与缺失运行时排障 |
| `filmcraft-cli-project` | 创建、打开、保存 fcproj 和组织序列、素材箱 |
| `filmcraft-cli-media` | 检查已有音视频、图片和素材引用，导入并收集或重关联素材 |
| `filmcraft-cli-timeline` | 排序、裁切、移动镜头，组织轨道与单镜头修改 |
| `filmcraft-cli-audio` | 组织已有配音和音乐、增益、混音与音画同步 |
| `filmcraft-cli-subtitles` | 导入、创建、修改字幕文本、时间、样式并交付 SRT |
| `filmcraft-cli-color` | 调整镜头色彩、使用许可明确的 LUT 与颜色预设 |
| `filmcraft-cli-motion` | 创建文字图形、效果参数与镜头关键帧 |
| `filmcraft-cli-export` | 导出预览帧、成片、交换文件与输出验证 |

`npx skills add full-aigc-skills/filmcraft-skills --skill <skill-name>`

## 场景技能的干净首次使用

八项 FilmCraft 场景技能均在 macOS arm64 通过独立首次安装与真实操作：只复制当前技能，从锁定公开地址安装到新运行时目录，核对原生修改、实际音频采样和渲染像素、原工程保留与未知命令拒绝。完整回归 31 项通过、零跳过。[证据](docs/evidence/task-skill-first-use.json)。该结果只覆盖列出的操作，全部命令、GUI 和创作最终验收仍未完成。

```bash
CRAFT_TASK_FIRST_USE=1 CRAFT_LIVE_TEST=1 CRAFT_LIVE_SUITE=1 python3 -B -m unittest discover -s tests -v
```

在独立 `filmcraft-skills` 仓库执行；真实测试另需 ffmpeg、ffprobe 与 Pillow。

命令统一使用 `SKILL_DIR`，其值为宿主实际加载的 `SKILL.md` 所在绝对目录。支持用户级、项目级 `.agents/skills` 及插件内部或缓存目录；CLI 运行时另外安装到用户数据目录。每个技能单独复制到三种含空格的布局后，文档中的脚本入口均可运行 `--help`。[路径验证](docs/evidence/installed-skill-paths.json)。既有宿主缓存需更新后才会收到修正文档。

中文字幕验收发现官方 CLI 0.2.0 忽略字幕轨指定字体，实际输出相同缺字方框。`runtime/` 保存绑定上游提交的修复候选与回归测试；既有公开技能标签保持原样。原生/SRT Unicode 保存与音频相关性已通过，但中文视觉验收仍失败，须修复运行时公开发布后完成隔离安装和成片检查。

有可见字幕轨时，工作流现在显式开启原生 `burnCaptions`；设置 `export.burnCaptions=false` 可仅保留工程字幕和侧车字幕。该修复解决成片字幕遗漏；官方 0.2.0 中文字幕缺字仍是独立阻塞项。

开发版 dev.5 锁定维护版 `0.2.0-craft.1`，由固定上游提交与字幕字体补丁构建。仅复制字幕技能、通过本地固定摘要发布归档完成全新安装后，Unicode/SRT、工程重开、成片烧录抽帧、中文字形区分、配音相关性与文字修订测试通过。公开 URL 全新首次安装已于 2026-10-06 通过。runtime/ 保留官方 0.2.0 锁作来源记录；新旧运行时分目录保存。

维护运行时已公开发布，在线单字幕技能首次安装验收通过；当前源码完整回归 44 项全部通过，无跳过。[限定范围证据](docs/evidence/chinese-first-use.json)。该证据覆盖列出的原生首次使用操作，不代表 GUI、模型分发或五插件整体验收。

当前实际安装的插件 dev.6／技能 dev.5 使用维护版 CLI 0.2.0-craft.1，八类独立场景冷启动全部通过（43.688 秒）。已记录输入、输出、测试驱动和原生摘要，全部 58 个安装摘要不变；补齐旧 0.2.0 场景证据的版本缺口，发行版字节不变。[证据](docs/evidence/maintained-runtime-task-first-use.json)。

候选安装回执复用校验已实现并验证，固定插件发布与 ArtCraft 同步仍待完成。[架构与证据](docs/FilmCraft-Runtime-Receipt-Architecture.zh_CN.md)。

固定 FilmCraft 插件 dev.7／技能源 dev.6 已通过 Codex 0.153.4 实际安装与四项安装快照测试：公开地址冷安装、保存重开、回执异常拒绝／恢复，以及 11 个独立 CLI 入口。执行后全部 58 个安装摘要保持不变。[固定发布证据](docs/evidence/codex-filmcraft7-receipt-first-use-20261006.json)。ArtCraft dev.42 仍锁定技能源 dev.5，其更新待完成。

[时间变化素材的裁切与移动验收](docs/FilmCraft-Temporal-Timeline-Acceptance.zh_CN.md)：实际安装的独立时间线技能空运行时测试 1 项通过；保存重开及原生导出均核对源入点，保留其他镜头、音轨、字幕和原交付。完整时间线／创作验收仍开放。

已发布技能源 dev.7 补齐原生工作流 mixer.setStrip 静态音轨增益、有限数值校验和真实解码 -6 dB 验收。参见[架构与范围](docs/FilmCraft-Audio-Gain-Architecture.zh_CN.md)。固定插件安装后真实增益验收通过，全部 58 项摘要保留；[证据](docs/evidence/codex-filmcraft8-audio-gain-first-use-20261006.json)。

固定插件 dev.8 已验证已有配音、音乐、视频原音三个独立音轨、错开起点和仅音乐增益返工，使用实际解码频率幅度核验；全部 58 项安装摘要保持不变。[范围与证据](docs/FilmCraft-Multitrack-Audio-Architecture.zh_CN.md)。

已发布技能源 dev.8 修复必需源音轨缺失却因自动静音 AAC 误成功的问题，保留失败诊断，明确无声视频与有意静音 WAV 仍可交付。[架构与范围](docs/FilmCraft-Required-Audio-Architecture.zh_CN.md)。固定插件 dev.9 安装后 3 项真实验收通过，全部 58 项摘要保留。[证据](docs/evidence/codex-filmcraft9-required-audio-first-use-20261006.json)。

公开维护版 craft.2 支持显式帧率序列、全帧收集与移动工程重关联。源码独立技能冷安装及实际 Effect→Film 交接已通过，固定插件与 Art 验收仍待完成。[证据与架构](docs/FilmCraft-Public-Sequence-First-Use-Architecture.zh_CN.md)。

固定 Film 插件 dev.10 已通过 Codex 0.153.4 隔离安装后的序列首次使用验收。58 项技能发现且零加载错误，Film 执行后全部摘要保持不变。[有界证据](docs/evidence/codex-filmcraft10-sequence-first-use-20261006.json)；Effect／Art 动态发行联调仍待完成。

候选运动／LUT 工作流已通过公开运行时首次使用测试：明确关键帧、登记 LUT、原生重开及移动返工；当前不可变插件 dev.10 与 Art 联调尚未包含此映射。 See [architecture](docs/FilmCraft-Motion-LUT-Workflow-Architecture.md) and [evidence](docs/evidence/motion-lut-workflow-candidate-20261006.json).
