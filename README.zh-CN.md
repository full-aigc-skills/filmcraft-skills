# FilmCraft 独立技能

dev.60 修复显式设置播放头后的工程保存重开误拒绝：只排除顶层selection与playhead临时状态，持久字段和嵌套字段继续严格比较。固定发布副本的原生交付另行验收。

dev.59 修复scopes.read在固定合同中声明的frame／seconds／timecode简写别名被共享参数守卫误拒绝的问题；其他命令及未知字段权限保持受限。目标红绿证据与不可变插件／原生验收分开记录。

dev.58 新增跨计划任务级实例复用：公开JSONL前台入口保持同一所属MCP和可选签名桌面，固定版本／授权／模型身份，失败或unknown后不重启、不重放，中断保留unknown逐计划回执。单次run兼容行为保留，固定发布安装验收单独记录。

dev.57使完整命令、领域native.command与旧exec共用固定原生顶层参数校验；未知字段在素材读取、安装和创建输出前以固定诊断拒绝，不回显字段和值。覆盖666份合同、别名、联合参数、匹配选项与整体结果引用，创作文本保留数据语义。241项源码、39项公开拒绝、39项原生根边界与十三候选真实业务通过；新固定安装及完整权限／全命令／宿主路由仍待验收。 [Evidence](docs/evidence/filmcraft-native-parameter-fields-20261009/report.json).

dev.56将旧cli.py原生转发纳入可信根及原生隔离；仅四种精确元数据查询兼容无编辑根，全部子进程过滤宿主环境。模型下载需独立维护标志及已存在的授权数据目录，进程仅可写该目录并使用网络出站。三项目标红灯转为六项通过，39项真实原生入口、缓存模型维护及实际沙箱越界／链接／监听拒绝通过。公开模型冷下载、实际28词识别／重开／SRT及十三项候选主要业务通过；新固定宿主及完整V1仍未验收。 [Evidence](docs/evidence/filmcraft56-raw-launcher-candidate-20261009/report.json).

dev.55补齐公开可执行文档的独立读写根与运行时目录参数，并在目录变量为空时停止；新增use、通用CLI、setup主要任务检查，固定插件72／源54的十三个独立复制技能取得业务任务证据。按既有重开合同修正界面选择夹具断言，原始失败和定向复验保留。宿主意图路由、完整权限、全命令及八项完整V1任务仍开放。 [Evidence](docs/evidence/filmcraft72-fixed-skill-tasks-20261009/report.json).

dev.54在完整命令与所属桌面执行中保留宿主提供的FILMCRAFT_DATA_DIR；显式模型缓存须处于可信读取根且受原生写保护，畸形／越界引用在安装、素材读取或输出创建前拒绝，临时截图仍写入独立授权目录。四项目标回归及现有只读缓存上的实际CLI Whisper推理通过，无需下载模型。完整权限、业务路由及全量命令验收仍开放。

公开工作流、完整命令执行和所属桌面执行要求独立提供真实读写根；原生子进程使用macOS系统沙箱，保护输入、技能代码与运行时缓存，所属桌面桥仅开放分配的本地端口。桌面与MCP共用授权临时目录以生成渲染帧。实际候选原生和签名桌面检查通过；完整FC-RL-002、固定宿主验收及八项V1任务仍开放。

开发版source52清理MCP／编辑子进程继承的宿主密钥、代理凭据与解释器注入，同时保留显式模型目录配置。新增经过测试的macOS目录隔离基础；公开工作流尚未接入根目录授权。[执行边界](docs/FilmCraft-Execution-Permissions.zh_CN.md)。

技能源dev.48为已登记普通媒体补齐安装/输出前的聚合素材问题清单；公开工作流失败保留原错误前缀，可返回alias/origin/reason，不泄露路径、不按文件名替代。完整FC-DM-001序列/HD/重关联验收另行完成。
[绑定版本的下载故障证据](docs/evidence/source47-download-error-candidate-20261009/acceptance.json)。离线220项中184通过、36项原生环境未运行；新技能源固定安装另行验收。

