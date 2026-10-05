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
