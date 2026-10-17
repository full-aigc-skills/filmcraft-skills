"""发现场景技能的精确字幕回归，直接执行配套脚本测试。"""
import importlib.util
from pathlib import Path
path=Path(__file__).resolve().parents[1]/'scripts/test_subtitle_sync.py'
spec=importlib.util.spec_from_file_location('subtitle_script_tests',path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
SubtitleSync=module.SubtitleSync