技能源 dev.47 修复 urllib 包装及嵌套包装的权限、磁盘满、只读文件系统、配额和证书错误误重试问题。全部13个独立安装器已同步；临时网络及408/429/5xx恢复仍有次数上限。源码与固定安装验收分开记录。

当前源 dev.46 默认锁定维护版 `0.2.0-craft.5`，修复真实VFR输入的PCM包采样时序；666条命令由新二进制重新采集，13技能同步。七类候选媒体场景及真实Whisper识别通过；公开冷安装、固定插件与完整V1另行验收。[维护版记录](docs/FilmCraft-PCM-Runtime.zh_CN.md)。

[分层发行检查](docs/FilmCraft-Release-Checks.zh_CN.md)：强制离线CI逐项记录原生环境缺口NOT_RUN，源码CI与安装／原生验收分开。

[解析后参数对象校验](docs/FilmCraft-Parameter-Container.zh_CN.md)：整体参数引用解析为非对象时，在依赖原生请求前结构化拒绝。

[命令目录身份修复](docs/FilmCraft-Catalog-Identity.zh_CN.md)：从锁定 CLI 重新采集，同步 13 技能的实际摘要并保留命令子集；固定插件验收另行记录。

## 能力快照候选

源码候选在依赖编辑前核对实际运行时身份、原生参数契约、模式及所需编解码器、字体或模型，成功和失败均保留能力证据。headless 代表任务、拥有进程的 bridge 保存重开及不兼容命令拒绝通过；固定发行与完整模式/命令验收仍开放。[能力合同](skills/filmcraft-use/references/capabilities.md) · [绑定证据](docs/evidence/filmcraft-capability-candidate-20261008.json)。

优化源码候选：已实现共享原生 tick 校验、意图路由语料及逐技能专项任务指南。固定快照和宿主实际路由仍需分别验收。[候选证据](docs/evidence/filmcraft-optimization-candidate-20261008.json)。

分段首用指南已根据固定 Film40／Effect38／Art117 的原生验收更新：覆盖 HD 全帧、返工、恢复和迁移。新指南快照的插件安装验收另行记录。[证据](docs/evidence/craft-fixed-segmented-hd-refresh-20261008.json)。

已有素材与剪辑需求进入，交付可重开的 `.fcproj`、素材清单、预览和成片。

当前技能源快照：`0.1.0-dev.60`；场景安装示例使用当前技能自身目录。既有固定插件证据保留原身份，新插件安装另行验证。

已验证首次使用平台：macOS arm64、Python 3.11+。固定运行时安装在用户数据目录，技能文件保留在宿主加载目录。当前为开发版本；完整首版验收及通用 Skills CLI 实际安装仍未完成。

历史craft.3证据：维护运行时 `0.2.0-craft.3` 已公开发布：音轨保留源采样 ticks，视频帧对齐保持。源技能实际冷安装通过两种非整帧音频尾部、增益另存、序列移动与原首版短片任务；坏素材在安装／恢复目录写入前被拒绝，开始编辑后的失败仍保留诊断。固定 Film／Art 分发验收待执行。[绑定证据](docs/evidence/audio-sample-public-first-use-20261007.json)。

维护运行时`0.2.0-craft.4`已发布，独立单技能公开CLI/模型冷安装及真实识别45.826秒通过：原生`--data-dir`、28词识别、重开/SRT及音视频／原工程保全。公开二进制重新采集666条命令，参数合同保持，源码回归130项执行通过／34项跳过。固定插件／Art仍待验收。[ASR证据](docs/evidence/whisper-candidate-inference-20261008.json)。

## 首次使用

在宿主中调用 **`filmcraft-use`**。直接使用 CLI 时，将 `SKILL_DIR` 设为宿主实际加载的 `SKILL.md` 所在绝对目录；可能位于用户／项目 `.agents/skills`、插件内部或宿主缓存，以实际路径为准。以下入口在调用前安装并核验固定运行时。

