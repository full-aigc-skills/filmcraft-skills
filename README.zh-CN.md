# FilmCraft 独立技能

当前正在实现，尚未完成插件发布验收。

`filmcraft-use` 自带 Python 3.11+ 安装器，固定官方 macOS arm64 CLI 制品，校验压缩包和二进制，保留许可证，原子安装新版本，复用完整的已有版本。技能目录可独立复制，不依赖兄弟技能或插件私有路径。

运行测试：`python3 -m unittest discover -s tests -v`。完整创作流程和宿主验收仍待完成。

规范和任务：[FilmCraft 插件 OpenSpec](https://github.com/full-aigc-plugins/filmcraft-plugin/tree/main/openspec/changes/establish-v1-plugin)。

[English](README.md)

原生剪辑入口支持素材导入与收集、整数 ticks 编排、独立音频、字幕样式、工程重开、H.264 导出，以及移动交付包后的摘要核对和局部修订。参见[工作流说明](skills/filmcraft-use/references/workflow.md)。入口只依赖 Python 标准库与自动安装的 CLI；真实验收测试额外需要 ffmpeg、ffprobe 和 Pillow。