<!-- CRAFT_FIRST_USE_START -->
```bash
: "${SKILL_DIR:?Set to the actual loaded skill directory}"
python3 -I -B "$SKILL_DIR/scripts/cli.py" -- --version
python3 -I -B "$SKILL_DIR/scripts/cli.py" -- commands --json
```
<!-- CRAFT_FIRST_USE_END -->

实际制作、所需输入、原生工程和局部修改参见[可编辑工作流](skills/filmcraft-use/references/workflow.md)。[安装与技能入口](skills/filmcraft-use/SKILL.md) · [版本绑定历史](RELEASE-HISTORY.zh-CN.md)。版本与命令查询验证安装和发现，不代表创作完成。

[首次使用入口证据](docs/evidence/craft-readme-first-use-navigation-20261007.json)。

固定安装路径验收：独立技能及 Art 混合工作流在含中文和空格的路径下，通过原生创建与重开、定点返工及导出；Art 另验证移动交付包。技能与运行时身份保持不变。该结果仅覆盖 macOS arm64 的本次首次使用场景。 [路径验收证据](docs/evidence/craft-fixed-unicode-path-first-use-20261007.json).

固定发行前的历史源码候选：结构损坏的 runtime／Node 锁在写运行时目录或下载前返回本地恢复诊断。五项候选原生首次使用通过；发布插件快照保持不变，新不可变发行安装需另行验收。 [锁诊断候选](docs/FilmCraft-Lock-Shape-Architecture.zh_CN.md).

---

固定原生首次安装与完整命令恢复验收通过：新版五插件58技能逐项独立冷安装，十个Art技能分别安装四领域；四个原生下载半包SSL EOF恢复、72个原生保存后故障、四个健康命令返工及混合HD返工／恢复／移动包通过，全部安装摘要保全。仅关闭领域2.10／8.11与Art4.10；2639条命令逐项、GUI、模型、通用Skills CLI及完整V1仍开放。 [版本及证据](docs/evidence/codex-native-download-first-use-20261007.json).

固定发布前的候选记录：原生下载恢复候选：最多三次只读重试并丢弃半包；此前固定版本冷安装遇到SSL EOF失败，修复后的固定安装验收仍开放。

历史发行记录：当前独立技能源：`0.1.0-dev.19`；固定原生命令网关首用已通过，全量逐命令／GUI／模型／完整V1仍开放。

当前固定失败暂存验收：插件 dev.18、独立技能源 dev.16。全部58项独立CLI冷启动、24个原暂存原生故障案例及37原生场景＋6合同检查通过；Art77领域包升级仍开放。[证据](docs/evidence/codex-failed-stage-first-use-20261007.json)。

固定领域客户端首用复验：Film 插件 dev.16／技能源 dev.15，Effect／Photo／Vector 插件 dev.15／技能源 dev.14。隔离 Codex 发现58项零错误；实际安装副本24类保存后故障、四个健康公开工作流和已发布 Art 引擎＋安装后 Vector 客户端六类故障通过，全部58项安装摘要保全。Art dev.75 内置旧领域分发包尚需升级，全量命令／GUI／模型验收仍开放。[版本绑定证据](docs/evidence/codex-public-workflow-session-first-use-20261007.json)。
独立技能源元数据：`0.1.0-dev.15`。公开工作流 Session 结构检查已纳入此源码；固定插件／Art 分发及实际安装验收另行记录。
先前固定版本协议故障首用复验通过：48个独立技能源共288例，实际安装副本24例及四领域健康返工通过；58项安装摘要保持一致。验收范围与固定标签见 [协议故障验收记录](docs/evidence/codex-protocol-fault-first-use-20261007.json)。全量逐命令／GUI验收以及Art领域包升级仍开放。

协议故障修复候选：本领域11项技能逐个单独复制、空运行时公开安装后，原生保存成功再注入六种坏回复全部通过（66例，零跳过）。不重放、未知回执、工程重开与交付／技能保全均已检查。[证据](docs/evidence/protocol-fault-first-use-20261007.json)。固定安装副本与Art领域包升级仍为独立门禁。

固定插件 0.1.0-dev.14／技能源 0.1.0-dev.13 已通过安装后的返工门禁：隔离 Codex 发现全部58项技能零加载错误，本领域安装技能从空运行时直接执行文档创建／返工计划、保存重开与非目标保全。全部58项安装摘要不变，当前固定发行CI通过。[固定返工证据](docs/evidence/codex-complete-command-revision-first-use-20261007.json)。全量命令／GUI／模型验收保持开放。

本领域 11 个技能逐个单独复制、从各自空运行时公开安装后，配套返工计划全部通过（67.161 秒，零跳过）。[返工证据](docs/evidence/complete-command-revision-first-use-20261007.json)。更新快照的真实固定宿主安装另设门禁。

完整命令入口补充了配套的创建／返工 JSON 示例、重新打开后的显式选择前置条件，以及原生保存重开、非目标对象与像素检查。每个独立技能均包含两个可执行计划。[调用指南](skills/filmcraft-use/references/command-usage.md#7-可执行局部返工--executable-targeted-revision)。全量逐命令及 GUI 验收保持开放。

先前固定 Codex 快照首用通过：五插件／58 技能发现、58 项安装技能分别空运行时公开安装、四领域完整命令代表样例、Art HD 返工／恢复／移动包、安装摘要保全与固定发行 CI。[证据](docs/evidence/codex-complete-command-first-use-20261007.json)。这是有范围的原生验收；通用 Skills CLI 安装和全命令／GUI 验收仍开放。

## 完整原生命令入口

全部 11 项独立技能分别从空运行时使用公开锁定 CLI 附件安装，随后完成创建、保存重开、领域参数及渲染检查（72.162 秒，零跳过）。[逐技能冷首用证据](docs/evidence/complete-commands-cold-first-use-20261007.json)。本轮覆盖每项技能的完整命令代表样例；全命令／GUI 和实际宿主安装另行验收。

已发布开发快照：skills dev.12 / plugin dev.13；固定宿主首用代表门禁通过。

666 条命令现在均有逐项参数说明、技能归属与同会话调用入口。运行 `commands.py list / describe / check / run`；原生状态按实时 enabled 校验。旧工作流的 17 项交付合同保留。GUI 命令需显式 bridge，命令目录覆盖不代表全量验收。

[架构与操作指南](docs/FilmCraft-Complete-Commands-Architecture.zh_CN.md) · [逐项参考](skills/filmcraft-use/references/command-reference.md) · [可运行示例](skills/filmcraft-use/examples/commands-advanced.json)

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

技能源 dev.10 将运动／LUT 工作流纳入十一项独立技能，原生 CLI 保持 0.2.0-craft.2。固定插件安装验收单独记录。

固定 Film dev.11／技能源 dev.10 安装后验收通过：隔离 Codex 发现 58 项技能零错误，Film 十一项分别空运行时冷启动通过；安装后的运动／LUT、音轨增益和序列场景三项通过、零跳过。全部 58 安装摘要保全。新 Art LUT 运行时发行与完整首版仍开放。 [Evidence](docs/evidence/codex-filmcraft11-motion-lut-first-use-20261006.json).

工作区分段素材消费候选可校验 Effect 检查点、收集连续帧并保留来源摘要。固定发布、完整 1080p 长片头和 Art 集成仍待完成。[架构](docs/FilmCraft-Segmented-Assets-Architecture.zh_CN.md)。

当前源码 HD 分段候选通过 1080p／24 fps／五秒及动态标题核验；固定安装版与 Art HD 仍待完成。[架构与证据](docs/FilmCraft-HD-Sequence-Architecture.zh_CN.md)。

技能源 0.1.0-dev.11 包含有界分段工作流与 HD RGBA 校验优化。原生 CLI 不变；对应固定插件及 Art 安装版验收另行记录。

公开工作流回复检查已同步领域技能源候选，并通过有界原生／Art 协议验证。新的固定领域和 Art 分发包仍待发行与实际安装验收。[候选架构](docs/FilmCraft-Complete-Commands-Architecture.zh_CN.md) · [证据](docs/evidence/public-workflow-session-candidate-20261007.json)。

失败暂存候选：公开工作流保留原生暂存原路径、依赖摘要、最后提交请求与已完成回执，禁止重放；固定发行与安装副本验收仍开放。[架构](docs/FilmCraft-Failed-Stage-Architecture.zh_CN.md)。

固定领域失败暂存首用门禁已通过：Film插件18／源16，其他领域插件17／源15；五插件58技能发现零错误，全部58项独立空运行时CLI冷启动通过（417.646秒），实际安装副本24个真实保存后故障直接重开产品保留的原工程及依赖，四个健康创作／返工通过。全部安装摘要和16项固定插件CI保持通过；源仓未提供CI运行，仅有本地回归。只关闭领域OpenSpec3.12；Art77内置旧领域源，4.9升级和完整V1仍开放。 [Evidence](docs/evidence/codex-failed-stage-first-use-20261007.json).

固定安装场景矩阵通过37个原生场景及6个合同检查，零跳过。Photo测试已从安装后的技能锁读取维护版原生版本，CLI与安装技能未修改。 [Evidence](docs/evidence/codex-failed-stage-first-use-20261007.json).


完整命令内层JSON修复候选：非有限值、溢出和重复键在绑定返回值前记录unknown，真实保存后九类故障与原工程重开通过。这是候选技能源证据，固定发布与实际安装复验尚未完成；逐命令／GUI门禁仍开放。

命令计划 JSON 源候选：重复键在安装和创建输出前被拒绝，全部 13 个领域技能的独立副本拒绝测试与有效计划校验通过，3 项专项测试通过。固定插件发布和安装后复验仍为 NOT_RUN。[证据](docs/evidence/command-plan-json-candidate-20261007.json)。

严格计划解析的固定安装复验通过：64 个 CLI 探测、54 个独立安装领域技能的 324 次重复键拒绝、54 次有效计划结构检查，以及四领域空缓存原生保存／重开／渲染实例通过；执行后全部 64 个安装技能摘要不变。仅关闭本次修复的发布门禁；通用 Skills CLI、Art 领域包升级、全部命令上下文和完整首版仍开放。[证据](docs/evidence/command-plan-json-fixed-first-use-20261007.json)。

原生 Whisper 自动识别仍在候选构建与真实模型验收阶段，固定安装锁保持原版本；目录隔离修复与发布门禁见 [原生语音识别架构](docs/FilmCraft-Native-ASR-Architecture.zh_CN.md)。

[Whisper 候选识别证据](docs/evidence/whisper-candidate-inference-20261008.json)：真实识别28词，本次样例参考词覆盖率1.0；使用显式环境目录，原生工程/SRT与源工程保留通过。原生 `--data-dir`、公开安装和固定插件/Art 仍需分别验收。

目录修复候选的独立技能首用39.339秒通过：空CLI/模型缓存、`--data-dir`固定模型下载、真实识别、原生重开/SRT及音视频保全。公开运行时和固定插件/Art安装仍待验收；上方证据绑定候选摘要。

源33最终验证：13个分别空运行时安装67.272秒、当前技能字节的公开ASR50.350秒、10项原生场景89.158秒及实际高级命令网关创建／重开／渲染通过，666条参数合同保持。固定Film／Art发布及宿主验收仍开放。

四域共六个场景目录示例已修正；本包运行时身份与每个随附运行时锁一致。原生CLI制品保持原摘要。

新场景自身目录已通过固定安装复验；64项宿主身份匹配。完整V1仍开放。 [Evidence / 证据](https://github.com/full-aigc-plugins/filmcraft-plugin/blob/main/docs/evidence/craft-scenario-paths-fixed-first-use-20261008.json).

独立安装依赖边界：当前摘要一致的冷安装记录与 128 项新固定副本安装器／CLI 失败检查验收四领域 SK-002。Art 与通用 Skills CLI 安装继续开放。[设计与证据](docs/Craft-Independent-Setup-Boundary-Architecture.zh_CN.md)。

当前固定协议引用发行矩阵（Film／Effect dev.37、Photo dev.36、Vector dev.34、Art dev.107）已通过隔离 Codex 安装／发现 64 项技能、16 项实际安装所有者文件摘要核对，以及五个全新领域缓存下的 64 项独立公开 CLI 探测。原生场景证据仅对字节一致的技能复用，完整首版仍开放。[固定发行证据](docs/evidence/craft-protocol-authority-fixed-first-use-20261008.json)。

小尺寸英文字幕模板按1080行归一修正字号；每项独立技能自含画面尺寸换算、预览及短配音源范围指引。源码原生验证与固定插件首用分别验收。[说明与证据](docs/Caption-Size-First-Use.zh_CN.md)。

固定 Film41/source38 与 Art118/source90 首用通过：64项安装身份一致；Film13和Art10分别独立冷安装，41项未变技能仅复用摘要匹配的历史冷安装证据。新Art安装副本通过1080p／24fps／120帧混合创建、Logo依赖返工、坏帧恢复及五子工程迁移；Film通过移动工程文字返工与关键帧保全。完整V1仍开放。 [Evidence](docs/evidence/craft-art118-segment-guide-fixed-first-use-20261008.json).

受控 Harness 可通过内部 FILMCRAFT_EXECUTION_CONTEXT 关联 taskId、attemptId、技能源提交和内容摘要；非法上下文在安装和写入前拒绝。输出执行 v1 增加可选 context，独立调用省略时不补造身份。此信息不是授权凭据，插件固定安装验收另行记录。

源42验证：4项上下文测试通过；全量212项，176通过、36项明确环境跳过；13个独立技能资源同步通过。[证据](docs/evidence/filmcraft-source42-execution-context-20261008.json)。固定插件安装单独验收。

Evidence: `docs/evidence/source48-asset-issues-candidate-20261009/acceptance.json`.

当前dev.49候选在原生裁切前拒绝显式越界源范围，避免静默钳制被误判为交付成功；非法／溢出／非整数源ticks返回安全clipTiming及十进制字符串片段ID。失败暂存保留单独摘要诊断，不扩充公共失败回执schema。候选目标拒绝和真实裁切／移动保全通过；新固定安装及完整FC-DM-002仍待验收。

[版本绑定候选检查](docs/evidence/source49-timeline-candidate-20261009/report.json)：195项通过、36项原生环境未运行；新固定宿主验收仍待完成。

dev.49发布后仅修正测试：缺音轨首用核验现有craft-failed-stage/v1、原暂存工程文件摘要及重复不覆盖诊断。固定插件66/source49生产字节保持不变；修正后实际安装首用通过，源码回归195通过／36项原生环境未运行。[检查](docs/evidence/source49-postrelease-missing-audio-test-20261009/report.json)。

dev.50拒绝工作流顶层及操作对象中的未定义字段，在素材读取／安装／输出创建前返回固定代码，不回显字段名或值。固定插件66/source49曾将测试metadata中的自建假凭据标记写入plan.json；26项逐技能公开拒绝及合法原生另存回归通过。本修复不等于原生参数、宿主秘密引用和根目录权限已验收；新插件固定安装另行验证。 [Evidence / 证据](docs/evidence/source50-plan-field-boundary-20261009/summary.json)。

技能源dev.51在素材读取与输出前拒绝领域包装操作的未定义参数及移动项元数据，保留合法创作文本；完整注册表原生参数、可信根与宿主秘密引用仍开放，新固定安装待验。

真实签名桌面已发现显式缓存和已安装 tiny 模型，但该官方桌面构建报告语音识别不可用，推理被拒绝；CLI 真实识别 28 个词且模型摘要不变。[证据](docs/evidence/source54-readonly-model-20261009/report.json)。

连续编辑新增公开任务入口 `task_session.py`：保持一个前台句柄、同一MCP及可选签名桌面，逐计划回执，失败后停止而不重启。参见[任务会话](skills/filmcraft-use/references/task-session.md)。固定发布验收另行记录。
